// Provisional assistant judgements from the displayed raw texts and source review.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const H=__dirname,ROOT=path.resolve(H,'../..'),load=p=>JSON.parse(fs.readFileSync(path.join(H,p),'utf8'));
const entries=load('INDEX.json'),hashes=load('SOURCE_HASHES.json');
const primary={
 'old:12':['SURFACE','Same institution with CSIC suffix; no substantive rejection.'],
 'old:13':['PUBLIC_NOT_CORRECT','Both works substitute Fliesteden birthplace and deny museum bridge.'],
 'old:26':['PUBLIC_NOT_CORRECT','Mentions band 38m but changes requested target to album and withholds/denies.'],
 'old:29':['PUBLIC_NOT_CORRECT','No correct founder commitment; producer organization vs film-production confusion.'],
 'old:37':['PUBLIC_NOT_CORRECT','Selects Vicki or denies answer; private final alone James.'],
 'old:47':['PUBLIC_NOT_CORRECT','Final work mentions expected party then explicitly disclaims evidence; not a clean complete valid explanation.'],
 'old:59':['PUBLIC_NOT_CORRECT','Mentions Kangchenjunga but concludes Everest/body discovery instead.'],
 'old:69':['LOCAL_REASON_WITH_SOURCE_BOUNDARY','Clearly distinguishes England2.5 from Southampton2.4; supplied source does not establish bandy origin in England.'],
 'old:72':['SURFACE','Same office plus Church of England qualifier.'],
 'old:32':['SHORT_THEN_WITHDRAWN_SOURCE_BOUNDARY','r1 1,270 mm only; r2 misbinds Barry Pepper and1024. Hanks/film/state wording and precipitation bridge need caution.'],
 'new:9':['SURFACE','three and3 same count.'],
 'new:31':['PUBLIC_NOT_CORRECT','Binds year to guide rather than author editorial organization and withdraws answer.'],
 'new:51':['SURFACE','Presidency in Civil War topic supported; not a clear substantive miss.'],
 'seed1:1':['PUBLIC_NOT_CORRECT','Both public works select Prelude or deny relevance; no Reprise valid explanation.'],
 'seed1:6':['CORRECT_SHORT_ONLY','Both public works Crawford County only; no expert-generated relation explanation. Neighbor evidence indirect.'],
 'seed1:9':['SURFACE','three and3 same count.'],
 'seed1:17':['SHORT_THEN_WITHDRAWN','r1 Greene County only; r2 explicitly Ulster, so final Greene does not mean last public relation was correct.'],
 'seed1:24':['PUBLIC_NOT_CORRECT','Both public works deny leave date rather than endorse23June2016.'],
 'seed1:49':['PUBLIC_NOT_CORRECT','Both public works conclude newspaper1963, not institute1960.'],
 'seed1:51':['SURFACE','Presidency in Civil War topic granularity.'],
 'seed1:54':['PUBLIC_NOT_CORRECT','Both public works deny label rather than endorse Reprise.']
};
const other={
 'old:5':['SOURCE_OR_TARGET_BOUNDARY','Geneva vs supplied Singapore process; not a clean receiver error.'],
 'old:10':['SURFACE','Everyone says neutral; formal target retains country qualifier.'],
 'old:11':['SOURCE_OR_TARGET_BOUNDARY','Production1964 vs concept1962 distinction; no clear correct expert public commitment.'],
 'old:46':['SURFACE','40% versus Forty percent.'],
 'old:48':['PUBLIC_WRONG','Both works1635 rather than1625.'],
 'old:49':['PUBLIC_NOT_CORRECT','Correct Athina relation mentioned, but question bridge denied; final concise answer is semantically plausible, no complete public chain.'],
 'old:52':['PUBLIC_WRONG','HiddenB both worksSantaClaritaCounty, not LosAngelesCounty; D first-work event is different condition.'],
 'old:56':['EARLY_LOCAL_RELATION_THEN_WRONG','r1 exact location highwayKisumu; r2 mismatches father/country and concludesSomalia. Early message lacks requested upstream chain.'],
 'old:60':['SURFACE','All members same school/location with differing specificity.'],
 'old:65':['PARTIAL_OR_OVERBROAD','All outputs include prestige/control; needed control of more Luftwaffe units not clearly isolated.'],
 'old:79':['PUBLIC_WRONG','58/NYC substituted for98/Chicago.'],
 'old:45':['SOURCE_OR_TARGET_BOUNDARY','Birthplace inferred from football schooling, border not directly established; team already says trolley service.'],
 'old:53':['LATE_CORRECT_LOCAL_WORK_FINAL_FAILURE','r2 Fox and10July1981 correct public relation, yet own final16Nov2004 and othersNBC/date. Natural r2 phrase needs no invented facts; r1 wrong; malformed composition wording retained as boundary.'],
 'old:73':['SHORT_THEN_WRONG_EXPLANATION','r1 JubileeRecords; r2 incorrectly assigns Jubilee to BlueKentuckyGirl. Supplied actual Jubilee evidence is GlidingBird[P14]. Record label is time-varying.'],
 'new:1':['PUBLIC_NOT_CORRECT','No correct label commitment.'],
 'new:13':['SURFACE_OR_TEMPORAL_BOUNDARY','Supplied2017HighSierra supports version answer; formal broadmacOS is not clean failure.'],
 'new:15':['SURFACE','France/French country adjective.'],
 'new:25':['SURFACE','21meters vs21.'],
 'new:37':['PUBLIC_WRONG','Statelegislature substituted for federal representative.'],
 'new:44':['PUBLIC_WRONG','JohnGay writer substituted for music arranger/composer.'],
 'new:52':['SURFACE','Guomindang martial-law era retained.'],
 'seed1:13':['SURFACE_OR_TEMPORAL_BOUNDARY','HighSierra in2017 passage versus outside-memorySonoma; not a clean expert-receiver rejection.'],
 'seed1:15':['SURFACE','France/French.'],
 'seed1:26':['MIXED_WITHDRAWN','Correct MidlandCounty intermediate repeatedly overridden by Jamaica.'],
 'seed1:44':['PUBLIC_WRONG','JohnGay substituted for Pepusch.'],
 'seed1:52':['SURFACE','Same Guomindang era with qualifier.'],
 'seed1:53':['SOURCE_OR_TARGET_BOUNDARY','TwoDoure villages in same country; Zorgho is a supplied competing referent.']
};
const ordinary={
 'old:62':['SURFACE','M1March1st1920 vsordinary1920; not substantive expert error.'],
 'new:43':['ORDINARY_FINAL_RIGHT_NOT_FULL_EXPLANATION','M1English r1, r2 adds unsupported native-language requirement, finalHindi; ordinaryEnglish retained. Correct final does not certify ordinary rationale.'],
 'seed1:43':['ORDINARY_FINAL_RIGHT_NOT_FULL_EXPLANATION','M1andordinaryworksconfuseMehraben grandmother with mother; ordinaryEnglish final correct despite misbound explanation.']
};
const annotations=entries.filter(e=>e.arm==='B'&&e.screen!=='OTHER').map(e=>{
 const pair=e.screen==='EXPERT_FINAL_TEAM_LOSS'?primary[e.key]:e.screen==='ORDINARY_CORRECT_EXPERT_WRONG'?ordinary[e.key]:other[e.key];assert(pair,'Missing review '+e.key);
 return {...e,classification:pair[0],note:pair[1],expertWork:e.expertWork.map(w=>({...w,text_sha256:crypto.createHash('sha256').update(w.text).digest('hex')})),reviewer:'assistant',independence:'none/provisional'};
});
assert.equal(annotations.length,51);
const main=annotations.filter(e=>e.screen==='EXPERT_FINAL_TEAM_LOSS');assert.equal(main.length,21);
const result={new_model_calls:0,primary_complete_paths:entries.filter(e=>e.arm==='B').length,primary_unique_tasks:new Set(entries.filter(e=>e.arm==='B').map(e=>e.id)).size,expert_final_team_loss_paths:21,expert_final_team_loss_unique_tasks:new Set(main.map(e=>e.id)).size,classes:Object.fromEntries([...new Set(main.map(e=>e.classification))].map(c=>[c,main.filter(e=>e.classification===c).length])),candidate_semantic_review:{paths:51,expert_work_messages:102},natural_explanation_route:'HOLD_NOT_ENOUGH_CLEAN_TARGET_FAILURE_INPUTS_FOR_12_TO_16_TASKS',source_hashes_unchanged:Object.entries(hashes.files).every(([p,h])=>crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT,p))).digest('hex')===h)};
assert(result.source_hashes_unchanged);
fs.writeFileSync(path.join(H,'ANNOTATIONS.json'),JSON.stringify({authority:'ASSISTANT_PROVISIONAL_NOT_INDEPENDENT',annotations},null,2));
fs.writeFileSync(path.join(H,'AUDIT_RESULT.json'),JSON.stringify(result,null,2));
const receipt=[];
for(const index of [53,69]){
 const e=entries.find(e=>e.key===`old:${index}`&&e.arm==='B');
 const t=JSON.parse(fs.readFileSync(path.join(ROOT,e.source),'utf8'));
 const work=t.records.filter(z=>z.arm==='B'&&z.stage==='work'),last=work.filter(z=>z.actor==='M1').at(-1);
 const finals=t.records.filter(z=>z.arm==='B'&&z.stage==='final');
 const checks=finals.map(z=>({actor:z.actor,request_id:z.request_id,contains_exact_escaped_expert_last_work:z.payload.user.includes(JSON.stringify(last.raw_output).slice(1,-1)),final:z.raw_output}));
 assert(checks.every(z=>z.contains_exact_escaped_expert_last_work));
 receipt.push({key:e.key,expert_request_id:last.request_id,expert_text:last.raw_output,expert_text_sha256:crypto.createHash('sha256').update(last.raw_output).digest('hex'),work_order:work.map(z=>({actor:z.actor,round:z.round,request_id:z.request_id})),ordinary_work_after_last_expert:work.slice(work.indexOf(last)+1).filter(z=>z.actor!=='M1').map(z=>z.request_id),final_input_checks:checks,scope:'Exact text delivery verified; no comprehension or causality claim.'});
}
fs.writeFileSync(path.join(H,'DELIVERY_AND_TIMING.json'),JSON.stringify(receipt,null,2));
fs.writeFileSync(path.join(H,'REVIEW_TABLE.md'),['# 候选逐条核读','','候选筛查不等于语义事件。完整原文见CANDIDATE_TEXTS，原件路径/文本哈希见ANNOTATIONS。','','|路径|筛查|分类|说明|','|---|---|---|---|',...annotations.map(e=>`|${e.key}/B|${e.screen}|${e.classification}|${e.note}|`)].join('\n'));
console.log(JSON.stringify(result,null,2));
