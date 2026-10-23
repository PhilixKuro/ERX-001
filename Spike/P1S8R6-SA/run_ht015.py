"""Live isolated HT-015 worker/scheduler experiment, no production edits."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from ht015_probe import BENCH, SITE, STATE, QUEUE
import frappe

CONFIG = BENCH / 'sites' / SITE / 'site_config.json'
DBS = ('_ht015_sa_a', '_ht015_sa_b')


def wait_file(name, timeout=30):
    end = time.monotonic() + timeout
    while not (STATE / name).exists():
        assert time.monotonic() < end, ('timeout', name)
        time.sleep(.1)


def init():
    os.chdir(BENCH / 'sites')
    frappe.init(SITE, force=True)
    frappe.connect()
    frappe.set_user('Administrator')


def queue_job(kind, label, gate=False):
    from rq import Queue
    from frappe.utils.background_jobs import get_redis_conn
    q = Queue(QUEUE + kind, connection=get_redis_conn())
    return q.enqueue_call('frappe.utils.background_jobs.execute_job',
        kwargs=dict(site=SITE, method='frappe.ht015_probe.job', event=None, job_name=label,
                    kwargs=dict(label=label, gate=gate), user='Administrator', is_async=True),
        timeout=140, result_ttl=600)


def wait_job(job):
    end = time.monotonic() + 30
    while True:
        status = str(job.get_status(refresh=True))
        if status.endswith('FINISHED') or status == 'finished':
            return job.return_value()
        assert not ('FAILED' in status or status == 'failed'), (job.id, job.exc_info)
        assert time.monotonic() < end, (job.id, status)
        time.sleep(.1)


def switch(db):
    init()
    from frappe.installer import update_site_config
    from frappe.config import clear_site_config_cache
    update_site_config('db_name', db)
    clear_site_config_cache()
    frappe.destroy()


def tick(label):
    (STATE / 'tick').write_text(label)
    wait_file('tick-' + label + '.done')
    # Wait for its native scheduled job's body, if due.
    time.sleep(.8)


def main():
    STATE.mkdir(exist_ok=True)
    assert not list(STATE.iterdir()), 'Use a new empty state directory'
    original = CONFIG.read_bytes()
    procs = []
    handles = []
    try:
        for db, method in zip(DBS, ('frappe.ht015_probe.scheduled_a', 'frappe.ht015_probe.scheduled_b')):
            switch(db); init()
            frappe.db.sql("delete from `tabScheduled Job Type` where method like 'frappe.ht015_probe.%'")
            frappe.db.sql('delete from ht015_audit')
            doc = frappe.get_doc(dict(doctype='Scheduled Job Type', method=method,
                  frequency='Cron', cron_format='* * * * *', stopped=0, create_log=1,
                  last_execution='2020-01-01 00:00:00'))
            doc.insert(ignore_permissions=True)
            frappe.db.commit(); frappe.destroy()
        switch(DBS[0])
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).parent))
        for kind in ('fork', 'nofork', 'scheduler'):
            handle = (BENCH / 'logs' / ('ht015-' + kind + '.log')).open('w')
            handles.append(handle)
            procs.append(subprocess.Popen([str(BENCH/'env/bin/python'),
                         str(Path(__file__).parent/'ht015_probe.py'), kind],
                         stdout=handle, stderr=subprocess.STDOUT, env=env))
            wait_file(kind + '.ready')
        init()
        print(json.dumps({'phase':'baseline', 'fork':wait_job(queue_job('fork','baseline-fork')),
                          'nofork':wait_job(queue_job('nofork','baseline-nofork'))}),flush=True)
        tick('before')
        inflight = queue_job('fork', 'inflight', gate=True)
        wait_file('inflight.started')
        # The pending job is enqueued before switch, but held behind inflight.
        pending = queue_job('fork', 'queued-before-switch')
        t0 = time.monotonic(); switch(DBS[1])
        print(json.dumps({'phase':'switched','t0':time.time()}),flush=True)
        init()
        result = wait_job(queue_job('nofork', 'new-under60'))
        print(json.dumps({'phase':'under60','elapsed':time.monotonic()-t0,'result':result}),flush=True)
        tick('under60')
        (STATE/'release').touch()
        print(json.dumps({'phase':'inflight','result':wait_job(inflight),
                          'queued_before':wait_job(pending)}),flush=True)
        # Let the actual 60s cache lifetime elapse; background processes keep running.
        while time.monotonic()-t0 < 62:
            time.sleep(.2)
        init()
        print(json.dumps({'phase':'after60','elapsed':time.monotonic()-t0,
                          'fork':wait_job(queue_job('fork','new-after60-fork')),
                          'nofork':wait_job(queue_job('nofork','new-after60-nofork'))}),flush=True)
        tick('after60')
        audits = {}
        for db in DBS:
            switch(db); init()
            audits[db] = frappe.db.sql('select * from ht015_audit order by ts',as_dict=True)
            frappe.destroy()
        print(json.dumps({'phase':'audits','rows':audits}),flush=True)
    finally:
        (STATE/'release').touch(); (STATE/'stop').touch()
        for p in procs:
            if p.poll() is None: p.terminate()
        for p in procs:
            try: p.wait(timeout=10)
            except subprocess.TimeoutExpired: p.kill(); p.wait()
        for h in handles: h.close()
        frappe.destroy()
        CONFIG.write_bytes(original)
        print(json.dumps({'phase':'process_cleanup','returncodes':[p.returncode for p in procs],
                          'config_restored':CONFIG.read_bytes()==original}),flush=True)


if __name__ == '__main__':
    main()
