import hashlib,json,tarfile
from pathlib import Path
from runner import OUT,HERE,ROOT,load,sha,verify_freeze
s=load(OUT/'STATUS.json')
if s.get('status')!='COMPLETE':
 print(json.dumps(s));raise SystemExit(0)
verify_freeze()
archive=HERE/'completed-run.tar.gz'
with tarfile.open(archive,'w:gz') as t:t.add(OUT,arcname=OUT.name)
print(json.dumps({'status':s,'archive':str(archive),'archive_sha256':sha(archive),'files':{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file()}}))
