# Usage: python3 render.py templates/<file>.html <out>.jpg
# Renders a 1080x1080 HTML creative to JPG (needs: npm i in repo root, playwright + chrome)
import sys, os
from playwright.sync_api import sync_playwright
src, out = os.path.abspath(sys.argv[1]), sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width':1080,'height':1080})
    pg.goto('file://'+src); pg.wait_for_timeout(1000)
    pg.screenshot(path=out, type='jpeg', quality=93); b.close()
