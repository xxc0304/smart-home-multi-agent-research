// Evidence viewer: exact source paragraphs and complete selected review texts, no generated summaries.
const fs=require('fs'),path=require('path'),H=__dirname;
const read=n=>JSON.parse(fs.readFileSync(path.join(H,n),'utf8'));
const a=read('ANALYSIS.json'),inputs=read('INPUTS.json').entries,labels=read('LABELS.json').targets;
const ids=process.argv[2].split(',').map(Number),arms=(process.argv[3]||'L').split(',');
for(const id of ids){const s=a.units.find(u=>u.unit===id),e=inputs.find(u=>u.unit===id),support=new Set(labels[s.id].paragraphs.filter(p=>p.is_supporting).map(p=>p.idx));
 console.log(`\n# UNIT ${id} INDEX ${s.index} SEED ${s.rep} ${s.stratum}\nQ ${s.question}\nGOLD ${s.gold}\nINITIAL ${JSON.stringify(s.initials)}\nEXPLANATION ${s.explanation}\nFINALS ${JSON.stringify(Object.fromEntries(Object.entries(s.arms).map(([a,x])=>[a,{answer:x.answer,em:x.metrics.em}])))}\n`);
 const cited=new Set(support);
 for(const ar of arms)for(const r of s.reviews[ar])for(const m of r.text.matchAll(/(?:paragraph|passage|\bP)\s*\[?(\d+)/gi))cited.add(Number(m[1]));
 for(const p of e.task.paragraphs.filter(p=>cited.has(p.idx)))console.log(`[P${p.idx} ${p.title}] ${p.paragraph_text}\n`);
 for(const ar of arms)for(const r of s.reviews[ar])console.log(`${ar}/SLOT${r.slot}: ${r.text}\n`);
}
