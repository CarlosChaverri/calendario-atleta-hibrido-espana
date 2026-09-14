/* Calendario Atleta Híbrido España - frontend sin build */
const NIVELES = {
  confirmada_web_oficial: { texto: 'Confirmada por web oficial', clase: 'n1' },
  confirmada_organizacion: { texto: 'Confirmada por la organización', clase: 'n2' },
  fecha_estimada: { texto: 'Fecha estimada', clase: 'n3' },
  por_verificar: { texto: 'Por verificar', clase: 'n4' },
};
const MOD = { medio_maraton: 'Media maratón', maraton: 'Maratón' };
const DIST = { medio_maraton: 21.097, maraton: 42.195 };
const MESES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
const COLORES = { medio_maraton: '#ff4d00', maraton: '#101418' };

let carreras = [], generado = null;
let mapa, capa, marcadores = new Map(), seleccionada = null;
let centroUsuario = null;

const $ = s => document.querySelector(s);
const estado = {
  modalidad: '', texto: '', ccaa: '', provincia: '', mes: '', nivel: '',
  precioMax: 120, soloPrecio: false, soloConfirmadas: false,
  ciudad: '', radio: 100, orden: 'fecha', bounds: true,
};

function fmtFecha(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return `${d} ${MESES[m-1]} ${y}`;
}
function mesClave(iso) { return iso.slice(0, 7); }
function mesTexto(clave) {
  const [y, m] = clave.split('-').map(Number);
  return `${MESES[m-1]} ${y}`;
}
function haystack(c) {
  return `${c.nombre} ${c.ciudad || ''} ${c.provincia || ''}`.toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g, '');
}
function distKm(a, b) {
  const R = 6371, rad = x => x * Math.PI / 180;
  const dLat = rad(b.lat - a.lat), dLon = rad(b.lng - a.lng);
  const h = Math.sin(dLat/2)**2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLon/2)**2;
  return 2 * R * Math.asin(Math.sqrt(h));
}
function precioTexto(c) {
  if (c.precio === 0) return 'gratis';
  if (c.precio != null) return `desde ${c.precio} €`;
  return null;
}

function pasaFiltros(c) {
  if (estado.modalidad && c.modalidad !== estado.modalidad) return false;
  if (estado.texto && !haystack(c).includes(estado.texto)) return false;
  if (estado.ccaa && c.ccaa !== estado.ccaa) return false;
  if (estado.provincia && c.provincia !== estado.provincia) return false;
  if (estado.mes && mesClave(c.fecha) !== estado.mes) return false;
  if (estado.nivel && c.nivel_validacion !== estado.nivel) return false;
  if (estado.soloConfirmadas && !c.fecha_confirmada) return false;
  if (estado.soloPrecio && c.precio == null) return false;
  if (estado.precioMax < 120 && c.precio != null && c.precio > estado.precioMax) return false;
  if (centroUsuario && c.lat && distKm(centroUsuario, c) > estado.radio) return false;
  if (centroUsuario && !c.lat) return false;
  return true;
}

function filtradas() {
  let out = carreras.filter(pasaFiltros);
  if (estado.bounds && mapa) {
    const b = mapa.getBounds();
    out = out.filter(c => c.lat && b.contains([c.lat, c.lng]));
  }
  const ord = estado.orden;
  out.sort((a, b) => {
    if (ord === 'precio') return (a.precio ?? 1e9) - (b.precio ?? 1e9) || a.fecha.localeCompare(b.fecha);
    if (ord === 'distancia') return DIST[a.modalidad] - DIST[b.modalidad] || a.fecha.localeCompare(b.fecha);
    if (ord === 'cercania' && centroUsuario)
      return distKm(centroUsuario, a) - distKm(centroUsuario, b);
    return a.fecha.localeCompare(b.fecha);
  });
  return out;
}

function badgeNivel(c) {
  const n = NIVELES[c.nivel_validacion];
  return `<span class="badge ${n.clase}"><span class="dot ${n.clase}"></span>${n.texto}</span>`;
}

function pintarMapa() {
  capa.clearLayers(); marcadores.clear();
  for (const c of carreras.filter(pasaFiltros)) {
    if (!c.lat) continue;
    const m = L.circleMarker([c.lat, c.lng], {
      radius: seleccionada === c.id ? 10 : 7,
      color: '#fff', weight: 1.5,
      fillColor: COLORES[c.modalidad], fillOpacity: seleccionada === c.id ? 1 : 0.85,
    });
    m.on('click', () => abrirFicha(c.id, false));
    m.bindTooltip(c.nombre, { direction: 'top', offset: [0, -6] });
    m.addTo(capa);
    marcadores.set(c.id, m);
  }
}

function pintarLista() {
  const out = filtradas();
  const totalFiltros = carreras.filter(pasaFiltros).length;
  $('#contador').textContent = out.length === totalFiltros
    ? `${out.length} ${out.length === 1 ? 'carrera' : 'carreras'}`
    : `${out.length} de ${totalFiltros} carreras en el mapa`;
  $('#lista-vacia').hidden = out.length > 0;
  const html = out.map(c => {
    const p = precioTexto(c);
    const lugar = [c.ciudad, c.provincia].filter(Boolean).join(', ');
    return `<article class="card${seleccionada === c.id ? ' seleccionada' : ''}" data-id="${c.id}">
      <div class="card-top"><h3>${c.nombre}</h3><span class="fecha">${fmtFecha(c.fecha)}</span></div>
      <div class="lugar">${lugar || c.ccaa || ''}${c.ubicacion_aproximada ? ' (ubicación aproximada)' : ''}</div>
      <div class="meta">
        <span class="badge mod">${MOD[c.modalidad]}</span>
        ${p ? `<span class="badge precio">${p}</span>` : ''}
        ${badgeNivel(c)}
      </div>
    </article>`;
  }).join('');
  $('#lista').innerHTML = html;
  document.querySelectorAll('.card').forEach(el =>
    el.addEventListener('click', () => abrirFicha(el.dataset.id, true)));
}

function abrirFicha(id, pan) {
  const c = carreras.find(x => x.id === id);
  if (!c) return;
  seleccionada = id;
  const n = NIVELES[c.nivel_validacion];
  const p = precioTexto(c);
  const lugar = [c.ciudad, c.provincia, c.ccaa].filter(Boolean).join(', ');
  $('#ficha-contenido').innerHTML = `
    <div class="f-mod">${MOD[c.modalidad]} · ${DIST[c.modalidad]} km</div>
    <h2>${c.nombre}</h2>
    <dl>
      <dt>Fecha</dt><dd>${fmtFecha(c.fecha)}${c.fecha_confirmada ? '' : ' (sin confirmar)'}</dd>
      <dt>Lugar</dt><dd>${lugar || 'no disponible'}${c.ubicacion_aproximada ? ' (aproximada)' : ''}</dd>
      <dt>Precio</dt><dd>${p || 'no disponible'}</dd>
      <dt>Validación</dt><dd>${badgeNivel(c)}</dd>
    </dl>
    ${c.web_estado === 'posible_cancelacion' ? '<div class="aviso">Su web oficial menciona una posible cancelación o aplazamiento. Compruébalo antes de planificar.</div>' : ''}
    ${c.web_estado === 'caida' ? '<div class="aviso">Su web oficial no responde en la última comprobación.</div>' : ''}
    <div class="acciones">
      ${c.web_oficial ? `<a class="btn" href="${c.web_oficial}" target="_blank" rel="noopener">Web oficial</a>` : ''}
      ${c.lat ? `<a class="btn sec" href="https://www.google.com/maps/search/?api=1&query=${c.lat},${c.lng}" target="_blank" rel="noopener">Cómo llegar</a>` : ''}
    </div>
    <div class="fuentes">Fuentes: ${c.fuentes.map(f => `<a href="${f.url}" target="_blank" rel="noopener">${f.nombre}</a>`).join(' · ')}<br>
    Última comprobación: ${fmtFecha(c.ultima_comprobacion)}</div>`;
  $('#ficha').hidden = false;
  pintarMapa(); pintarLista();
  if (pan && c.lat) mapa.setView([c.lat, c.lng], Math.max(mapa.getZoom(), 9), { animate: true });
}

function actualizar() { pintarMapa(); pintarLista(); }

function rellenarSelects() {
  const ccaas = [...new Set(carreras.map(c => c.ccaa).filter(Boolean))].sort();
  $('#f-ccaa').innerHTML = '<option value="">Comunidad autónoma</option>' + ccaas.map(x => `<option>${x}</option>`).join('');
  rellenarProvincias();
  const meses = [...new Set(carreras.map(c => mesClave(c.fecha)))].sort();
  $('#f-mes').innerHTML = '<option value="">Cualquier mes</option>' + meses.map(x => `<option value="${x}">${mesTexto(x)}</option>`).join('');
}
function rellenarProvincias() {
  const provs = [...new Set(carreras.filter(c => !estado.ccaa || c.ccaa === estado.ccaa)
    .map(c => c.provincia).filter(Boolean))].sort();
  $('#f-provincia').innerHTML = '<option value="">Provincia</option>' + provs.map(x => `<option>${x}</option>`).join('');
}

async function geocodificarCiudad(q) {
  const url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&countrycodes=es&q=' + encodeURIComponent(q);
  const r = await fetch(url, { headers: { 'Accept': 'application/json' } });
  const arr = await r.json();
  return arr[0] ? { lat: +arr[0].lat, lng: +arr[0].lon } : null;
}

function bindFiltros() {
  document.querySelectorAll('#f-modalidad button').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('#f-modalidad button').forEach(x => x.classList.remove('activo'));
    b.classList.add('activo');
    estado.modalidad = b.dataset.v; actualizar();
  }));
  let t;
  $('#f-texto').addEventListener('input', e => {
    clearTimeout(t);
    t = setTimeout(() => { estado.texto = e.target.value.trim().toLowerCase()
      .normalize('NFD').replace(/[̀-ͯ]/g, ''); actualizar(); }, 200);
  });
  $('#f-ccaa').addEventListener('change', e => { estado.ccaa = e.target.value; estado.provincia = ''; rellenarProvincias(); actualizar(); });
  $('#f-provincia').addEventListener('change', e => { estado.provincia = e.target.value; actualizar(); });
  $('#f-mes').addEventListener('change', e => { estado.mes = e.target.value; actualizar(); });
  $('#f-nivel').addEventListener('change', e => { estado.nivel = e.target.value; actualizar(); });
  $('#f-precio').addEventListener('input', e => {
    estado.precioMax = +e.target.value;
    $('#f-precio-v').textContent = estado.precioMax >= 120 ? 'sin límite' : estado.precioMax + ' €';
    actualizar();
  });
  $('#f-solo-precio').addEventListener('change', e => { estado.soloPrecio = e.target.checked; actualizar(); });
  $('#f-solo-confirmadas').addEventListener('change', e => { estado.soloConfirmadas = e.target.checked; actualizar(); });
  $('#f-radio').addEventListener('change', e => { estado.radio = +e.target.value; actualizar(); });
  $('#f-orden').addEventListener('change', e => { estado.orden = e.target.value; pintarLista(); });
  $('#f-bounds').addEventListener('change', e => { estado.bounds = e.target.checked; pintarLista(); });
  let t2;
  $('#f-ciudad').addEventListener('input', e => {
    clearTimeout(t2);
    const q = e.target.value.trim();
    t2 = setTimeout(async () => {
      if (q.length < 3) { centroUsuario = null; actualizar(); return; }
      const p = await geocodificarCiudad(q);
      if (p) { centroUsuario = p; mapa.setView([p.lat, p.lng], 8); actualizar(); }
    }, 600);
  });
  $('#f-limpiar').addEventListener('click', () => location.reload());
  $('#f-toggle').addEventListener('click', () => {
    const abierto = document.getElementById('filtros').classList.toggle('abierto');
    $('#f-toggle').textContent = abierto ? 'Ocultar filtros ▲' : 'Filtros ▼';
  });
  $('#ficha-cerrar').addEventListener('click', () => { $('#ficha').hidden = true; seleccionada = null; actualizar(); });
}

async function init() {
  const r = await fetch('data/races.json');
  const d = await r.json();
  carreras = d.carreras; generado = d.generado;
  const nHM = carreras.filter(c => c.modalidad === 'medio_maraton').length;
  const nM = carreras.length - nHM;
  $('#stats').textContent = `${nHM} medias maratones · ${nM} maratones`;
  $('#actualizado').textContent = 'Datos actualizados el ' + fmtFecha(generado.slice(0, 10)) +
    ' · se regeneran automáticamente cada 15 días.';
  mapa = L.map('mapa', { scrollWheelZoom: true }).setView([40.2, -3.5], 6);
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Esri, HERE, Garmin &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 16,
  }).addTo(mapa);
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 16,
  }).addTo(mapa);
  capa = L.layerGroup().addTo(mapa);
  mapa.on('moveend', () => { if (estado.bounds) pintarLista(); });
  rellenarSelects(); bindFiltros(); actualizar();
  const pts = carreras.filter(c => c.lat && c.lng > -9).map(c => [c.lat, c.lng]);
  if (pts.length) mapa.fitBounds(pts, { padding: [24, 24] });
  const q = new URLSearchParams(location.search);
  if (q.get('carrera')) abrirFicha(q.get('carrera'), false);
  if (q.get('modalidad')) {
    estado.modalidad = q.get('modalidad');
    document.querySelectorAll('#f-modalidad button').forEach(x =>
      x.classList.toggle('activo', x.dataset.v === estado.modalidad));
    actualizar();
  }
}
init();
