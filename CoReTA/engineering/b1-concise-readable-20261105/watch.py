"""Keep one read-only SSH monitor open until the bounded job ends."""
import contextlib,io,runpy,time
from pathlib import Path
while True:
    with contextlib.redirect_stdout(io.StringIO()):
        d=runpy.run_path(str(Path(__file__).with_name('progress.py')),run_name='__main__')
    r=d['result']
    print({k:r[k] for k in ('n_requests','n_complete_52_request_tasks','task_request_counts','format_warnings','technical_non_ok','results')},flush=True)
    if r['results'] is not None:break
    time.sleep(40)
