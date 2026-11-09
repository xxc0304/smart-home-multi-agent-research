// Assistant decisions from conclusion screening, followed by full-text checks of positives.
const fs=require('fs'),path=require('path');const read=n=>JSON.parse(fs.readFileSync(path.join(__dirname,n),'utf8'));
const screen=read('SCREEN.json'),pack=read('REVIEW_PACK.json'),filtered=read('FILTERED_REVIEW.json');
const ordinary=filtered.filter(z=>z.refs.some(r=>r.role==='ordinary'));
// These are observed candidate->different target switches, not automatic gold hits.
const positives=new Set([2,3,162,163,164,169,170,171,208,209]);
const fullRead=new Set([1,2,3,5,6,7,13,15,20,25,41,42,43,44,45,46,47,50,51,53,162,163,164,169,170,171,208,209,210]);
const notes={2:'Explicit final geographic description is correct; short final returns country entity. Source owner-origin bridge limited.',3:'Same local location/entity switch; correlated with UID2.',162:'Clear school-location conclusion -> school name.',163:'Clear school-location conclusion -> school name.',164:'Correct location explicitly retained in school description -> school name.',169:'Clear school-location conclusion -> school name.',170:'Clear school-location conclusion -> school name.',171:'Clear school-location conclusion -> school name.',208:'Clear school-type conclusion -> university name.',209:'Clear public land-grant type -> university name.',210:'Mixed magazine/type/university binding, not strict correct target commitment.'};
const annotations=ordinary.map(z=>({uid:z.uid,refs:z.refs.filter(r=>r.role==='ordinary'),judgment:positives.has(z.uid)?'CONFIRMED_LOCAL_TARGET_SWITCH':'NOT_CONFIRMED_CLEAR_COMMITMENT_SWITCH',review_scope:fullRead.has(z.uid)?'full_work_text_read':'last_550_character_conclusion_screen',note:notes[z.uid]??'Conclusion is wrong/withdrawn/mixed or retains a task/source boundary; lexical target mention alone does not qualify.',reviewer:'assistant',independence:'none/provisional'}));
const events=annotations.filter(a=>positives.has(a.uid)).flatMap(a=>a.refs.map(r=>({...r,uid:a.uid,work:pack.find(z=>z.uid===a.uid).work,final:pack.find(z=>z.uid===a.uid).final,note:a.note})));
const stats={};for(const cohort of ['D80','fresh56'])for(const role of ['expert','ordinary'])for(const vis of ['private','public']){
 const xs=screen.rows.filter(z=>z.cohort===cohort&&z.role===role&&(['A','C'].includes(z.arm)===(vis==='private')));
 const known=JSON.parse(fs.readFileSync(path.join(__dirname,'../b1-phenomenon-prioritization-20261107/ANNOTATIONS.json'),'utf8')).terminalSwitch;
 const es=role==='ordinary'?events.filter(e=>xs.some(x=>e.request_id===x.request_id&&e.arm===x.arm&&e.actor===x.actor)):known.filter(e=>xs.some(x=>e.key===x.key&&e.arm===x.arm));
 const noHit=xs.filter(x=>!x.finalEM&&!x.hits.length).length;
 stats[cohort+'/'+role+'/'+vis]={paths:xs.length,confirmedEvents:es.length,confirmedEventTasks:new Set(es.map(e=>e.key)).size,screenCandidatePaths:xs.filter(x=>!x.finalEM&&x.hits.length).length,EM0NoLexicalHit:noHit,unreviewedNoHitPaths:role==='ordinary'?noHit:0};
}
fs.writeFileSync(path.join(__dirname,'ORDINARY_REVIEW.json'),JSON.stringify({scope:'ASSISTANT_CANDIDATE_SCREEN_PLUS_FULL_POSITIVE_REVIEW_NOT_FULL_SEMANTIC_CENSUS',definitions:'Same criterion as expert: last work explicitly commits a correct local target; final substitutes a different target/entity/value. Partial/same-entity/granularity and mixed/withdrawn work separate.',annotations,events,stats,new_model_calls:0,warning:'Confirmed event counts are lower bounds under this screen, not total ordinary risk or an unbiased expert-vs-base rate comparison; unhit EM0 work remains incompletely reviewed.'},null,2)+'\n');
console.log(JSON.stringify({uniqueOrdinaryCandidateConclusions:ordinary.length,confirmedOrdinaryPaths:events.length,stats}));
