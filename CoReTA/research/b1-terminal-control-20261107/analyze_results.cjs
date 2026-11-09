const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict,cp=require('child_process');
const root=path.resolve(__dirname,'../..'),run=path.join(root,'runs/b1-terminal-adapter-20261107-v1');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex'),read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const archive=path.join(__dirname,'completed-run.tar.gz');assert.equal(sha(archive),'d5a0c449a77a8d439856c5c31334728ad3ce62dc2bab100bc44f457043f130e8');
if(!fs.existsSync(run)){
 const names=cp.execFileSync('tar',['-tzf',archive],{encoding:'utf8'}).trim().split(/\r?\n/);
 assert(names.every(n=>n.startsWith('b1-terminal-adapter-20261107-v1/')&&!n.split('/').includes('..')&&!path.isAbsolute(n)));
 assert(run.startsWith(path.join(root,'runs')+path.sep));
 cp.execFileSync('tar',['-xzf',archive,'-C',path.join(root,'runs')]);
}
const members=cp.execFileSync('tar',['-tzf',archive],{encoding:'utf8'}).trim().split(/\r?\n/).filter(n=>!n.endsWith('/'));
const runHashes={};for(const member of members){const rel=member.slice('b1-terminal-adapter-20261107-v1/'.length),file=path.join(run,rel);assert(file.startsWith(run+path.sep));const expected=crypto.createHash('sha256').update(cp.execFileSync('tar',['-xOf',archive,member],{maxBuffer:20*1024*1024})).digest('hex');assert.equal(sha(file),expected);runHashes[rel]=expected;}
const pack=read(path.join(run,'DIAGNOSTIC_INPUTS.json')),labels=read(path.join(run,'DIAGNOSTIC_LABELS.json')).labels;
const recs=fs.readFileSync(path.join(run,'responses.jsonl'),'utf8').trim().split(/\r?\n/).map(JSON.parse),score=read(path.join(run,'scores.json'));
assert.equal(recs.length,48);assert.equal(read(path.join(run,'STATUS.json')).status,'COMPLETE');
const norm=x=>x.toLowerCase().replace(/[!"#$%&'()*+,\-./:;<=>?@[\]\\^_`{|}~]/g,'').replace(/\b(a|an|the)\b/g,' ').trim().replace(/\s+/g,' ');
function metrics(text,target){const answer=text.trim().replace(/^(?:answer|答案)\s*[:：]\s*/i,'').trim(),a=norm(answer);const scores=[target.answer,...target.answer_aliases].map(g=>{const b=norm(g),x=a.split(/\s+/).filter(Boolean),y=b.split(/\s+/).filter(Boolean);let common=0;const m={};for(const t of y)m[t]=(m[t]??0)+1;for(const t of x)if(m[t]){common++;m[t]--;}return{em:Number(a===b),f1:!x.length||!y.length?Number(x.length===y.length):common?2*common/(x.length+y.length):0};});return{answer,em:Math.max(...scores.map(s=>s.em)),f1:Math.max(...scores.map(s=>s.f1))};}
for(const r of recs){const req=pack.schedule.find(q=>q.id===r.request.id);assert.deepEqual(r.request,req);assert.equal(r.response.status,'OK');const sc=metrics(r.response.raw_output,labels[req.case_id].target),official=score.rows.find(z=>z.id===req.id).score;assert.equal(sc.em,official.em);assert(Math.abs(sc.f1-official.f1)<1e-12);assert.equal(sc.answer,official.answer);}
const cases=pack.cases.map(p=>({id:p.id,key:p.key,task_id:p.task_id,group:p.sourceGroup,stratum:p.stratum,gold:labels[p.id].target.answer,original:labels[p.id].originalFinal,work:labels[p.id].originalLastWork,rep:[0,1].map(rep=>{const on=score.rows.find(r=>r.case_id===p.id&&r.rep===rep&&r.adapter==='on'),off=score.rows.find(r=>r.case_id===p.id&&r.rep===rep&&r.adapter==='off');return{rep,on:on.answer,off:off.answer,onEM:on.score.em,offEM:off.score.em,delta:off.score.em-on.score.em,originalOnExact:on.originalFinalMatch};})}));
const summary={};for(const stratum of ['original_private_terminal_failure','original_stable_correct_control']){const xs=cases.filter(p=>p.stratum===stratum),pairs=xs.flatMap(p=>p.rep);summary[stratum]={differentGroups:xs.length,pairedGenerations:pairs.length,onCorrect:pairs.reduce((n,p)=>n+p.onEM,0),offCorrect:pairs.reduce((n,p)=>n+p.offEM,0),gains:pairs.filter(p=>p.delta>0).length,losses:pairs.filter(p=>p.delta<0).length,unchanged:pairs.filter(p=>p.delta===0).length,affectedTasks:xs.filter(p=>p.rep.some(r=>r.delta!==0)).map(p=>p.key)};}
const original=read(path.join(root,'research/b1-phenomenon-prioritization-20261107/INDEX.json'));
const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
const stageAdvantage={};for(const cohort of ['old','new']){const xs=original.filter(p=>p.key.startsWith(cohort+':'));stageAdvantage[cohort]={n:xs.length,initial:{expert:mean(xs.map(p=>p.initialEM.M1)),ordinary:mean(xs.flatMap(p=>['M2','M3','M4'].map(a=>p.initialEM[a])))},arms:Object.fromEntries(['A','B','C','D'].map(c=>[c,{expert:mean(xs.map(p=>p.arms[c].memberEM.M1)),ordinary:mean(xs.flatMap(p=>['M2','M3','M4'].map(a=>p.arms[c].memberEM[a])))}]))};}
const result={scope:'PURPOSEFUL_FIXED_PREFIX_ADAPTER_EFFECT_AND_EXISTING_TRAJECTORY_DESCRIPTIVES',new_model_calls:48,independentHumanReview:false,reviewer:'assistant',independence:'none/provisional',differentSourceGroups:12,summary,cases,stageAdvantage,all48OfficialScoresRecomputed:true,onOriginalSeedExact:cases.filter(p=>p.rep[0].originalOnExact).length,archiveSHA256:sha(archive),freezeSHA256:sha(path.join(run,'FREEZE.json')),runFilesMatchArchive:runHashes,remoteAudit:read(path.join(__dirname,'POST_RUN_AUDIT.json'))};
fs.writeFileSync(path.join(__dirname,'ANALYSIS.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({summary,cases,stageAdvantage},null,2));
