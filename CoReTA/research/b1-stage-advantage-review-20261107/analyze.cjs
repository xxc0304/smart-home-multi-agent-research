// Retrospective auxiliary interpretation. Never writes to frozen runs or old scores.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const root=path.resolve(__dirname,'../..');const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const indexFile=path.join(root,'research/b1-phenomenon-prioritization-20261107/INDEX.json');
const rulesFile=path.join(__dirname,'rules.json'),rules=JSON.parse(fs.readFileSync(rulesFile,'utf8'));
const input=JSON.parse(fs.readFileSync(indexFile,'utf8'));
const detailFile=path.join(root,'research/b1-phenomenon-prioritization-20261107/ROWS.json');
const detailed=new Map(JSON.parse(fs.readFileSync(detailFile,'utf8')).map(r=>[r.key,r]));
const clean=x=>x.trim().replace(/^(?:answer|答案)\s*[:：]\s*/i,'').trim();
const norm=x=>clean(x).toLowerCase().replace(/[!"#$%&'()*+,\-./:;<=>?@[\]\\^_`{|}~]/g,'').replace(/\b(a|an|the)\b/g,' ').trim().replace(/\s+/g,' ');
const base=['M2','M3','M4'],actors=['M1',...base],stages=['I','A','C','B','D'];
const changes=[],hashes={[indexFile]:sha(indexFile),[detailFile]:sha(detailFile),[rulesFile]:sha(rulesFile)};
function value(r,stage,actor,profile){if(profile==='officialF1'){if(r.f1)return r.f1[stage][actor];const d=detailed.get(r.key);return stage==='I'?d.initialScores[actor].f1:d.arms[stage].score.members[actor].f1;}const text=stage==='I'?r.initials[actor]:r.arms[stage].finals[actor],formal=stage==='I'?r.initialEM[actor]:r.arms[stage].memberEM[actor];if(profile==='official'||formal)return formal;const lists=[['strict',rules.strict[r.key]],...(profile==='lenient'?[['lenient_additional',rules.lenient_additional[r.key]]]:[])];for(const [tier,rule]of lists)if(rule&&rule.aliases.some(t=>norm(t)===norm(text))){changes.push({key:r.key,id:r.id,source:r.source??'main',rep:r.rep??null,stage,actor,profile,tier,raw:text,formal,auxiliary:1,reason:rule.reason});return 1;}return formal;}
const profiles=['official','officialF1','strict','lenient'];
const rows=input.map(r=>({...r,cohort:r.key.startsWith('old:')?'D80':'fresh56',values:Object.fromEntries(profiles.map(profile=>[profile,Object.fromEntries(stages.map(stage=>[stage,Object.fromEntries(actors.map(a=>[a,value(r,stage,a,profile)]))]))]))}));
assert.equal(rows.filter(r=>r.cohort==='fresh56'&&r.strict===true).length,29);
assert.equal(rows.filter(r=>r.cohort==='fresh56'&&r.strict===false).length,27);
const sum=a=>a.reduce((s,x)=>s+x,0),mean=a=>sum(a)/a.length;
function vector(r,profile){const x=r.values[profile],out={};for(const st of stages){out['E_'+st]=x[st].M1;out['O_'+st]=mean(base.map(a=>x[st][a]));out['gap_'+st]=out['E_'+st]-out['O_'+st];for(const a of base)out['gap_'+st+'_'+a]=x[st].M1-x[st][a];}
 for(const st of ['A','C']){out['gap_change_'+st+'I']=out['gap_'+st]-out.gap_I;out['E_change_'+st+'I']=out['E_'+st]-out.E_I;out['O_change_'+st+'I']=out['O_'+st]-out.O_I;}
 for(const [l,p]of [['B','A'],['D','C']]){out['E_communication_'+l+p]=out['E_'+l]-out['E_'+p];out['O_communication_'+l+p]=out['O_'+l]-out['O_'+p];out['gap_communication_'+l+p]=out['gap_'+l]-out['gap_'+p];}
 return out;}
function summarize(rs,profile,boot=true){
 const vs=rs.map(r=>vector(r,profile)),names=Object.keys(vs[0]),point=Object.fromEntries(names.map(k=>[k,mean(vs.map(v=>v[k]))]));
 const groups=[...new Set(rs.map(r=>r.group))];const bins=groups.map(g=>rs.map((r,i)=>r.group===g?i:-1).filter(i=>i>=0));
 const results={n:rs.length,groups:groups.length,profile,point,stagePairs:Object.fromEntries(stages.map(st=>[st,{expertHigher:vs.filter(v=>v['gap_'+st]>0).length,same:vs.filter(v=>v['gap_'+st]===0).length,expertLower:vs.filter(v=>v['gap_'+st]<0).length,ordinaryMembers:Object.fromEntries(base.map(a=>[a,mean(rs.map(r=>r.values[profile][st][a]))]))}])),leaveOneGroupOut:Object.fromEntries(['gap_I','gap_A','gap_C','gap_change_AI','gap_change_CI'].map(k=>{const out=groups.map(g=>({omitted:g,value:mean(vs.filter((v,i)=>rs[i].group!==g).map(v=>v[k]))}));return[k,{min:Math.min(...out.map(z=>z.value)),max:Math.max(...out.map(z=>z.value))}];}))};
 if(boot){const sums=bins.map(ids=>Object.fromEntries(names.map(k=>[k,sum(ids.map(i=>vs[i][k]))]))),dist=Object.fromEntries(names.map(k=>[k,[]]));let state=20261107>>>0;const rand=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296;};for(let b=0;b<10000;b++){const counts=groups.map(()=>0);let n=0;for(let j=0;j<groups.length;j++){const k=Math.floor(rand()*groups.length);counts[k]++;n+=bins[k].length;}for(const k of names){let s=0;for(let g=0;g<groups.length;g++)s+=counts[g]*sums[g][k];dist[k].push(s/n);}}results.groupBootstrap95=Object.fromEntries(names.map(k=>{dist[k].sort((a,b)=>a-b);return[k,[dist[k][250],dist[k][9749]]];}));results.bootstrap={repeats:10000,seed:20261107,unit:'Declared dependency group; preserves same-task roles, stages and all related items',status:'Exploratory percentile intervals, not representative-population inference or confirmation'};}
 return results;
}
const summaries={};for(const cohort of ['D80','fresh56']){const all=rows.filter(r=>r.cohort===cohort);const flagged=new Set([...Object.keys(rules.known_question_flags.definite_nonunique),...Object.keys(rules.known_question_flags.expanded_stress)]);
 const samples={all,without_definite_nonunique:all.filter(r=>!rules.known_question_flags.definite_nonunique[r.key]),without_expanded_known_flags:all.filter(r=>!flagged.has(r.key))};
 if(cohort==='fresh56'){samples.strict_training_answer=all.filter(r=>r.strict===true);samples.training_answer_string_overlap=all.filter(r=>r.strict===false);}
 summaries[cohort]=Object.fromEntries(Object.entries(samples).map(([sample,rs])=>[sample,Object.fromEntries(profiles.map(profile=>[profile,summarize(rs,profile)]))]));
}
// Actual work-token cost from original records, preserving cohort and condition.
const cost={};const med=a=>{const s=[...a].sort((a,b)=>a-b);return(s[Math.floor((s.length-1)/2)]+s[Math.ceil((s.length-1)/2)])/2;};
for(const r of rows){const p=path.join(root,r.cohort==='D80'?`runs/b1-dev80-20261106-v1/trials/${String(+r.key.split(':')[1]).padStart(3,'0')}.json`:`runs/b1-grounded-revision-20261107-v1/trials/${String(+r.key.split(':')[1]).padStart(3,'0')}.json`);hashes[p]=sha(p);const t=JSON.parse(fs.readFileSync(p,'utf8'));
 for(const c of ['A','C','B','D'])for(const role of ['expert','ordinary']){const records=(r.cohort==='D80'?t.records.filter(z=>z.arm===c):t.branches[c].records).filter(z=>z.stage==='work'&&(role==='expert'?z.actor==='M1':base.includes(z.actor)));
 const k=r.cohort+'/'+c+'/'+role;if(!cost[k])cost[k]={tokens:[],caps:[],inputTokens:[]};for(const z of records){cost[k].tokens.push(z.usage.output_tokens);cost[k].caps.push(z.max_new_tokens);cost[k].inputTokens.push(z.usage.input_tokens);}}
}
const outputCost=Object.fromEntries(Object.entries(cost).map(([k,z])=>[k,{workCalls:z.tokens.length,outputTokens:sum(z.tokens),meanOutputPerWork:mean(z.tokens),medianOutputPerWork:med(z.tokens),meanInputPerWork:mean(z.inputTokens),caps:[...new Set(z.caps)]}]));
// Reuse already-completed two-seed private controls as ancillary evidence only.
// These are selected old tasks, NOT a second seed on the new56 or independent new N.
const repeatScore=path.join(root,'runs/b1-independent-first-work-20261106-v1/scores.json');
const repeatInput=path.join(root,'runs/b1-independent-first-work-20261106-v1/INPUTS.json');
hashes[repeatScore]=sha(repeatScore);hashes[repeatInput]=sha(repeatInput);
const priorRepeat=JSON.parse(fs.readFileSync(repeatScore,'utf8')),priorRepeatInput=JSON.parse(fs.readFileSync(repeatInput,'utf8'));
const fullOldFile=path.join(root,'research/b1-dev80-analysis-20261106/ANALYSIS.json'),oldInputFile=path.join(root,'runs/b1-dev80-20261106-v1/INPUTS.json'),oldScoreFile=path.join(root,'runs/b1-dev80-20261106-v1/checkpoints/080/scores.json');
for(const p of [fullOldFile,oldInputFile,oldScoreFile])hashes[p]=sha(p);
const fullOld=JSON.parse(fs.readFileSync(fullOldFile,'utf8')),oldPack=JSON.parse(fs.readFileSync(oldInputFile,'utf8')),oldScore=JSON.parse(fs.readFileSync(oldScoreFile,'utf8'));
const auxRows=priorRepeat.rows.map(x=>{let old=input.find(r=>r.id===x.id);if(!old){const m=fullOld.cases.find(r=>r.id===x.id);assert(m);old={key:`old:${m.index}`,id:m.id,group:oldPack.groups[m.id],question:m.question,gold:m.target.answer,aliases:m.target.answer_aliases};}assert(old.key===`old:${x.index}`);const q={...old,source:'existing_selected_D25_two_seed',rep:x.rep,coverage:x.coverage,group:old.group,initials:Object.fromEntries(actors.map(a=>[a,x.initial[a].answer])),initialEM:Object.fromEntries(actors.map(a=>[a,x.initial[a].em])),arms:Object.fromEntries(['A','B','C','D'].map(c=>{assert(x.conditions[c].complete);return[c,{finals:Object.fromEntries(actors.map(a=>[a,x.conditions[c].members[a].answer])),memberEM:Object.fromEntries(actors.map(a=>[a,x.conditions[c].members[a].em]))}];})),f1:Object.fromEntries(stages.map(st=>[st,Object.fromEntries(actors.map(a=>[a,st==='I'?x.initial[a].f1:x.conditions[st].members[a].f1]))]))};return{...q,values:Object.fromEntries(profiles.map(p=>[p,Object.fromEntries(stages.map(st=>[st,Object.fromEntries(actors.map(a=>[a,value(q,st,a,p)]))]))]))};});
assert.equal(auxRows.length,50);assert.equal(new Set(auxRows.map(r=>r.id)).size,25);
const existingTwoSeed={scope:'ANCILLARY_PURPOSEFULLY_SELECTED_OLD_25_NOT_NEW56_REPLICATION',nDistinctTasks:25,protocol:'Rep affects sampling and speaking order; private A/C has own history only, so no peer-order exposure. Public contrasts do not isolate order.',byRep:Object.fromEntries([0,1].map(rep=>[rep,Object.fromEntries(['coverage24','all25'].map(subset=>{const rs=auxRows.filter(r=>r.rep===rep&&(subset==='all25'||r.coverage));assert.equal(rs.length,subset==='all25'?25:24);return[subset,Object.fromEntries(profiles.map(p=>[p,summarize(rs,p,false)]))];}))])),inputOriginalRepeats:priorRepeatInput.repeats};
// Fixed80 missing-outcome envelopes: arithmetic limits, not population intervals.
const oldBounds={scope:'OFFICIAL_ONLY_FIXED80_MISSING_OUTCOME_ARITHMETIC_BOUNDS_NOT_CONFIDENCE_INTERVALS',planned:80,initialComplete:0,stages:{}};
const gap=m=>m.M1.em-mean(base.map(a=>m[a].em));
const interval=(r,st)=>{const m=st==='I'?r.initial?.members:r.arms[st]?.complete?r.arms[st].members:null;return m&&actors.every(a=>m[a])?[gap(m),gap(m)]:[-1,1];};
oldBounds.initialComplete=oldScore.reports.filter(r=>interval(r,'I')[0]===interval(r,'I')[1]).length;
for(const st of ['A','C']){let lower=0,upper=0,gapL=0,gapU=0,n=0;for(const r of oldScore.reports){const [a,b]=interval(r,st),[c,d]=interval(r,'I');gapL+=a;gapU+=b;lower+=a-d;upper+=b-c;if(a===b)n++;}oldBounds.stages[st]={complete:n,gapBounds:[gapL/80,gapU/80],gapChangeFromInitialBounds:[lower/80,upper/80]};}
const sourceUnchanged=Object.entries(hashes).every(([p,h])=>sha(p)===h);assert(sourceUnchanged);
// Meaningful safeguards: auxiliary interpretation cannot repair a changed target.
const bykey=new Map(rows.map(r=>[r.key,r]));
for(const [key,stage,actor]of [['new:34','C','M1'],['old:52','B','M1'],['new:37','B','M1'],['new:44','B','M1']])assert.equal(bykey.get(key).values.strict[stage][actor],0);
assert.equal(bykey.get('new:9').values.strict.B.M2,1);
assert.equal(bykey.get('new:16').values.strict.I.M2,0);assert.equal(bykey.get('new:16').values.lenient.I.M2,1);
for(const r of rows)for(const st of stages)for(const a of actors){assert(r.values.official[st][a]<=r.values.strict[st][a]&&r.values.strict[st][a]<=r.values.lenient[st][a]);assert(r.values.officialF1[st][a]>=0&&r.values.officialF1[st][a]<=1);}
for(const c of Object.values(summaries))for(const s of Object.values(c))for(const p of Object.values(s))for(const st of ['A','C'])assert(Math.abs(p.point['gap_change_'+st+'I']-(p.point['E_change_'+st+'I']-p.point['O_change_'+st+'I']))<1e-12);
const out={scope:'RETROSPECTIVE_PAIRED_STAGE_ADVANTAGE_AND_SENSITIVITY_NOT_FULL_SEMANTIC_CENSUS',reviewer:'assistant',independence:'none/provisional',new_model_calls:0,rulesSHA256:sha(rulesFile),summaries,changes,outputCost,existingTwoSeed,oldBounds,auxRows:auxRows.map(r=>({key:r.key,id:r.id,group:r.group,rep:r.rep,coverage:r.coverage,values:r.values})),rows:rows.map(({values,...r})=>({key:r.key,id:r.id,group:r.group,cohort:r.cohort,strict:r.strict,values})),sourceUnchanged};
fs.writeFileSync(path.join(__dirname,'ANALYSIS.json'),JSON.stringify(out,null,2)+'\n');fs.writeFileSync(path.join(__dirname,'SOURCE_HASHES.json'),JSON.stringify({files:hashes,sourceUnchanged},null,2)+'\n');
console.log(JSON.stringify({main:Object.fromEntries(['D80','fresh56'].map(c=>[c,Object.fromEntries(profiles.map(p=>{const s=summaries[c].all[p];return[p,{n:s.n,groups:s.groups,point:s.point,intervals:s.groupBootstrap95,pairs:s.stagePairs}];}))])),changes:changes.length,outputCost},null,2));
