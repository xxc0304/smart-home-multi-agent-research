"""Read-only outcome summary; never generates or changes frozen raw data."""
import json
from collections import defaultdict
from experiment import HERE,ROOT,load,source,Team,equal,score,write
from b0_answers import paired_interval

c=load(HERE/'config.json');out=ROOT/c['run_dir'];entries=load(HERE/'INPUTS.json')['units'];labels=load(HERE/'LABELS.json')['targets']
new={s['unit']:s for s in load(out/'scores.json')};rows=[]
for e in entries:
 t=Team(e);idx=source(e)
 while (r:=t.next_request()) is not None:
  z=idx.get((r['actor'],r['stage'],r['arm'],r['round']))
  if z is None:break
  assert equal(r,z)
  t.submit(r['request_id'],z['raw_output'],status=z['status'],usage=z['usage'],source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
 rows.append(dict(entry={k:e[k] for k in ['unit','id','rep','cohort','group','strict']},mixed=score(e,t,labels),all_expert=new.get(e['unit'])))

def complete(r):return r['all_expert'] and all(r[k]['arms'][a]['complete'] for k in ['mixed','all_expert'] for a in ['A','B'])
fresh=[r for r in rows if r['entry']['cohort']=='fresh'];eligible={r['entry']['id'] for r in fresh if sum(x['entry']['id']==r['entry']['id'] and complete(x) for x in fresh)==2}
primary=[r for r in fresh if r['entry']['id'] in eligible]

def summary(rs):
 result=dict(paired_units=len(rs),unique_questions=len({r['entry']['id'] for r in rs}),conditions={},contrasts={})
 if not rs:return result
 for model in ['mixed','all_expert']:
  for arm in ['A','B']:
   ss=[r[model]['arms'][arm] for r in rs];result['conditions'][model+'_'+arm]=dict(team_expected_em=sum(s['expected_em'] for s in ss)/len(ss),M1_em=sum(s['M1_em'] for s in ss)/len(ss),mean_members_em=sum(s['members'][a]['em'] for s in ss for a in ['M1','M2','M3','M4'])/(4*len(ss)))
 contrasts=[('all_expert_B','mixed_B'),('all_expert_A','mixed_A'),('mixed_B','mixed_A'),('all_expert_B','all_expert_A')]
 for left,right in contrasts:
  def val(r,k):model,arm=k.rsplit('_',1);return r[model]['arms'][arm]['expected_em']
  grouped=defaultdict(list);groups={}
  for r in rs:
   i=r['entry']['id'];grouped[i].append(val(r,left)-val(r,right));groups[i]=r['entry']['group']
  values={i:sum(v)/len(v) for i,v in grouped.items()}
  result['contrasts'][left+'-'+right]=dict(mean_task_difference=sum(values.values())/len(values),exploratory_group_ci95=paired_interval(values,groups,10000,20261109),gained_units=sum(val(r,left)>val(r,right) for r in rs),lost_units=sum(val(r,left)<val(r,right) for r in rs))
 return result

views=dict(primary_fresh_both_seeds=summary(primary),fresh_each_complete_unit=summary([r for r in fresh if complete(r)]),fresh_strict_both_seeds=summary([r for r in primary if r['entry']['strict']]),fresh_answer_overlap_both_seeds=summary([r for r in primary if not r['entry']['strict']]),first_seed_all100_exploratory=summary([r for r in rows if r['entry']['rep']==0 and complete(r)]))
for cohort in ['old_coverage','mechanism']:views[cohort]=summary([r for r in rows if r['entry']['cohort']==cohort and complete(r)])
result=dict(status=load(out/'STATUS.json')['status'],scope='DEVELOPMENT_COMPOSITION_DIAGNOSTIC_NOT_CONFIRMATORY',expected_unique_questions=100,expected_fresh_questions=56,expected_units=156,processed_units=len(new),missing_or_incomplete=[r['entry'] for r in rows if not complete(r)],views=views,rows=rows)
write(HERE/'SUMMARY.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ['rows','missing_or_incomplete']},ensure_ascii=False),flush=True)
