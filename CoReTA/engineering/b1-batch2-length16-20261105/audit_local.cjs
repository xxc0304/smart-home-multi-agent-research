const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const base=path.resolve(__dirname,'../../../../lab-diagnostics-20261105/b1-batch2-length16-20261105-v1');
const read=n=>JSON.parse(fs.readFileSync(path.join(base,n),'utf8'));
const lines=n=>fs.readFileSync(path.join(base,n),'utf8').trim().split('\n').filter(Boolean).map(JSON.parse);
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const inputs=read('INPUTS.json'),result=read('RESULTS.json'),freeze=read('FREEZE.json'),approval=read('APPROVAL.json');
assert.equal(hash(path.join(base,'FREEZE.json')),approval.freeze_sha256);
let sourceCount=0;
for(const [p,h] of Object.entries(freeze.files)){
 if(p.endsWith('.py')){assert.equal(hash(path.join(base,'frozen_sources',p.split('/CoReTA/')[1])),h);sourceCount++;}
 if(p.includes('/runs/b1-batch2-length16-20261105-v1/'))assert.equal(hash(path.join(base,p.split('/runs/b1-batch2-length16-20261105-v1/')[1])),h);
}
const rows=lines('responses.jsonl'),attempts=lines('ATTEMPTS.jsonl');
assert.equal(rows.length,16);assert.equal(attempts.reduce((n,a)=>n+a.indices.length,0),16);
const key=r=>[r.cap,r.engine,r.index].join(':');const byKey=new Map(rows.map(r=>[key(r),r]));assert.equal(byKey.size,16);
let eos=read('BACKEND.json').effective_generation_config.eos_token_id;if(!Array.isArray(eos))eos=[eos];
for(const r of rows){
 assert.deepEqual(r.request,{...inputs.requests[r.index],max_new_tokens:r.cap});
 const u=r.usage;assert.equal(u.adapter_enabled,false);assert.equal(u.disabled_layers,u.lora_layers);
 assert.equal(u.input_tokens,inputs.lengths[r.index]);assert.equal(u.output_ids.length,u.output_tokens);
 if(u.batch_size>1){assert.equal(u.rng_seed,r.request.seed);assert.notEqual(u.rng_before,u.rng_after);}
 if(r.status==='OK'){assert.equal(u.finish_reason,'EOS');assert(eos.includes(u.output_ids.at(-1)));}
 else{assert.equal(r.status,'OUTPUT_LIMIT');assert.equal(u.finish_reason,'TOKEN_LIMIT');assert.equal(u.output_tokens,r.cap);assert(!eos.includes(u.output_ids.at(-1)));}
}
const caps=[512,1024],engines=['serial','batch2'],summary={};
for(const cap of caps)for(const engine of engines){
 const rs=rows.filter(r=>r.cap===cap&&r.engine===engine);assert.equal(rs.length,4);
 const aa=attempts.filter(r=>r.cap===cap&&r.engine===engine),size={serial:1,batch2:2}[engine];
 assert.deepEqual(aa.flatMap(a=>a.indices),[0,1,2,3]);assert(aa.every(a=>a.indices.length===size));
 for(const a of aa)for(const i of a.indices){const r=byKey.get(`${cap}:${engine}:${i}`);assert.equal(r.usage.batch_size,size);assert.equal(r.usage.padded_input_tokens,Math.max(...a.indices.map(j=>inputs.lengths[j])));}
 summary[`${cap}:${engine}`]={EOS:rs.filter(r=>r.status==='OK').length,TOKEN_LIMIT:rs.filter(r=>r.status==='OUTPUT_LIMIT').length};
}
let prefixSame=0,originalBatchSame=0;
for(let i=0;i<4;i++){
 if(JSON.stringify(byKey.get(`512:batch2:${i}`).usage.output_ids)===JSON.stringify(inputs.original_records[i].usage.output_ids))originalBatchSame++;
 for(const e of engines){const a=byKey.get(`512:${e}:${i}`),b=byKey.get(`1024:${e}:${i}`);if(JSON.stringify(a.usage.output_ids)===JSON.stringify(b.usage.output_ids.slice(0,a.usage.output_ids.length)))prefixSame++;}
}
for(const t of result.targets)for(const c of t.cases){const r=byKey.get(`${c.cap}:${c.engine}:${t.index}`);assert.equal(c.status,r.status);assert.equal(c.output_tokens,r.usage.output_tokens);assert.equal(c.raw_output,r.raw_output);}
assert.equal(result.attempted_requests,16);assert.equal(result.returned_responses,16);assert.equal(result.status,'COMPLETE');
const audit={verdict:'PASS_DIAGNOSTIC_INTEGRITY',reviewer:'assistant',independence:'none/provisional',source_hashes_verified:sourceCount,approval_bound:true,actual_attempts:16,actual_returns:16,all_payloads_and_seeds_match:true,route_flags_and_EOS_valid:true,each_cell_all4_inputs:true,prefix_pairs_identical_of8:prefixSame,original_batch2_token_reproductions_of4:originalBatchSame,summary,scope:'SELECTED_FAILURE_WORK_DIAGNOSTIC_NOT_TEAM_QUALITY'};
fs.writeFileSync(path.join(__dirname,'POST_RUN_AUDIT.json'),JSON.stringify(audit,null,2)+'\n');console.log(JSON.stringify(audit));
