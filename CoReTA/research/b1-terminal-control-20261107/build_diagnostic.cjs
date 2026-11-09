const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const root=path.resolve(__dirname,'../..'),read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const rows=read('research/b1-phenomenon-prioritization-20261107/ROWS.json').filter(r=>r.cohort==='fresh56');
const ann=read('research/b1-phenomenon-prioritization-20261107/ANNOTATIONS.json');
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const rank=z=>sha(z.key+'/'+z.arm),failureCandidates=ann.terminalSwitch.filter(z=>rows.some(r=>r.key===z.key)).sort((a,b)=>rank(a).localeCompare(rank(b)));
const failures=[],used=new Set();for(const z of failureCandidates)if(!used.has(z.group)){failures.push({...z,stratum:'original_private_terminal_failure'});used.add(z.group);}
assert.equal(failures.length,6);
// Stable in all four original expert final EM, correct private last-work target;
// exclude already-known source/semantic ambiguities and overlapping source groups.
const sourceBoundary=new Set([9,13,15,20,22,24,32,38,42,49,51,52,53,54,55]);
const controls=rows.filter(r=>!used.has(r.group)&&!sourceBoundary.has(r.index)&&['A','B','C','D'].every(c=>r.arms[c].score.expert_em===1)).flatMap(r=>['A','C'].filter(c=>ann.lastWork.find(z=>z.key===r.key&&z.arm===c).label==='C').map(arm=>({key:r.key,arm,group:r.group,stratum:'original_stable_correct_control'}))).sort((a,b)=>rank(a).localeCompare(rank(b)));
const selected=[...failures];for(const z of controls)if(selected.length<12&&!used.has(z.group)){selected.push(z);used.add(z.group);}
assert.equal(selected.length,12);assert.equal(used.size,12);
const cases=[],labels={};
for(const [i,z]of selected.entries()){
 const r=rows.find(r=>r.key===z.key),source=`runs/b1-grounded-revision-20261107-v1/trials/${String(r.index).padStart(3,'0')}.json`,trial=read(source);
 const rec=trial.branches[z.arm].records.find(q=>q.actor==='M1'&&q.stage==='final');
 const work=trial.branches[z.arm].records.find(q=>q.actor==='M1'&&q.stage==='work'&&q.round===2);
 const data=JSON.parse(rec.payload.user.slice(rec.payload.user.indexOf('{'),rec.payload.user.lastIndexOf('}')+1));
 assert.equal(data.own_actor,'M1');assert(data.history.every(h=>h.sender==='M1'));assert.equal(data.history.at(-1).text,work.raw_output);assert.equal(rec.max_new_tokens,256);
 const id=`p${String(i).padStart(2,'0')}`;
 cases.push({id,key:z.key,task_id:r.id,sourceGroup:r.group,stratum:z.stratum,sourceArm:z.arm,sourcePath:source,sourceSHA256:sha(fs.readFileSync(path.join(root,source))),request:{payload:rec.payload,seed:rec.seed,max_new_tokens:256},payloadSHA256:sha(JSON.stringify(rec.payload)),sourceFinalRequestId:rec.request_id,workSHA256:sha(work.raw_output)});
 labels[id]={task_id:r.id,target:r.target,originalFinal:rec.raw_output,originalLastWork:work.raw_output,originalStatus:rec.status,stratum:z.stratum};
}
const schedule=[];for(const p of cases)for(const rep of [0,1]){const routes=(parseInt(sha(p.id+'/'+rep).slice(0,2),16)%2)?['on','off']:['off','on'];for(const route of routes)schedule.push({id:`${p.id}/r${rep}/${route}`,case_id:p.id,rep,adapter:route,actor:route==='on'?'M1':'M2',seed:p.request.seed+rep*100000000,max_new_tokens:256,payload:p.request.payload});}
assert.equal(schedule.length,48);assert(schedule.every(r=>!JSON.stringify(r.payload).includes('originalFinal')));
for(const p of cases)for(const rep of [0,1]){const pair=schedule.filter(r=>r.case_id===p.id&&r.rep===rep);assert.deepEqual(pair[0].payload,pair[1].payload);assert.equal(pair[0].seed,pair[1].seed);}
const pack={version:1,scope:'PURPOSEFUL_FIXED_FINAL_PREFIX_ADAPTER_ROUTE_DIAGNOSTIC_NOT_TEAM_METHOD_OR_PREVALENCE',cases,schedule,seeds:'original final seed and +100000000; paired on/off',route:'actor is backend routing metadata only; model-visible own_actor remains M1 in both conditions',new_model_calls:0};
const config=read('runs/b1-grounded-revision-20261107-v1/config.json');config.purpose='FIXED_FINAL_PREFIX_ADAPTER_DIAGNOSTIC';
for(const [n,v]of Object.entries({'DIAGNOSTIC_INPUTS.json':pack,'DIAGNOSTIC_LABELS.json':{labels},'diagnostic_config.json':config}))fs.writeFileSync(path.join(__dirname,n),JSON.stringify(v,null,2)+'\n');
console.log(JSON.stringify({cases:cases.map(p=>({id:p.id,key:p.key,arm:p.sourceArm,group:p.sourceGroup,stratum:p.stratum})),max_calls:48,max_output_tokens:12288,model_visible_payload_same:true}));
