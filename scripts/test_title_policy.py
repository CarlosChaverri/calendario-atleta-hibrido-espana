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
    def test_no_multidistance_erasure(self):
        records = json.loads((ROOT / 'data' / 'races.json').read_text())['carreras']
        binter = [r for r in records if 'binter' in r['nombre'].lower()]
        self.assertEqual({r['modalidad'] for r in binter}, {'5k', '10k'})
        self.assertEqual(len(records), 232)

if __name__ == '__main__': unittest.main()
