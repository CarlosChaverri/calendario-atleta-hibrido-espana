const $ = s => document.querySelector(s);
let carreras = [], markers = [], seleccionada = null;
const MOD = {
  '5k':'5K','10k':'10K',medio_maraton:'Media maratón',maraton:'Maratón',
  triatlon_sprint:'Triatlón sprint',triatlon_olimpico:'Triatlón olímpico',
  triatlon_media:'Triatlón media / 70.3',triatlon_larga:'Triatlón larga / Ironman',
  hyrox:'HYROX',hibrida:'Híbrida tipo HYROX',obstaculos:'Obstáculos / Spartan'
};
const GRUPO = { '5k':'running','10k':'running',medio_maraton:'running',maraton:'running',
  triatlon_sprint:'triatlon',triatlon_olimpico:'triatlon',triatlon_media:'triatlon',triatlon_larga:'triatlon',
  hyrox:'hibrido',hibrida:'hibrido',obstaculos:'obstaculos' };
const COLORES = {running:'#ff4d00',triatlon:'#087f8c',hibrido:'#7c3aed',obstaculos:'#a16207'};
const DIST = {'5k':'5 km','10k':'10 km',medio_maraton:'21,097 km',maraton:'42,195 km',
 triatlon_sprint:'Sprint',triatlon_olimpico:'Olímpica',triatlon_media:'Media distancia / 70.3',triatlon_larga:'Larga distancia / Ironman',
 hyrox:'Carrera funcional',hibrida:'Carrera funcional',obstaculos:'Distancia según evento'};
const ORDER = Object.keys(MOD);
const NIVELES = {
 confirmada_web_oficial:{txt:'Confirmada por web oficial',cl:'n1'},
 confirmada_organizacion:{txt:'Confirmada por la organización',cl:'n2'},
 fecha_estimada:{txt:'Fecha estimada',cl:'n3'},por_verificar:{txt:'Por verificar',cl:'n4'}
};
let estado={modalidad:'',texto:'',ccaa:'',provincia:'',mes:'',nivel:'',orden:'fecha',soloMapa:false};
const map=L.map('mapa',{zoomControl:false}).setView([40.1,-3.6],6);L.control.zoom({position:'bottomright'}).addTo(map);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap',maxZoom:18}).addTo(map);
const capa=L.layerGroup().addTo(map);
function norm(s){return (s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()}
function pasa(c){if(estado.modalidad&&c.modalidad!==estado.modalidad)return false;if(estado.texto&&!norm(c.nombre+' '+c.ciudad+' '+c.provincia).includes(norm(estado.texto)))return false;if(estado.ccaa&&c.ccaa!==estado.ccaa)return false;if(estado.provincia&&c.provincia!==estado.provincia)return false;if(estado.mes&&c.fecha.slice(5,7)!==estado.mes)return false;if(estado.nivel&&c.nivel_validacion!==estado.nivel)return false;return true}
function filtradas(){let out=carreras.filter(pasa);if(estado.soloMapa){const b=map.getBounds();out=out.filter(c=>c.lat&&b.contains([c.lat,c.lng]))}out.sort((a,b)=>estado.orden==='nombre'?a.nombre.localeCompare(b.nombre):estado.orden==='distancia'?ORDER.indexOf(a.modalidad)-ORDER.indexOf(b.modalidad)||a.fecha.localeCompare(b.fecha):a.fecha.localeCompare(b.fecha));return out}
function fecha(x){return new Date(x+'T12:00:00').toLocaleDateString('es-ES',{weekday:'short',day:'numeric',month:'short',year:'numeric'})}
function pintaMapa(){capa.clearLayers();markers=[];for(const c of carreras.filter(pasa)){if(!c.lat||!c.lng)continue;const m=L.circleMarker([c.lat,c.lng],{radius:seleccionada===c.id?9:6,color:'#fff',weight:1.5,fillColor:COLORES[GRUPO[c.modalidad]],fillOpacity:seleccionada===c.id?1:.86}).addTo(capa);m.bindTooltip(c.nombre);m.on('click',()=>abre(c));markers.push({id:c.id,m})}}
function pintaLista(){const out=filtradas(), total=carreras.filter(pasa).length;$('#contador').textContent=`${out.length} de ${total} eventos${estado.soloMapa?' en el mapa':''}`;$('#lista').innerHTML=out.length?out.map(c=>{const n=NIVELES[c.nivel_validacion];const lugar=[c.ciudad,c.provincia].filter(Boolean).join(', ')||'Ubicación no disponible';return `<article class="card ${seleccionada===c.id?'seleccionada':''}" data-id="${c.id}"><div><div class="fecha">${fecha(c.fecha)}</div><h3>${c.nombre}</h3><div class="lugar">${lugar}</div><div class="badges"><span class="badge mod g-${GRUPO[c.modalidad]}">${MOD[c.modalidad]}</span><span class="badge ${n.cl}">${n.txt}</span></div></div></article>`}).join(''):'<p class="vacia">No hay eventos con estos filtros.</p>';document.querySelectorAll('.card').forEach(x=>x.onclick=()=>abre(carreras.find(c=>c.id===x.dataset.id)))}
function actualizar(){pintaMapa();pintaLista()}
function abre(c){seleccionada=c.id;actualizar();if(c.lat)map.flyTo([c.lat,c.lng],9);const n=NIVELES[c.nivel_validacion],l=[c.ciudad,c.provincia,c.ccaa].filter(Boolean).join(', ')||'No disponible';$('#ficha').innerHTML=`<button class="ficha-cerrar" aria-label="Cerrar">×</button><div class="f-mod">${MOD[c.modalidad]} · ${DIST[c.modalidad]}</div><h2>${c.nombre}</h2><dl><dt>Fecha</dt><dd>${fecha(c.fecha)}</dd><dt>Lugar</dt><dd>${l}</dd><dt>Precio</dt><dd>${c.precio_texto||'No disponible'}</dd><dt>Validación</dt><dd><span class="badge ${n.cl}">${n.txt}</span></dd></dl>${c.web_oficial?`<a class="btn" href="${c.web_oficial}" target="_blank" rel="noopener">Web oficial</a>`:''}${c.lat?` <a class="btn sec" href="https://www.google.com/maps/dir/?api=1&destination=${c.lat},${c.lng}" target="_blank" rel="noopener">Cómo llegar</a>`:''}<div class="fuentes">Fuentes: ${c.fuentes.map(f=>`<a href="${f.url}" target="_blank" rel="noopener">${f.nombre}</a>`).join(' · ')}</div>`;$('#ficha').classList.add('visible');$('#ficha .ficha-cerrar').onclick=cierra;history.replaceState(null,'',`?carrera=${c.id}`)}
function cierra(){seleccionada=null;$('#ficha').classList.remove('visible');actualizar();history.replaceState(null,'',location.pathname)}
function options(){const ccaas=[...new Set(carreras.map(c=>c.ccaa).filter(Boolean))].sort();$('#f-ccaa').innerHTML='<option value="">Toda España</option>'+ccaas.map(x=>`<option>${x}</option>`).join('');const provs=[...new Set(carreras.filter(c=>!estado.ccaa||c.ccaa===estado.ccaa).map(c=>c.provincia).filter(Boolean))].sort();$('#f-provincia').innerHTML='<option value="">Todas las provincias</option>'+provs.map(x=>`<option>${x}</option>`).join('')}
function bind(){$('#f-toggle').onclick=()=>$('#filtros').classList.toggle('abierto');document.querySelectorAll('#f-modalidad button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#f-modalidad button').forEach(x=>x.classList.remove('activo'));b.classList.add('activo');estado.modalidad=b.dataset.v;actualizar()});$('#f-texto').oninput=e=>{estado.texto=e.target.value;actualizar()};$('#f-ccaa').onchange=e=>{estado.ccaa=e.target.value;estado.provincia='';options();actualizar()};$('#f-provincia').onchange=e=>{estado.provincia=e.target.value;actualizar()};$('#f-mes').onchange=e=>{estado.mes=e.target.value;actualizar()};$('#f-nivel').onchange=e=>{estado.nivel=e.target.value;actualizar()};$('#f-orden').onchange=e=>{estado.orden=e.target.value;pintaLista()};$('#solo-mapa').onchange=e=>{estado.soloMapa=e.target.checked;pintaLista()};$('#limpiar').onclick=()=>location.reload();map.on('moveend',()=>{if(estado.soloMapa)pintaLista()})}
async function init(){const r=await fetch('data/races.json');carreras=(await r.json()).carreras;const by=Object.fromEntries(ORDER.map(m=>[m,carreras.filter(c=>c.modalidad===m).length]));$('#stats').textContent=`${carreras.length} eventos confirmados · ${by['5k']} 5K · ${by['10k']} 10K · ${by.medio_maraton} medias · ${by.maraton} maratones · ${ORDER.filter(x=>x.startsWith('triatlon')).reduce((a,x)=>a+by[x],0)} triatlones · ${by.hyrox+by.hibrida} híbridas · ${by.obstaculos} obstáculos`;options();bind();actualizar();const pts=carreras.filter(c=>c.lat&&c.lng>-9).map(c=>[c.lat,c.lng]);if(pts.length)map.fitBounds(pts,{padding:[20,20]});const id=new URLSearchParams(location.search).get('carrera');if(id){const c=carreras.find(x=>x.id===id);if(c)abre(c)}$('#actualizado').textContent=`Actualizado: ${new Date().toLocaleDateString('es-ES')}`}
init();
