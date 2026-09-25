"""Public-facing names. IDs and source URLs stay tied to their feed records."""
import re
import unicodedata

# Reviewed commercial/media prefixes and suffixes, not generic words that could
# be part of an event's actual name. Keep these exact so new sources get review.
REPLACEMENTS = (
    (r'\s*[-–]\s*Heraldo(?: de Aragón)?\b', ''),
    (r'\s*\(?Bimbo Global Race\)?', ''),
    (r'^Rural Kutxa\s+', ''),
    (r'\s+Trinidad Alfonso\b', ''),
    (r'\s*\(Generali Maratón Málaga\)', ''),
    (r'^Leapmotor\s+', ''),
    (r'^Zurich\s+', ''),
    (r'^Allianz\s+', ''),
    (r'\s+Ibercaja By KIPRUN\b', ''),
    (r'^TotalEnergies\s+', ''),
    (r'^Hyundai\s+', ''),
    (r'\s*\(TotalEnergies\)', ''),
    (r'^Movistar\s+', ''),
    (r'^Mann-filter\s+', ''),
    (r'^Tui\s+', ''),
    (r'\s+Ayto de Piélagos\b', ''),
)
LABEL = {'5k':'5K', '10k':'10K', 'medio_maraton':'Media maratón',
         'maraton':'Maratón', 'triatlon_sprint':'Triatlón sprint',
         'triatlon_olimpico':'Triatlón olímpico', 'triatlon_media':'Triatlón media',
         'triatlon_larga':'Triatlón larga'}

def fold(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower())
                   if unicodedata.category(c) != 'Mn')

def present_name(name, modality):
    for pattern, replacement in REPLACEMENTS:
        name = re.sub(pattern, replacement, name, flags=re.I)
    name = re.sub(r'\s+', ' ', name).strip()
    name = name.rstrip(' -–')
    if name.endswith('('): name = name[:-1].rstrip()
    if name.startswith(')'): name = name[1:].lstrip()
    if name.count('(') > name.count(')'):
        name += ')' * (name.count('(') - name.count(')'))
    # Explicit distance is needed when the event has several modalities. Never
    # infer modality from the event brand (e.g. "Half Marathon" has a 5K too).
    plain = fold(name)
    patterns = {
        '5k':r'(?<!\d)5\s*(?:k|km)\b',
        '10k':r'(?<!\d)10\s*(?:k|km)\b',
        'medio_maraton':r'\b(?:media|medio|mitja|half|semi)\s*[- ]?marat|\b21(?:[.,]097)?\s*(?:k|km)\b',
        'maraton':r'\b(?:maraton|marato|marathon)\b|\b42(?:[.,]195)?\s*(?:k|km)\b',
        'triatlon_sprint':r'\bsprint\b',
        'triatlon_olimpico':r'\bolimpic',
        'triatlon_media':r'\b(?:half|media|70[.,]3|113)\b',
        'triatlon_larga':r'\b(?:ironman|larga|full|226)\b',
    }
    if modality in LABEL and not re.search(patterns[modality], plain):
        name += ' - ' + LABEL[modality]
    return name

def apply_titles(races):
    for race in races:
        race['nombre'] = present_name(race['nombre'], race['modalidad'])
