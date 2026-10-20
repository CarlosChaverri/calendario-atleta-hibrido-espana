import json
import pathlib
import unittest
from title_policy import present_name

ROOT = pathlib.Path(__file__).resolve().parent.parent

class TitlePolicyTest(unittest.TestCase):
    def test_binter_distances_and_sponsor(self):
        self.assertEqual(present_name('Binter Nightrun Zaragoza - Heraldo', '10k'),
                         'Binter Nightrun Zaragoza - 10K')
        self.assertEqual(present_name('Binter NightRun Zaragoza', '5k'),
                         'Binter NightRun Zaragoza - 5K')
    def test_multidistance_without_collapsing(self):
        self.assertEqual(present_name('Carrera Niños sin Cáncer', '5k'),
                         'Carrera Niños sin Cáncer - 5K')
        self.assertEqual(present_name('Carrera Niños sin Cáncer', '10k'),
                         'Carrera Niños sin Cáncer - 10K')
    def test_idempotent_and_existing_distance(self):
        for path in ('races.json', 'races_full.json'):
            records = json.loads((ROOT / 'data' / path).read_text())['carreras']
            for r in records:
                with self.subTest(id=r['id']):
                    self.assertEqual(r['nombre'], present_name(r['nombre'], r['modalidad']))
        self.assertEqual(present_name('10K Ciudad Lineal', '10k'), '10K Ciudad Lineal')
    def test_dataset_invariants(self):
        # Invariantes del dataset publicado, sin conteos ni carreras concretas
        # (el catalogo cambia con cada regeneracion).
        from datetime import date
        records = json.loads((ROOT / 'data' / 'races.json').read_text())['carreras']
        hoy = date.today().isoformat()
        ids = [r['id'] for r in records]
        self.assertEqual(len(ids), len(set(ids)), 'ids duplicados')
        self.assertTrue(all(r['fecha'] >= hoy for r in records),
                        'ediciones pasadas publicadas')
        self.assertTrue(all(r['nivel_validacion'] in ('confirmada_web_oficial', 'confirmada_organizacion')
                            for r in records), 'fichas sin confirmar publicadas')
        tarjetas = [(r['nombre'].lower(), r['modalidad'], r['fecha']) for r in records]
        self.assertEqual(len(tarjetas), len(set(tarjetas)), 'tarjetas duplicadas')

if __name__ == '__main__': unittest.main()
