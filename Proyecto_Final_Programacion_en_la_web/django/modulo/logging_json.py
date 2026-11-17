import json
import logging

# Campos extra que se pueden enviar con logger.info(..., extra={...})
CAMPOS_EXTRA = ('tipo', 'method', 'path', 'status', 'response_time_ms', 'user_id', 'rol', 'ip',
                'cancha', 'reserva', 'valor', 'medio_pago')


class FormatoJSON(logging.Formatter):
    """Escribe cada log como una línea JSON."""

    def format(self, record):
        datos = {
            'level': record.levelname,
            'service': 'multi-dust',
            'logger': record.name,
            'message': record.getMessage(),
        }
        for campo in CAMPOS_EXTRA:
            if hasattr(record, campo):
                datos[campo] = getattr(record, campo)
        if record.exc_info:
            datos['error'] = self.formatException(record.exc_info)
        return json.dumps(datos, ensure_ascii=False)
