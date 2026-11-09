// Independent payload/provenance check on a stable prefix archive. No model or gold repair.
const fs=require('fs'),path=require('path'),assert=require('assert').strict,crypto=require('crypto');
const H=__dirname,R=path.resolve(H,'../..');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const config=read(path.join(H,'config.json')),inputs=read(path.join(H,'INPUTS.json')).entries;
const run=path.join(R,config.run_dir),rows=fs.readFileSync(path.join(run,'responses.jsonl'),'utf8').trim().split('\n').filter(Boolean).map(JSON.parse);
const old=fs.readFileSync(path.join(R,config.reused_response_source),'utf8').trim().split('\n').map(JSON.parse);
const expected={};let checks=0;
for(const r of rows){
 const e=inputs.find(x=>x.unit===r.unit),d=JSON.parse(r.payload.user.slice(10));
 assert.deepEqual(d.question,e.task.question);assert.deepEqual(d.paragraphs,e.task.paragraphs);
 assert.deepEqual(Object.keys(d).sort(),['question','paragraphs','own_earlier_answer','proposal',...(r.stage==='revision'?['independent_reviews']:[])].sort());
 assert.deepEqual(d.proposal,{answer:e.prefix.candidate,explanation:e.prefix.explanation});
 assert.equal(d.own_earlier_answer,e.prefix.initials[r.actor]);
 assert.equal(r.adapter_enabled,r.actor==='M1');
 assert.equal(r.usage.disabled_layers,r.actor==='M1'?0:252);assert.equal(r.usage.lora_layers,252);
 assert.equal(r.max_new_tokens,r.stage==='review'?768:256);
 assert.equal(r.seed,1200000000+r.unit*100000+(r.stage==='revision'?4000:r.slot));
 const k=r.unit+':'+r.arm;expected[k]??=[];
 if(r.stage==='review'){
  assert.equal(expected[k].length,r.slot);expected[k].push({slot:r.slot+1,text:r.raw_output});
 }else{assert.deepEqual(d.independent_reviews,expected[k]);}
 if(r.origin==='reused_model_response_v1'){
  const p=old[r.source_call];assert.equal(p.stage,'review');
  for(const key of ['payload','seed','max_new_tokens','raw_output','status','usage'])assert.deepEqual(r[key],p[key]);
 }
 checks++;
}
const result={result:'PASS',responses:rows.length,independent_payload_provenance_checks:checks,
 reused:rows.filter(r=>r.origin==='reused_model_response_v1').length,fresh:rows.filter(r=>r.origin==='model').length,
 response_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(run,'responses.jsonl'))).digest('hex'),
 scores_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(run,'scores.json'))).digest('hex')};
fs.writeFileSync(path.join(H,'LOCAL_ARCHIVE_CHECK.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
