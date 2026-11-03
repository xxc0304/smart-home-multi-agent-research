"""Freeze natural-failure recovery controls; labels are offline, never in packets."""
import argparse
from pathlib import Path
from order_collaboration import ROOT,prepare as prepare_base,read,write,sha,CAP


def prepare(output):
    if output.exists():raise ValueError('new directory required')
    output.mkdir(parents=True)
    archive=ROOT/'runs/order-collaboration-development-live-20261024-r2'
    pack=ROOT/'runs/distributed-order-tasks-prepared-20261024-r2'
    units=[];labels={};selected=[]
    # Every natural failed W0 in the batch; one first-correct A/B/C control
    # from the same episode. Selection does not consult future repair outcomes.
    for ep in ['episode-02','episode-03','episode-04']:
        scoring=read(archive/ep/'offline_scores.json')
        failed=[a['arm'] for a in scoring['arms'] if not a['raw_work_scores']['W0']['correct']]
        if not failed:continue
        good=next(a['arm'] for a in scoring['arms'] if a['raw_work_scores']['W0']['correct'])
        selected += [(ep,arm,False) for arm in failed]+[(ep,good,True)]
    if len(selected)!=4:raise ValueError('archived roster differs; review selection before freezing')
    for i,(ep,arm,correct) in enumerate(selected):
        name=f'draft-{i+1:02d}';p=output/name
        archived_manifest=read(archive/ep/'manifest.json');progress=read(archive/ep/'progress.json')
        ordering=[('A','B','C'),('B','C','A'),('C','A','B')][i%3]
        prepare_base(pack,p,case=archived_manifest['case'],editor=archived_manifest['editor'],arm_order=ordering)
        initial={r['owner']:r['answer'] for r in progress['completed'] if r['stage']=='INIT'}
        work=progress['arm_states'][arm]['selection']['raw_works']['W0']
        replay=dict(initial_answers=initial,shared_work=dict(reason=work['reason'],order=work['order']))
        write(p/'replay.json',replay)
        m=read(p/'manifest.json')
        m.update(kind='order_same_work_diagnostic',schedule=[r for r in m['schedule'] if r['stage'] in {'REVIEW','FINAL'}],
                 max_requests=12,max_output_tokens=12*CAP,
                 interpretation='selected natural-error recovery and correct-work preservation diagnostic; not overall accuracy',
                 archive_provenance=dict(episode=ep,arm=arm,progress_sha256=sha(archive/ep/'progress.json')))
        m['files']['replay.json']=sha(p/'replay.json')
        m['code_sha256']['tools/prepare_order_same_work.py']=sha(ROOT/'tools/prepare_order_same_work.py')
        write(p/'manifest.json',m)
        labels[name]=dict(initial_correct=correct,episode=ep,source_arm=arm)
        units.append(dict(directory=name,manifest_sha256=sha(p/'manifest.json')))
    write(output/'offline_labels.json',labels)
    write(output/'PLAN.json',dict(kind='same_work_three_member_recovery_diagnostic',units=units,
        max_requests=48,max_output_tokens=48*CAP,offline_labels_sha256=sha(output/'offline_labels.json'),
        selection='all natural failures plus first correct A/B/C work from each affected episode',
        real_requests=0,stop_after_first_technical_failure=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    prepare(parser.parse_args().output)
