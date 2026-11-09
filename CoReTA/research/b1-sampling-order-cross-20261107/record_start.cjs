const fs=require('fs'),path=require('path'),crypto=require('crypto');
const ROOT=path.resolve(__dirname,'../..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(path.join(__dirname,p),'utf8'));
const s=read('START_SNAPSHOT.json'),p=read('prepared/PREFLIGHT.json'),i=read('FIRST_CROSS_INTEGRITY.json'),t=read('TESTS.json');
if(!s.process_alive||s.new_confirmed_returns<1||p.science!=='PASS'||p.engineering!=='PASS'||!i.first_expert_input_verified||!i.second_expert_history_restored||!i.downstream_reads_new_work)throw Error('Startup not verified');
if(t.code_sha256!==sha(fs.readFileSync(path.join(__dirname,'experiment.py')))||t.tests_sha256!==sha(fs.readFileSync(path.join(__dirname,'test_experiment.py'))))throw Error('Stale tests');
if(sha(fs.readFileSync(path.join(__dirname,'prepared/FREEZE.json')))!=='86e92af0c0967429f9bc54a0c50f1139a921560e516eb393a43c82789e33bc23')throw Error('Freeze mismatch');
const heading='## 2026-11-07 采样×顺序交叉诊断已启动：只补两个缺失组合';
const entry=`${heading}

用户授权开始。见research/b1-sampling-order-cross-20261107/BRIEF.md、READY_REVIEW.md、START_VERIFICATION.md和STAGE_REVIEW.md。原25题（24覆盖+8机制重合7）不换；原S0O0/S1O1完整B/B_delay对角继承，新增S0O1/S1O0共50格/100分支。S控制初答和后续模型seed，O控制展示和两轮发言顺序，匹配初答按S精确复用；每格B/B_delay同S/O，后者仅首次E删全部peer历史、后来恢复。新交叉全部下游新生，仅同格干预前新上游共享。原A/C/D和所有旧评分保留作参照，对角100分支与200独立初答不充新调用。

11CPU检查、1200精确对角真实响应回放、1200交叉真实全文重组通过，固定S换O/固定O换S互斥性与全执行器故障隔离已核；原资格SUPPORTED_TASK_ADVANTAGE复用。真实最大输入+cap10379、压力14816<16384；逐请求精确长度保护。最多1200新生成/921600输出token，完整预计1133（67同格新共享）；无时间硬截止、不自动重试，独立格隔离失败、系统故障停止。FREEZE SHA86e92af0c0967429f9bc54a0c50f1139a921560e516eb393a43c82789e33bc23，已绑定代码、源run/权重/资格、复用初答/对角引用、标签和预算。

01:25:50后台PID${s.pid}，run runs/b1-sampling-order-cross-20261107-v1；快照${s.new_confirmed_returns}新返回全OK、进程存活。首S0O1实际核验初答源S0/展示及发言取O1/生成seed取S0、E首次隔离及第二轮恢复、队友新消息和adapter252层/batch1通过。约2–3小时估计不是截止；启动非完成，无中途质量结论。下一只读status.py跟进并完成后对照四格δ及固定O采样差、固定S顺序差、交互/平均增益，按24题关联组绑定全矩阵；8机制另列，缺失格/共同题另报。仅两个预定level，非一般方差分解/未见任务/专家特有机制确认。无训练/C-H新评估，助手自审none/provisional，PASS准备和启动。

`;
for(const p of ['handoff.md','CURRENT_STATE.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md','experiment/results.md']){const f=path.join(ROOT,p),old=fs.readFileSync(f,'utf8');if(!old.includes(heading))fs.writeFileSync(f,entry+old);}
const files=['BRIEF.md','EXPERIMENT_REVIEW.md','READY_REVIEW.md','START_VERIFICATION.md','STAGE_REVIEW.md','experiment.py','test_experiment.py','launch.py','run_checks.py','status.py','audit_live.py','TESTS.json','FIRST_CROSS_INTEGRITY.json','START_SNAPSHOT.json','record_start.cjs'];
fs.writeFileSync(path.join(__dirname,'ARTIFACT_HASHES.json'),JSON.stringify(files.map(p=>({path:p,sha256:sha(fs.readFileSync(path.join(__dirname,p)))})),null,2)+'\n');
console.log(JSON.stringify({recordsUpdated:7,pid:s.pid,newReturns:s.new_confirmed_returns,status:s.status.status}));
