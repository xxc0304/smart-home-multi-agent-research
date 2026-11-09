const fs=require('fs'),path=require('path'),crypto=require('crypto');const root=path.resolve(__dirname,'../..');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const block=`## 2026-11-07 普通末步对照与48次adapter诊断完成：局部修复有代价，资格需分阶段

见research/b1-terminal-control-20261107/REPORT.md、OFFLINE_REPORT.md、ANALYSIS.json、POST_RUN_AUDIT.json和STAGE_REVIEW.md；实际新run为runs/b1-terminal-adapter-20261107-v1。普通1572路径全数值/词串扫描、131非边界候选结论筛查及正例全文：私人旧6/450（1题）、新3/336（1题），讨论旧2/450（1题，来源桥接弱）/新0；386个普通EM0无命中未全部语义读，均为已确认下界，非总体率/专家风险比。专家旧16/150、新12/112来源复用。

用户本轮开始授权内，科学PASS、7项真实输入/故障检查和实际tokenizer预检PASS后冻结12新开发来源组（6原失败/6稳定）、48次固定终答输入adapter开/关配对，模型可见M1身份/原问题/全文/自身初答两工作/cap/seed不变，仅backend权重route改变。首次SSH工作目录相对资格路径拦截已修复，原C资格guard保留，最大3617<16384。FREEZE SHA b9e5d7361f62cc2b53f96c9ec44efee5244f8a72cb5f5b5f95778488e4ceb8c3；原档SHA d5a0c449a77a8d439856c5c31334728ad3ce62dc2bab100bc44f457043f130e8。

48尝试/返回全OK/EOS，227输出token、53.79秒生成、无超限/重试，进程退出/GPU空闲。实际payload/seed/252层开关/输出ID/长度/冻结及本机48评分复算PASS，原seed/on12/12逐字复现。原失败层on1/12→off6/12（6升1降），稳定层12/12→7/12（5降）；人为等量合计13/24对13/24，非总体等效。三来源组关后两seed恢复，但地区年份/相邻县两route均错；年龄另seed关后退步。5控制正式损失含2日期缩略、3目标对象换错，另失败层1新增目标错；不把关adapter作有效方法或唯一病因。

对既有全程阶段新增汇总：新56初答E66.07/普通均值29.17，A私人后62.50/61.90、C58.93/59.52；旧75初答61.33/12，A58.67/44、C60/46.22仍有优势。短答独立C资格未失效，但不自动覆盖多阶段/等私人计算优势或工作质量。当前下一优先明确专家资格适用阶段、私人复议/交付与互动额外影响的比较口径，再决定最小自然覆盖确认或构造修正，不追加提示方法/百题/新seed。

PASS本阶段明确范围的普通对照、所选固定前缀局部诊断及后审；REVISE专家特有、普通总体率、普遍adapter/心理机制、方法净增益或论文主现象确认。维持专家有效判断向团队收益与有益普通纠正主线。新增模型调用48，无训练/新C-H评估/付费API/完整团队重跑，助手none/provisional，非独立人工。

`;
const files=['CORE_RESEARCH_BRIEF.md','CURRENT_STATE.md','handoff.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md','refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md'];
const changes=[];for(const f of files){const p=path.join(root,f),t=fs.readFileSync(p,'utf8'),before=sha(p);if(!t.includes(block.split('\n')[0]))fs.writeFileSync(p,block+t);changes.push({path:f,before,after:sha(p)});}
fs.writeFileSync(path.join(__dirname,'RECORD_UPDATE.json'),JSON.stringify({date:'2026-11-07',scope:'OFFLINE_ORDINARY_COMPARISON_AND_COMPLETED_FIXED_PREFIX_DIAGNOSTIC',new_model_calls:48,changes},null,2)+'\n');
const hashes=Object.fromEntries(fs.readdirSync(__dirname).filter(n=>n!=='ARTIFACT_HASHES.json').map(n=>[n,sha(path.join(__dirname,n))]));
fs.writeFileSync(path.join(__dirname,'ARTIFACT_HASHES.json'),JSON.stringify({files:hashes,reviewer:'assistant',independence:'none/provisional',new_model_calls:48},null,2)+'\n');console.log(JSON.stringify({records:changes.length,artifacts:Object.keys(hashes).length,new_model_calls:48}));
