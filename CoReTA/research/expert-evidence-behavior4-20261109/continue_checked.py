from probe import HERE, ROOT, load, write
c = load(HERE / 'config.json')
s = load(ROOT / c['run_dir'] / 'STATUS.json')
a = load(HERE / 'RUN_AUDIT.json')
assert s['status'] == 'WAITING_FIRST_UNIT_AUDIT'
assert a['result'] == 'PASS' and a['responses_checked'] == 16
write(HERE / 'CONTINUE_CHECKED.json', dict(technical_audit=a, first_unit_review_read=True, scope='Continue remaining seven fixed units; recognition errors and evidence misuse remain outcomes, not exclusion criteria.'))
print('CONTINUE_CHECKED')
