import csv, re
rows = list(csv.reader(open('D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv', encoding='utf-8', newline='')))
TW = ['预设', '档案', '程式', '资料库', '软体', '网路', '列印', '伺服器', '登入', '登出', '物件', '帐号', '帐户', '影片', '视窗', '游标', '剪贴簿', '项目符号', '讯息', '资讯', '品质', '使用者', '介面', '数位', '储存', '回应', '新增', '编辑器', '撷取', '连结', '支援', '执行绪', '变数', '函式', '位元', '硬碟', '记忆体', 'digit', '载入', '汇出', '汇入', '设定', '选单', '标签页', '透过', '萤幕', '滑鼠', '列表单', '营运', '公尺', '公斤', '备注栏', '日志档']
with open('tw.txt', 'w', encoding='utf-8') as f:
    for w in TW:
        hits = [r for r in rows if w in r[1]]
        if hits:
            f.write(f'## {w}: {len(hits)}\n')
            for r in hits[:4]: f.write(f'   {r[0][:70]!r} | {r[1][:60]}\n')
