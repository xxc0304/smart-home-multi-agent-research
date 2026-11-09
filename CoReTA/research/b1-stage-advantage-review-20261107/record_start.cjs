const fs=require('fs'),path=require('path'),crypto=require('crypto');const root=path.resolve(__dirname,'../..'),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const block=`## 2026-11-07 分阶段优势核验完成，原56题固定顺序新增seed复核已启动

见research/b1-stage-advantage-review-20261107/REPORT.md、ANALYSIS.json、rules.json、REPEAT_EXPERIMENT_REVIEW.md、REPEAT_BUDGET.json。现有新56正式/明确表述/F1均见初答优势到私人阶段缩小；明确表述口径初答E73.21/普通32.74，A71.43/69.64、C67.86/67.26；A差1.79pp关联组区间[-12.02,16.00]，不能称等效。主要普通提高而非E大幅崩塌。旧75私人仍有优势，两批不合并；既有旧24两seed仅辅助。新私人A实际工作E13.85token/普通206.42，相同调用/cap不等于相同实际输出计算；提示/历史形状也是未隔离因素。无重写原评分，辅助规则回溯探索非独立语义真值。

用户明确授权后，原新56题/46来源组/29严格训练答案隔离、27仅答案串重合保留；A/B/C/D完整四组、原展示及两轮顺序、提示/资料/预算不变，唯一生成seed+100000000，全部上游/下游重新生成，无提示方法或训练。2912原真实响应逐字回放PASS、初答/分支失败隔离测试PASS；实际5824回放/长回复压力请求最大11262<16384，独立C短答资格SUPPORTED。科学/工程双PASS后FREEZE d38b57ad26ba3aa44d4ef69cfc870724f8669e4675737c3500974b027174df59，后台PID2240079启动，run为runs/b1-stage-advantage-seed1-20261107-v1。

最多2912调用/2121728输出token，singleton，参考原同量4.32小时，预计4–6小时非硬截止；无时间杀进程/生成重试，逐响应日志与原子检查点，单分支失败隔离，系统异常停止并保留。此次是同56跨seed复核，不是新增56独立题，不自动将小差说成无优势或将长度说成质量。初步实际状态见START_VERIFICATION.json；尚未完成，后续查进度→归档/评分/语义和两seed配对分析，不自动追加seed/方法/训练/C-H评估。助手自审none/provisional。

`;
const files=['CORE_RESEARCH_BRIEF.md','CURRENT_STATE.md','handoff.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md','refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md'];const changes=[];
for(const f of files){const p=path.join(root,f),t=fs.readFileSync(p,'utf8'),before=sha(p);if(!t.includes(block.split('\n')[0]))fs.writeFileSync(p,block+t);changes.push({path:f,before,after:sha(p)});}
fs.writeFileSync(path.join(__dirname,'RECORD_UPDATE.json'),JSON.stringify({scope:'OFFLINE_REVIEW_COMPLETE_REPLICATION_RUNNING_NOT_COMPLETED',changes},null,2)+'\n');console.log(JSON.stringify({records:changes.length}));
