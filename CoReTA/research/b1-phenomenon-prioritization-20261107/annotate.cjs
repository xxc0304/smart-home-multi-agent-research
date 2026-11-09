// Assistant exploratory annotations after reading extracted text; no model calls.
// Maps are human-readable decisions, not an automatic semantic correctness judge.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const root=path.resolve(__dirname,'../..'),read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const rows=JSON.parse(fs.readFileSync(path.join(__dirname,'ROWS.json'),'utf8'));
const oldLabels=read('research/b1-d80-phenomenon-census-20261106/LAST_WORK_LABELS.json');
const freshB=read('research/b1-grounded-revision-analysis-20261107/FRESH_E2_LABELS.json').records.filter(z=>z.condition==='B');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const oldByKey=new Map();for(const z of oldLabels)for(const r of z.refs)oldByKey.set(`old:${r.i}/${r.arm}`,z);
const C='C',M='M',N='N';
// New D final-work judgments: exact-target commitment (C), mixed/partial (M), absent (N).
const newDN=new Set([1,3,21,24,31,33,35,37,38,44,49,51,53,55]);
const newDM=new Set([13,20,42,54]);
// Fresh private final-work text read in full, including all EM-correct final controls.
const privateN=new Set([8,21,24,27,28,31,33,39,44,51,53,55]);
const privateM=new Set([0,13]);
const notes={
 'new:0/A':'Correct school-type words are assigned to the magazine, not its publisher; mixed binding, not strict correct work.',
 'new:35/A':'Distinguishes territory creation 1994 from office opening 1966; final wrongly takes office date.',
 'new:3/C':'Final 74 is correct, but last work only names Ronald Reagan.',
 'new:22/C':'Last work gives 1950s, not exact 1954; partial specificity.',
 'new:29/A':'Municipality is the type expressed by Italian comune; no harmful change.',
 'new:29/C':'Municipality is the type expressed by Italian comune; no harmful change.',
 'new:20/D':'Correct guitarist is mentioned but the final public conclusion splits singer/guitarist roles.',
 'new:42/D':'Names expected genre as plausible, then explicitly withholds direct support.',
 'new:54/D':'Names expected label as likely, then closes with uncertainty; source temporal limitation separate.',
 'old:66/A':'Only gives 12th century, insufficient to commit to exact target year.',
 'old:66/C':'Only gives 12th century, insufficient to commit to exact target year.',
 'old:51/A':'County appears in city/county building description; not a clear county-seat answer.',
 'old:51/C':'County appears in city/county building description; not a clear county-seat answer.'
};
const annotations=[];
for(const r of rows)for(const arm of ['A','B','C','D']){
 const z=r.arms[arm].records.find(z=>z.actor==='M1'&&z.stage==='work'&&z.round===2);assert(z);
 let label,source;
 if(r.cohort==='D80'){
  const prior=oldByKey.get(`${r.key}/${arm}`);
  if(prior){assert.equal(prior.text,z.raw_output);label=prior.conclusion==='CORRECT_TARGET_CANDIDATE'?C:prior.conclusion==='MIXED_OR_INCORRECT_BINDING'?M:N;source='prior_assistant_label_exact_text_verified';}
  else {assert(['A','C'].includes(arm)&&r.arms[arm].score.expert_em===1);label=[17,19,58,69].includes(r.index)?N:[51,66].includes(r.index)?M:C;source='new_full_last_work_read';}
 }else if(arm==='B'){
  const prior=freshB.find(x=>x.index===r.index);assert.equal(prior.text_sha256,hash(z.raw_output));label=prior.label;source='prior_assistant_label_sha256_verified_and_rechecked';
 }else if(arm==='D'){label=newDN.has(r.index)?N:newDM.has(r.index)?M:C;source='new_full_last_work_read';}
 else {
  label=privateN.has(r.index)?N:privateM.has(r.index)?M:C;
  if(r.index===0&&arm==='C')label=C;
  if(r.index===3&&arm==='C')label=N;
  if(r.index===28&&arm==='A')label=C;
  if(r.index===22&&arm==='C')label=M;
  source='new_full_last_work_read';
 }
 annotations.push({key:r.key,id:r.id,arm,request_id:z.request_id,text_sha256:hash(z.raw_output),label,source,note:notes[`${r.key}/${arm}`]??null,reviewer:'assistant',independence:'none/provisional',scope:'Target relation/candidate commitment only, not complete reasoning correctness, internal belief, or source certification.'});
}
// Strict target-switch events; separate partial/underspecified, equivalents and task ambiguity.
const oldSwitch={23:['A','C'],27:['A','C'],34:['A','C'],37:['A','C'],38:['A','C'],55:['C'],56:['A','C'],65:['A'],79:['A','C']};
const newSwitch={2:['A','C'],3:['A'],17:['A','C'],19:['C'],34:['C'],35:['A','C'],45:['C'],46:['A','C']};
const switchRows=[];
for(const [prefix,mp] of [['old',oldSwitch],['new',newSwitch]])for(const [i,arms]of Object.entries(mp))for(const arm of arms){
 const r=rows.find(r=>r.key===`${prefix}:${i}`),a=annotations.find(z=>z.key===r.key&&z.arm===arm);assert.equal(a.label,C);assert.equal(r.arms[arm].score.expert_em,0);
 switchRows.push({key:r.key,arm,id:r.id,group:r.group,request_id:a.request_id,work:r.arms[arm].records.find(z=>z.request_id===a.request_id).raw_output,final:r.arms[arm].finals.M1,gold:r.target.answer,judgment:'Different entity/value/target relation at final after correct target candidate in last work; source validity assessed separately.'});
}
// All matched expert-score changes get an explicit narrative, including non-events.
const judgments={
 'old:11':{kind:'QUESTION_BOUNDARY',note:'Concept car 1962 vs production 1964; not clean unreasonable expert harm.'},
 'old:17':{kind:'PRIVATE_RECOVERY_VS_PUBLIC_WRONG_BINDING',note:'Private last work Washington -> final Waukesha; discussion picks Grand. Multiple Murphy Lake entries; do not call persuasion of a committed correct private work.'},
 'old:48':{kind:'LOCAL_DATE_SWITCH_WEAK_CHAIN',note:'Arrival 1625 vs colony 1635; long triangular-trade geographic bridge not fully secured.'},
 'old:52':{kind:'CLEAR_LOCAL_TARGET_HARM',note:'Park->Santa Clarita->Los Angeles County is explicit; public replaces city with invented county. D first work is correct, second becomes wrong.'},
 'old:66':{kind:'LOCAL_DATE_ROLE_HARM',note:'1167 first landing vs 1177 appointment; D wrong date role. Private last work only 12th century; no claim full private public state correct.'},
 'new:1':{kind:'ENTITY_BINDING_HARM_WITH_SOURCE_BOUNDARY',note:'Dwight Yoakam/Reprise replaced by same-title Bonnie Tyler/Scorpions package; full-context ambiguity/temporal label boundary retained.'},
 'new:3':{kind:'TEMPORAL_RELATION_HARM',note:'Turns soon after term start=74; discussion answers age at start=73. C final 74 but last work names Reagan only.'},
 'new:37':{kind:'CLEAR_LOCAL_TARGET_HARM',note:'Federal Congress representative Debbie Dingell replaced by state legislature; private final and work correct. Ordinary final already wrong in private, so team net score need not decline.'},
 'new:38':{kind:'GRANULARITY_BOUNDARY',note:'Fairfield County vs Connecticut for underspecified region; different administrative levels, not a clean false fact.'},
 'new:43':{kind:'UNSUPPORTED_LANGUAGE_HARM_TEAM_RETAINS_CORRECT',note:'Writing English is changed into mother-tongue uncertainty and final Hindi; all ordinary members retain English, team correct.'},
 'new:44':{kind:'PRIVATE_RECOVERY_VS_PUBLIC_WRONG_ROLE',note:'Composer/arranger Pepusch vs author Gay; private work itself says Gay, correct only at final. Initial expert wrong. Do not label correct expertise persuaded wrong.'},
 'new:51':{kind:'TOPIC_GRANULARITY_BOUNDARY',note:'Civil War vs history; B longer presidency/Civil War supported, D too broad. Source topic/metric ambiguity; no clean expert ignored claim.'}
};
const gainNotes={
 'old:12':'Private work correct; final Andalusian headquarters under-specifies institution. Discussion/base CSIC strings semantically aligned; formal boundary.',
 'old:22':'Chinese-majority vs Chinese is wording equivalence; no substantive D expert improvement.',
 'old:27':'Private correct mother->wrong father at final; discussion preserves mother, not new knowledge demonstrated.',
 'old:34':'Private work already correct first Muslim; private final picks second. B/D first public wrong, second recovers. Cannot assign gain wholly to new knowledge.',
 'old:37':'Private work already correct child; private final returns father. Discussion public does not endorse child but final correct; no clear public expert utilization.',
 'old:38':'Private correct county->cemetery final; discussion retains county. Primarily terminal mismatch candidate.',
 'old:47':'Private wrong, public B correct party mentioned then disclaimed; final correct. Bridge/source weak, no clean grounded correction.',
 'old:69':'B improves 2.4->2.5 with city/country distinction; origin-of-bandy bridge weak. C also recovers at final.',
 'old:71':'Sawatch vs nested Rocky Mountains is granularity boundary; private work already names Sawatch.',
 'new:0':'Private last work attaches land-grant type to magazine, final university entity; discussion resolves target type. Mixed private work, not strict terminal switch.',
 'new:2':'Private correct sibling -> genre at final; discussion retains sibling.',
 'new:8':'D public correct accession year appears second round, private remains wrong; accession-treaty wording defines source-specific year.',
 'new:11':'Private date 8 November 2001 already answers requested year 2001; formal-only gain.',
 'new:17':'Private work already Greene, final Ulster; same source family as new19/new46, not three independent mechanisms.',
 'new:19':'Private C work Greene, final Ulster; shared source family.',
 'new:25':'21 meters vs21 is unit formatting; no substantive D gain.',
 'new:27':'Private confidently wrong bridge; ordinary initial/first work correct before expert adopts; later public B mixed. Positive correction candidate, not pure private-final artifact.',
 'new:28':'C work and final wrong actor, D correct; ordinary initial includes right actor. Useful correction candidate; exposure package not psychological mechanism.',
 'new:31':'Private wrong year; B1878 mentioned under wrong guide/author binding then withheld. Final correct; no clean correct public expert ignored.',
 'new:34':'C correct county->city at final; D retains county.',
 'new:35':'Both private last works distinguish correct1994, finals choose1966. B clear correct public, D public denies availability but final correct.',
 'new:39':'Private first work Towson, second and final county; public correct. Work drift before final, not strict last-work terminal switch.',
 'new:45':'C last work correct child, final mother; D retains child.',
 'new:46':'Private Greene->Ulster final; shared source family.'
};
const pairRows=[];
for(const r of rows)for(const [p,d]of [['A','B'],['C','D']])if(r.arms[p].score.expert_em!==r.arms[d].score.expert_em){
 const gain=r.arms[d].score.expert_em===1;const sw=switchRows.some(z=>z.key===r.key&&z.arm===p);
 pairRows.push({key:r.key,id:r.id,group:r.group,contrast:`${d}-${p}`,direction:gain?'gain':'harm',privateFinal:r.arms[p].finals.M1,talkFinal:r.arms[d].finals.M1,privateLastLabel:annotations.find(z=>z.key===r.key&&z.arm===p).label,talkLastLabel:annotations.find(z=>z.key===r.key&&z.arm===d).label,privateTerminalSwitch:gain&&sw,judgment:gain?{kind:sw?'PRIVATE_TERMINAL_SWITCH_ALREADY_HAS_CORRECT_CANDIDATE':'OTHER_GAIN_OR_BOUNDARY',note:gainNotes[r.key]}:judgments[r.key]});
 assert(pairRows.at(-1).judgment&&pairRows.at(-1).judgment.note,'Missing annotation '+r.key);
}
const nonSwitchNotes={
 'old:1':['PARTIAL_SPECIFICITY','western Europe retains broad location but drops coastal specificity.'],
 'old:5':['PARTIAL_SPECIFICITY','President authority retained, appointment action omitted; not different entity.'],
 'old:10':['SEMANTIC_WORDING','neutral/neutral side/powers answers side; gold includes country.'],
 'old:12':['PARTIAL_INSTITUTION_OR_QUALIFIER','Andalusian headquarters shortens institution, or adds regional qualifier; not distinct contradictory institution.'],
 'old:22':['SEMANTIC_WORDING','Chinese-majority vsChinese.'],
 'old:41':['SEMANTIC_WORDING','linear defence with omitted concept or US spelling.'],
 'old:46':['NUMERIC_EQUIVALENCE','40% vsForty percent.'],
 'old:49':['SAME_PERSON_WORDING','Athina Andrelos, with relationship qualifier optional.'],
 'old:55':['NUMERIC_EQUIVALENCE','40% vsForty percent.'],
 'old:60':['PARTIAL_LOCATION','Westminster retained, full location qualifier omitted.'],
 'old:62':['DATE_YEAR_EQUIVALENCE','March1,1920 includes requested year1920.'],
 'old:65':['PARTIAL_SPECIFICITY','Luftwaffe units omits gaining control; not switch to another organization.'],
 'old:71':['NESTED_RANGE_BOUNDARY','Rocky Mountains broader than nested Sawatch; not strict distinct-entity failure.'],
 'new:11':['DATE_YEAR_EQUIVALENCE','8 November2001 includes requested year2001.'],
 'new:15':['NATIONALITY_WORDING','French actor impliesFrance; country/nationality form mismatch, no changed country.'],
 'new:25':['NUMERIC_UNIT_EQUIVALENCE','21meters vs21.'],
 'new:32':['LOCATION_QUALIFIER','Lop Lake retained; in the west omitted.'],
 'new:52':['ERA_WORDING','Guomindang martial-law era retained; wording and dates more specific.']
};
const terminalReviews=[];
for(const r of rows)for(const arm of ['A','B','C','D'])if(annotations.find(z=>z.key===r.key&&z.arm===arm).label===C&&!r.arms[arm].score.expert_em){
 const sw=switchRows.some(z=>z.key===r.key&&z.arm===arm),n=nonSwitchNotes[r.key];assert(sw||n,'Unreviewed terminal discrepancy '+r.key+'/'+arm);
 terminalReviews.push({key:r.key,arm,kind:sw?'SUBSTANTIVE_DIFFERENT_TARGET':n[0],note:sw?'Correct local target candidate replaced by different entity/value/role; source validity separate.':n[1],final:r.arms[arm].finals.M1});
}
const out={reviewer:'assistant',independence:'none/provisional',new_model_calls:0,definitions:{C:'Explicit correctly bound target candidate; not full chain certification.',M:'Target present with partial specificity, incorrect binding or withdrawn/mixed commitment.',N:'No explicit correctly bound target conclusion; not proof all text false.'},lastWork:annotations,terminalSwitch:switchRows,terminalReviews,matchedExpertChanges:pairRows};
fs.writeFileSync(path.join(__dirname,'ANNOTATIONS.json'),JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify({lastWork:annotations.length,sourceCounts:Object.fromEntries([...new Set(annotations.map(x=>x.source))].map(s=>[s,annotations.filter(x=>x.source===s).length])),terminalSwitch:switchRows.length,pairs:pairRows.length}));
