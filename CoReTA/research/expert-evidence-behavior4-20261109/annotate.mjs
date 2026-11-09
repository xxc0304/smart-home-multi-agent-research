// Provisional assistant annotations after reading all 64 reviews and 64 finals.
// These are observable text judgements, not independent human labels or internal reasoning.
import fs from 'node:fs';
const here=new URL('./',import.meta.url);
const root=new URL('../../',here);
const read=p=>JSON.parse(fs.readFileSync(new URL(p,here),'utf8'));
const rows=fs.readFileSync(new URL('runs/expert-evidence-behavior4-20261109-v1/responses.jsonl',root),'utf8').trim().split('\n').map(JSON.parse);
const entries=read('INPUTS.json').entries;
const rfail=new Set([0,8,49,105,112]);
const tfail=new Set([0,1,2,3,9,10,11,16,17,18,19,24,25,26,27,33,34,35,40,41,42,43,65,67,80,88,89,91]);
const afail=new Set([0,1,2,3,9,10,11,16,17,18,19,24,25,26,27,33,34,35,40,41,42,43,67,80,88,89,90,91,82,83]);
const qfail=new Set([0,1,8,9,10,11,24,32,33,34,35,40,41,42,49,50,57,58,59,67,88,114,121,122,123]);
const qpass=new Set([25,81,82,83,89,90,91]);
const output=rows.filter(r=>r.stage==='review').map(r=>{
 const f=rows.find(z=>z.unit===r.unit&&z.arm===r.arm&&z.actor===r.actor&&z.stage==='final');
 const current=r.raw_output.split('CURRENT ANSWER:').at(-1).trim();
 const note=r.call===40?'DECISION选择Ulster，CURRENT ANSWER/末答Greene，内部不一致。':r.call===8?'NEW RECORDS只列自己而漏三同伴；P2/P3段号错；末答正确不认证过程。':r.call===0?'A无新记录却列四人；段号偏移；出生县替代邻县。':r.call===65?'目标复述有contains歧义，末答正确；不能直接认证完整关系应用。':r.index===43?'区分母亲Ruth/祖母Mehraben；used不等于native/spoken；写作语言已构成使用证据。':r.index===6?'P2跨县水库仅间接支持邻接，不能声称唯一邻县得到严格证明。':r.index===17?'P16为Chichester附近县界，不能改成Kingston与Greene接壤。':'稳定正确控制；省略号或改写不能算逐字引文。';
 return {call:r.call,unit:r.unit,index:r.index,rep:r.rep,arm:r.arm,actor:r.actor,R:rfail.has(r.call)?'FAIL':'PASS',T:tfail.has(r.call)?'FAIL':'PASS',Q:qfail.has(r.call)?'FAIL':qpass.has(r.call)?'PASS':'UNOBSERVED',A:afail.has(r.call)?'FAIL':r.call===65?'UNOBSERVED':'PASS',D:r.call===40?'FAIL':'PASS',current_answer:current,final:f.raw_output,note};
});
fs.writeFileSync(new URL('BEHAVIOR_ANNOTATIONS.json',here),JSON.stringify({authority:'PROVISIONAL_ASSISTANT_TEXT_REVIEW_NOT_INDEPENDENT_HUMAN',coverage:{reviews:64,finals:64},notes:['Q is strict: attributed false statements or edited quotation are FAIL; paraphrase without exact quotation is UNOBSERVED, not proof of bad comprehension.','D tests expressed decision/current/final consistency; uncertain best guesses are not automatically inconsistent.','A PASS on county6 retains indirect-neighbor evidence limitation; no universal or unique-border proof.','R ignores terminal sentence punctuation but requires correct sender set and answer content.'],annotations:output},null,2));
const lines=['# 逐条行为核读（助手暂定）','','64核对＋64末答均已核读；非独立人工标注。R/T/Q/A/D见事前RUBRIC。Q严格区分逐字引文、释义、错归段落；引文格式FAIL不等于实体理解FAIL。D是表达一致性，非正确率。R末尾句号按句子标点处理，不将其计为答案内容变更。','','|call|unit|组/成员|R|T|Q|A|D|末答|说明|','|---|---|---|---|---|---|---|---|---|---|',...output.map(z=>`|${z.call}|${z.unit}|${z.arm[0]}/${z.actor}|${z.R}|${z.T}|${z.Q}|${z.A}|${z.D}|${z.final.replaceAll('|','/')}|${z.note}|`)];
fs.writeFileSync(new URL('BEHAVIOR_TABLE.md',here),lines.join('\n'));
console.log(JSON.stringify({reviews:output.length,R_A:output.filter(z=>z.arm[0]==='A'&&z.R==='PASS').length,R_B:output.filter(z=>z.arm[0]==='B'&&z.R==='PASS').length,review_tokens:rows.filter(r=>r.stage==='review').reduce((s,r)=>s+r.usage.output_tokens,0),final_tokens:rows.filter(r=>r.stage==='final').reduce((s,r)=>s+r.usage.output_tokens,0),response_seconds:rows.reduce((s,r)=>s+r.usage.elapsed_seconds,0)}));
