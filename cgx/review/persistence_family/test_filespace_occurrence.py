#!/usr/bin/env python3
"""Session-only browser fallback: per-path occurrence, dedup references, shred/restore, portable manifest.
No stable origin available in this sandbox; IndexedDB persistence across reload remains UNTESTED.
"""
import hashlib,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
checks=[];errors=[];requests=[]
def ok(name,test):
 if not test:raise AssertionError(name)
 checks.append(name)
body=(ROOT/'UniSpace_FileSpace_Handshake.cgx.html').read_text('utf8')
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-gpu'])
 context=browser.new_context(accept_downloads=True)
 page=context.new_page();page.set_default_timeout(9000);page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
 page.set_content(body,wait_until='domcontentloaded');page.wait_for_timeout(350)
 ok('session fallback clearly disclosed',page.get_by_text('Session-only review').count()>0)
 page.locator('#profile').fill('Lab Reviewer');page.locator('#persist').click();page.locator('[data-tab="files"]').first.click()
 raw=b'Same exact source bytes for two paths.\n';expected=hashlib.sha256(raw).hexdigest()
 page.locator('#pickInput').set_input_files([{'name':'first.md','mimeType':'text/markdown','buffer':raw},{'name':'second.md','mimeType':'text/markdown','buffer':raw}])
 page.wait_for_function("document.querySelectorAll('.item').length===2")
 ok('two independent source occurrences',page.locator('.item').count()==2)
 ok('one shared content payload labelled',page.get_by_text('1 unique payloads').count()==1)
 with page.expect_download() as d:page.locator('#snapshot').click()
 manifest=json.loads(Path(d.value.path()).read_text())
 ok('snapshot two objects unique ids',len(manifest['objects'])==2 and len({x['id'] for x in manifest['objects']})==2)
 ok('snapshot SHA exact and shared',all(x['sha256']==expected for x in manifest['objects']))
 ok('snapshot source paths retained',set(x['path'] for x in manifest['objects'])=={'first.md','second.md'})
 ok('snapshot does not pretend to contain bytes',manifest['unique_payload_count']==1 and not manifest['content_bytes_included'])
 ok('snapshot is not minted',not manifest['native_minted'] and not manifest['network_action'])
 page.locator('[data-shred]').first.click();page.locator('[data-tab="shred"]').first.click()
 ok('one occurrence shredded',page.locator('.item.deleted').count()==1)
 page.locator('[data-restore]').first.click();page.locator('[data-tab="files"]').first.click()
 ok('one occurrence restored without affecting twin',page.locator('.item').count()==2)
 page.locator('#pickInput').set_input_files({'name':'first.md','mimeType':'text/markdown','buffer':b'Changed content, same relative path.\n'})
 page.wait_for_function("document.querySelectorAll('.item').length===3")
 ok('changed source preserves old occurrence',page.locator('.item').count()==3)
 page.locator('#pickInput').set_input_files({'name':'first.md','mimeType':'text/markdown','buffer':b'Changed content, same relative path.\n'})
 page.wait_for_timeout(170)
 ok('identical repeated occurrence idempotent',page.locator('.item').count()==3)
 page.locator('[data-select]').first.click();page.wait_for_timeout(60)
 ok('copied source bytes previewed',page.locator('#preview pre').count()==1 and page.get_by_text('Same exact source bytes').count()>0)
 # Imported unsigned manifest references remain metadata-only in a fresh page.
 other=context.new_page();other.set_content(body);other.wait_for_timeout(320)
 other.locator('#manifestInput').set_input_files({'name':'FileSpace.review.cgx','mimeType':'application/json','buffer':json.dumps(manifest).encode()});other.wait_for_timeout(350)
 other.locator('[data-tab="files"]').first.click()
 ok('manifest imports two separate path references',other.locator('.item').count()==2)
 other.locator('[data-select]').first.click();other.wait_for_timeout(90)
 ok('imported metadata does not hallucinate source bytes',other.get_by_text('Source bytes absent; metadata reference only.').count()>0)
 ok('zero JavaScript errors',not errors)
 ok('zero external requests',not requests)
 other.close();context.close();browser.close()
print(json.dumps({'passed':len(checks),'checks':checks,'errors':errors,'external_requests':requests,'actual_indexeddb_reload_test':False,'browser_fallback_only':True,'native_mint':False},indent=2))
