// Assistant diagnostic only. Keep all official scores/vote groups unchanged.
const fs=require('fs'),path=require('path');
const ROOT=path.resolve(__dirname,'../..'),RUN=path.join(ROOT,'runs/b1-independent-first-work-20261106-v1');
const read=p=>JSON.parse(fs.readFileSync(path.join(RUN,p),'utf8'));
const s=read('scores.json');
const extra={55:new Set(['40%']),73:new Set(['Jubilee Records']),62:new Set(['March 1st, 1920']),38:new Set(['Kershaw County, South Carolina.'])};
const optional={70:new Set(['French Revolution'])};
function hit(i,answer,em,broad=false){return em||extra[i]?.has(answer)||(broad&&optional[i]?.has(answer))?1:0;}
function evaluate(broad){const rs=s.rows.filter(r=>r.coverage),out={scope:'ASSISTANT_AUXILIARY_NO_OFFICIAL_LABEL_OR_VOTE_CHANGE',extra_aliases:Object.fromEntries(Object.entries(extra).map(([k,v])=>[k,[...v]])),optional_period_equivalence:broad,conditions:{}};
for(const c of ['A','B','C','D','B_delay']){let team=0,expert=0;for(const r of rs){const z=r.conditions[c];const winners=z.vote.winners.length?z.vote.winners:[''];team+=winners.reduce((a,v)=>a+hit(r.index,v,z.members[Object.keys(z.members).find(a=>z.members[a].answer===v)]?.em||0,broad),0)/winners.length;expert+=hit(r.index,z.members.M1.answer,z.members.M1.em,broad);}out.conditions[c]={teamEM:team/rs.length,expertEM:expert/rs.length};}
out.teamDelta=out.conditions.B_delay.teamEM-out.conditions.B.teamEM;out.expertDelta=out.conditions.B_delay.expertEM-out.conditions.B.expertEM;return out;}
const result={clearSurfaceEquivalences:evaluate(false),withOptionalPeriodEquivalence:evaluate(true)};
fs.writeFileSync(path.join(__dirname,'SEMANTIC_SENSITIVITY.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
