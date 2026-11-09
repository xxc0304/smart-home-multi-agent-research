const fs=require('fs'),path=require('path');
const source=path.resolve(__dirname,'../b1-audit-20261104/PROCESS_CASES.json');
const cases=JSON.parse(fs.readFileSync(source,'utf8'));
const start=Number(process.argv[2]||0),end=Number(process.argv[3]||cases.length);
for(let n=start;n<end;n++){
 const c=cases[n];console.log('\nCASE',n,c.id,c.question,'GOLD',c.target.answer,'INITIAL',JSON.stringify(c.initials));
 if(process.argv[4]==='peerbrief'){
  for(const arm of 'ABCD')for(const m of c.messages[arm].filter(m=>m.actor!=='M1'))console.log(arm,m.request_id,m.actor,'R'+m.round,m.text.length>340?m.text.slice(0,150)+' [...OMITTED; see original...] '+m.text.slice(-190):m.text);
  continue;
 }
 const support=c.target.paragraphs.filter(p=>p.is_supporting).map(p=>p.idx);
 for(const p of c.paragraphs.filter(p=>support.includes(p.idx)))console.log('SUPPORT',p.idx,p.title,p.paragraph_text);
 for(const arm of 'ABCD'){
  const s=c.score.arms[arm];console.log('\nARM',arm,'FINAL',JSON.stringify(s.members),'VOTE',JSON.stringify(s.vote),'EXPECTED',s.expected_em);
  for(const m of c.messages[arm]){
   if(process.argv[4]==='peers'&&m.actor==='M1')continue;
   if(process.argv[4]!=='peers'&&m.actor!=='M1')continue;
   console.log(m.request_id,m.actor,'R'+m.round,m.text);
  }
 }
}
