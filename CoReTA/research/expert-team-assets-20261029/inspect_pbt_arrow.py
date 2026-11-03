"""Inspect official preprocessed Arrow tables offline; no model calls or extraction."""
from pathlib import Path
import argparse
import json
import sys
import tarfile

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent.parent / 'data/external/pbt-preprocessed-20261029/data.tar.gz'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--module-dir', help='Optional local directory containing pyarrow')
    args = parser.parse_args()
    if args.module_dir:
        sys.path.insert(0, args.module_dir)
    import pyarrow as pa
    import pyarrow.ipc as ipc

    datasets, tables = [], {}
    with tarfile.open(ARCHIVE, mode='r|gz') as archive:
        for member in archive:
            if not member.isfile() or not member.name.endswith('/data-00000-of-00001.arrow'):
                continue
            handle = archive.extractfile(member)
            if handle is None:
                continue
            table = ipc.open_stream(pa.BufferReader(handle.read())).read_all()
            tables[member.name.split('/')[-2]] = table
            row = {'member': member.name, 'rows': table.num_rows, 'columns': table.column_names}
            if any(split in member.name for split in ('_test/', '_valid/')) and 'gold_answers' in table.column_names:
                row['first_two_records'] = table.slice(0, 2).to_pylist()
            if 'type' in table.column_names:
                from collections import Counter
                row['type_counts'] = dict(Counter(table['type'].to_pylist()))
            datasets.append(row)
    pairs = []
    for split in ('train', 'valid', 'test'):
        a, b = tables['mistral_' + split], tables['llama_' + split]
        keys = [key for key in ('code', 'pref_score', 'dispref_score', 'parent_answers', 'pref_answers', 'dispref_answers', 'gold_answers', 'type')
                if key in a.column_names and key in b.column_names]
        pairs.append({'split': split, 'comparison_fields': keys, 'same_order_metadata_equal': all(a[key].to_pylist() == b[key].to_pylist() for key in keys),
                      'scope': 'Metadata equality only; question/prompt/continuation text not normalized'})
    result = {'scope': 'Official preprocessed PBT Arrow values read offline; no model loaded or executed',
              'archive': str(ARCHIVE), 'pyarrow_version': pa.__version__, 'datasets': datasets, 'template_comparisons': pairs}
    (HERE / 'PBT_ARROW_FIELDS.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps([{k: v for k, v in d.items() if k != 'first_two_records'} for d in datasets], ensure_ascii=True))


if __name__ == '__main__':
    main()
