"""HT-015 independent target-prefix cache experiment on disposable clone only."""
import json
import os
import subprocess
import sys
from pathlib import Path

import frappe

BENCH=Path('/workspace/frappe-bench')
SITE='s8ht015.localhost'
CONFIG=BENCH/'sites'/SITE/'site_config.json'


def init():
    os.chdir(BENCH/'sites')
    frappe.init(SITE,force=True)
    frappe.connect()
    assert frappe.conf.db_name in ('_ht015_sa_a','_ht015_sa_b')


def switch(db):
    init()
    from frappe.installer import update_site_config
    from frappe.config import clear_site_config_cache
    update_site_config('db_name',db)
    clear_site_config_cache()
    frappe.destroy()


def read():
    init()
    return dict(db=frappe.db.sql('select database()')[0][0],
        raw=frappe.db.sql("select value from tabSingles where doctype='System Settings' and field='float_precision'")[0][0],
        cached=frappe.get_cached_doc('System Settings').float_precision, pid=os.getpid())


def fresh():
    result=subprocess.run([sys.executable,__file__,'read'],capture_output=True,text=True,check=True)
    return json.loads(result.stdout)


def main():
    original=CONFIG.read_bytes()
    try:
        switch('_ht015_sa_b'); init()
        frappe.db.sql("delete from tabSingles where doctype='System Settings' and field='float_precision'")
        frappe.db.sql("insert into tabSingles (doctype,field,value) values ('System Settings','float_precision','4')")
        frappe.db.commit()
        keys=frappe.cache.keys(b'_ht015_sa_b|*')
        if keys: frappe.cache.delete(*keys)
        frappe.destroy()
        before=fresh()
        init()
        # Raw database replacement simulates DROP/reclone: cache is intentionally untouched.
        frappe.db.sql("update tabSingles set value='7' where doctype='System Settings' and field='float_precision'")
        frappe.db.commit(); frappe.destroy()
        switch('_ht015_sa_a'); switch('_ht015_sa_b')
        stale=fresh()
        init()
        keys=frappe.cache.keys(b'_ht015_sa_b|*')
        count=len(keys)
        assert b'_ht015_sa_b|document_cache::System Settings::System Settings' in keys
        frappe.cache.delete(*keys)
        remaining=len(frappe.cache.keys(b'_ht015_sa_b|*'))
        frappe.destroy()
        cleared=fresh()
        assert str(before['cached'])=='4' and stale['raw']=='7' and str(stale['cached'])=='4'
        assert cleared['raw']=='7' and str(cleared['cached'])=='7' and remaining==0
        print(json.dumps(dict(warm=before,without_deletion=stale,deleted_count=count,
                              remaining_immediate=remaining,with_deletion=cleared)))
    finally:
        frappe.destroy(); CONFIG.write_bytes(original)


if __name__=='__main__':
    if len(sys.argv)>1: print(json.dumps(read()))
    else: main()
