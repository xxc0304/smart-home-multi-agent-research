"""Fetch official public archive; read only Ans train/dev and the published leakage blacklist."""
from pathlib import Path
import hashlib
import json
import time
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
DATA = HERE.parent.parent / 'data/external/musique-v1.0-20261030'
ARCHIVE = DATA / 'upstream/musique_v1.0.zip'
URL = 'https://drive.usercontent.google.com/download?id=1tGdADlNjWFaHLeZZGShh2IRcpO6Lv24h&export=download&confirm=t'
ALLOWED = {'musique_ans_v1.0_train.jsonl', 'musique_ans_v1.0_dev.jsonl', 'dev_test_singlehop_questions_v1.0.json'}


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as handle:
        while data := handle.read(4 * 1024 * 1024):
            result.update(data)
    return result.hexdigest()


def main():
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE.exists():
        partial = ARCHIVE.with_suffix('.zip.part')
        count, last = 0, 0
        request = urllib.request.Request(URL, headers={'User-Agent': 'CoReTA-public-data-audit/1.0'})
        with urllib.request.urlopen(request, timeout=60) as response, partial.open('wb') as out:
            while block := response.read(1024 * 1024):
                if count == 0 and block[:2] != b'PK':
                    raise ValueError('Official download did not return ZIP data')
                count += len(block)
                if count > 1024 * 1024 * 1024:
                    raise ValueError('Archive exceeded 1 GiB bound; partial retained')
                out.write(block)
                if count - last >= 16 * 1024 * 1024:
                    print(json.dumps({'downloaded_bytes': count}), flush=True)
                    last = count
        if not zipfile.is_zipfile(partial):
            raise ValueError('Download is not a complete valid ZIP')
        partial.replace(ARCHIVE)
    metadata = {'date': '2026-10-30', 'source_url': URL,
                'source_index': 'https://github.com/StonyBrookNLP/musique/blob/main/download_data.sh',
                'archive_bytes': ARCHIVE.stat().st_size, 'archive_sha256': sha(ARCHIVE),
                'scope': 'Only Ans train/dev and author-published single-hop leakage blacklist opened; no test or Full records read',
                'archive_members': [], 'extracted': []}
    with zipfile.ZipFile(ARCHIVE) as archive:
        for member in archive.infolist():
            metadata['archive_members'].append({'name': member.filename, 'bytes': member.file_size})
            basename = Path(member.filename).name
            if basename not in ALLOWED or member.is_dir() or '__MACOSX' in member.filename:
                continue
            target = DATA / basename
            if member.file_size > 2 * 1024 * 1024 * 1024:
                raise ValueError('Uncompressed file exceeds 2 GiB bound')
            with archive.open(member) as source, target.open('wb') as out:
                while block := source.read(4 * 1024 * 1024):
                    out.write(block)
            metadata['extracted'].append({'file': basename, 'bytes': target.stat().st_size, 'sha256': sha(target)})
    if {x['file'] for x in metadata['extracted']} != ALLOWED:
        raise ValueError('Official archive did not contain all expected allowed files')
    (DATA / 'PROVENANCE.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    (HERE / 'SOURCE_MANIFEST.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in metadata.items() if k != 'archive_members'}, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
