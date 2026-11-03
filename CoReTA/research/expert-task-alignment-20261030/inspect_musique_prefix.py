"""Read bounded prefixes of two official author-hosted raw data files; no model calls."""
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent
TARGET = HERE.parent.parent / 'data/external/musique-inspection-20261030'
SOURCES = {
    'train': '1X3rJEAofrJ_tI55U2bquCZ-StVeaWnWu',
    'dev': '1TRXU68wveSehVbQrRRtWsUsFkKUF43QS',
}
LIMIT = 2 * 1024 * 1024


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    rows = []
    for split, drive_id in SOURCES.items():
        url = 'https://drive.usercontent.google.com/download?id=' + drive_id + '&export=download&confirm=t'
        output = TARGET / (split + '_raw_prefix.jsonl')
        record = {'split': split, 'url': url, 'official_index': 'https://github.com/StonyBrookNLP/musique/blob/main/.all_data_information.json',
                  'scope': 'At most 30 complete records from a bounded raw-file prefix; not a random sample or frozen split'}
        try:
            if output.exists():
                values = [json.loads(line) for line in output.read_text(encoding='utf-8').splitlines()]
                record['read_mode'] = 'existing-local-prefix'
            else:
                request = urllib.request.Request(url, headers={'User-Agent': 'CoReTA-offline-task-inspection/1.0'})
                with urllib.request.urlopen(request, timeout=40) as response:
                    prefix = response.read(LIMIT)
                    record['response_content_type'] = response.headers.get('Content-Type')
                text = prefix.decode('utf-8', errors='ignore')
                if text.lstrip().startswith('<'):
                    raise ValueError('Received HTML instead of raw JSONL data')
                values = []
                for line in text.splitlines():
                    try:
                        value = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(value, dict):
                        values.append(value)
                    if len(values) == 30:
                        break
                if not values:
                    raise ValueError('No complete JSON records in bounded response')
                output.write_text(''.join(json.dumps(v, ensure_ascii=False) + '\n' for v in values), encoding='utf-8')
                record['read_mode'] = 'bounded-public-download'
            record.update({'status': 'read', 'records': len(values), 'file': str(output),
                           'first_record_keys': list(values[0]), 'first_record': values[0]})
        except Exception as exc:
            record.update({'status': 'unavailable_in_this_attempt', 'error': type(exc).__name__ + ': ' + str(exc)})
        rows.append(record)
    (HERE / 'MUSIQUE_PREFIX_INSPECTION.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps([{k: v for k, v in r.items() if k != 'first_record'} for r in rows], ensure_ascii=True))


if __name__ == '__main__':
    main()
