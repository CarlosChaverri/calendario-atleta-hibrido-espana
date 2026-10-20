#!/usr/bin/env python3
# Coincidencia tolerante para las exclusiones curadas de data/official_curations.json.
# Las fuentes renombran carreras entre ediciones; una exclusion exacta por
# (nombre, modalidad, fecha) deja pasar la misma carrera con otro titulo.
import re
import unicodedata

STOP = set('''media medio mitja mig maraton marato marathon half triatlon triathlon hyrox carrera de del la el los las les en y e i a al
internacional international popular villa vila ciudad city ciutat edicion edicio memorial
trofeo trofeu gran grande premio circuit circuito cursa cross cros ano de san sant santa
santo saint the and'''.split())
ROMAN = re.compile(r'^(m{0,3}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))$')


def norm(s):
    if not s:
        return ''
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.lower().strip()


def tokens(nombre):
    n = re.sub(r'[^a-z0-9 ]', ' ', norm(nombre))
    return {t for t in n.split() if t and t not in STOP and not t.isdigit()
            and not ROMAN.match(t) and not re.match(r'^20\d\d$', t)}


def matches_exclusion(r, e):
    # Coincidencia exacta (comportamiento original).
    if all(r.get(k) == v for k, v in e.items()):
        return True
    # Coincidencia tolerante: exige misma modalidad y fecha, y nombre claramente
    # el mismo (contencion de tokens o de texto normalizado).
    if not e.get('modalidad') or not e.get('fecha'):
        return False
    if r.get('modalidad') != e['modalidad'] or r.get('fecha') != e['fecha']:
        return False
    te, tr = tokens(e.get('nombre')), tokens(r.get('nombre'))
    if te and tr:
        inter = len(te & tr)
        if inter > 0 and inter / min(len(te), len(tr)) >= 0.5:
            return True
    en, rn = norm(e.get('nombre')), norm(r.get('nombre'))
    if en and rn and (en in rn or rn in en):
        return True
    return False


def is_excluded(r, exclusions):
    return any(matches_exclusion(r, e) for e in exclusions)
