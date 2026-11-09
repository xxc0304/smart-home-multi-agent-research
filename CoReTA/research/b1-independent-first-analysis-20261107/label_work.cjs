// Assistant read all 142 full unique E texts, mapping 200 B/B_delay work records.
// C = endorses the task target candidate, N = no correct endorsement,
// M = target mentioned but binding/commitment remains mixed. Not proof of reasoning.
const fs=require('fs'),path=require('path');
const read=n=>JSON.parse(fs.readFileSync(path.join(__dirname,n),'utf8'));
const texts=read('E_WORK_UNIQUE.json'),a=read('ANALYSIS.json');
const n=new Set([4,5,8,9,10,11,12,13,15,28,29,30,31,32,33,34,36,39,41,42,44,52,53,60,64,69,74,75,80,83,84,86,87,88,90,91,92,94,95,96,97,117,119,121,123,124,125,126,127,128,129,130,131,132,133,134]);
const mixed=new Set([14,58,81]);
const notes={14:'法国大革命与变更联系已提，但继续要求确切日期，未承诺问题所需时段。',58:'同时列奥地利40%和瑞士30%，未选定问的第三国。',81:'提出Astrid且解释共同父亲，但最后否认能确定。',25:'WHO候选正确，但UN Women/UN机构关系解释不可靠，C不认证解释。',73:'Jubilee Records与Jubilee候选同一标签，长短表述另记，非完整推理认证。',89:'gain more Luftwaffe units为目标候选的语义近似，缺control词不直接判完整逻辑。',108:'完整日期包含正确年份，工作候选C不按最终短串EM机械评分。',141:'最后条件式回答30000，候选C，仍混有误读村庄为国家的前文。'};
const labels=texts.map(x=>({...x,label:mixed.has(x.uid)?'M':n.has(x.uid)?'N':'C',note:notes[x.uid]||null,reviewer:'assistant',independence:'none/provisional',scope:'Explicit endorsed target candidate only; not full grounding or internal reasoning quality.'}));
fs.writeFileSync(path.join(__dirname,'E_WORK_LABELS.json'),JSON.stringify(labels,null,2)+'\n');
const label=uid=>labels[uid].label;
const rows=a.pairs.map(r=>({...r,workLabelsB:r.expertWorkB.map(x=>label(x.uid)),workLabelsDelay:r.expertWorkDelay.map(x=>label(x.uid))}));
function summarize(rs){const out={units:rs.length,conditions:{},firstChanges:[],secondChanges:[],firstImprovementLostBeforeFinal:[]};for(const [c,key]of[['B','workLabelsB'],['B_delay','workLabelsDelay']])out.conditions[c]={first:Object.fromEntries(['C','N','M'].map(l=>[l,rs.filter(r=>r[key][0]===l).length])),second:Object.fromEntries(['C','N','M'].map(l=>[l,rs.filter(r=>r[key][1]===l).length]))};
for(const r of rs){if(r.workLabelsB[0]!==r.workLabelsDelay[0])out.firstChanges.push({index:r.index,rep:r.rep,b:r.workLabelsB[0],d:r.workLabelsDelay[0],team:r.team});if(r.workLabelsB[1]!==r.workLabelsDelay[1])out.secondChanges.push({index:r.index,rep:r.rep,b:r.workLabelsB[1],d:r.workLabelsDelay[1],team:r.team});if(r.workLabelsB[0]!=='C'&&r.workLabelsDelay[0]==='C'&&r.workLabelsDelay[1]!=='C')out.firstImprovementLostBeforeFinal.push({index:r.index,rep:r.rep,second:r.workLabelsDelay[1],team:r.team});}
return out;}
const result={scope:'ASSISTANT_CANDIDATE_LABELS_NOT_INDEPENDENT_GROUNDING',summaries:{coverage:summarize(rows.filter(r=>r.coverage)),mechanism:summarize(rows.filter(r=>r.mechanism)),union:summarize(rows)},rows};
fs.writeFileSync(path.join(__dirname,'PROCESS_ANALYSIS.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({labelCounts:Object.fromEntries(['C','N','M'].map(l=>[l,labels.filter(x=>x.label===l).length])),summaries:result.summaries},null,2));
