// Assistant text review: all 97 new unique E-work texts read; 142 old labels inherited.
const fs=require('fs'),path=require('path');
const read=p=>JSON.parse(fs.readFileSync(path.join(__dirname,p),'utf8'));
const unique=read('E_WORK_UNIQUE.json'),a=read('ANALYSIS.json');
const negative=new Set([16,17,18,19,21,38,48,49,50,51,52,54,59,60,61,92,93,124,125,133,134,142,143,144,145,146,148,168,169,208,209,210,211,219,220,221,222,224]);
const mixed=new Set([37,74,115,116,131,233,234,235,237]);
const labels=unique.map(x=>({...x,label:x.previous_label??(negative.has(x.uid)?'N':mixed.has(x.uid)?'M':'C'),provenance:x.previous_label===null?'NEW_ASSISTANT_TEXT_REVIEW':'INHERITED_EXACT_QUESTION_AND_TEXT',reviewer:'assistant',independence:'none/provisional',scope:'Explicit endorsed correct target candidate; C does not certify complete reasoning or grounding. M=qualified/mixed target commitment; N=wrong or not endorsing target.'}));
const byreq=new Map(labels.flatMap(x=>x.refs.map(r=>[r.request_id,x.label])));
const pairs=a.pairs.map(p=>({...p,workLabels:Object.fromEntries(['B','B_delay'].map(c=>[c,p.work[c].map(r=>byreq.get(r.request_id))]))}));
function summarize(ps){let out={units:ps.length,first:{},second:{},firstGains:[],firstLosses:[],gainsLostSecond:[],recoveredAfterWrongFirst:[]};
 for(const c of ['B','B_delay'])for(const [k,i] of [['first',0],['second',1]])out[k][c]=Object.fromEntries(['C','M','N'].map(l=>[l,ps.filter(p=>p.workLabels[c][i]===l).length]));
 for(const p of ps){const b=p.workLabels.B,d=p.workLabels.B_delay;const ref={q:p.q,S:p.S,O:p.O,B:b,B_delay:d,team:p.team,expert:p.expert};if(b[0]!=='C'&&d[0]==='C'){out.firstGains.push(ref);if(d[1]!=='C')out.gainsLostSecond.push(ref);}if(b[0]==='C'&&d[0]!=='C')out.firstLosses.push(ref);if(d[0]!=='C'&&d[1]==='C')out.recoveredAfterWrongFirst.push(ref);}
 return out;}
const cov=pairs.filter(p=>p.coverage);const process={scope:'ASSISTANT_CANDIDATE_COMMITMENT_LABELS_NOT_INDEPENDENT_REASONING_ANNOTATION',coverage:summarize(cov),cells:Object.fromEntries([0,1].flatMap(s=>[0,1].map(o=>[`S${s}O${o}`,summarize(cov.filter(p=>p.S===s&&p.O===o))]))),allExpertWorkRecords:400,uniqueTexts:labels.length,newUniqueReviewed:labels.filter(x=>x.previous_label===null).length,priorExactTextLabels:labels.filter(x=>x.previous_label!==null).length,pairs};
fs.writeFileSync(path.join(__dirname,'E_WORK_LABELS.json'),JSON.stringify(labels,null,2)+'\n');fs.writeFileSync(path.join(__dirname,'PROCESS_ANALYSIS.json'),JSON.stringify(process,null,2)+'\n');
console.log(JSON.stringify({coverage:process.coverage,cells:Object.fromEntries(Object.entries(process.cells).map(([k,v])=>[k,{first:v.first,second:v.second,gain:v.firstGains.length,loss:v.firstLosses.length,laterLost:v.gainsLostSecond.length}]))},null,2));
