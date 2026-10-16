#!/bin/bash
# E: SL-002 ① on test.localhost only — displace frappe_china, migrate, count alerts; restore, migrate again.
set -u
cd /workspace/frappe-bench
S=test.localhost
count() {
  bench --site $S execute frappe.db.count --kwargs "{'dt':'Error Log','filters':{'method':'frappe_china override self-check failed'}}" 2>/dev/null | tail -1
  bench --site $S execute frappe.db.count --kwargs "{'dt':'Notification Log','filters':{'subject':['like','%self-check%'],'for_user':'Administrator'}}" 2>/dev/null | tail -1
}
echo "== before"; count
bench --site $S execute "exec(\"from frappe.core.doctype.installed_applications.installed_applications import update_installed_apps_order\nimport frappe\no=frappe.get_installed_apps()\no.remove('frappe_china')\no.insert(o.index('crm'),'frappe_china')\nupdate_installed_apps_order(o)\nfrappe.db.commit()\nprint(frappe.get_installed_apps())\")"
bench --site $S clear-cache
echo "== migrate displaced"; bench --site $S migrate > /workspace/frappe-bench/logs/s7-r6-e-sl002-displaced.log 2>&1; echo "migrate exit=$?"
grep -n "self-check" /workspace/frappe-bench/logs/s7-r6-e-sl002-displaced.log | cut -c1-300
echo "== after displaced"; count
bench --site $S execute frappe_china.install.reorder_installed_apps | tail -1
bench --site $S clear-cache
echo "== migrate restored"; bench --site $S migrate > /workspace/frappe-bench/logs/s7-r6-e-sl002-restored.log 2>&1; echo "migrate exit=$?"
grep -n "self-check" /workspace/frappe-bench/logs/s7-r6-e-sl002-restored.log | cut -c1-300
echo "== after restored"; count
bench --site $S execute "exec(\"from frappe_china.install import check_app_order\nr=check_app_order()\nprint(r['ok'], r['order'])\")" | tail -1
