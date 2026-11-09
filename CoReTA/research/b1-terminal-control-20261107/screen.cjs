const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const root=path.resolve(__dirname,'../..');const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const rs=read('research/b1-phenomenon-prioritization-20261107/ROWS.json'),prior=read('research/b1-phenomenon-prioritization-20261107/ANNOTATIONS.json');
const norm=x=>x.toLowerCase().normalize('NFKD').replace(/\p{M}/gu,'').replace(/[^\p{L}\p{N}]/gu,' ').replace(/\b(a|an|the)\b/g,' ').trim().replace(/\s+/g,' ');
const extras={'old:46':['40%','40 percent'],'old:55':['40%','40 percent'],'new:15':['France'],'new:55':['1899'],'new:32':['Lop Lake'],'old:1':['north western coast','northwest coast']};
const all=[],candidates=[];
for(const r of rs)for(const arm of ['A','B','C','D'])for(const actor of ['M1','M2','M3','M4']){
 const rec=r.arms[arm].records.find(z=>z.stage==='work'&&z.round===2&&z.actor===actor);assert(rec);
 const final=r.arms[arm].finals[actor],em=r.arms[arm].score.members[actor].em;
 const variants=[r.target.answer,...r.target.answer_aliases,...(extras[r.key]??[])].map(norm).filter(Boolean);
 const hits=variants.filter(v=>(' '+norm(rec.raw_output)+' ').includes(' '+v+' '));
 const z={key:r.key,id:r.id,group:r.group,cohort:r.cohort,arm,actor,role:actor==='M1'?'expert':'ordinary',request_id:rec.request_id,question:r.task.question,gold:r.target.answer,aliases:r.target.answer_aliases,work:rec.raw_output,final,finalEM:em,hits,workEqualsFinal: norm(rec.raw_output)===norm(final),text_sha256:crypto.createHash('sha256').update(rec.raw_output).digest('hex')};
 all.push(z);if(!em&&hits.length)candidates.push(z);
}
const recall=prior.terminalSwitch.map(z=>({key:z.key,arm:z.arm,hit:candidates.some(c=>c.key===z.key&&c.arm===z.arm&&c.actor==='M1')}));assert(recall.every(z=>z.hit));
const unique=new Map();for(const z of candidates){const key=z.id+'|'+z.work+'|'+z.final;if(!unique.has(key))unique.set(key,{uid:unique.size,question:z.question,gold:z.gold,aliases:z.aliases,work:z.work,final:z.final,refs:[]});unique.get(key).refs.push({key:z.key,arm:z.arm,actor:z.actor,role:z.role,request_id:z.request_id});}
const write=(n,x)=>fs.writeFileSync(path.join(__dirname,n),JSON.stringify(x,null,2)+'\n');
write('SCREEN.json',{scope:'LEXICAL_WIDE_RECALL_NOT_SEMANTIC_EVENT_JUDGE',norm: norm.toString(),extras,rows:all.map(({work,...z})=>z),candidates,knownExpertRecall:recall});write('REVIEW_PACK.json',[...unique.values()]);
const sizes={};for(const c of ['D80','fresh56'])for(const role of ['expert','ordinary'])for(const vis of ['private','public']){const xs=all.filter(z=>z.cohort===c&&z.role===role&&(['A','C'].includes(z.arm)===(vis==='private'))),ys=candidates.filter(z=>xs.some(x=>x.request_id===z.request_id&&x.arm===z.arm));sizes[c+'/'+role+'/'+vis]={paths:xs.length,finalEM0:xs.filter(z=>!z.finalEM).length,candidatePaths:ys.length,uniqueCandidateWork:new Set(ys.map(z=>z.work)).size};}
console.log(JSON.stringify({sizes,candidateUnique:unique.size,knownExpertRecall:recall.length,reviewWords:[...unique.values()].reduce((n,z)=>n+z.work.split(/\s+/).length,0)}));
