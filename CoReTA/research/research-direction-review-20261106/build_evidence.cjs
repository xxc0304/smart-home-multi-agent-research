const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const root = path.resolve(__dirname, '../..');
const read = p => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8'));
const sources = new Set();
function input(p) { sources.add(p); return read(p); }
const census = input('research/b1-d80-phenomenon-census-20261106/CENSUS.json');
const prior = input('research/b1-dev80-review-20261106/REVIEW_EVIDENCE.json');
const analysis = input('research/b1-dev80-analysis-20261106/ANALYSIS.json');
const scores = input('runs/b1-dev80-20261106-v1/checkpoints/080/scores.json');
function trial(i) { return input(`runs/b1-dev80-20261106-v1/trials/${String(i).padStart(3, '0')}.json`); }
const score = i => scores.reports.find(s => s.config.task_index === i);
const work = (t, arm, actor = 'M1') => t.records.filter(r => r.arm === arm && r.stage === 'work' && r.actor === actor).map(r => ({request_id:r.request_id, actor:r.actor, round:r.round, text:r.raw_output}));
const annotations = {
  2:'私人工作直接给Hillary；公开工作找到伴唱人却否认桥接。',
  13:'私人目标串匹配；公开错接Fliesteden；支持材料的出生地桥接仍弱，不能把私人短串认证为完整推理。',
  19:'私人第一次1976、第二次1979、终答1976，私人阶段也不稳定；公开未建立队伍/球场桥接。',
  21:'私人明确Neil与Astrid兄妹；公开列出同父事实却拒绝推出姐妹关系。',
  26:'私人明确乐队总销量；公开把问乐队的销量错改为问专辑销量；是较清楚的任务目标错绑。',
  29:'私人给官方人名/首任军官事实；首任Commandant与创办者的等价桥接不足，不把公开质疑全算错误。',
  31:'私人正确识别村庄所属国家；公开把题目误读为村庄本身是国家。团队反而改善，不能据工作标签推断团队伤害。',
  35:'Chrysler/DaimlerChrysler归属桥接有边界；私人目标短串不证明公开质疑不合理。',
  37:'私人工作James是Paul的孩子、私人终答却Paul；公开工作未承诺James，但公开终答James。两个阶段优劣相反。',
  39:'私人短串匹配；公开增加出生当年时点限制，题意时间边界保留。',
  47:'私人工作center-right本身不对；公开末次提出目标党名却否认材料支持，不能叫稳定私人优势被破坏。',
  50:'私人关系陈述匹配；公开混淆父子Dodgson身份；原资料父子桥接边界保留。',
  59:'私人候选匹配；公开将发现珠峰误读为发现尸体；题句时间歧义保留。',
  63:'私人明确乐队成立年；公开将Carnival专辑误读为嘉年华活动。',
  67:'私人末次虽1934，但B错误把英国年份赋给意大利、D未建立国家桥接；金标/原资料国家指代有疑问，不能称正确推理被讨论损坏。'
};
const matched = census.type2.rows.map(r => {
  const t=trial(r.index), s=score(r.index), a=r.arm==='B'?'A':'C';
  const clear=r.boundary==='ASSISTANT_RELATION_LEVEL_CANDIDATE';
  return {index:r.index, question_number:r.index+1, public_arm:r.arm, private_arm:a,
    question:t.task.question, gold:analysis.cases.find(x=>x.index===r.index).target.answer,
    boundary:r.boundary, assistant_label_independence:'none/provisional',
    private_last_endorses_gold_candidate:![19,47].includes(r.index),
    private_last_label_scope:'candidate-only, not full reasoning/grounding certification',
    clearer_original_stratum:clear,
    initial_expert:{answer:t.initials.M1, official_em:s.arms[r.arm].expert_initial_em, public_in_B_D:true},
    private_work:work(t,a), public_work:work(t,r.arm),
    private_final:s.arms[a].members.M1, public_final:s.arms[r.arm].members.M1,
    private_team_expected_em:s.arms[a].expected_em, public_team_expected_em:s.arms[r.arm].expected_em,
    team_delta:s.arms[r.arm].expected_em-s.arms[a].expected_em,
    note:annotations[r.index]};
});
const readout = prior.readout_event_classifications.map(r=> {
  const t=trial(r.index), s=score(r.index);
  return {...r, initial_expert:{answer:t.initials.M1, official_em:s.arms[r.arm].expert_initial_em, public_in_B_D:true},
    all_public_work_references:work(t,r.arm).map(x=>x.request_id),
    late_private_correct_answer_is_not_necessarily_new_information:true,
    scope_note:'Inherited E-work classification. All-peer causal/semantic census not claimed. First correct public E initial checked mechanically; later correct local binding reviewed in case69.'};
});
const corrections=[];
for(const s of scores.reports.filter(s=>s.complete)) for(const arm of ['B','D']) {
  if(s.arms[arm].expert_initial_em===0 && s.arms[arm].expert_em===1) {
    const t=trial(s.config.task_index), a=arm==='B'?'A':'C';
    corrections.push({index:s.config.task_index, question_number:s.config.task_index+1, arm,
      initial:t.initials.M1, final:s.arms[arm].members.M1.answer,
      matched_private_final_correct:s.arms[a].expert_em===1,
      note:s.arms[a].expert_em===1?'私人也已答对，不能据初终答转移证明同伴必要。':
      ({22:'Chinese-majority→Chinese，表述边界。',47:'公开猜党名且材料桥接弱。',69:'城市/全国局部关系清楚，但运动起源桥接弱。',71:'Collegiate Peaks/Sawatch/Rocky山系粒度边界；私人工作已经给过目标候选。'})[s.config.task_index]});
  }
}
const examples=[0,26,34,69].map(i=> {
  const t=trial(i), x=analysis.cases.find(x=>x.index===i);
  return {index:i, question_number:i+1, question:t.task.question, initials:t.initials,
    support_paragraphs:t.task.paragraphs.filter(p=>x.target.paragraphs.find(z=>z.idx===p.idx)?.is_supporting),
    work:t.records.filter(r=>r.arm==='B'&&r.stage==='work').map(r=>({request_id:r.request_id,actor:r.actor,text:r.raw_output})),
    finals:t.finals.B,
    interpretation:({0:'普通M4首先形成材料目标对应的1843，E随即采用；私人E也能1843，不证明必要性，且各成员解释含错误的材料缺失断言。',26:'普通成员先把乐队误读为专辑，E随后同样误读；仅时间顺序不证明机制，需实际分叉和下游再生。',34:'E首次公开工作错误，普通M4/M2/M3据第一/第二位区分给正确候选，E第二次公开工作恢复正确。E初答本来正确，故不是普通独有稳定知识证明。',69:'普通成员先给城市/全国的正确区分却最后从历史选错；E后期公开正确局部关系，后续普通仍错。全题起源桥接弱，不作主导频率证据。'})[i]};
});
const stats={
  matched_paths:matched.length, matched_unique_questions:new Set(matched.map(x=>x.index)).size,
  initial_expert_correct_public_paths:matched.filter(x=>x.initial_expert.official_em===1).length,
  private_last_gold_candidate_paths:matched.filter(x=>x.private_last_endorses_gold_candidate).length,
  clearer_paths:matched.filter(x=>x.clearer_original_stratum).length,
  clearer_private_last_gold_candidate_paths:matched.filter(x=>x.clearer_original_stratum&&x.private_last_endorses_gold_candidate).length,
  selected_team_improved:matched.filter(x=>x.team_delta>0).map(x=>[x.index,x.public_arm,x.team_delta]),
  selected_team_worsened:matched.filter(x=>x.team_delta<0).map(x=>[x.index,x.public_arm,x.team_delta]),
  selected_team_unchanged:matched.filter(x=>x.team_delta===0).length,
  private_final_correct:matched.filter(x=>x.private_final.em===1).length,
  readout_paths:readout.length, readout_initial_expert_correct:readout.filter(x=>x.initial_expert.official_em===1).length,
  discussion_initial_wrong_final_correct_paths:corrections.length,
  discussion_correction_already_correct_in_private:corrections.filter(x=>x.matched_private_final_correct).length
};
if(stats.matched_paths!==19||stats.readout_paths!==15||stats.private_last_gold_candidate_paths!==17||stats.clearer_private_last_gold_candidate_paths!==8||stats.discussion_initial_wrong_final_correct_paths!==13||stats.discussion_correction_already_correct_in_private!==9) throw Error('Unexpected evidence counts');
const out={date:'2026-11-06',scope:'Offline research direction audit',new_model_calls:0,reviewer:'assistant',independence:'none/provisional',stats,matched,readout,corrections,examples};
fs.writeFileSync(path.join(__dirname,'MATCHED_EVIDENCE.json'),JSON.stringify(out,null,2)+'\n');
const hashes=[...sources].sort().map(p=>({path:p,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,p))).digest('hex')}));
fs.writeFileSync(path.join(__dirname,'INPUT_HASHES.json'),JSON.stringify(hashes,null,2)+'\n');
const lines=['# 匹配证据决策表','', '2026-11-06；助手候选/关系判读，非独立标注。题号为index+1。全原文/消息ID见MATCHED_EVIDENCE.json。只对已选19条做条件描述，不能反推总体伤害频率。','', '|题号/讨论|私人末工作目标候选|初答已公开正确|私人E末答→讨论E末答（官方EM）|团队期望EM 私人→讨论|边界与解释|','|---|---|---|---|---|---|'];
for(const r of matched)lines.push(`|${r.question_number}/${r.public_arm}|${r.private_last_endorses_gold_candidate?'是（不认证全推理）':'否'}|${r.initial_expert.official_em?'是':'否'}|${r.private_final.em}→${r.public_final.em}|${r.private_team_expected_em}→${r.public_team_expected_em}|${r.note}|`);
lines.push('','## 15条讨论最终漏选的解释边界','','下表不将官方分数事后修正。对初答正确的事件，该初答在全部讨论成员首次工作前已经可见；末答本身仍私有。公开初答可见不等于被认真使用。','','|题号/条件|E初答已公开匹配金标|期望团队EM|已有语义分类|','|---|---|---|---|');
for(const r of readout)lines.push(`|${r.question_number}/${r.arm}|${r.initial_expert.official_em?'是':'否'}|${r.official_expected_em}|${r.classification}|`);
fs.writeFileSync(path.join(__dirname,'DECISION_TABLE.md'),lines.join('\n')+'\n');
console.log(JSON.stringify(stats,null,2));
