#!/usr/bin/env python3
# Descarga las fuentes, normaliza, deduplica, geocodifica y genera data/races.json
import json, re, os, sys, subprocess, time, unicodedata, hashlib
from datetime import date, datetime
from urllib.parse import urlparse, parse_qs
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fuentes import (PROVINCIAS_INE, SLUG_PROVINCIA, PROVINCIA_A_CCAA, SLUG_REGION,
                     MESES_ES, MESES_EN, MESES_CA, ISO_PROVINCIA, ISO_CCAA)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'data', 'raw')
OUT = os.path.join(ROOT, 'data', 'races.json')
GEOCACHE = os.path.join(ROOT, 'data', 'geocache.json')
HOY = date.today()
REFRESH = '--refresh' in sys.argv
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

os.makedirs(RAW, exist_ok=True)

def curl(url, dest, follow=True, timeout=45):
    if os.path.exists(dest) and not REFRESH and os.path.getsize(dest) > 100:
        return True
    cmd = ['curl', '-s', '--compressed', '--max-time', str(timeout), '--retry', '2', '-A', UA]
    if follow: cmd.append('-L')
    cmd += ['-o', dest, '-w', '%{http_code}', url]
    try:
        code = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+20).stdout.strip()
    except Exception:
        return False
    return code.startswith('2') and os.path.exists(dest) and os.path.getsize(dest) > 100

def norm(s):
    if not s: return ''
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.lower().strip()

STOP = set('''media medio mitja mig mitja maraton marato marathon half de del la el los las les en y e i a al
internacional internacional international popular villa vila ciudad city ciutat edicion edicio edicio memorial
trofeo trofeu gran grande premio premio circuit circuito carrera cursa cross cros ano ano de san sant santa
santo saint de del el la los las the and de'''.split())
ROMAN = re.compile(r'^(m{0,3}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))$')

def tokens_nombre(nombre):
    n = norm(nombre)
    n = re.sub(r'[^a-z0-9 ]', ' ', n)
    toks = [t for t in n.split() if t and t not in STOP and not t.isdigit()
            and not ROMAN.match(t) and not re.match(r'^20\d\d$', t)]
    return set(toks)

def slugify(s):
    n = norm(s)
    n = re.sub(r'[^a-z0-9]+', '-', n).strip('-')
    return n[:60] or 'carrera'

def parse_fecha_ed(s):  # "01/08/2026"
    try:
        d, m, y = s.strip().split('/')[:3]
        return date(int(y), int(m), int(d))
    except Exception:
        return None

# ---------- FUENTE 1: carreraspopulares ----------
def load_cp():
    dest = os.path.join(RAW, 'carreraspopulares.json')
    if not curl('https://carreraspopulares.com/api/calendario_carreras/getCarreras/es', dest):
        print('AVISO: fallo descarga carreraspopulares'); return []
    d = json.load(open(dest))
    ediciones = d.get('data', {}).get('ediciones', [])
    races = []
    for e in ediciones:
        if str(e.get('idPais')) != '10': continue
        f = parse_fecha_ed(e.get('fechaED') or '')
        if not f or f < HOY: continue
        titulo = (e.get('titulo') or '').strip()
        tn = norm(titulo)
        dist = e.get('distanciaTxt') or ''
        metros = [int(x.replace('.', '').replace(',', '')) for x in re.findall(r'(\d[\d.,]*)\s*m\b', dist)]
        modalidades = set()
        if any(19000 <= m <= 23000 for m in metros) or re.search(r'\b(media|medio|mitja|mig)\b.*\bmarat', tn):
            modalidades.add('medio_maraton')
        if any(40000 <= m <= 44000 for m in metros) or (re.search(r'\bmarat', tn) and 'media' not in tn and 'medio' not in tn and 'mitja' not in tn):
            modalidades.add('maraton')
        if not modalidades: continue
        pob = (e.get('poblacion') or '').strip()
        m2 = re.match(r'^(.*?)\s*\(([^)]+)\)\s*$', pob)
        ciudad = (m2.group(1) if m2 else pob).strip() or None
        prov, ccaa = PROVINCIAS_INE.get(str(e.get('idProv')).zfill(2), (None, None))
        for mod in modalidades:
            races.append({
                'nombre': titulo, 'modalidad': mod, 'fecha': f.isoformat(),
                'ciudad': ciudad, 'provincia': prov, 'ccaa': ccaa,
                'precio': None, 'web_oficial': None, 'lat': None, 'lng': None,
                'fuentes': [{'nombre': 'carreraspopulares', 'url': e.get('url_FC')}],
                'cp_organiza': e.get('organiza'),
            })
    print(f'carreraspopulares: {len(races)} (de {len(ediciones)} ediciones)')
    return races

# ---------- FUENTE 2: Finishers ----------
FIN_PAGES = [
    ('medio_maraton', 'https://www.finishers.com/en/activities/road-running/half-marathon/half-marathons-in-spain', 'finishers-hm.html'),
    ('maraton', 'https://www.finishers.com/en/activities/road-running/marathon/marathons-in-spain', 'finishers-m.html'),
]

def next_data(path):
    h = open(path, encoding='utf-8', errors='replace').read()
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    return json.loads(m.group(1)) if m else None

def load_finishers():
    races = []
    fichas = {}
    for mod, url, fn in FIN_PAGES:
        dest = os.path.join(RAW, fn)
        if not curl(url, dest):
            print(f'AVISO: fallo descarga finishers {fn}'); continue
        d = next_data(dest)
        if not d: continue
        pp = d['props']['pageProps']
        grupos = pp.get('calendarSection', {}).get('events', {})
        for mes, evs in (grupos.items() if isinstance(grupos, dict) else []):
            for e in evs:
                try:
                    f = date.fromisoformat(e['date'][:10])
                except Exception:
                    continue
                if f < HOY: continue
                href = e.get('href') or ''
                slug = href.rstrip('/').split('/')[-1]
                races.append({
                    'nombre': e.get('name'), 'modalidad': mod, 'fecha': f.isoformat(),
                    'ciudad': e.get('city'), 'provincia': None, 'ccaa': None,
                    'precio': None, 'web_oficial': None, 'lat': None, 'lng': None,
                    'fuentes': [{'nombre': 'finishers', 'url': 'https://www.finishers.com' + href}],
                    'fin_status': e.get('status'), 'fin_slug': slug,
                })
                fichas[slug] = 'https://www.finishers.com' + href
    print(f'finishers: {len(races)} calendario')
    # fichas individuales: web oficial y coordenadas
    n_ok = 0
    for slug, url in sorted(fichas.items()):
        dest = os.path.join(RAW, f'fin-ev-{slug}.html')
        if not curl(url, dest): continue
        d = next_data(dest)
        if not d: continue
        ev = d.get('props', {}).get('pageProps', {}).get('event') or {}
        web = None
        links = ev.get('links') or {}
        w = links.get('website')
        if w and 'url=' in w:
            web = parse_qs(urlparse(w).query).get('url', [None])[0]
        cc = ev.get('cityCoordinates') or {}
        for r in races:
            if r.get('fin_slug') == slug:
                if web: r['web_oficial'] = web
                if cc.get('lat'): r['lat'], r['lng'] = cc['lat'], cc.get('lng')
                n_ok += 1
    print(f'finishers fichas enriquecidas: {n_ok}')
    return races

# ---------- FUENTE 3: Runnea ----------
RUN_CALS = [
    ('medio_maraton', 'https://www.runnea.com/carreras-populares/calendario/medias-maratones/espana/'),
    ('maraton', 'https://www.runnea.com/carreras-populares/calendario/maratones/espana/'),
]

def parse_nuxt(path):
    r = subprocess.run(['node', os.path.join(ROOT, 'scripts', 'parse_nuxt.js'), path],
                       capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout)
    except Exception:
        return None

def runnea_ficha(slug):
    dest = os.path.join(RAW, f'runnea-ficha-{slug}.html')
    url = f'https://www.runnea.com/carreras-populares/{slug}/'
    if not curl(url, dest): return {}
    h = open(dest, encoding='utf-8', errors='replace').read()
    out = {}
    m = re.search(r'href="(https?://[^"]+)"[^>]*>\s*(?:Ver web de la carrera|Web oficial)', h)
    if m and 'runnea.com' not in m.group(1): out['web_oficial'] = m.group(1)
    if re.search(r'confirmad[ao][^.<]{0,80}organizaci', h, re.I) or re.search(r'fecha oficialmente confirmada', h, re.I):
        out['confirmada_org'] = True
    precios = []
    for pm in re.finditer(r'(\d{1,3})\s*(?:€|euros)', h):
        v = int(pm.group(1))
        if 3 <= v <= 400: precios.append(v)
    if re.search(r'inscripci[oó]n gratuita|entrada gratuita', h, re.I):
        out['precio'] = 0
    elif precios:
        out['precio'] = min(precios)
    return out

def load_runnea():
    races = []
    for mod, base in RUN_CALS:
        items, seen = [], set()
        for page in range(1, 9):
            url = base if page == 1 else f'{base}{page}/'
            dest = os.path.join(RAW, f'runnea-{mod}-{page}.html')
            if not curl(url, dest): break
            d = parse_nuxt(dest)
            if not d or not d.get('lists'): break
            nuevos = 0
            for lst in d['lists']:
                for c in (lst.get('contents') or []):
                    p = c.get('path') or ''
                    if p in seen: continue
                    seen.add(p); items.append(c); nuevos += 1
            if nuevos == 0: break
        print(f'runnea {mod}: {len(items)}')
        for c in items:
            try:
                f = datetime.strptime(c.get('date', ''), '%d-%m-%Y').date()
            except Exception:
                continue
            if f < HOY: continue
            slug = (c.get('path') or '').split('/')[-2] if c.get('path') else slugify(c.get('title', ''))
            prov = SLUG_PROVINCIA.get(norm(c.get('province') or ''))
            ccaa = SLUG_REGION.get(norm(c.get('region') or '')) or (PROVINCIA_A_CCAA.get(prov) if prov else None)
            ficha = runnea_ficha(slug)
            races.append({
                'nombre': c.get('title'), 'modalidad': mod, 'fecha': f.isoformat(),
                'ciudad': (c.get('place') or '').strip() or None, 'provincia': prov, 'ccaa': ccaa,
                'precio': ficha.get('precio'), 'web_oficial': ficha.get('web_oficial'),
                'lat': None, 'lng': None,
                'fuentes': [{'nombre': 'runnea', 'url': f'https://www.runnea.com/carreras-populares/{slug}/'}],
                'runnea_confirmada': ficha.get('confirmada_org', False),
            })
    print(f'runnea total: {len(races)}')
    return races

# ---------- FUENTE 4: Runner's World (contraste editorial) ----------
def load_rw():
    dest = os.path.join(RAW, 'runnersworld.html')
    url = 'https://www.runnersworld.com/es/training/a70075791/calendario-carreras-medio-maraton-espana-2026/'
    if not curl(url, dest):
        print('AVISO: fallo descarga runnersworld'); return []
    h = open(dest, encoding='utf-8', errors='replace').read()
    h2 = re.findall(r'<h2[^>]*>(.*?)</h2>', h, re.S)
    out = []
    for x in h2:
        t = re.sub(r'<[^>]+>', '', x).strip()
        t = t.replace('&amp;', '&').replace('&#8211;', '-').replace('&#8217;', "'")
        m = re.match(r'^\w+\s+(\d{1,2})\s+de\s+(\w+)\s*[-–]\s*(.+)$', t)
        if not m: continue
        dia, mes_n, nombre = int(m.group(1)), norm(m.group(2)), m.group(3).strip()
        mes = None
        for i, mn in enumerate(MESES_ES):
            if mes_n.startswith(mn[:4]): mes = i + 1; break
        if not mes: continue
        try:
            f = date(2026, mes, dia)
        except Exception:
            continue
        out.append({'nombre': nombre, 'fecha': f.isoformat(), 'modalidad': 'medio_maraton',
                    'fuentes': [{'nombre': 'runnersworld', 'url': url}]})
    print(f'runnersworld: {len(out)} entradas editoriales')
    return out

# ---------- DEDUPE ----------
def sim(a, b):
    ta, tb = tokens_nombre(a), tokens_nombre(b)
    if not ta or not tb: return 0.0
    return len(ta & tb) / len(ta | tb)

CIUDAD_ALIAS = {'donostia': 'san sebastian', 'donosti': 'san sebastian', 'gasteiz': 'vitoria',
                'vitoria-gasteiz': 'vitoria', 'xixon': 'gijon', 'coruna': 'a coruna'}
def norm_ciudad(c):
    n = norm(c or '')
    return CIUDAD_ALIAS.get(n, n)

def mismo(a, b):
    if a['modalidad'] != b['modalidad']: return False
    da = date.fromisoformat(a['fecha']); db = date.fromisoformat(b['fecha'])
    if abs((da - db).days) > 3: return False
    ca, cb = norm_ciudad(a.get('ciudad')), norm_ciudad(b.get('ciudad'))
    pa, pb = norm(a.get('provincia') or ''), norm(b.get('provincia') or '')
    s = sim(a['nombre'], b['nombre'])
    if da == db and pa and pa == pb and (not ca or not cb or ca == cb):
        return True
    if ca and cb:
        if ca == cb: return True
        if s >= 0.6: return True
        if ca in norm(b['nombre']) or cb in norm(a['nombre']): return True
        return False
    return s >= 0.55

def merge(base, inc):
    base['fuentes'] = base['fuentes'] + [f for f in inc['fuentes'] if f['url'] not in {x['url'] for x in base['fuentes']}]
    for k in ['ciudad', 'provincia', 'ccaa', 'web_oficial', 'lat', 'lng']:
        if not base.get(k) and inc.get(k): base[k] = inc[k]
    if base.get('precio') is None and inc.get('precio') is not None: base['precio'] = inc['precio']
    for k in ['fin_status', 'runnea_confirmada', 'cp_organiza', 'fin_slug']:
        if inc.get(k) and not base.get(k): base[k] = inc[k]
    # nombre preferido: el mas informativo (mas largo sin ser redundante)
    if inc['nombre'] and len(inc['nombre']) > len(base['nombre'] or ''):
        base['nombre'] = inc['nombre']
    return base

# ---------- GEOCODIFICACION ----------
def nominatim(q):
    from urllib.parse import quote_plus
    url = ('https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&addressdetails=1&countrycodes=es&q='
           + quote_plus(q))
    dest = os.path.join(RAW, 'geo_tmp.json')
    cmd = ['curl', '-s', '--compressed', '--max-time', '20', '--retry', '2',
           '-A', 'CalendarioAtletaHibridoEspana/0.1 (github.com/CarlosChaverri/calendario-atleta-hibrido-espana)',
           '-o', dest, '-w', '%{http_code}', url]
    try:
        code = subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout.strip()
        if not code.startswith('2'): return None
        arr = json.load(open(dest))
        return arr[0] if arr else None
    except Exception:
        return None

def ciudad_desde_nombre(nombre):
    toks = [t for t in tokens_nombre(nombre) if len(t) > 2]
    return ' '.join(sorted(toks, key=lambda t: -len(t))[:3]) if toks else None

def geocode(races):
    cache = {}
    if os.path.exists(GEOCACHE):
        cache = {k: v for k, v in json.load(open(GEOCACHE)).items() if v}
    pend = [r for r in races if not r.get('lat') or not r.get('provincia')]
    print(f'geocodificar: {len(pend)} carreras')
    for r in pend:
        consultas = []
        if r.get('ciudad'):
            consultas.append((norm(r['ciudad'] + '|' + (r.get('provincia') or '')),
                              r['ciudad'] + (', ' + r['provincia'] if r.get('provincia') else '') + ', España', False))
        else:
            cand = ciudad_desde_nombre(r.get('nombre') or '')
            if cand:
                consultas.append((norm(cand + '|' + (r.get('provincia') or '')),
                                  cand + (', ' + r['provincia'] if r.get('provincia') else '') + ', España', True))
            if r.get('provincia'):
                consultas.append((norm('provincia:' + r['provincia']), r['provincia'] + ', España', True))
        for key, q, aprox in consultas:
            if key not in cache:
                res = nominatim(q)
                if res:
                    ad = res.get('address') or {}
                    prov_iso = ISO_PROVINCIA.get(ad.get('ISO3166-2-lvl6') or '')
                    prov_raw = ad.get('province') or ad.get('state_district')
                    cache[key] = {'lat': float(res['lat']), 'lng': float(res['lon']),
                                  'provincia': prov_iso or (prov_raw if prov_raw in PROVINCIA_A_CCAA else None),
                                  'ccaa': ISO_CCAA.get(ad.get('ISO3166-2-lvl4') or '') or ad.get('state')}
                else:
                    cache[key] = None
                json.dump(cache, open(GEOCACHE, 'w'), ensure_ascii=False, indent=1)
                time.sleep(1.1)
            g = cache.get(key)
            if g:
                if not r.get('lat'): r['lat'], r['lng'] = g['lat'], g['lng']
                if aprox and not r.get('ciudad'): r['ubicacion_aproximada'] = True
                if not r.get('provincia') and g.get('provincia'):
                    r['provincia'] = g['provincia']
                if not r.get('ccaa'):
                    r['ccaa'] = g.get('ccaa') or (PROVINCIA_A_CCAA.get(r.get('provincia')) if r.get('provincia') else None)
                break
            elif not r.get('ccaa') and r.get('provincia'):
                r['ccaa'] = PROVINCIA_A_CCAA.get(r['provincia'])
    json.dump(cache, open(GEOCACHE, 'w'), ensure_ascii=False, indent=1)

MENORES = {'de', 'del', 'la', 'las', 'los', 'el', 'y', 'en'}
def limpia_nombre(n):
    if not n: return n
    n = ' '.join(n.split())
    if len(n) > 8 and n.isupper():
        partes = n.lower().split(' ')
        n = ' '.join(w if w in MENORES else w.capitalize() for w in partes)
        n = n[0].upper() + n[1:]
        n = re.sub(r'\b(\d+)k\b', lambda m: m.group(1) + 'K', n, flags=re.I)
    return n
def limpia_ciudad(c):
    if not c: return c
    c = ' '.join(c.split())
    if c.isupper() or c.islower():
        partes = c.lower().split(' ')
        c = ' '.join(w if w in MENORES else w.capitalize() for w in partes)
        c = c[0].upper() + c[1:]
    return c

# ---------- NIVEL DE VALIDACION ----------
def limpia_url(u):
    if not u: return u
    try:
        from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
        p = urlsplit(u)
        qs = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith('utm_')]
        return urlunsplit((p.scheme, p.netloc, p.path, urlencode(qs), ''))
    except Exception:
        return u

def nivel(r, n_fuentes_agenda):
    if r.get('runnea_confirmada') or r.get('fin_status') == 'confirmed':
        return 'confirmada_organizacion'
    if r.get('fin_status') == 'tba' and n_fuentes_agenda <= 1:
        return 'fecha_estimada'
    if r.get('fin_status') == 'tba':
        return 'fecha_estimada'
    if n_fuentes_agenda >= 2:
        return 'confirmada_organizacion'
    return 'por_verificar'

def main():
    cp = load_cp()
    fin = load_finishers()
    run = load_runnea()
    rw = load_rw()
    agendas = cp + fin + run
    merged = []
    for r in agendas:
        hit = None
        for m in merged:
            if mismo(m, r): hit = m; break
        if hit: merge(hit, r)
        else: merged.append(dict(r))
    # contraste RW: solo anade fuente a coincidencias
    n_rw = 0
    for e in rw:
        for m in merged:
            if m['modalidad'] != 'medio_maraton': continue
            if abs((date.fromisoformat(m['fecha']) - date.fromisoformat(e['fecha'])).days) <= 3 and sim(m['nombre'], e['nombre']) >= 0.5:
                if e['fuentes'][0]['url'] not in {f['url'] for f in m['fuentes']}:
                    m['fuentes'].append(e['fuentes'][0]); n_rw += 1
                break
    print(f'contraste RW aplicado a {n_rw} carreras')
    geocode(merged)
    # comunidades uniprovinciales: la provincia se deduce de la ccaa
    UNIPROV = {'Comunidad de Madrid': 'Madrid', 'La Rioja': 'La Rioja', 'Región de Murcia': 'Murcia',
               'Asturias': 'Asturias', 'Cantabria': 'Cantabria', 'Navarra': 'Navarra', 'Illes Balears': 'Illes Balears'}
    for r in merged:
        if not r.get('provincia') and r.get('ccaa') in UNIPROV:
            r['provincia'] = UNIPROV[r['ccaa']]
    # segunda pasada de dedupe: ahora ya hay provincia/ciudad geocodificadas
    merged2 = []
    for r in merged:
        hit = None
        for m in merged2:
            if mismo(m, r): hit = m; break
        if hit: merge(hit, r)
        else: merged2.append(dict(r))
    if len(merged2) < len(merged):
        print(f'dedupe post-geocode: {len(merged)} -> {len(merged2)}')
        merged = merged2
    out = []
    for r in merged:
        noms = {f['nombre'] for f in r['fuentes']}
        n_agenda = len({'carreraspopulares', 'finishers', 'runnea'} & noms)
        nv = nivel(r, n_agenda)
        rid = hashlib.md5((slugify(r['nombre'] or '') + r['fecha'] + r['modalidad']).encode()).hexdigest()[:12]
        out.append({
            'id': rid,
            'nombre': limpia_nombre(r['nombre']), 'modalidad': r['modalidad'], 'fecha': r['fecha'],
            'fecha_confirmada': nv in ('confirmada_web_oficial', 'confirmada_organizacion'),
            'ciudad': limpia_ciudad(r.get('ciudad')), 'provincia': r.get('provincia'), 'ccaa': r.get('ccaa'),
            'lat': r.get('lat'), 'lng': r.get('lng'),
            'precio': r.get('precio'), 'precio_texto': ('desde ' + str(r['precio']) + ' €') if r.get('precio') else None,
            'web_oficial': limpia_url(r.get('web_oficial')), 'ubicacion_aproximada': r.get('ubicacion_aproximada', False),
            'fuentes': r['fuentes'], 'nivel_validacion': nv,
            'ultima_comprobacion': HOY.isoformat(),
        })
    out.sort(key=lambda x: (x['fecha'], x['nombre'] or ''))
    stats = {
        'generado': datetime.now().isoformat(timespec='seconds'),
        'total': len(out),
        'por_modalidad': {},
        'por_nivel': {},
        'sin_coordenadas': sum(1 for r in out if not r['lat']),
        'con_precio': sum(1 for r in out if r['precio'] is not None),
        'con_web_oficial': sum(1 for r in out if r['web_oficial']),
    }
    for r in out:
        stats['por_modalidad'][r['modalidad']] = stats['por_modalidad'].get(r['modalidad'], 0) + 1
        stats['por_nivel'][r['nivel_validacion']] = stats['por_nivel'].get(r['nivel_validacion'], 0) + 1
    json.dump({'generado': stats['generado'], 'carreras': out},
              open(os.path.join(ROOT, 'data', 'races_full.json'), 'w'), ensure_ascii=False, indent=1)
    visibles = [r for r in out if r['nivel_validacion'] in ('confirmada_web_oficial', 'confirmada_organizacion')]
    json.dump({'generado': stats['generado'], 'carreras': visibles}, open(OUT, 'w'), ensure_ascii=False, indent=1)
    stats['visibles'] = len(visibles)
    json.dump(stats, open(os.path.join(ROOT, 'data', 'stats.json'), 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(stats, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main()
