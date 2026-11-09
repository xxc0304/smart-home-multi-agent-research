const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'../..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(path.join(__dirname,p),'utf8'));
const s=read('START_SNAPSHOT.json'),pf=read('prepared/PREFLIGHT.json'),tests=read('TESTS.json'),pack=read('INPUTS.json');
if(!s.process_alive||!s.confirmed_returns||pf.science!=='PASS'||pf.engineering!=='PASS'||tests.verdict!=='PASS')throw Error('Start not verified');
if(tests.code_sha256!==sha(fs.readFileSync(path.join(__dirname,'experiment.py')))||tests.tests_sha256!==sha(fs.readFileSync(path.join(__dirname,'test_experiment.py'))))throw Error('Tests/source mismatch');
if(sha(fs.readFileSync(path.join(__dirname,'prepared/FREEZE.json')))!=='9c9f8616414f8c2b03cb2d852e1c43fe89ee2cab896e752c501f06cfaaf75edb')throw Error('Freeze mismatch');
const header='## 2026-11-06 首次独立工作闭环实验已启动：25题双seed、五分支';
const entry=`${header}

用户授权开始并要求仔细设置/有价值选题。见research/b1-independent-first-work-20261106/BRIEF.md、SELECTION_REVIEW.json、READY_REVIEW.md、START_VERIFICATION.md。24输入合格覆盖题按固定hash排序审阅首41条、排17明确缺链/核心指代或粒度争议；另8机制病例含有益普通纠正/私人阶段翻转/团队不损失反例，7重合，实际25题。覆盖题旧E初答15/24、B团队16/24；未按旧终答成功筛题，仍为已见开发资料和助手非盲质量判读，不是原80代表性或留出确认。

四基线A/B/C/D全部新生，加隐藏B_delay；只在E第一轮工作删全部非自身历史，原system/资料/公开位置/两轮/终答/投票保持，后来恢复全历史并真实生成所有受影响下游。共同初答和同批B/B_delay干预前完全相同上游明确共享，不用旧batch2响应当新对照。25题×2固定seed最多3200物理调用/2355200输出token，全部singleton，无时间硬截止，不自动重试。独立分支上限/长度/空输出隔离，共同初答失败跳本题seed，系统故障停止留档。主读数24覆盖题B_delay-B团队期望EM，按资料关联组聚类并含双seed；8机制题另列，不重复计题。四组/五支共同比较与缺失分母另列，官方分数/金标/投票不改。

13CPU检查PASS（含真实执行器与故障回放），1490真实响应重放；实际tokenizer最大10257、长实际回复压力15395<16384，运行时精确长度保护。原专家资格复用、adapter权重和代码/数据/预算冻结；FREEZE SHA 9c9f8616414f8c2b03cb2d852e1c43fe89ee2cab896e752c501f06cfaaf75edb。PID${s.pid}，run runs/b1-independent-first-work-20261106-v1，真实返回${s.confirmed_returns}，状态${s.status.status}，进程存活，已核M1启用adapter/普通关闭252层/batch1；启动不等完成，无质量结论。下一只读status.py跟进并完成后全量审计/原文分析，不按阶段正确率改选题/扩大批次。无新训练/C-H评估/API。助手自审none/provisional，PASS限准备/启动，研究收益/独立确认未通过。

`;
for(const p of ['handoff.md','CURRENT_STATE.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md','experiment/results.md']){
 const f=path.join(root,p),old=fs.readFileSync(f,'utf8');if(!old.includes(header))fs.writeFileSync(f,entry+old);
}
const names=['BRIEF.md','build_pack.cjs','INPUTS.json','LABELS.json','SELECTION_REVIEW.json','SELECTION.md','write_selection.cjs','experiment.py','launch.py','test_experiment.py','run_checks.py','TESTS.json','READY_REVIEW.md','START_VERIFICATION.md','START_SNAPSHOT.json','FIRST_BRANCH_INTEGRITY.json','STAGE_REVIEW.md','record_start.cjs','status.py','audit_live.py'];
fs.writeFileSync(path.join(__dirname,'ARTIFACT_HASHES.json'),JSON.stringify(names.map(p=>({path:p,sha256:sha(fs.readFileSync(path.join(__dirname,p)))})),null,2)+'\n');
console.log(JSON.stringify({records:7,pid:s.pid,confirmed_returns:s.confirmed_returns,unique_questions:pack.unique_questions,status:s.status.status}));
