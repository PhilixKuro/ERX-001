"""R9 TS-036 第 5 步：由 Spike/P1S6R6-screens.json 生成 Spike/P1S6R9-screens.json（旧文件不改）。
用法（宿主）：PYTHONUTF8=1 python Spike/P1S6R9/screens-build.py
改动（SL-022 ①）：
  - 新增 4 屏：「选工时单」对话框、Raven 个人资料状态下拉、BOM 与 WO 普通取消确认框；
  - 原 confirm-cancel-bom／confirm-cancel-work-order 两屏保留，标 kind_expected: "cancel_all"；新增两屏标 "confirm"；
  - variables 加 bom_cancel、wo_cancel（造数脚本 cancel-opens 一步写入状态文件）；
  - 称呼下拉不进（演示站 tabSalutation 0 条）；采购发票「公司间销售发票」不进（演示站无内部供应商），两者只在测试站截（TS-035 第 8、2 屏）。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
src = json.loads((ROOT / 'Spike/P1S6R6-screens.json').read_text(encoding='utf-8'))
spec = dict(src)
spec['note'] = ('R9 TS-036 由 Spike/P1S6R9/screens-build.py 从 P1S6R6-screens.json 生成；'
                '占位值由 values.json（Spike/P1S6R9-closed-loop-erx.json）提供')
spec['variables'] = dict(src['variables'])
for key in ('bom_cancel', 'wo_cancel'):
    spec['variables'][key] = {'from': 'Spike/P1S6R9-closed-loop-<site>.json 同名键（cancel-opens 一步写入；作 values.json 传入）'}

FORM = lambda dt: f'window.cur_frm?.doctype==="{dt}" && !!cur_frm.fields_dict && !frappe.dom.freeze_count'

new_screens = {
    # SL-020 ①：销售发票草稿 → 取物料来源 → 工时单，对话框两个日期标签
    '22-sales-invoice-timesheet-dialog': {
        'id': '22-sales-invoice-timesheet-dialog', 'stage': '环节22', 'state': 'dialog',
        'route': 'desk/sales-invoice/{{si_draft}}', 'wait_for': FORM('Sales Invoice'), 'sidebar': 'Business Flow',
        'steps': [{'menu': ['取物料来源', 'Get Items From'], 'item': ['工时单', 'Timesheet'],
                   'wait_for': "!!document.querySelector('.modal.show [data-fieldname=\"from_time\"]')"}],
        'extract_root': '.modal.show', 'after': [{'dialog_close': True}],
        'added_r9': 'R8 IT-041：「选工时单」对话框的 From／To 标签（TS-031）',
    },
    # SL-020 ②：Raven 头像菜单 → 设置 → 个人资料状态下拉（桌面版无 /raven/profile 路由，NavUserMenu.tsx:104）
    'raven-profile-status': {
        'id': 'raven-profile-status', 'stage': 'Raven', 'state': 'dialog', 'url': '/raven',
        'wait_for': "!!document.body.innerText.trim() && !document.querySelector('.animate-spin, .loading-indicator')"
                    " && !!document.querySelector('[data-sidebar] button, aside button, nav button')",
        'timeout': 60000,
        'steps': [
            {'evaluate': "(() => { const vis = b => { const r = b.getBoundingClientRect(); return r.width > 0 && r.left < 80; };"
                         " const hit = [...document.querySelectorAll('button')].filter(b => b.querySelector('img, [class*=\"avatar\" i], span[class*=\"rounded\"]'))"
                         ".filter(vis).sort((a, b) => b.getBoundingClientRect().top - a.getBoundingClientRect().top)[0];"
                         " if (!hit) throw Error('Raven avatar button not found'); hit.setAttribute('data-ts036', 'avatar'); return true; })()"},
            {'click': 'button[data-ts036="avatar"]', 'real': True, 'wait_for': "!!document.querySelector('[role=\"menuitem\"]')", 'timeout': 10000},
            {'click': '[role="menuitem"]', 'text': ['设置', 'Settings'], 'real': True,
             'wait_for': "!!document.querySelector('[role=\"dialog\"] button[role=\"combobox\"]')", 'timeout': 20000, 'pause': 1500},
            {'click': '[role="dialog"] button[role="combobox"]', 'real': True,
             'wait_for': "!!document.querySelector('[role=\"option\"]')", 'timeout': 10000, 'pause': 800},
        ],
        # Radix 对话框不是 .modal.show，下拉选项又挂在对话框外的 portal 里，故取整页；
        # 下拉打开时 Radix 给其余节点加 aria-hidden，取词时被排除，取到的主要是状态下拉选项（本屏要核的就是它）
        'extract_root': 'body',
        'after': [{'key': 'Escape'}, {'key': 'Escape'}],
        'added_r9': 'R8 IT-048：Raven 个人状态 Available 显示「有空」（TS-032，HT-025）',
    },
    # SL-022 ③（HT-026）：无已提交下游的 BOM、WO，取消走 frappe.confirm 普通确认框
    'confirm-cancel-bom-plain': {
        'id': 'confirm-cancel-bom-plain', 'stage': '确认框', 'state': 'dialog',
        'route': 'desk/bom/{{bom_cancel}}', 'sidebar': 'Business Flow', 'kind_expected': 'confirm',
        'dialog': {'action': 'cancel', 'doctype': 'BOM', 'name': '{{bom_cancel}}'},
        'added_r9': 'R8 发现 confirm-cancel-bom 截到的是「取消所有单据」框；补截普通取消框（HT-026）',
    },
    'confirm-cancel-work-order-plain': {
        'id': 'confirm-cancel-work-order-plain', 'stage': '确认框', 'state': 'dialog',
        'route': 'desk/work-order/{{wo_cancel}}', 'sidebar': 'Business Flow', 'kind_expected': 'confirm',
        'dialog': {'action': 'cancel', 'doctype': 'Work Order', 'name': '{{wo_cancel}}'},
        'added_r9': '同上，工单（HT-026）',
    },
}

screens = []
for screen in src['screens']:
    screen = dict(screen)
    if screen['id'] in ('confirm-cancel-bom', 'confirm-cancel-work-order'):
        screen['kind_expected'] = 'cancel_all'
    screens.append(screen)
    # 新增屏放在同环节旁边，便于对照截图
    if screen['id'] == '22-sales-invoice-list':
        screens.append(new_screens['22-sales-invoice-timesheet-dialog'])
    elif screen['id'] == 'raven':
        screens.append(new_screens['raven-profile-status'])
    elif screen['id'] == 'confirm-cancel-bom':
        screens.append(new_screens['confirm-cancel-bom-plain'])
    elif screen['id'] == 'confirm-cancel-work-order':
        screens.append(new_screens['confirm-cancel-work-order-plain'])
spec['screens'] = screens
ids = [s['id'] for s in screens]
assert len(ids) == len(set(ids)) == len(src['screens']) + 4, len(ids)
(ROOT / 'Spike/P1S6R9-screens.json').write_text(json.dumps(spec, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'{len(src["screens"])} -> {len(screens)} screens; added: {list(new_screens)}')
