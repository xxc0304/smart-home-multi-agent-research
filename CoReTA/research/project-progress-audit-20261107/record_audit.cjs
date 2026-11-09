// Idempotent, additive project-status correction. Never touches run data/contracts.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const hash = s => crypto.createHash('sha256').update(s).digest('hex');
const fileHash = p => hash(fs.readFileSync(path.join(root, p)));
const plan = 'refine-logs/expert-mechanism-pilot-20261030/';
const oldPlan = 'refine-logs/acl2027-expert-transfer-20261029/';
const audit = 'research/project-progress-audit-20261107/';
const freezePath = 'research/b1-sampling-order-cross-20261107/prepared/FREEZE.json';
const sources = [
  oldPlan+'WORK_PLAN.md', oldPlan+'WORK_TRACKER.md',
  plan+'EXPERIMENT_PLAN.md', plan+'EXPERIMENT_TRACKER.md',
  'CORE_RESEARCH_BRIEF.md', 'STAGE_REVIEW.md',
  'engineering/b0-first-run-20261103/RESULTS.md',
  'engineering/b0-first-run-20261103/C160_RESULTS.md',
  'research/b1-dev80-analysis-20261106/REPORT.md',
  'research/b1-message-probe-analysis-20261106/REPORT.md',
  'research/core-audit-20261106/AUDIT.md',
  'research/research-direction-review-20261106/REPORT.md',
  'research/b1-independent-first-analysis-20261107/REPORT.md',
  'research/b1-independent-first-analysis-review-20261107/AUDIT.md',
  'research/b1-sampling-order-cross-20261107/BRIEF.md', freezePath
];
const current = `## 2026-11-07 项目进度与主线总审核（优先于下方历史状态）

见research/project-progress-audit-20261107/REPORT.md及STAGE_REVIEW.md。原排期P2为11/06–12，当前处P2/B2→B3探索性机制验证；工程与开发基线较快，科学主张尚未完成。11/03一次答案训练与独立C160完成（E51.25%、base13.75%、+37.5pp）；D8/D32/D80及25题完整下游实验已完成，D80有5个上限失败保留，当前采样×顺序交叉继续。下方11/01“训练/C/团队0、待资源”仅历史，不作当前状态。

核心仍为真实专家优势如何转为团队收益并保留有效纠错。D80不支持普遍专家拖累；B_delay主覆盖+4.17pp仅两单位且同一原S/O组合，稳定机制/方法未立。D16选样/下游局限、重复S/O混合和局部假设提升过快已记录，当前交叉修复后者。原C1仅部分、C2未建立；H未用，独立语义复核未记完成。下一先完成当前交叉后审，争取11/12形成单一可证伪预测与继续/修改/停止决策，11/13–19条件性冻结研究合同。内部节点不是运行硬截止。不新增GPU批、训练或C/H评估；原评分/投票/冻结合同不改。助手自审none/provisional，PASS本次审核和记录，研究贡献确认REVISE。

`;
const overview = `## 2026-11-07 实际进度覆盖层

本页旧排期与历史状态保留。当前为原P2（11/06–12）/B2→B3探索性验证，非论文确认完成。资格、四组开发基线已完成；稳定机制、主张冻结与H确认尚未完成。见[项目进度审核](../../research/project-progress-audit-20261107/REPORT.md)及[当前执行状态](../expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER.md)。11/01及更早“训练/C/团队0”“资源待验”的文字仅历史。下一节点是当前交叉后审和11/12内部研究决策，非给运行设硬截止。

`;
const tracker = `## 2026-11-07 实际执行状态（覆盖下方11/01旧状态）

| 原项目 | 当前状态 | 限制与依据 |
|---|---|---|
| R001 实机验收 | DONE_REAL，11/03 | 3090/Qwen/精度/长度及真实执行已验；后续新合同仍逐批预检 |
| R002 任务SFT/V | DONE_REAL，11/03 | 一次答案LoRA训练，1796步；非协作训练 |
| R003 C160资格 | SUPPORTED_TASK_ADVANTAGE，11/03 | E82/160、base22/160；答案优势，C关闭调参 |
| R004 1/2→8技术验收 | DONE_REAL | 已完成；后续版本各自保留，不混合作独立题 |
| R005 D32/D80开发 | DONE_DEVELOPMENT | D80处理80、75四组共同完整、5上限失败保留；非H |
| R006 机制干预 | EXPLORATORY_ONGOING | D16探针和25题闭环已完；采样×顺序交叉运行中；稳定响应尚未建立 |
| R007 H确认/一个扩展 | NOT_FROZEN / NOT_RUN | 论文主张、必要强/简单控制和确认预算待冻结；H未用 |

详见[宏观审核](../../research/project-progress-audit-20261107/REPORT.md)。原P2日期11/06–12，当前未明显超窗；C1部分满足、C2未建立。独立语义标注与导师决策不能由助手记录替代。下方旧表保留作历史，不再代表当前运行状态。

`;
const entries = new Map([
  ['handoff.md', current], ['CURRENT_STATE.md', current], ['brainstorm.md', current],
  [plan+'WORK_TRACKER.md', current], [plan+'STAGE_REVIEWS.md', current],
  [plan+'NEXT_TASKS_20261104.md', current],
  [plan+'EXPERIMENT_PLAN.md', overview], [plan+'EXPERIMENT_TRACKER.md', tracker],
  [oldPlan+'WORK_PLAN.md', overview], [oldPlan+'WORK_TRACKER.md', overview]
]);
const freezeBefore = fileHash(freezePath);
const frozen = Object.keys(JSON.parse(read(freezePath)).files);
for (const p of entries.keys()) {
  if (!fs.existsSync(path.join(root,p))) throw new Error('Missing record '+p);
  if (frozen.some(f => f.replaceAll('\\','/').endsWith('/'+p)))
    throw new Error('Refuse modifying frozen input: '+p);
}
const inputs = Object.fromEntries(sources.map(p => [p,fileHash(p)]));
const inputPath = path.join(__dirname,'INPUT_HASHES.json');
if (!fs.existsSync(inputPath)) fs.writeFileSync(inputPath, JSON.stringify({
  date:'2026-11-07', scope:'before additive status updates', files:inputs
},null,2)+'\n');
const updates=[];
for (const [p, block] of entries) {
  const original = read(p), marker=block.split('\n')[0];
  const before=fileHash(p);
  if (!original.includes(marker)) fs.writeFileSync(path.join(root,p),block+original);
  updates.push({path:p,before,after:fileHash(p),added:!original.includes(marker)});
}
if (fileHash(freezePath)!==freezeBefore) throw new Error('Frozen manifest changed');
const changed = new Set(entries.keys());
for (const p of sources) if (!changed.has(p) && fileHash(p)!==inputs[p])
  throw new Error('Unexpected evidence mutation: '+p);
fs.writeFileSync(path.join(__dirname,'RECORD_UPDATE.json'),JSON.stringify({
  date:'2026-11-07', review:'assistant none/provisional',updates,
  frozen_manifest_unchanged:true, evidence_outside_status_records_unchanged:true,
  report_sha256:fileHash(audit+'REPORT.md'),
  stage_review_sha256:fileHash(audit+'STAGE_REVIEW.md'),
  new_model_calls:0, new_training:0, new_C_H_evaluation:0
},null,2)+'\n');
console.log(JSON.stringify({records:updates.length,added:updates.filter(x=>x.added).length,
  sources:sources.length,frozen_manifest_unchanged:true}));
