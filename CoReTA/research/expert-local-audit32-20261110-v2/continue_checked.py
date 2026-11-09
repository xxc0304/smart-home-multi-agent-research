"""Release only the already-reviewed fixed prefix, with technical evidence bound."""
from experiment import HERE,ROOT,load,write
c=load(HERE/'config.json');out=ROOT/c['run_dir'];s=load(out/'STATUS.json');a=load(HERE/'RUN_AUDIT.json')
assert s['status']=='WAITING_PREFIX_AUDIT' and s['processed_units']==2 and s['eligible_complete_units']==2
assert a['result']=='PASS' and a['responses_checked']==24 and a['unit_scores_reconstructed']==2
assert a['fresh_model_calls']==6 and a['reused_v1_responses']==18
p=load(HERE/'PREFIX_REVIEW.json');assert p['technical_result']=='PASS' and p['allow_continue'] is True
write(HERE/'CONTINUE_CHECKED.json',{'actual_prefix_audit':a,'prefix_review':p,
 'scope':'Continue remaining 60 eligible frozen prefixes plus 2 inherited missing entries; no positive outcome required; no additional user confirmation.'})
print('CONTINUE_CHECKED')
