const fs=require('fs'),path=require('path');const root=path.resolve(__dirname,'../..'),read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const a=read(path.join(__dirname,'TWO_SEED_ANALYSIS.json'));const main=a.rows.filter(r=>a.rows.some(q=>q.id===r.id&&q.seed===1&&q.complete));const changes=[];
for(const seed of [0,1])for(const [l,p]of [['B','A'],['D','C']]){const xs=main.filter(r=>r.seed===seed);changes.push({seed,contrast:l+p,harm:xs.filter(r=>r.vals.official[p].M1>r.vals.official[l].M1).map(r=>r.index),gain:xs.filter(r=>r.vals.official[p].M1<r.vals.official[l].M1).map(r=>r.index),miss:xs.filter(r=>r.vals.official[l].M1&&r.team.official[l]<1).map(r=>r.index)});}
fs.writeFileSync(path.join(__dirname,'REPEAT_TRANSITIONS.json'),JSON.stringify(changes,null,2));console.log(JSON.stringify(changes));
const labels=read(path.join(__dirname,'REPEAT_LABELS.json')).targets,pack=read(path.join(__dirname,'REPEAT_INPUTS.json'));
let out='';for(const index of [6,17,27,35,43,44,49,54]){const e=pack.tasks.find(e=>e.index===index),t=read(path.join(root,`runs/b1-stage-advantage-seed1-20261107-v1/trials/${String(index).padStart(3,'0')}.json`));out+=`\n## index${index} ${e.task.question}\nGold:${labels[e.id].answer}\nInitial:${JSON.stringify(t.initials)}\n`;
const supports=new Set(labels[e.id].paragraphs.filter(p=>p.is_supporting).map(p=>p.idx));for(const p of e.task.paragraphs.filter(p=>supports.has(p.idx)))out+=`P${p.idx} ${p.title}: ${p.paragraph_text}\n`;
for(const c of ['A','B','C','D']){out+=`${c} Finals:${JSON.stringify(t.finals[c])}\n`;for(const z of t.records.filter(z=>z.arm===c&&z.actor==='M1'&&z.stage==='work'))out+=`${c}/E${z.round}: ${z.raw_output}\n`;}}
fs.writeFileSync(path.join(__dirname,'REPEAT_CASES.md'),out);console.log(out);
