"""CPU/fixture regressions followed by real historical compatibility replay."""
import json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
r=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_b1*.py','-v'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(HERE/'TESTS.log').write_text(r.stdout)
m=re.search(r'Ran (\d+) tests',r.stdout)
summary=dict(verdict='PASS' if r.returncode==0 else 'FAIL',returncode=r.returncode,n_tests=int(m.group(1)) if m else None,evidence='CPU_FIXTURES_NOT_MODEL_QUALITY')
(HERE/'TESTS.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
assert r.returncode==0,'fixture_tests_failed_see_TESTS.log'
subprocess.run([sys.executable,str(HERE/'compatibility.py')],cwd=ROOT,check=True)
