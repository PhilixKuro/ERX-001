"""Read-only renderer probe: in-memory template loader; no hooks/files registered."""
import json
import re
from pathlib import Path

import frappe
from jinja2 import ChoiceLoader, DictLoader
from frappe.website.page_renderers.template_page import TemplatePage

env = frappe.get_jenv()
original_loader = env.loader
result = []
try:
    for app in ('crm', 'raven', 'insights'):
        upstream = f'{app}/www/{app}.html'
        wrapper = 'templates/s6_probe.html'
        marker = '<script src="/assets/frappe_china/js/s6-probe-only.js"></script>'
        source = '{% set original %}{% include "' + upstream + '" %}{% endset %}{{ original|replace("</body>", injection ~ "</body>")|safe }}'
        env.loader = ChoiceLoader([DictLoader({wrapper: source}), original_loader])
        env.cache.clear()
        # Same context.template handoff used by update_website_context.
        page = TemplatePage(app)
        page.context = frappe._dict(template=upstream, boot='{}' if app == 'raven' else {}, csrf_token='probe-token')
        page.source = page.original_source = env.loader.get_source(env, upstream)[0]
        before = page.render_template()
        page.context.template = wrapper
        page.context.injection = marker
        page.post_process_context()
        after = page.render_template()
        assert after.count(marker) == 1, app
        assert after.replace(marker, '').strip() == before.strip(), app
        scripts_before = re.findall(r'<script[^>]+src="([^"]+)"', before)
        scripts_after = re.findall(r'<script[^>]+src="([^"]+)"', after)
        assert scripts_after[:-1] == scripts_before, app
        result.append({'app': app, 'pass': True, 'upstream': upstream, 'original_scripts': scripts_before, 'injection_count': after.count(marker)})
finally:
    env.loader = original_loader
    env.cache.clear()
Path('/workspace/Spike/P1S6R4-template-probe.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=True))
