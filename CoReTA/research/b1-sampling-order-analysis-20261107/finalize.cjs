const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'../..'),stage='research/b1-sampling-order-analysis-20261107/';
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const audit=read(stage+'POST_RUN_AUDIT.json');let verified=0;
for(const [p,h]of Object.entries(audit.original_run_file_hashes)){const local=path.join(root,p.split('/CoReTA/')[1]);if(hash(local)!==h)throw Error('Downloaded run mismatch '+p);verified++;}
const a=read(stage+'ANALYSIS.json'),labels=read(stage+'E_WORK_LABELS.json');
const finalUnique=new Map();for(const p of a.pairs)for(const c of ['B','B_delay'])for(const [actor,text]of Object.entries(p.finals[c])){const key=p.q+'|'+text;if(!finalUnique.has(key))finalUnique.set(key,{q:p.q,text,refs:[]});finalUnique.get(key).refs.push({S:p.S,O:p.O,condition:c,actor});}
if(labels.length!==239||labels.reduce((s,x)=>s+x.refs.length,0)!==400)throw Error('Label coverage mismatch');
const coverage={reviewer:'assistant',independence:'none/provisional',final_records:800,final_unique_question_texts:finalUnique.size,final_texts_reviewed:'All unique question/text final strings read in this stage',expert_work_records:400,expert_unique_texts:239,new_expert_unique_texts_reviewed:97,exact_old_text_labels_inherited:142,ordinary_work_full_new_branches:[{q:35,S:0,O:1,conditions:['B','B_delay']},{q:53,S:0,O:1,conditions:['B_delay']},{q:53,S:1,O:0,conditions:['B_delay']},{q:1,S:1,O:0,conditions:['B_delay']}],support_paragraphs_reviewed:[{q:53,titles:['Six Flags Magic Mountain','Santa Clarita, California']},{q:35,titles:['Jai Kishan','Rahimtulla M. Sayani']},{q:1,titles:['Yale University','Wesley Alba Sturges']}],prior_qualified_case_reviews:'Original q78/q19 complete benefit paths and q18 process review retained; all q78/q19 expert work compared across four cells in this stage',not_claimed:'Independent annotation; all ordinary work; complete reasoning/grounding validation; hidden belief states; unseen-task replication',downloaded_original_run_files_sha_verified:verified};
fs.writeFileSync(path.join(__dirname,'SEMANTIC_REVIEW_COVERAGE.json'),JSON.stringify(coverage,null,2)+'\n');
fs.writeFileSync(path.join(__dirname,'FINAL_UNIQUE.json'),JSON.stringify([...finalUnique.values()],null,2)+'\n');
const block=`## 2026-11-07 采样×顺序交叉审计分析完成：收益集中，首次保护尚不充分

见research/b1-sampling-order-analysis-20261107/REPORT.md、POST_RUN_AUDIT.json及STAGE_REVIEW.md。新1133物理/1200逻辑返回全EOS，67共享；50屏蔽/50恢复、路由/token/冻结/官方100行评分复核通过，实际最大输入+cap10213，原件未改；2h01m02s、131217输出token，档案SHA793fe3c83d46075ef074ee984f09b3a39c4de8f63f8cf26adae6715470002ef0。

主24覆盖题四格B→B_delay：S0O0 66.67→66.67（旧）、S0O1 62.50→63.54（新）、S1O0 70.83→70.83（新）、S1O1 58.33→66.67（旧）。四格均值64.58→66.93，+2.34pp/CI[0,5.47]；新增交叉仅+0.52pp，来自第35题S0O1两种拒答措辞拆票，正确专家与错误普通内容均未实质改善，0→0.25期望而非一道完整纠正。原第78/19实质收益仍仅S1O1，其余格B本来已正确。O0两S无效，O1幅度依S；交互+7.29pp区间跨0，非一般顺序/采样机制证明。50对首次独立E跨O输入/seed/输出全文相同。

400E工作去重239（旧142精确继承，新97全文读）、800末答按题去重核读；普通工作核读范围另存。首次正确候选58→74，第二57→66，E末答61→62；21首次改善中12后来丢失，均为相关重复单元。第53四格均私人E/首次独立正确、恢复后错且团队全错，当前4次初对终错皆该题；首次保护不能解决后续失守，不能算4题。第1题S1O0仍见普通正确1843、E屏蔽后1810、恢复后1843的有益纠正路径，未证单条必要性。

原D80团队低于独立E事实保留；本筛选批官方团队可高于独立E，不能否定原80。清楚等价表述辅助B团队69.79/E76.04，B_delay72.14/E77.08；不改官方投票/评分，不能由0官方EM下降称普遍无损。主24题8因子区间确定顺序重放一致，联合25题3辅助区间有set顺序Monte Carlo端点微差已留档。

PASS完整审计与探索分析，REVISE稳定方法/专家特有/心理机制/普遍无损。B_delay保留诊断基线，停止直接当主方法推广；下一准备一个针对互动中正确判断保留/有依据修订的有限机制对照与P2决策页，保留有效普通纠正、简单控制和独立确认需求。仅允许准备；不自动再加seed或题、不新生成/训练/C-H评估。助手自审none/provisional。

`;
const records=['CURRENT_STATE.md','handoff.md','brainstorm.md','experiment/results.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md','refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER.md'];
const changes=[];
for(const p of records){const f=path.join(root,p),old=fs.readFileSync(f,'utf8'),before=hash(f);if(!old.includes(block.split('\n')[0]))fs.writeFileSync(f,block+old);changes.push({path:p,before,after:hash(f)});}
const evidence=['runs/b1-sampling-order-cross-20261107-v1/FREEZE.json','runs/b1-sampling-order-cross-20261107-v1/scores.json','runs/b1-sampling-order-cross-20261107-v1/RESULTS.json','research/b1-independent-first-analysis-20261107/E_WORK_LABELS.json','research/b1-independent-first-analysis-20261107/REPORT.md'];
fs.writeFileSync(path.join(__dirname,'RECORD_UPDATE.json'),JSON.stringify({date:'2026-11-07',review:'assistant none/provisional',records:changes,source_hashes:Object.fromEntries(evidence.map(p=>[p,hash(path.join(root,p))])),new_model_calls:0,new_training:0,new_C_H_evaluation:0},null,2)+'\n');
const files=fs.readdirSync(__dirname).filter(f=>f!=='ARTIFACT_HASHES.json'&&fs.statSync(path.join(__dirname,f)).isFile());
fs.writeFileSync(path.join(__dirname,'ARTIFACT_HASHES.json'),JSON.stringify({files:Object.fromEntries(files.map(f=>[f,hash(path.join(__dirname,f))]))},null,2)+'\n');
console.log(JSON.stringify({verified_run_files:verified,final_unique:finalUnique.size,expert_unique:labels.length,record_updates:changes.length,artifacts:files.length}));
