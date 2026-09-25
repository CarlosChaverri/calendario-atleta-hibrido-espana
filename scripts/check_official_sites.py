#!/usr/bin/env python3
# Comprueba que la web oficial de cada carrera responde y que la fecha aparece en ella.
# Actualiza nivel_validacion en data/races.json. Lo ejecuta el cron tras build_dataset.py.
import json, re, os, sys, subprocess, html as htmllib
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL = os.path.join(ROOT, 'data', 'races_full.json')
OUT = os.path.join(ROOT, 'data', 'races.json')
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fuentes import MESES_ES, MESES_EN, MESES_CA
from title_policy import apply_titles

PARKED = re.compile(r'domain is for sale|sedoparking|parked free|buy this domain|hugedomains|domain parking', re.I)
CANCEL = re.compile(r'(carrera|prueba|evento|edicion|maraton|media)[^.]{0,60}(cancelad|cancel·l|aplazad|suspendid)'
    r'|(cancelad|cancel·l|aplazad|suspendid)[a-záéíóú ]{0,40}(carrera|prueba|evento|edicion|maraton)', re.I)

def fetch(url):
    dest = '/tmp/check_site.html'
    cmd = ['curl', '-s', '--compressed', '-L', '--max-time', '20', '--retry', '1', '-A', UA,
           '-o', dest, '-w', '%{http_code}', url]
    try:
        code = subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return None, ''
    if not code.startswith('2'):
        return code, ''
    try:
        raw = open(dest, 'rb').read()[:900000]
        h = raw.decode('utf-8', errors='replace')
        h = re.sub(r'<script[^>]*>.*?</script>', ' ', h, flags=re.S | re.I)
        h = re.sub(r'<style[^>]*>.*?</style>', ' ', h, flags=re.S | re.I)
        txt = htmllib.unescape(re.sub(r'<[^>]+>', ' ', h))
        return code, re.sub(r'\s+', ' ', txt).lower()
    except Exception:
        return code, ''

def fecha_en_texto(txt, f_iso):
    try:
        y, m, d = int(f_iso[:4]), int(f_iso[5:7]), int(f_iso[8:10])
    except Exception:
        return False
    meses = [MESES_ES[m-1], MESES_EN[m-1], MESES_CA[m-1]]
    for mn in meses:
        for pat in [rf'\b{d}\s+de\s+{mn}', rf'\b{d}\s+{mn}\b', rf'{mn}\s+{d}\b']:
            if re.search(pat, txt): return True
    for pat in [rf'\b{d:02d}[/.-]{m:02d}[/.-]{y}\b', rf'\b{d}[/.-]{m}[/.-]{y}\b',
                rf'\b{d:02d}[/.-]{m:02d}[/.-]{str(y)[2:]}\b', rf'\b{y}-{m:02d}-{d:02d}\b']:
        if re.search(pat, txt): return True
    return False

def main():
    data = json.load(open(FULL if os.path.exists(FULL) else OUT))
    carreras = data['carreras']
    hoy = date.today().isoformat()
    resumen = {'comprobadas': 0, 'ok': 0, 'sin_fecha': 0, 'caidas': 0, 'posible_cancelacion': 0}
    for r in carreras:
        web = r.get('web_oficial')
        if not web: continue
        resumen['comprobadas'] += 1
        code, txt = fetch(web)
        r['ultima_comprobacion'] = hoy
        if code is None or not str(code).startswith('2'):
            r['nivel_validacion'] = 'por_verificar'
            r['web_estado'] = 'caida'
            resumen['caidas'] += 1
            continue
        if PARKED.search(txt):
            r['nivel_validacion'] = 'por_verificar'
            r['web_estado'] = 'caida'
            resumen['caidas'] += 1
            continue
        if CANCEL.search(txt):
            r['nivel_validacion'] = 'por_verificar'
            r['web_estado'] = 'posible_cancelacion'
            resumen['posible_cancelacion'] += 1
            continue
        if fecha_en_texto(txt, r['fecha']):
            r['nivel_validacion'] = 'confirmada_web_oficial'
            r['web_estado'] = 'activa'
            resumen['ok'] += 1
        else:
            r['web_estado'] = 'activa_sin_fecha'
            resumen['sin_fecha'] += 1
        if resumen['comprobadas'] % 10 == 0:
            print(f"  {resumen['comprobadas']} comprobadas...", flush=True)
    # The check is generic and can mistake a blocked organizer page for a
    # cancelled edition. Restore exactly reviewed sources unless cancellation
    # language was detected; that case remains flagged for a human decision.
    curations = os.path.join(ROOT, 'data', 'official_curations.json')
    if os.path.exists(curations):
        cfg = json.load(open(curations))
        reviewed = {e['record']['id']: e['record'] for e in cfg['entries']}
        for i, r in enumerate(carreras):
            if r['id'] in reviewed and r.get('web_estado') != 'posible_cancelacion':
                carreras[i] = dict(reviewed[r['id']])
        # Do not publish a possible cancellation automatically, even if the
        # record was in the prior public dataset.
    apply_titles(carreras)
    niveles = {}
    for r in carreras:
        r['fecha_confirmada'] = r['nivel_validacion'] in ('confirmada_web_oficial', 'confirmada_organizacion')
        niveles[r['nivel_validacion']] = niveles.get(r['nivel_validacion'], 0) + 1
    json.dump(data, open(FULL, 'w'), ensure_ascii=False, indent=1)
    visibles = [r for r in data['carreras'] if r['nivel_validacion'] in ('confirmada_web_oficial', 'confirmada_organizacion')]
    json.dump({'generado': data['generado'], 'carreras': visibles}, open(OUT, 'w'), ensure_ascii=False, indent=1)
    print(f'visibles en la web: {len(visibles)} de {len(data["carreras"])}')
    print('resumen chequeo:', json.dumps(resumen, ensure_ascii=False))
    print('niveles finales:', json.dumps(niveles, ensure_ascii=False))

if __name__ == '__main__':
    main()
