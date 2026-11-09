import json,sys,unittest
from experiment import HERE,atomic,sha
suite=unittest.defaultTestLoader.discover(str(HERE),pattern='test_experiment.py')
with (HERE/'TESTS.log').open('w') as f:r=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
out=dict(verdict='PASS' if r.wasSuccessful() else 'FAIL',tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),code_sha256=sha(HERE/'experiment.py'),tests_sha256=sha(HERE/'test_experiment.py'),new_model_calls=0,scope='ACTUAL_FULL_RESPONSE_REPLAY_PLUS_TEMPORARY_FAULT_INJECTION_NOT_MODEL_RESULTS')
atomic(HERE/'TESTS.json',out);print(json.dumps(out),flush=True)
if not r.wasSuccessful():print((HERE/'TESTS.log').read_text());sys.exit(1)
