// Dibuja una cancha según el deporte. El color de fondo indica el estado; la imagen no lleva texto.
const ESTADOS = {
  uso:       { color: '#2f9e5b', nombre: 'En uso' },
  fuera:     { color: '#c8473d', nombre: 'Fuera de servicio' },
  reservada: { color: '#3b6fd4', nombre: 'Reservada' },
  libre:     { color: '#9aa1a8', nombre: 'Disponible' },
};
const L = 'stroke="rgba(255,255,255,.92)" fill="none" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"';
let uid = 0;

function fondo(w, h, color, rayas, id) {
  let s = `<rect width="${w}" height="${h}" rx="10" fill="${color}"/>`;
  if (rayas) {
    const n = 10, bw = w / n;
    for (let i = 0; i < n; i += 2) s += `<rect x="${i*bw}" y="0" width="${bw}" height="${h}" fill="rgba(255,255,255,.07)"/>`;
  }
  return s;
}

function futbol(estado, grande) {
  const w = grande ? 440 : 400, h = grande ? 260 : 200, m = 14;
  const cy = h / 2, ax = grande ? 70 : 52, ah = grande ? 140 : 90, sx = grande ? 26 : 0, sh = 70;
  let s = fondo(w, h, ESTADOS[estado].color, true);
  s += `<rect x="${m}" y="${m}" width="${w-2*m}" height="${h-2*m}" ${L}/>`;
  s += `<line x1="${w/2}" y1="${m}" x2="${w/2}" y2="${h-m}" ${L}/>`;
  s += `<circle cx="${w/2}" cy="${cy}" r="${grande?36:30}" ${L}/><circle cx="${w/2}" cy="${cy}" r="3" fill="#fff"/>`;
  for (const lado of [0, 1]) {
    const x0 = lado ? w - m - ax : m;
    s += `<rect x="${x0}" y="${cy-ah/2}" width="${ax}" height="${ah}" ${L}/>`;
    if (sx) s += `<rect x="${lado ? w-m-sx : m}" y="${cy-sh/2}" width="${sx}" height="${sh}" ${L}/>`;
    const px = lado ? w - m - ax*0.7 : m + ax*0.7;
    s += `<circle cx="${px}" cy="${cy}" r="2.6" fill="#fff"/>`;
    s += `<rect x="${lado ? w-m : m-8}" y="${cy-18}" width="8" height="36" ${L}/>`;
  }
  return [w, h, s];
}

function baloncesto(estado) {
  const w = 420, h = 225, m = 14, cy = h / 2;
  let s = fondo(w, h, ESTADOS[estado].color, false);
  s += `<rect x="${m-6}" y="${m-6}" width="${w-2*m+12}" height="${h-2*m+12}" rx="6" fill="rgba(0,0,0,.08)"/>`;
  s += `<rect x="${m}" y="${m}" width="${w-2*m}" height="${h-2*m}" ${L}/>`;
  s += `<line x1="${w/2}" y1="${m}" x2="${w/2}" y2="${h-m}" ${L}/><circle cx="${w/2}" cy="${cy}" r="26" ${L}/>`;
  for (const lado of [0, 1]) {
    const t = lado ? `transform="translate(${w},0) scale(-1,1)"` : '';
    s += `<g ${t}>
      <rect x="${m}" y="${cy-30}" width="82" height="60" fill="rgba(255,255,255,.12)" ${L}/>
      <circle cx="${m+82}" cy="${cy}" r="30" ${L}/>
      <path d="M${m},${m+18} H${m+48} A 98 98 0 0 1 ${m+48} ${h-m-18} H${m}" ${L}/>
      <line x1="${m+12}" y1="${cy-14}" x2="${m+12}" y2="${cy+14}" ${L}/>
      <circle cx="${m+20}" cy="${cy}" r="6" ${L}/></g>`;
  }
  return [w, h, s];
}

function voleibol(estado) {
  const w = 380, h = 200, m = 22, cy = h / 2;
  let s = fondo(w, h, ESTADOS[estado].color, false);
  s += `<rect x="${m}" y="${m}" width="${w-2*m}" height="${h-2*m}" fill="rgba(255,255,255,.08)" ${L}/>`;
  s += `<line x1="${w/2-56}" y1="${m}" x2="${w/2-56}" y2="${h-m}" ${L}/><line x1="${w/2+56}" y1="${m}" x2="${w/2+56}" y2="${h-m}" ${L}/>`;
  s += `<line x1="${w/2}" y1="${m-12}" x2="${w/2}" y2="${h-m+12}" stroke="#fff" stroke-width="5" stroke-linecap="round"/>`;
  s += `<circle cx="${w/2}" cy="${m-12}" r="4" fill="#fff"/><circle cx="${w/2}" cy="${h-m+12}" r="4" fill="#fff"/>`;
  return [w, h, s];
}

function tenis(estado) {
  const w = 476, h = 230, mx = 22, my = 18, cy = h / 2;
  let s = fondo(w, h, ESTADOS[estado].color, false);
  s += `<rect x="${mx}" y="${my}" width="${w-2*mx}" height="${h-2*my}" fill="rgba(255,255,255,.10)" ${L}/>`;
  const sy1 = my + 25, sy2 = h - my - 25, sv = 120;
  s += `<line x1="${mx}" y1="${sy1}" x2="${w-mx}" y2="${sy1}" ${L}/><line x1="${mx}" y1="${sy2}" x2="${w-mx}" y2="${sy2}" ${L}/>`;
  s += `<line x1="${w/2-sv}" y1="${sy1}" x2="${w/2-sv}" y2="${sy2}" ${L}/><line x1="${w/2+sv}" y1="${sy1}" x2="${w/2+sv}" y2="${sy2}" ${L}/>`;
  s += `<line x1="${w/2-sv}" y1="${cy}" x2="${w/2+sv}" y2="${cy}" ${L}/>`;
  s += `<line x1="${mx}" y1="${cy}" x2="${mx+8}" y2="${cy}" ${L}/><line x1="${w-mx-8}" y1="${cy}" x2="${w-mx}" y2="${cy}" ${L}/>`;
  s += `<line x1="${w/2}" y1="${my-10}" x2="${w/2}" y2="${h-my+10}" stroke="#fff" stroke-width="5" stroke-linecap="round"/>`;
  return [w, h, s];
}

function padel(estado) {
  const w = 400, h = 200, m = 16, cy = h / 2, sv = 139;
  let s = fondo(w, h, ESTADOS[estado].color, false);
  s += `<rect x="${m}" y="${m}" width="${w-2*m}" height="${h-2*m}" ${L}/>`;
  // paredes de vidrio en los fondos y esquinas
  const vid = 'stroke="rgba(255,255,255,.55)" stroke-width="7" fill="none" stroke-linecap="round"';
  s += `<path d="M${m+60},${m} H${m} V${h-m} H${m+60}" ${vid}/><path d="M${w-m-60},${m} H${w-m} V${h-m} H${w-m-60}" ${vid}/>`;
  s += `<line x1="${w/2-sv}" y1="${m}" x2="${w/2-sv}" y2="${h-m}" ${L}/><line x1="${w/2+sv}" y1="${m}" x2="${w/2+sv}" y2="${h-m}" ${L}/>`;
  s += `<line x1="${w/2-sv}" y1="${cy}" x2="${w/2+sv}" y2="${cy}" ${L}/>`;
  s += `<line x1="${w/2}" y1="${m-8}" x2="${w/2}" y2="${h-m+8}" stroke="#fff" stroke-width="5" stroke-linecap="round"/>`;
  return [w, h, s];
}

function cancha(deporte, estado) {
  const f = { futbol5: e => futbol(e, false), futbol8: e => futbol(e, true), baloncesto, voleibol, tenis, padel }[deporte];
  const [w, h, s] = f(estado);
  return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Cancha de ${deporte}, ${ESTADOS[estado].nombre}" xmlns="http://www.w3.org/2000/svg">${s}</svg>`;
}

// Coloca una cancha dentro del plano en (x, y) con un ancho dado
function canchaEn(deporte, estado, x, y, ancho) {
  const f = { futbol5: e => futbol(e, false), futbol8: e => futbol(e, true), baloncesto, voleibol, tenis, padel }[deporte];
  const [w, h, s] = f(estado);
  const alto = ancho * h / w;
  return { svg: `<svg x="${x}" y="${y}" width="${ancho}" height="${alto}" viewBox="0 0 ${w} ${h}">${s}</svg>`, alto };
}

const COLOR_TEXTO = { uso: '#23794a', reservada: '#2c58ad', libre: '#5b6168', fuera: '#a8362d' };

function arbolesMapa() {
  let semilla = 7; const r = () => (semilla = (semilla * 9301 + 49297) % 233280) / 233280;
  const cajas = [[140,40,930,252],[170,262,860,28],[50,290,445,280],[720,282,430,330],[580,250,40,560],[440,400,320,40],
                 [740,640,330,110],[80,610,350,140],[560,380,80,80],[430,672,180,30],[600,672,170,30]];
  const libre = (x, y) => !cajas.some(([a,b,c,d]) => x > a-14 && x < a+c+14 && y > b-14 && y < b+d+14) && x > 40 && x < 1160 && y > 40 && y < 770;
  let s = '', n = 0, i = 0;
  while (n < 120 && i++ < 4000) {
    const x = 30 + r()*1140, y = 30 + r()*740;
    if (!libre(x, y)) continue;
    const t = 9 + r()*7;
    s += `<circle cx="${x+2}" cy="${y+3}" r="${t}" fill="rgba(0,0,0,.10)"/><circle cx="${x}" cy="${y}" r="${t}" fill="${r()>.5?'#5f9b4c':'#6fab58'}"/><circle cx="${x-t*.3}" cy="${y-t*.3}" r="${t*.45}" fill="rgba(255,255,255,.15)"/>`;
    n++;
  }
  return s;
}

function sendero(d) {
  return `<path d="${d}" fill="none" stroke="#d6c38f" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="${d}" fill="none" stroke="#ecdfb6" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="${d}" fill="none" stroke="rgba(255,255,255,.7)" stroke-width="1.6" stroke-dasharray="6 9"/>`;
}

function edificio(x, y, w, h, titulo, extra) {
  return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="12" fill="rgba(0,0,0,.18)" transform="translate(6,8)"/>
  <rect x="${x}" y="${y}" width="${w}" height="${h}" rx="12" fill="#f4f2ec" stroke="#39463d" stroke-width="5"/>
  <rect x="${x}" y="${y}" width="${w}" height="34" rx="12" fill="#39463d"/><rect x="${x}" y="${y+20}" width="${w}" height="14" fill="#39463d"/>
  <text x="${x+20}" y="${y+23}" font-size="14" font-weight="800" fill="#fff" letter-spacing="1.4">${titulo}</text>${extra || ''}`;
}

// Dibuja el plano completo del complejo con las canchas que vienen de la base de datos
function dibujarMapa(contenedor, canchas) {
  let s = `<svg class="plano" viewBox="0 0 1200 800" xmlns="http://www.w3.org/2000/svg">
  <defs><filter id="sombra" x="-5%" y="-5%" width="115%" height="120%"><feDropShadow dx="0" dy="3" stdDeviation="3" flood-opacity=".22"/></filter></defs>
  <rect width="1200" height="800" fill="#c9cdc5"/><rect x="22" y="22" width="1156" height="756" rx="26" fill="#cfe3b6"/>`;
  s += `<rect x="86" y="616" width="340" height="128" rx="10" fill="#b8bcb4"/>`;
  for (let i = 0; i < 9; i++) s += `<line x1="${110+i*36}" y1="626" x2="${110+i*36}" y2="666" stroke="#fff" stroke-width="2"/><line x1="${110+i*36}" y1="694" x2="${110+i*36}" y2="734" stroke="#fff" stroke-width="2"/>`;
  s += `<rect x="236" y="660" width="34" height="34" rx="7" fill="#2f5aa8"/><text x="253" y="684" text-anchor="middle" font-size="20" font-weight="800" fill="#fff">P</text>`;
  s += sendero('M600,790 V470') + sendero('M600,375 V262') + sendero('M556,420 H482') + sendero('M644,420 H722')
     + sendero('M600,690 H760') + sendero('M600,690 H432') + sendero('M188,276 H1012');
  s += `<circle cx="600" cy="420" r="52" fill="#d6c38f"/><circle cx="600" cy="420" r="47" fill="#ecdfb6"/><circle cx="600" cy="420" r="20" fill="#8cc4e0" stroke="#fff" stroke-width="3"/>`;
  s += arbolesMapa();
  s += `<rect x="150" y="48" width="900" height="208" rx="14" fill="#bcd8a3" stroke="#6c7a63" stroke-width="2.5" stroke-dasharray="9 7"/>
  <rect x="584" y="249" width="32" height="14" rx="3" fill="#ecdfb6" stroke="#6c7a63" stroke-width="2"/>
  <text x="166" y="40" font-size="13" font-weight="800" fill="#2a3b2e" letter-spacing="1.5">ZONA DE FÚTBOL</text>`;
  s += edificio(62, 302, 426, 258, 'COLISEO CUBIERTO', `<rect x="480" y="404" width="12" height="32" rx="3" fill="#d9a321"/>`);
  s += `<rect x="726" y="290" width="424" height="314" rx="14" fill="#bcd8a3" stroke="#6c7a63" stroke-width="2.5" stroke-dasharray="9 7"/>
  <rect x="719" y="404" width="14" height="32" rx="3" fill="#ecdfb6" stroke="#6c7a63" stroke-width="2"/>
  <text x="742" y="282" font-size="13" font-weight="800" fill="#2a3b2e" letter-spacing="1.5">ZONA DE RAQUETA</text>`;
  s += edificio(760, 646, 300, 92, 'EDIFICIO DE SERVICIOS',
    `<text x="780" y="704" font-size="13" font-weight="600" fill="#39463d">Recepción y pagos · Vestieres</text>
     <text x="780" y="724" font-size="13" font-weight="600" fill="#39463d">Cafetería · Baños</text>
     <rect x="752" y="674" width="12" height="32" rx="3" fill="#d9a321"/>`);
  for (const c of canchas) {
    const k = canchaEn(c.deporte, c.estado, c.x, c.y, c.ancho);
    const ancho = Math.max(c.ancho, 150), x0 = c.x + (c.ancho - ancho) / 2, y0 = c.y + k.alto + 6;
    s += `<a href="${c.url}" class="enlace-cancha"><title>${c.nombre}: ${c.texto}</title><g filter="url(#sombra)">${k.svg}</g>
      <rect x="${x0}" y="${y0}" width="${ancho}" height="40" rx="8" fill="#fff" stroke="rgba(0,0,0,.08)"/>
      <text x="${x0+10}" y="${y0+16}" font-size="12.5" font-weight="700" fill="#1a1a1a">${c.nombre}</text>
      <circle cx="${x0+14}" cy="${y0+29}" r="4" fill="${ESTADOS[c.estado].color}"/>
      <text x="${x0+23}" y="${y0+33}" font-size="11.5" font-weight="600" fill="${COLOR_TEXTO[c.estado]}">${c.texto}</text></a>`;
  }
  s += `<rect x="560" y="770" width="80" height="30" rx="8" fill="#d9a321"/><text x="600" y="790" text-anchor="middle" font-size="13" font-weight="800" fill="#3d2f08">ENTRADA</text>
  <g transform="translate(1130,80)"><circle r="22" fill="#fff" opacity=".85"/><path d="M0,-17 L6,0 L0,17 L-6,0Z" fill="#39463d"/><path d="M0,-17 L6,0 L-6,0Z" fill="#d9a321"/></g></svg>`;
  contenedor.innerHTML = s;
}
