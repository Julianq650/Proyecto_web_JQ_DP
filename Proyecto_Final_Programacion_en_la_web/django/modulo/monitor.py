"""Monitor de logs: consulta Elasticsearch y muestra los mensajes en vivo (solo administrador)."""
import datetime
import json
import urllib.error
import urllib.request

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from .permisos import solo_admin

APP, NGINX = 'app-logs-*', 'nginx-logs-*'
CAMPOS = ['@timestamp', 'level', 'tipo', 'message', 'rol', 'user_id', 'cancha', 'reserva', 'valor',
          'medio_pago', 'method', 'path', 'status', 'response_time_ms', 'ip']


def _buscar(indice, cuerpo):
    peticion = urllib.request.Request(
        f"{settings.ELASTICSEARCH_URL.rstrip('/')}/{indice}/_search?ignore_unavailable=true&allow_no_indices=true",
        data=json.dumps(cuerpo).encode(), headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(peticion, timeout=4) as r:
        return json.loads(r.read())


def _hora_local(iso):
    try:
        t = datetime.datetime.fromisoformat(iso.replace('Z', '+00:00'))
        return timezone.localtime(t).strftime('%H:%M:%S')
    except (ValueError, AttributeError):
        return ''


def _filtros(get):
    filtros = [{'range': {'@timestamp': {'gte': 'now-60m'}}}]
    for campo in ('level', 'rol', 'tipo'):
        if get.get(campo):
            filtros.append({'term': {campo: get[campo]}})
    if get.get('q'):
        filtros.append({'simple_query_string': {'query': get['q'], 'fields': ['message', 'cancha', 'reserva', 'user_id', 'path'],
                                                'default_operator': 'and'}})
    return filtros


@solo_admin
def monitor(request):
    return render(request, 'modulo/administracion/monitor.html', {'es_url': settings.ELASTICSEARCH_URL})


@solo_admin
def monitor_datos(request):
    ultima_hora = {'range': {'@timestamp': {'gte': 'now-60m'}}}
    try:
        resumen = _buscar(APP, {
            'size': 0, 'track_total_hits': True, 'query': {'bool': {'filter': [ultima_hora]}},
            'aggs': {
                'eventos': {'filter': {'term': {'tipo': 'evento'}}},
                'errores': {'filter': {'term': {'level': 'ERROR'}}},
                'fallidos': {'filter': {'match_phrase': {'message': 'Intento de inicio de sesión fallido'}}},
                'cobros': {'filter': {'match_phrase': {'message': 'Pago registrado'}}, 'aggs': {'total': {'sum': {'field': 'valor'}}}},
                'reservas': {'filter': {'match_phrase': {'message': 'Reserva'}}},
                'por_rol': {'terms': {'field': 'rol', 'size': 5}},
                'por_minuto': {
                    'date_histogram': {'field': '@timestamp', 'fixed_interval': '2m', 'min_doc_count': 0,
                                       'extended_bounds': {'min': 'now-60m', 'max': 'now'}},
                    'aggs': {'avisos': {'filter': {'term': {'level': 'WARNING'}}},
                             'errores': {'filter': {'term': {'level': 'ERROR'}}}}},
            }})
        web = _buscar(NGINX, {'size': 0, 'track_total_hits': True, 'query': {'bool': {'filter': [ultima_hora]}},
                              'aggs': {'codigos': {'terms': {'field': 'code', 'size': 8}}}})
        feed = _buscar(APP, {'size': 40, 'sort': [{'@timestamp': 'desc'}], '_source': CAMPOS,
                             'query': {'bool': {'filter': _filtros(request.GET)}}})
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        return JsonResponse({'ok': False, 'error': f'No se pudo consultar Elasticsearch en {settings.ELASTICSEARCH_URL} ({e.__class__.__name__}).'})

    a = resumen.get('aggregations', {})
    minutos = [{'hora': _hora_local(b.get('key_as_string', '')),
                'total': b['doc_count'], 'avisos': b['avisos']['doc_count'], 'errores': b['errores']['doc_count']}
               for b in a.get('por_minuto', {}).get('buckets', [])]
    mensajes = []
    for h in feed.get('hits', {}).get('hits', []):
        s = h.get('_source', {})
        s['hora'] = _hora_local(s.get('@timestamp', ''))
        s['indice'] = h.get('_index', '')
        mensajes.append(s)
    return JsonResponse({
        'ok': True,
        'kpis': {
            'total': resumen.get('hits', {}).get('total', {}).get('value', 0),
            'eventos': a.get('eventos', {}).get('doc_count', 0),
            'errores': a.get('errores', {}).get('doc_count', 0),
            'fallidos': a.get('fallidos', {}).get('doc_count', 0),
            'cobrado': int(a.get('cobros', {}).get('total', {}).get('value') or 0),
            'cobros': a.get('cobros', {}).get('doc_count', 0),
            'web': web.get('hits', {}).get('total', {}).get('value', 0),
        },
        'por_rol': [{'rol': b['key'], 'n': b['doc_count']} for b in a.get('por_rol', {}).get('buckets', [])],
        'codigos': sorted([{'code': b['key'], 'n': b['doc_count']} for b in web.get('aggregations', {}).get('codigos', {}).get('buckets', [])], key=lambda x: x['code']),
        'minutos': minutos,
        'mensajes': mensajes,
        'actualizado': timezone.localtime().strftime('%H:%M:%S'),
    })
