const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const root=path.resolve(__dirname,'../..');const load=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const rows=load('research/b1-phenomenon-prioritization-20261107/ROWS.json'),ann=load('research/b1-phenomenon-prioritization-20261107/ANNOTATIONS.json');
const at=(r,c)=>ann.lastWork.find(z=>z.key===r.key&&z.arm===c),sum=(xs,fn)=>xs.reduce((n,x)=>n+fn(x),0),mean=(xs,fn)=>sum(xs,fn)/xs.length;
const wilson=(k,n)=>{if(!n)return null;const z=1.959963984540054,p=k/n,d=1+z*z/n,m=(p+z*z/(2*n))/d,h=z*Math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return[Math.max(0,m-h),Math.min(1,m+h)];};
function bin(k,n){return{events:k,opportunities:n,rate:k/n,descriptive_wilson95_iid_reference_only:wilson(k,n)};}
// Resample task-dependency groups, carrying every item in the selected group.
// Exploratory precision only: not representative sampling, no confirmatory testing.
function groupCI(rs,fn,seed=20261107){let state=seed>>>0;const rand=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296;};const groups=[...new Set(rs.map(r=>r.group))].map(g=>rs.filter(r=>r.group===g));const bs=[];for(let b=0;b<4000;b++){let s=0,n=0;for(let j=0;j<groups.length;j++)for(const r of groups[Math.floor(rand()*groups.length)]){s+=fn(r);n++;}bs.push(s/n);}bs.sort((a,b)=>a-b);return[bs[Math.floor(.025*bs.length)],bs[Math.floor(.975*bs.length)]];}
const readoutNotes={
 'old:12/B':['SURFACE_EQUIVALENCE','CSIC abbreviation appended; peers share institution semantically.'],
 'old:13/B':['NO_CLEAR_PUBLIC_TARGET','Public work misbinds birthplace/denies source; final E target alone is not public contribution.'],
 'old:13/D':['MIXED_PUBLIC_AND_WEAK_SOURCE','Correct agency appears after wrong birthplace reasoning; source bridge incomplete.'],
 'old:26/B':['PUBLIC_TARGET_WITHDRAWN','38m mentioned then band-sales question changed to album sales.'],
 'old:26/D':['PUBLIC_TARGET_WITHDRAWN','Correct band total appears but is denied as answering question.'],
 'old:29/B':['NO_CLEAR_PUBLIC_TARGET_AND_SOURCE_BOUNDARY','Denies founder availability; multi-producer source bridge weak.'],
 'old:29/D':['NO_CLEAR_PUBLIC_TARGET_AND_SOURCE_BOUNDARY','Denies founder availability; no correct contribution commitment.'],
 'old:35/D':['NO_CLEAR_PUBLIC_TARGET_AND_SOURCE_BOUNDARY','Denies founder; Chrysler/DaimlerChrysler corporate identity boundary.'],
 'old:37/B':['NO_CLEAR_PUBLIC_TARGET','Correct child never clearly endorsed in either public work; private final recovery.'],
 'old:37/D':['NO_CLEAR_PUBLIC_TARGET','Correct child never clearly endorsed in either public work; private final recovery.'],
 'old:47/B':['MIXED_PUBLIC_AND_WEAK_SOURCE','Expected party inferred then explicitly disclaimed; weak source bridge.'],
 'old:50/D':['NO_CLEAR_PUBLIC_TARGET_AND_SOURCE_BOUNDARY','No clear correct father relation; homonymous Dodgsons and missing bridge.'],
 'old:59/B':['PUBLIC_TARGET_WITHDRAWN','Kangchenjunga mentioned but answer redirected to body discovery/Everest.'],
 'old:69/B':['CLEAR_LOCAL_PUBLIC_NONADOPTION_WEAK_UPSTREAM','2.5 country vs2.4city explicitly distinguished; peers keep2.4; origin-of-sport premise not fully established.'],
 'old:72/B':['SURFACE_EQUIVALENCE','Peers give same office plus Church qualifier.'],
 'new:9/B':['SURFACE_EQUIVALENCE','three and3 same number.'],
 'new:9/D':['SURFACE_EQUIVALENCE','three and3 same number.'],
 'new:31/B':['MIXED_PUBLIC_TARGET','1878 bound to guide then withheld; not unambiguously correct public author relation.'],
 'new:35/D':['NO_CLEAR_PUBLIC_TARGET','Both public works deny creation date; final E1994 correct only at private submission.'],
 'new:49/D':['NO_CLEAR_PUBLIC_TARGET','Both public works choose newspaper1963 rather than university1960.'],
 'new:51/B':['SUPPORTED_TOPIC_GRANULARITY','Peers presidency during Civil War supported by source; not clear substantive rejection.']
};
const misses=[];for(const r of rows)for(const c of ['B','D'])if(r.arms[c].score.expert_em===1&&r.arms[c].score.expected_em<1){const note=readoutNotes[`${r.key}/${c}`];assert(note);misses.push({key:r.key,arm:c,id:r.id,group:r.group,expectedEM:r.arms[c].score.expected_em,expertFinal:r.arms[c].finals.M1,lastWorkLabel:at(r,c).label,kind:note[0],note:note[1],finals:r.arms[c].finals});}
assert.equal(misses.length,Object.keys(readoutNotes).length);
const publicSwitches=ann.terminalReviews.filter(z=>['B','D'].includes(z.arm)&&z.kind==='SUBSTANTIVE_DIFFERENT_TARGET');
assert.equal(publicSwitches.length,0); // Verified list of every C->EM0 public discrepancy.
const summaries={};
for(const cohort of ['D80','fresh56']){
 const rs=rows.filter(r=>r.cohort===cohort),ps=ann.matchedExpertChanges.filter(z=>rs.some(r=>r.key===z.key)),ts=ann.terminalSwitch.filter(z=>rs.some(r=>r.key===z.key));
 const arms=Object.fromEntries(['A','B','C','D'].map(c=>[c,{n:rs.length,expertEM:mean(rs,r=>r.arms[c].score.expert_em),teamExpectedEM:mean(rs,r=>r.arms[c].score.expected_em),lastWorkLabels:Object.fromEntries(['C','M','N'].map(l=>[l,rs.filter(r=>at(r,c).label===l).length])),strictTerminalSwitch:ts.filter(z=>z.arm===c).length}]));
 const pairs=Object.fromEntries([['A','B'],['C','D']].map(([p,d])=>{const harms=ps.filter(z=>z.contrast===`${d}-${p}`&&z.direction==='harm'),gains=ps.filter(z=>z.contrast===`${d}-${p}`&&z.direction==='gain');return[`${d}-${p}`,{expertHarm:bin(harms.length,rs.filter(r=>r.arms[p].score.expert_em===1).length),expertGain:bin(gains.length,rs.filter(r=>r.arms[p].score.expert_em===0).length),gainWithPrivateTerminalSwitch:gains.filter(z=>z.privateTerminalSwitch).length,expertDelta:mean(rs,r=>r.arms[d].score.expert_em-r.arms[p].score.expert_em),expertDeltaGroupBootstrap95:groupCI(rs,r=>r.arms[d].score.expert_em-r.arms[p].score.expert_em),teamDelta:mean(rs,r=>r.arms[d].score.expected_em-r.arms[p].score.expected_em),teamDeltaGroupBootstrap95:groupCI(rs,r=>r.arms[d].score.expected_em-r.arms[p].score.expected_em),harmKeys:harms.map(z=>z.key),gainKeys:gains.map(z=>z.key)}];}));
 const strata={};for(const name of ['E_initial_only_correct','E_initial_wrong_any_base_correct']){const sub=rs.filter(r=>name==='E_initial_only_correct'?r.initialScores.M1.em===1&&['M2','M3','M4'].every(a=>r.initialScores[a].em===0):r.initialScores.M1.em===0&&['M2','M3','M4'].some(a=>r.initialScores[a].em===1));strata[name]={n:sub.length,groups:new Set(sub.map(r=>r.group)).size,Aexpert:sum(sub,r=>r.arms.A.score.expert_em),Bexpert:sum(sub,r=>r.arms.B.score.expert_em),BteamExpected:sum(sub,r=>r.arms.B.score.expected_em),keys:sub.map(r=>r.key)};}
 const privateCommitted=sum(rs,r=>['A','C'].filter(c=>at(r,c).label==='C').length),publicCommitted=sum(rs,r=>['B','D'].filter(c=>at(r,c).label==='C').length);
 const terminalTasks=rs.filter(r=>ts.some(z=>z.key===r.key));
 summaries[cohort]={n:rs.length,dependencyGroups:new Set(rs.map(r=>r.group)).size,arms,pairs,strata,terminal:{privatePathRate:bin(ts.length,2*rs.length),privateGivenCommittedCandidate:bin(ts.length,privateCommitted),privateTasks:bin(terminalTasks.length,rs.length),privateEventDependencyGroups:new Set(terminalTasks.map(r=>r.group)).size,privateTaskGroupBootstrap95:groupCI(rs,r=>Number(ts.some(z=>z.key===r.key))),privatePathGroupBootstrap95:groupCI(rs,r=>ts.filter(z=>z.key===r.key).length/2),publicStrictEvents:0,publicPaths:2*rs.length,publicCommittedCandidatePaths:publicCommitted,scope:'No substantive different-target public-last-work->expert-final switches found in this coarse target review. Zero not population absence; partial/underspecification/semantic equivalents excluded.'},readout:{formalPaths:misses.filter(z=>rs.some(r=>r.key===z.key)).length,formalTasks:new Set(misses.filter(z=>rs.some(r=>r.key===z.key)).map(z=>z.key)).size,rows:misses.filter(z=>rs.some(r=>r.key===z.key))},homogeneity:{baseInitialRawSame:rs.filter(r=>new Set(['M2','M3','M4'].map(a=>r.initials[a])).size===1).length,baseFinalBRawSame:rs.filter(r=>new Set(['M2','M3','M4'].map(a=>r.arms.B.finals[a])).size===1).length}};
}
// Source-specific examples: input, final history and raw answer recording checks.
const payloadChecks=[];
for(const r of rows){
 const trial=r.cohort==='D80'?load(`runs/b1-dev80-20261106-v1/trials/${String(r.index).padStart(3,'0')}.json`):load(`runs/b1-grounded-revision-20261107-v1/trials/${String(r.index).padStart(3,'0')}.json`);
 for(const c of ['A','B','C','D']){
  const recs=r.cohort==='D80'?trial.records.filter(z=>z.arm===c):trial.branches[c].records;
  const e2=recs.find(z=>z.actor==='M1'&&z.stage==='work'&&z.round===2),final=recs.find(z=>z.actor==='M1'&&z.stage==='final');
  const txt=final.payload.user,data=JSON.parse(txt.slice(txt.indexOf('{'),txt.lastIndexOf('}')+1));
  assert.equal(data.question,r.task.question);assert.equal(data.own_actor,'M1');assert.equal(final.raw_output,r.arms[c].finals.M1);
  const hs=data.history.filter(z=>z.sender==='M1'&&z.phase==='work'&&z.round===2);assert.equal(hs.length,1);assert.equal(hs[0].text,e2.raw_output);
  assert.deepEqual(data.paragraphs,r.task.paragraphs);assert.equal(final.status,'OK');assert.equal(final.usage.adapter_enabled,true);
  if(['A','C'].includes(c))assert(data.history.every(z=>z.sender==='M1'));
  if(['B','D'].includes(c))for(const a of ['M2','M3','M4']){
   const bf=recs.find(z=>z.actor===a&&z.stage==='final'),q=bf.payload.user,p=JSON.parse(q.slice(q.indexOf('{'),q.lastIndexOf('}')+1));
   assert(p.history.some(h=>h.sender==='M1'&&h.phase==='work'&&h.round===2&&h.text===e2.raw_output));
  }
  payloadChecks.push({key:r.key,arm:c,EfinalIncludesExactE2:true,questionMatches:true,rawFinalMatchesSaved:true,adapterEnabled:true,ordinaryFinalsIncludeE2:['B','D'].includes(c)?true:null});
 }
}
const sourceHashes=load('research/b1-phenomenon-prioritization-20261107/SOURCE_HASHES.json');
const unchanged=Object.entries(sourceHashes.before).every(([p,h])=>crypto.createHash('sha256').update(fs.readFileSync(path.join(root,p))).digest('hex')===h);assert(unchanged);
const freshAnswerStrata=Object.fromEntries([true,false].map(strict=>{const xs=rows.filter(r=>r.cohort==='fresh56'&&r.strict===strict),ts=ann.terminalSwitch.filter(z=>xs.some(r=>r.key===z.key));return[strict?'strict_T_answer_disjoint':'T_answer_string_overlap_only',{n:xs.length,privatePaths:2*xs.length,terminalSwitchPaths:ts.length,terminalSwitchTasks:new Set(ts.map(z=>z.key)).size,eventDependencyGroups:new Set(ts.map(z=>z.group)).size,keys:[...new Set(ts.map(z=>z.key))]}];}));
const out={scope:'EXPLORATORY_ASSISTANT_CANDIDATE_PRIORITIZATION_NOT_FULL_REASONING_OR_POPULATION_CENSUS',reviewer:'assistant',independentHumanReview:false,new_model_calls:0,cohortsNotPooled:true,summaries,freshAnswerStrata,matchedExpertChanges:ann.matchedExpertChanges,payloadAudit:{expertFinals:payloadChecks.length,ordinaryFinals:rows.length*2*3,allPassed:true,checks:payloadChecks},inputHashesUnchanged:unchanged,uncertainty:'Wilson is descriptive iid reference only and ignores dependencies. Group bootstrap resamples declared dependency groups, retains all items per group; exploratory selection and single configuration prevent representative/population or confirmatory causal inference.'};
fs.writeFileSync(path.join(__dirname,'RESULTS.json'),JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify({summaries:Object.fromEntries(Object.entries(summaries).map(([k,s])=>[k,{n:s.n,groups:s.dependencyGroups,pairs:s.pairs,terminal:s.terminal,readoutPaths:s.readout.formalPaths,strata:s.strata}])),payloadAudit:{expertFinals:524,ordinaryFinals:786,allPassed:true},inputHashesUnchanged:unchanged},null,2));
