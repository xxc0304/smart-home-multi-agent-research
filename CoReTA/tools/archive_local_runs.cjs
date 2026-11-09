// Preserve locally available run artifacts in Git-sized, checksummed archives.
// No models, raw datasets, environment folders, or original run bytes are changed.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),cp=require('child_process');
const root=path.resolve(__dirname,'..'),runs=path.join(root,'runs');
const label=process.argv[2];if(!/^\d{8}$/.test(label||''))throw Error('usage: node tools/archive_local_runs.cjs YYYYMMDD');
const out=path.join(root,'experiment','archives','local-runs-'+label);fs.mkdirSync(out,{recursive:true});
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
function files(dir){let result=[];for(const e of fs.readdirSync(dir,{withFileTypes:true})){if(e.name==='__pycache__'||/\.py[co]$/.test(e.name))continue;const p=path.join(dir,e.name);if(e.isDirectory())result=result.concat(files(p));else if(e.isFile())result.push(p);else throw Error('unexpected link/special file: '+p);}return result;}
const manifest={scope:'All locally available CoReTA/runs folders at sync time, including partial/stopped snapshots; statuses are not assertions of full remote coverage.',archives:[]};
for(const e of fs.readdirSync(runs,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name))){
 if(!e.isDirectory())continue;
 const dir=path.join(runs,e.name),members=files(dir).sort().map(p=>({path:path.relative(runs,p).split(path.sep).join('/'),bytes:fs.statSync(p).size,sha256:sha(p)}));
 for(const m of members)if(/\.(safetensors|bin|pt|pth|ckpt)$/i.test(m.path))throw Error('model-like file requires separate storage: '+m.path);
 const archive=path.join(out,e.name+'.tar.gz');
 cp.execFileSync('tar',['-czf',archive,'--exclude=__pycache__','--exclude=*.pyc','--exclude=*.pyo','-C',runs,e.name],{stdio:['ignore','pipe','pipe']});
 const listing=cp.execFileSync('tar',['-tzf',archive],{encoding:'utf8',maxBuffer:30*1024*1024}).split(/\r?\n/).filter(s=>s&&!s.endsWith('/')).sort();
 if(JSON.stringify(listing)!==JSON.stringify(members.map(m=>m.path).sort()))throw Error('archive member mismatch: '+e.name);
 for(const m of members)if(sha(path.join(runs,m.path))!==m.sha256)throw Error('source changed during archive: '+m.path);
 let status=null;for(const n of ['STATUS.json','execution.json']){const p=path.join(dir,n);if(fs.existsSync(p)){const x=JSON.parse(fs.readFileSync(p,'utf8'));status={file:n,status:x.status||null,processed_units:x.processed_units??null,eligible_complete_units:x.eligible_complete_units??null,fatal_error:x.fatal_error??null};break;}}
 const bytes=fs.statSync(archive).size;if(bytes>=95*1024*1024)throw Error('archive too large for normal Git: '+e.name);
 manifest.archives.push({run:e.name,archive:path.basename(archive),archive_bytes:bytes,archive_sha256:sha(archive),uncompressed_bytes:members.reduce((s,m)=>s+m.bytes,0),local_status:status,members});
 console.log(JSON.stringify({run:e.name,files:members.length,archive_bytes:bytes}));
}
manifest.totals={archives:manifest.archives.length,files:manifest.archives.reduce((s,a)=>s+a.members.length,0),archive_bytes:manifest.archives.reduce((s,a)=>s+a.archive_bytes,0),uncompressed_bytes:manifest.archives.reduce((s,a)=>s+a.uncompressed_bytes,0)};
fs.writeFileSync(path.join(out,'MANIFEST.json'),JSON.stringify(manifest,null,2)+'\n');
fs.writeFileSync(path.join(out,'SHA256SUMS'),manifest.archives.map(a=>a.archive_sha256+'  '+a.archive).join('\n')+'\n');
console.log(JSON.stringify({completed:true,...manifest.totals}));
