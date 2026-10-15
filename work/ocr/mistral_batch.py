"""Mistral OCR over every Verizon PDF, via the Batch API (/v1/ocr, 50% cheaper than sync).

Output: work/.ocrcache/<md5>.json (raw OCR response) and <md5>.md (pages joined, page breaks as \\f), keyed by the
same md5 as analysis/billing_index.csv and work/.txtcache, so OCR text and pdftotext text can be compared per document.

    python3 -I work/ocr/mistral_batch.py probe  <pdf>            # one sync call: validates key + request shape
    python3 -I work/ocr/mistral_batch.py submit <pdf_dir> [--per-file 100]
    python3 -I work/ocr/mistral_batch.py status                  # poll jobs in work/ocr/jobs.json
    python3 -I work/ocr/mistral_batch.py fetch                   # download finished outputs into .ocrcache

Needs MISTRAL_API_KEY in the environment. Stdlib only. NTT documents are skipped (path contains 'NTT').
"""
import base64, hashlib, json, os, sys, time, uuid, urllib.request, urllib.error

API = 'https://api.mistral.ai/v1'
MODEL = 'mistral-ocr-latest'
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
CACHE = os.path.join(ROOT, 'work', '.ocrcache')
JOBS = os.path.join(ROOT, 'work', 'ocr', 'jobs.json')
STAGE = os.path.join(ROOT, 'work', 'ocr', 'batches')


def key():
    k = os.environ.get('MISTRAL_API_KEY')
    if not k:
        sys.exit('MISTRAL_API_KEY is not set in this session (add it as an environment secret, then start a new session)')
    return k


def call(method, path, body=None, raw=None, ctype='application/json', timeout=600):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={'Authorization': f'Bearer {key()}', 'Content-Type': ctype, 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b = r.read()
            return json.loads(b) if r.headers.get_content_type() == 'application/json' else b
    except urllib.error.HTTPError as e:
        sys.exit(f'{method} {path} -> HTTP {e.code}: {e.read()[:800].decode(errors="replace")}')


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def body_for(pdf):
    b64 = base64.b64encode(open(pdf, 'rb').read()).decode()
    return {'model': MODEL, 'document': {'type': 'document_url', 'document_url': f'data:application/pdf;base64,{b64}'},
            'table_format': 'html', 'extract_header': True, 'extract_footer': True}


def save(h, resp):
    os.makedirs(CACHE, exist_ok=True)
    json.dump(resp, open(os.path.join(CACHE, f'{h}.json'), 'w'))
    pages = sorted(resp.get('pages', []), key=lambda p: p.get('index', 0))
    open(os.path.join(CACHE, f'{h}.md'), 'w').write('\f'.join(p.get('markdown', '') for p in pages))
    return len(pages)


def pdfs(d):
    seen = {}
    for dp, _, fs in os.walk(d):
        for fn in sorted(fs):
            p = os.path.join(dp, fn)
            if fn.lower().endswith('.pdf') and 'ntt' not in p.lower():
                seen.setdefault(md5(p), p)            # Drive dump has duplicate copies; OCR each document once
    return seen


def probe(pdf):
    resp = call('POST', '/ocr', body_for(pdf))
    h = md5(pdf); n = save(h, resp)
    print(f'OK {n} pages, md5 {h}, usage {resp.get("usage_info")}')
    print(open(os.path.join(CACHE, f'{h}.md')).read()[:800])


def submit(d, per_file=100):
    docs = {h: p for h, p in pdfs(d).items() if not os.path.exists(os.path.join(CACHE, f'{h}.json'))}
    print(f'{len(docs)} PDFs to OCR')
    os.makedirs(STAGE, exist_ok=True)
    jobs = json.load(open(JOBS)) if os.path.exists(JOBS) else []
    items = sorted(docs.items())
    for i in range(0, len(items), per_file):
        chunk = items[i:i + per_file]
        fn = os.path.join(STAGE, f'batch_{len(jobs):03d}.jsonl')
        with open(fn, 'w') as f:
            for h, p in chunk:
                b = body_for(p); b.pop('model')
                f.write(json.dumps({'custom_id': h, 'body': b}) + '\n')
        boundary = uuid.uuid4().hex
        payload = (f'--{boundary}\r\nContent-Disposition: form-data; name="purpose"\r\n\r\nbatch\r\n'
                   f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{os.path.basename(fn)}"\r\n'
                   f'Content-Type: application/jsonl\r\n\r\n').encode() + open(fn, 'rb').read() + f'\r\n--{boundary}--\r\n'.encode()
        up = call('POST', '/files', raw=payload, ctype=f'multipart/form-data; boundary={boundary}', timeout=1800)
        job = call('POST', '/batch/jobs', {'input_files': [up['id']], 'endpoint': '/v1/ocr', 'model': MODEL,
                                           'metadata': {'project': 'ez-verizon-tem', 'chunk': str(len(jobs))}})
        jobs.append(dict(job_id=job['id'], input_file=up['id'], docs={h: os.path.relpath(p, ROOT) for h, p in chunk}))
        json.dump(jobs, open(JOBS, 'w'), indent=1)
        print(f'job {job["id"]}: {len(chunk)} docs, status {job.get("status")}')


def status():
    for j in json.load(open(JOBS)):
        s = call('GET', f'/batch/jobs/{j["job_id"]}')
        print(j['job_id'], s['status'], f'{s.get("succeeded_requests")}/{s.get("total_requests")} ok, {s.get("failed_requests")} failed')


def fetch():
    jobs = json.load(open(JOBS)); done = failed = 0
    for j in jobs:
        s = call('GET', f'/batch/jobs/{j["job_id"]}')
        if s['status'] != 'SUCCESS' and not s.get('output_file'):
            print(j['job_id'], s['status'], '(not ready)'); continue
        if s.get('output_file'):
            for line in call('GET', f'/files/{s["output_file"]}/content', timeout=1800).decode().splitlines():
                r = json.loads(line)
                resp = (r.get('response') or {}).get('body')
                if resp and resp.get('pages') is not None:
                    save(r['custom_id'], resp); done += 1
                else:
                    failed += 1; print('FAILED', r['custom_id'], j['docs'].get(r['custom_id']), str(r.get('error'))[:200])
        if s.get('error_file'):
            for line in call('GET', f'/files/{s["error_file"]}/content').decode().splitlines():
                r = json.loads(line); failed += 1
                print('ERROR', r.get('custom_id'), j['docs'].get(r.get('custom_id')), str(r.get('error') or r)[:200])
    print(f'saved {done} documents to {CACHE}; {failed} failed')


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == 'probe':
        probe(a[1])
    elif a[0] == 'submit':
        submit(a[1], int(a[a.index('--per-file') + 1]) if '--per-file' in a else 100)
    elif a[0] == 'status':
        status()
    elif a[0] == 'fetch':
        fetch()
    else:
        sys.exit(__doc__)
