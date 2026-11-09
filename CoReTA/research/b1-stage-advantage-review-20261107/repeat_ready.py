import json
from repeat import HERE,OUT,load,sha,verify_freeze,atomic
verify_freeze();p=load(OUT/'PREFLIGHT.json');assert p['science']==p['engineering']=='PASS' and p['real_replay_and_pressure_requests']==5824 and p['max_input_plus_cap']<=16384
assert load(HERE/'REPEAT_TESTS.json')['real_replayed_requests']==2912
r=dict(verdict='RUN_ALLOWED',scope='SAME56_FOUR_UNCHANGED_ARMS_FIXED_ORDERS_GENERATION_SEED_PLUS100000000',science='PASS',engineering='PASS',freeze_sha256=sha(OUT/'FREEZE.json'),max_calls=2912,max_output_tokens=2121728,wall_clock_cutoff=None,generation_retry=False,actual_preflight=p,reviewer='assistant',independence='none/provisional')
atomic(HERE/'REPEAT_READY.json',r);print(json.dumps(r),flush=True)
