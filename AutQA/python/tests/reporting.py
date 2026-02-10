import json
from datetime import datetime, timezone
from pathlib import Path

REPORT_DIR = Path(__file__).resolve().parents[1] / 'test-reports'
REPORT_DIR.mkdir(parents=True, exist_ok=True)
_records = []


def _safe_text(resp):
    try:
        return resp.text
    except Exception:
        return str(resp)


def record(name: str, resp):
    """Record a requests.Response or a dict-like result under a test step name."""
    entry = {
        'name': name,
        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }
    try:
        # requests Response
        import requests
        if isinstance(resp, requests.Response):
            entry.update({
                'status_code': resp.status_code,
                'url': getattr(resp, 'url', None),
                'request_body': None,
                'response_text': _safe_text(resp)
            })
            try:
                entry['response_json'] = resp.json()
            except Exception:
                entry['response_json'] = None
            try:
                req = resp.request
                entry['request_body'] = req.body.decode() if isinstance(req.body, (bytes, bytearray)) else req.body
            except Exception:
                entry['request_body'] = None
    except Exception:
        # not a requests.Response; try to write repr
        entry['response_text'] = repr(resp)
    _records.append(entry)


def write_report():
    out_json = REPORT_DIR / 'report.json'
    with out_json.open('w', encoding='utf-8') as f:
        json.dump({'generated': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'), 'records': _records}, f, indent=2, ensure_ascii=False)

    # also write a simple HTML
    out_html = REPORT_DIR / 'report.html'
    with out_html.open('w', encoding='utf-8') as f:
        f.write('<html><head><meta charset="utf-8"><title>Test Report</title></head><body>')
        f.write(f'<h1>Test Report - {datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}</h1>')
        for r in _records:
            f.write('<div style="margin-bottom:1.2em;padding:8px;border:1px solid #ddd;">')
            f.write(f'<h3>{r.get("name")} - {r.get("status_code")}</h3>')
            f.write(f'<div><strong>time:</strong> {r.get("timestamp")}</div>')
            if r.get('url'):
                f.write(f'<div><strong>url:</strong> {r.get("url")}</div>')
            if r.get('request_body'):
                f.write(f'<pre>{json.dumps(r.get("request_body"), ensure_ascii=False) if not isinstance(r.get("request_body"), str) else r.get("request_body")}</pre>')
            if r.get('response_json'):
                f.write('<div><strong>response_json:</strong><pre>')
                f.write(json.dumps(r.get('response_json'), indent=2, ensure_ascii=False))
                f.write('</pre></div>')
            else:
                if r.get('response_text'):
                    f.write('<div><strong>response_text:</strong><pre>')
                    f.write(r.get('response_text'))
                    f.write('</pre></div>')
            f.write('</div>')
        f.write('</body></html>')
