from experiment import HERE,ROOT,load,write
c=load(HERE/'config.json');s=load(ROOT/c['run_dir']/'STATUS.json');a=load(HERE/'RUN_AUDIT.json')
assert s['status']=='WAITING_PREFIX_AUDIT' and s['processed_units']==2
assert a['result']=='PASS' and a['responses_checked']==s['calls'] and a['complete_unit_scores_reconstructed']==2
write(HERE/'CONTINUE_CHECKED.json',dict(actual_prefix_audit=a,actual_explanation_candidate_and_peer_visibility_reviewed=True,scope='Continue remaining fixed62 units; no semantic success or positive gain required; no new user approval.'))
print('CONTINUE_CHECKED')
