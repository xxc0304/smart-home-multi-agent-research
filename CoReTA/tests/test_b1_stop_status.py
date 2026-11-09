import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from b1_stop_status import termination_status
class StopChecks(unittest.TestCase):
    def test_eos_at_cap_is_success(self):
        self.assertEqual(termination_status([1,2],[2],2,10,10),('OK','EOS'))
    def test_cap_without_eos(self):
        self.assertEqual(termination_status([1,1],[2],2,1,10),('OUTPUT_LIMIT','TOKEN_LIMIT'))
    def test_time_limit_is_not_token_limit(self):
        self.assertEqual(termination_status([1],[2],256,10,10),('WALL_BUDGET','TIME_LIMIT'))
    def test_unknown_stop_never_passes(self):
        self.assertEqual(termination_status([],[2],256,1,10),('UNEXPECTED_STOP','NO_EOS'))
