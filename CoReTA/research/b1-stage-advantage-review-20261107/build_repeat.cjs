const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const root=path.resolve(__dirname,'../..'),source=path.join(root,'runs/b1-grounded-revision-20261107-v1');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const original=read(path.join(source,'INPUTS.json')),labels=read(path.join(source,'LABELS.json')).targets;
const config=read(path.join(source,'config.json'));config.purpose='FIXED_ORDER_ADDITIONAL_GENERATION_SEED_STAGE_ADVANTAGE_REPLICATION';
let elapsed=0,outTokens=0;const tasks=[],sources={};
for(const e of original.tasks.filter(e=>e.cohort==='fresh')){
 const rel=`runs/b1-grounded-revision-20261107-v1/trials/${String(e.index).padStart(3,'0')}.json`,t=read(path.join(root,rel));sources['/data2/xiaoxinchen/agent-research/CoReTA/'+rel]=sha(path.join(root,rel));
 assert(['A','B','C','D'].every(c=>t.branches[c].complete));
 assert.deepEqual(t.branches.A.config,t.branches.B.config);assert.deepEqual(t.branches.A.initial_order,t.branches.D.initial_order);assert.deepEqual(t.branches.A.orders,t.branches.D.orders);
 const recs=[...t.initial_records,...['A','B','C','D'].flatMap(c=>t.branches[c].records)];assert.equal(recs.length,52);
 elapsed+=recs.reduce((n,r)=>n+r.usage.elapsed_seconds,0);outTokens+=recs.reduce((n,r)=>n+r.usage.output_tokens,0);
 tasks.push({index:e.index,id:e.id,task:e.task,strict:e.strict_training_answer_isolation,group:original.groups[e.id],sourcePath:rel,sourceConfig:t.branches.A.config,initial_order:t.branches.A.initial_order,orders:t.branches.A.orders});
}
assert.equal(tasks.length,56);assert.equal(tasks.filter(e=>e.strict).length,29);
const pack={scope:'SAME56_DEVELOPMENT_TASKS_ADDITIONAL_SEED_NOT_NEW_INDEPENDENT_N',generation_seed_offset:100000000,order_policy:'Original initial display order and both work speaking orders unchanged; only generation seeds offset',tasks,source_sha256:sources};
const budget={questions:56,sourceGroups:new Set(tasks.map(e=>e.group)).size,conditions:['A','B','C','D'],max_calls:56*52,max_output_tokens:56*(4*256+4*(8*1024+4*256)),wall_clock_cutoff:null,generation_retry:false,execution:'ALL_SINGLETON',actual_source_comparable_seconds:elapsed,actual_source_output_tokens:outTokens,source_time_is_reference_not_deadline:true};
for(const [name,x] of Object.entries({'REPEAT_INPUTS.json':pack,'REPEAT_LABELS.json':{targets:Object.fromEntries(tasks.map(e=>[e.id,labels[e.id]]))},'repeat_config.json':config,'REPEAT_BUDGET.json':budget}))fs.writeFileSync(path.join(__dirname,name),JSON.stringify(x,null,2)+'\n');
console.log(JSON.stringify(budget));
