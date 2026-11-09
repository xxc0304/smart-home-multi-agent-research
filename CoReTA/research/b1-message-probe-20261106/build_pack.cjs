const fs=require('fs'),path=require('path');const ROOT=path.resolve(__dirname,'../..');
const read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
const evidence=read('research/b1-dev80-review-20261106/REVIEW_EVIDENCE.json');
const all=read('research/b1-dev80-analysis-20261106/ANALYSIS.json');
const cards=evidence.event_inventory.map(e=>{const t=read(`runs/b1-dev80-20261106-v1/trials/${String(e.index).padStart(3,'0')}.json`),c=all.cases[e.index];return {index:e.index,question:t.task.question,target:c.target.answer,aliases:c.target.answer_aliases,support:t.task.paragraphs.filter(p=>c.target.paragraphs.some(v=>v.idx===p.idx&&v.is_supporting)),initials:t.initials,finals:t.finals,reasons:e.reasons,expert_public_work:t.records.filter(q=>q.actor==='M1'&&q.stage==='work'&&['B','D'].includes(q.arm)).map(q=>({id:q.request_id,arm:q.arm,text:q.raw_output}))};});
fs.writeFileSync(path.join(__dirname,'EVENT_CARDS.json'),JSON.stringify(cards,null,2)+'\n');
const start=Number(process.argv[2]??0),end=Number(process.argv[3]??5);
for(const c of cards.slice(start,end))console.log(JSON.stringify(c));
