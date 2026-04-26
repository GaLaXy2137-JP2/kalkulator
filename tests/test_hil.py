import os
import sys
import unittest


sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from silnik.hil import get_adjusted_volume, get_hil_multiplier
from app import policz


class HilNormalizationTests(unittest.TestCase):
    def test_cholesterol_aliases_match_lipemia_multiplier(self):
        self.assertEqual(get_hil_multiplier("Cholesterol", lipemia="high"), 1.3)
        self.assertEqual(get_hil_multiplier("Cholesterol całkowity", lipemia="high"), 1.3)
        self.assertEqual(get_hil_multiplier("Cholesterol calkowity", lipemia="high"), 1.3)

    def test_triglyceride_aliases_match_lipemia_multiplier(self):
        self.assertEqual(get_hil_multiplier("Trójglicerydy", lipemia="high"), 1.3)
        self.assertEqual(get_hil_multiplier("Trojglicerydy", lipemia="high"), 1.3)

    def test_single_parameter_volume_uses_lipemia_multiplier(self):
        self.assertEqual(get_adjusted_volume(7.0, "Cholesterol", lipemia="high"), 9.1)
        self.assertEqual(get_adjusted_volume(7.0, "Cholesterol całkowity", lipemia="high"), 9.1)
        self.assertEqual(get_adjusted_volume(2.0, "Trójglicerydy", lipemia="high"), 2.6)

    def test_single_parameter_calculation_uses_alias_lookup(self):
        cholesterol = policz(59, "", "", ["Cholesterol całkowity"], lipemia="high")
        triglycerides = policz(52, "", "", ["Trojglicerydy"], lipemia="high")

        self.assertEqual(cholesterol["potrzebne_ul"], 59.1)
        self.assertEqual(triglycerides["potrzebne_ul"], 52.6)


if __name__ == "__main__":
    unittest.main()