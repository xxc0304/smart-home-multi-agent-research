import json,re,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
commands=([sys.executable,'-m','unittest','discover','-s','tests','-p','test_b1*.py','-v'],[sys.executable,str(HERE/'test_runner.py'),'-v'])
logs=[];results=[]
for command in commands:
    p=subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    logs.append(p.stdout);match=re.search(r'Ran (\d+) tests',p.stdout);results.append(dict(returncode=p.returncode,n_tests=int(match.group(1)) if match else None))
(HERE/'TESTS.log').write_text('\n\n'.join(logs))
result=dict(verdict='PASS' if all(r['returncode']==0 for r in results) else 'FAIL',suites=results,scope='CPU_FIXTURES_NO_MODEL_CALLS')
(HERE/'TESTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
assert result['verdict']=='PASS','see_TESTS.log'
