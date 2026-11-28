#!/usr/bin/env python3
"""Review-only static security/accessibility preflight for the immutable PrintSpace private RC.

No browser, public hosting, live assets, credentials, physical process or owner
rights assertions. This is a bounded parser/audit, never a WCAG or security
certification; findings are an input to independent SW-03/SW-04 review.
"""
from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import zipfile

SCHEMA = 'CGX-PRINTSPACE-RC2-STATIC-QA/0.1'
RC2_SHA256 = '2f81a22ac0d00e22086d5e3f0d77f3026a4a971f1bb6a4e0267f704efb4911c2'
RC2_NAME = 'PrintSpace_Software_0.1.0-rc.2_PRIVATE.zip'
LIMIT = 8 * 1024 * 1024
ALLOWED_HTML = 'PrintSpace.Studio.offline.html'

class AuditHold(ValueError):
    pass

class Controls(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.labels_for = set()
        self.label_depth = 0
        self.stack = []
        self.button_text = {}
        self.current_buttons = []
    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if tag == 'label':
            self.label_depth += 1
            if attrs.get('for'): self.labels_for.add(attrs['for'])
        self.elements.append({'tag': tag, 'attrs': attrs,
                              'nested_label': self.label_depth > 0})
        if tag == 'button':
            index = len(self.elements) - 1
            self.current_buttons.append(index)
            self.button_text[index] = ''
        self.stack.append(tag)
    def handle_endtag(self, tag):
        if tag == 'label': self.label_depth = max(0, self.label_depth - 1)
        if tag == 'button' and self.current_buttons: self.current_buttons.pop()
        if tag in self.stack: self.stack.remove(tag)
    def handle_data(self, data):
        for index in self.current_buttons: self.button_text[index] += data

def audit_bytes(data: bytes) -> dict:
    if not isinstance(data, bytes) or len(data) > LIMIT:
        raise AuditHold('ARCHIVE_SIZE_OR_FORMAT')
    digest = hashlib.sha256(data).hexdigest()
    if digest != RC2_SHA256: raise AuditHold('IMMUTABLE_RC2_SHA256_MISMATCH')
    try:
        with zipfile.ZipFile(__import__('io').BytesIO(data)) as z:
            if z.testzip() is not None: raise AuditHold('CRC_ERROR')
            names = z.namelist()
            if len(names) != len(set(names)) or ALLOWED_HTML not in names:
                raise AuditHold('ZIP_DUPLICATE_OR_HTML_MISSING')
            manifest = json.loads(z.read('MANIFEST.json'))
            if manifest.get('version') != '0.1.0-rc.2' or manifest.get('distribution_scope') != 'OWNER_PRIVATE_EVALUATION_ONLY':
                raise AuditHold('NOT_PRIVATE_RC2')
            if manifest.get('software_release_ready_for_public') is not False or any(manifest.get('safety_flags', {}).values()):
                raise AuditHold('AUTHORITY_ESCALATION')
            html = z.read(ALLOWED_HTML).decode('utf-8')
    except (OSError, zipfile.BadZipFile, KeyError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuditHold('ZIP_OR_HTML_PARSING_FAILED') from exc
    parser = Controls(); parser.feed(html); parser.close()
    els = parser.elements
    tags = lambda x: [e for e in els if e['tag'] == x]
    root = tags('html')
    viewport = [x for x in tags('meta') if x['attrs'].get('name') == 'viewport']
    controls = [e for e in els if e['tag'] in ('select', 'input', 'textarea')]
    missing_names = [e['attrs'].get('id', '(missing id)') for e in controls
                     if not (e['attrs'].get('aria-label') or
                             e['attrs'].get('aria-labelledby') or
                             e['nested_label'] or
                             e['attrs'].get('id') in parser.labels_for)]
    buttons = tags('button')
    button_unlabelled = [i for i,b in enumerate(buttons) if not
                         (b['attrs'].get('aria-label') or b['attrs'].get('aria-labelledby') or
                          re.sub(r'\s+', ' ', parser.button_text.get(els.index(b), '')).strip())]
    canvas = tags('canvas')
    remote_apis = [p for p in (r'\bfetch\s*\(', r'\bXMLHttpRequest\b', r'\bWebSocket\b',
                             r'\bsendBeacon\s*\(', r'<script[^>]+\bsrc\s*=',
                             r'<iframe\b', r'\bEventSource\s*\(')
                   if re.search(p, html, flags=re.I)]
    dynamic_html = re.findall(r'\.innerHTML\s*=\s*([^;\n]+)', html)
    # Any non-empty or computed HTML sink is a hold, even if syntactically quoted.
    unsafe_html_sinks = [x[:80] for x in dynamic_html if x.strip() not in ("''", '""')]
    hard_holds = []
    if not root or root[0]['attrs'].get('lang') != 'en': hard_holds.append('HTML_DOCUMENT_LANGUAGE')
    if not viewport or not re.search(r'width=device-width',viewport[0]['attrs'].get('content','')):
        hard_holds.append('MOBILE_VIEWPORT')
    if missing_names: hard_holds.append('UNLABELLED_FORM_CONTROLS')
    if button_unlabelled: hard_holds.append('UNLABELLED_BUTTONS')
    if not canvas or not canvas[0]['attrs'].get('aria-label'): hard_holds.append('CANVAS_ALTERNATIVE_NAME')
    if remote_apis or unsafe_html_sinks: hard_holds.append('OFFLINE_OR_HTML_SINK_SECURITY')
    if ':focus-visible' not in html: hard_holds.append('VISIBLE_KEYBOARD_FOCUS')
    if '@media' not in html: hard_holds.append('RESPONSIVE_CSS')
    review_findings = []
    if re.search(r'row\.tabIndex\s*=\s*0',html) and 'row.setAttribute(\'role\',' not in html:
        review_findings.append('CUSTOM_PART_TREE_MISSING_SEMANTIC_ROLE')
    if "e.key==='Enter'" in html and "e.key===' '" not in html:
        review_findings.append('CUSTOM_PART_TREE_SPACE_KEY_ACTIVATION')
    if 'aria-live' not in html and 'role="status"' not in html:
        review_findings.append('DYNAMIC_STAGE_STATUS_ANNOUNCEMENT')
    if 'setInterval(' in html and 'prefers-reduced-motion' not in html:
        review_findings.append('ANIMATION_REDUCED_MOTION')
    if 'pointerdown' in html and not re.search(r'canvas\.addEventListener\(\s*[\'\"]keydown',html):
        review_findings.append('CANVAS_POINTER_ONLY_ORBIT_NEEDS_EQUIVALENCE_REVIEW')
    return {'schema': SCHEMA, 'state': 'HOLD_STATIC_SECURITY_OR_A11Y' if hard_holds else 'PASS_STATIC_PRELIMINARY_REVIEW_ONLY',
            'rc_version': '0.1.0-rc.2', 'rc_zip_sha256': digest,
            'html_sha256': hashlib.sha256(html.encode()).hexdigest(),
            'control_count': len(controls), 'button_count': len(buttons),
            'hard_hold_codes': sorted(hard_holds), 'independent_review_findings': sorted(review_findings),
            'static_security_review_complete': False, 'wcag_conformance_verified': False,
            'interactive_browser_uat_verified': False, 'owner_accepted': False,
            'public_distribution_authorised': False, 'native_admitted': False,
            'machine_authorised': False, 'next_owner_gates': ['SW-03','SW-04']}

def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out');args=p.parse_args()
    report=audit_bytes(Path(args.archive).read_bytes())
    payload=json.dumps(report,indent=2,sort_keys=True)+'\n'
    if args.out:Path(args.out).write_text(payload,encoding='utf-8')
    print(payload,end='')
    if report['hard_hold_codes']:
        return 2
    return 0
if __name__=='__main__':raise SystemExit(main())
