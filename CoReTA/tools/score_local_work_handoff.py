"""Release-checked offline scoring. Runtime never imports or reads evaluation labels."""
import argparse
from pathlib import Path

from coreta.local_work.data import write
from run_local_work_handoff import verify, digest
from score_local_work_v2 import evaluate


def score(prepared, run):
    prepared, run = Path(prepared), Path(run)
    verify(prepared)
    if digest(prepared / 'manifest.json') != digest(run / 'manifest.json'):
        raise ValueError('Run and prepared scoring release differ')
    return evaluate(prepared, run, prepared / 'offline')


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    write(args.output, score(args.prepared, args.run))


if __name__ == '__main__':
    main()
