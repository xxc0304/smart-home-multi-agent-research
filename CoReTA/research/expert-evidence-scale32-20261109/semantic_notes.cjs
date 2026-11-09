// Provisional assistant text/source judgements. Not independent human annotations.
const fs=require('fs'),path=require('path'),assert=require('assert').strict;
const H=__dirname,R=path.resolve(H,'../..'),a=JSON.parse(fs.readFileSync(path.join(H,'ANALYSIS.json')));
const rr=fs.readFileSync(path.join(R,'runs/expert-evidence-scale32-20261109-v1/responses.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const special={
 3:['WRONG_TARGET','EU申请加入May1992替代UK退出；leave/join及主语错。'],
 5:['ANSWER_ONLY','仅English language，没有解释。'],
 6:['WRONG_SCOPE','Egongyan在China而Logan回USA；说明自身即给出矛盾。'],
 14:['SOURCE_BOUNDARY','KNFM服务区域不直接证明licensedMidland；事前边界。'],
 15:['UNRESOLVED_WRONG_DISTRACTOR','正确YaleDailyNews作者线索伴随另一刊物YaleRecord1872，说明未支持候选1878。'],
 17:['WRONG_TARGET','UN机构名替代问到的称号FourPolicemen。'],
 22:['PARTIAL_CLAIM','comune/地点片段，没有完整死亡地桥接。'],
 23:['MIXED_SOURCE_DETAIL','国家正确，但把Wei河口说成Shandong，材料为nearTianjin汇入Hai。'],
 24:['PARTIAL_CLAIM','仅医院位于OklahomaCounty结论，无城市到县依据。'],
 25:['WRONG_RELATION','glacier名称首次记录1900不等于goldrush开始。'],
 26:['SUPPORTED_RELATION_CANDIDATE_MISMATCH','说明采用日2001正确，候选1949取了理事会驻地年份。'],
 28:['SUPPORTED_RELATION_CANDIDATE_TYPE_MISMATCH','说明地域创建1994，短候选却只给地域名EastofEngland。'],
 34:['MIXED_TARGET_BINDING','开头Ulster/Greene相邻属实，Kingston位于县界说法错，且未明确选外邻县；候选Greene正确。'],
 35:['WRONG_TARGET','Austria加入1995替代UK退出决定。'],
 37:['ANSWER_ONLY','仅English，C比B多一次重复答案，并没有新增实质理由。'],
 38:['WRONG_SCOPE','1937开通时世界最长不能推出题目材料中的美国最长。'],
 39:['WRONG_ROLE_LINK','JohnHancock签名与RyanEggold饰JosephWarren均出现，却错误连接到同一目标。'],
 46:['SOURCE_BOUNDARY','MidlandOdessa都市区域与MidlandCounty/licensed概念混合，事前边界。'],
 47:['UNRESOLVED_WRONG_DISTRACTOR','再次 foreground YaleRecord1872，而候选1878；并非清楚正确的专家理由。'],
 48:['SUPPORTED_TARGET_EXTRA_ERROR','Brinkley县名目标正确，但城市命名源自电影狗的因果说法无据。'],
 49:['WRONG_TARGET','UN机构名/同义反复，没有FourPolicemen称号。'],
 51:['SUPPORTED_TARGET_LOCATOR_ERROR','Lille正确，所述P2/P3的电影/出生依据段号需分开，不能以答对认证引用。'],
 54:['ANSWER_ONLY','仅comune，无解释。'],
 55:['MIXED_SOURCE_DETAIL','国家正确，河口Shandong的地理绑定有误。'],
 56:['PARTIAL_CLAIM','仅医院县名结论。'],
 57:['WRONG_RELATION','再次用命名记录1900代替goldrush年份。'],
 58:['SUPPORTED_RELATION_CANDIDATE_MISMATCH','说明2001采用、1949驻地，候选却取1949。'],
 59:['MIXED_TARGET_BINDING','首句将杂志直接归为landgrant大学，后句大学类别正确；候选对不认证首句。'],
 60:['SUPPORTED_DISTINCTION_CANDIDATE_MISMATCH','说明已区别地域1994/办公室1966，候选却取1966。']
};
const qualifier=new Set([18,29,50,61]);
const notes=a.units.map(u=>{const rs=rr.filter(r=>r.unit===u.unit);let pair=special[u.unit]||(qualifier.has(u.unit)?['SUPPORTED_LABEL_WITH_TIME_BOUNDARY','歌手另一专辑上的唱片label支持当前候选，不认证给定歌曲年份独占label。']:['SUPPORTED_TARGET_OR_PARTIAL_CHAIN','主要目标关系/事实与材料一致；不是完整推理、所有细节或所有引用均正确的认证。']);return {unit:u.unit,index:u.index,rep:u.rep,explanation_call:rs.find(r=>r.stage==='explanation').call,candidate_call:rs.find(r=>r.stage==='candidate').call,classification:pair[0],note:pair[1],candidate_em:u.candidate.em};});
assert.equal(notes.length,62);
const cases={
 4:'Collegian seed0：A虽收到后续专家1960正确解释，普通仍多取1963；B/C在更早额外曝光后全取1960。C不比B增益。A部分普通最后工作已说1960但末答1963。',
 15:'Guide seed0：A0/B0.5/C1；独立说明停在YaleRecord1872，候选1878。公开工作大量称题义不明，C终答才有三票1878；不能作为正确说明被理解的清楚正例。',
 27:'大学类别seed0：A和C都对，B普通把学校名称当类别，虽工作同时提landgrant，末答Wyoming。C-B正收益属于避免B相对A的新退步；不是C超过A。',
 28:'RIBA seed0：说明1994正确但候选只给EastofEngland。B普通第一工作call1142就已区别地域/办公室并取1994；A仍1966。B=C，不能将此收益归于新增理由。',
 34:'Foss县seed1：A/B普通正确Greene；C普通第一工作call1418转Ulster，后call1423等明确看见Greene但反转问到的关系终点。M1最后公开仍Greene，却被三票Ulster覆盖。独立说明还误将Kingston放到县界。',
 36:'Collegian seed1：A/C团队对而B错，与seed0 B-A方向反转。B首普通call1490明确拒绝独立候选1960，M1第二公开也说1963，私答恢复1960；C说明较清楚绑定大学年份，最终全对。来源同名报纸边界仍保留。',
 37:'语言seed1：说明只有English，C多一条重复内容而非理由。C专家公开不确定English/Hindi，最后Hindi；三普通English保住团队。不得称为错误解释导致团队失败。',
 38:'桥梁seed1：同一错候选GoldenGate在B/C相同。C first普通call1562显式使用additional记录中的1937最长论据，后续承认冲突仍选GoldenGate，全员末答错。B中间普通也会倾向GoldenGate，但最终三普通回Verrazano，专家仍错；不是B每步都对。',
 39:'演员seed1：同一错候选Ryan在B/C相同。C首普通call1604把Hancock签名接Ryan/Warren，三普通末答Ryan；专家第二工作识别Warren不是目标却编造KevinJRyan演Hancock，最终Kevin。A/B公开专家两次都已说Rafe，最终却回Ryan；普通末答Rafe，团队对。',
 47:'Guide seed1：A0/B1/C0，与seed0 C-B方向反转；C转述1878与1872混杂且否认作者可确定。此题在事前边界敏感性排除表里。',
 60:'RIBA seed1：私人说明正确区别1994/1966但候选1966；B/C全员末答1966。A专家公开也说1966，私人末答却恢复1994，团队仍错。C-B没有团队差，但专家损失不可忽略。'
};
const publicLosses=[[6,'A'],[6,'B'],[6,'C'],[39,'A'],[39,'B'],[49,'C']].map(([unit,arm])=>{const r=rr.find(r=>r.unit===unit&&r.arm===arm&&r.stage==='work'&&r.actor==='M1'&&r.round===2);const u=a.units.find(u=>u.unit===unit);return {unit,index:u.index,arm,last_public_call:r.call,last_public:r.raw_output,final:u.arms[arm].finals.M1,note:'Explicit supported target in public last work but final changes away. Provisional assistant judgement; conditions within one question are not independent replications.'};});
const out={reviewer:'assistant',independence:'none/provisional',explanation_annotations:notes,case_notes:cases,clear_explanation_candidate_mismatches:[26,28,58,60],public_correct_to_wrong_final_examples:publicLosses,scope:'All62 expert explanations and candidates read. All744 finals indexed by48 unique strings and45 changing member paths. Eleven EM-difference units: expert work and first ordinary work plus later target conclusions; selected harmful branches read more fully. Not all1488 ordinary/expert work outputs claimed fully read, not independent human labels.'};
fs.writeFileSync(path.join(H,'SEMANTIC_NOTES.json'),JSON.stringify(out,null,2));
fs.writeFileSync(path.join(H,'CASE_NOTES.md'),['# 过程核读笔记（助手暂定）','','非独立人工；完整原始输出和来源已分别导出CASE文件。这里区分观察和解释，不以末答评分认证理由。','',...Object.entries(cases).map(([u,s])=>`## unit${u}\n\n${s}\n`)].join('\n'));
fs.writeFileSync(path.join(H,'EXPLANATION_TABLE.md'),['# 62份独立说明的目标/依据核读','','标注聚焦可观察实体/关系与支持边界，SUPPORTED_TARGET_OR_PARTIAL_CHAIN不代表完整推理全部正确。','','|unit|index/seed|call|候选EM|类别|说明|','|---|---|---|---|---|---|',...notes.map(n=>`|${n.unit}|${n.index}/${n.rep}|${n.explanation_call}|${n.candidate_em}|${n.classification}|${n.note}|`)].join('\n'));
const finalStrings=new Set(a.units.flatMap(u=>['A','B','C'].flatMap(c=>Object.values(u.arms[c].finals))));
const derived={seed_results:{},candidate_strata:{},all_initial_correct_units:a.units.filter(u=>Object.values(u.initial).every(z=>z.em===1)).length,final_unique_strings:finalStrings.size};
for(const stratum of ['background','diagnostic'])for(const rep of [0,1]){const uu=a.units.filter(u=>u.stratum===stratum&&u.rep===rep);derived.seed_results[stratum+'/'+rep]=Object.fromEntries(['A','B','C'].map(c=>[c,uu.reduce((s,u)=>s+u.arms[c].expected_em,0)/uu.length]));}
for(const em of [0,1]){const uu=a.units.filter(u=>u.candidate.em===em);derived.candidate_strata[em]={units:uu.length,C_minus_B_expected_sum:uu.reduce((s,u)=>s+u.arms.C.expected_em-u.arms.B.expected_em,0),changed_units:uu.filter(u=>u.arms.C.expected_em!==u.arms.B.expected_em).map(u=>u.unit)};}
derived.fixed24_missing_task_C_minus_B_arithmetic_bounds=[(.5-2)/48,(.5+2)/48];
fs.writeFileSync(path.join(H,'ADDITIONAL_ANALYSIS.json'),JSON.stringify(derived,null,2));
console.log(JSON.stringify({explanations:62,unique_final_strings:finalStrings.size,case_units:Object.keys(cases),answer_only:notes.filter(n=>n.classification==='ANSWER_ONLY').map(n=>n.unit),candidate_mismatch_units:out.clear_explanation_candidate_mismatches,public_loss_paths:publicLosses.length,public_loss_tasks:new Set(publicLosses.map(x=>x.index)).size}));
