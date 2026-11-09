import json,sys,unittest
from experiment import HERE,atomic,sha
suite=unittest.defaultTestLoader.discover(str(HERE),pattern='test_experiment.py')
with (HERE/'TESTS.log').open('w') as log:result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
summary=dict(verdict='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),code_sha256=sha(HERE/'experiment.py'),tests_sha256=sha(HERE/'test_experiment.py'),scope='OFFLINE_DIAGONAL_EXACT_REPLAY_CROSS_REASSEMBLY_AND_FAILURES',new_model_calls=0)
atomic(HERE/'TESTS.json',summary);print(json.dumps(summary),flush=True)
if not result.wasSuccessful():print((HERE/'TESTS.log').read_text());sys.exit(1)
