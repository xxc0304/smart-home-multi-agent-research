"""Download the official public PBT archive and inspect data, without extracting or executing it."""
from pathlib import Path
import json
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parent
TARGET = ROOT.parent.parent / 'data' / 'external' / 'pbt-preprocessed-20261029' / 'data.tar.gz'
URL = 'https://media.githubusercontent.com/media/esteng/persuasion_balanced_training/main/data.tar.gz'
EXPECTED_BYTES = 170222819


def main():
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if not TARGET.exists():
        partial = TARGET.with_suffix(TARGET.suffix + '.part')
        request = urllib.request.Request(URL, headers={'User-Agent': 'CoReTA-research-asset-audit/1.0'})
        total = 0
        with urllib.request.urlopen(request, timeout=60) as response, partial.open('wb') as output:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                total += len(block)
                if total > EXPECTED_BYTES + 1024:
                    raise ValueError('Unexpectedly large response; partial download retained')
                output.write(block)
        if total != EXPECTED_BYTES:
            raise ValueError(f'Expected {EXPECTED_BYTES} bytes; received {total}; partial retained')
        partial.replace(TARGET)
    if TARGET.stat().st_size != EXPECTED_BYTES:
        raise ValueError('Existing archive size differs from the official LFS pointer')
    members, samples = [], []
    with tarfile.open(TARGET, mode='r|gz') as archive:
        for member in archive:
            members.append({'name': member.name, 'bytes': member.size, 'is_file': member.isfile()})
            if member.isfile() and member.name.endswith(('.json', '.jsonl', '.csv', '.txt')) and len(samples) < 4:
                handle = archive.extractfile(member)
                if handle is not None:
                    prefix = handle.read(min(member.size, 32768)).decode('utf-8', errors='replace')
                    row = {'name': member.name, 'prefix': prefix, 'prefix_only': member.size > 32768}
                    try:
                        value = json.loads(prefix.splitlines()[0]) if member.name.endswith('.jsonl') else json.loads(prefix)
                        row['parsed_type'] = type(value).__name__
                        if isinstance(value, dict):
                            row['parsed_keys'] = list(value)
                        elif isinstance(value, list) and value and isinstance(value[0], dict):
                            row['first_record_keys'] = list(value[0])
                    except (ValueError, IndexError):
                        row['parse_note'] = 'Prefix is not a complete JSON value'
                    samples.append(row)
            if len(members) >= 2000:
                break
    result = {'source_url': URL, 'local_path': str(TARGET), 'bytes': TARGET.stat().st_size,
              'scope': 'Archive member listing plus bounded text prefixes; no files extracted, no pickle or executable loaded',
              'members_seen': len(members), 'listing_limit': 2000, 'members': members, 'text_samples': samples}
    out = ROOT / 'PBT_ARCHIVE_INSPECTION.json'
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'download_bytes': result['bytes'], 'members_seen': len(members),
                      'first_members': members[:20], 'sample_fields': [{k: v for k, v in s.items() if k != 'prefix'} for s in samples],
                      'inspection': str(out)}, ensure_ascii=True))


if __name__ == '__main__':
    main()
