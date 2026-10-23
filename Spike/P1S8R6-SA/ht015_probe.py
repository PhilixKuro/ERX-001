"""HT-015 RQ/scheduler instrumentation. Importable only via probe PYTHONPATH."""
import json
import os
import time
import sys
from pathlib import Path

import frappe
sys.modules["frappe.ht015_probe"] = sys.modules[__name__]
frappe.ht015_probe = sys.modules[__name__]

BENCH = Path('/workspace/frappe-bench')
SITE = 's8ht015.localhost'
STATE = BENCH / 'logs/ht015-state'
QUEUE = 'ht015-sa-'


def observe(label):
    db = frappe.db.sql('select database()')[0][0]
    assert frappe.local.site == SITE and db in ('_ht015_sa_a', '_ht015_sa_b')
    marker = frappe.db.sql(
        "select value from tabSingles where doctype='HT015 Probe' and field='marker'"
    )[0][0]
    row = dict(label=label, db=db, marker=marker, pid=os.getpid(), ts=time.time())
    frappe.db.sql('insert into ht015_audit values (%s,%s,%s,%s)',
                  (label, marker, row['pid'], row['ts']))
    frappe.db.commit()
    with (STATE / 'observations.jsonl').open('a') as f:
        f.write(json.dumps(row) + '\n')
    return row


def job(label, gate=False):
    first = observe(label + '-start')
    if gate:
        (STATE / 'inflight.started').write_text(json.dumps(first))
        until = time.monotonic() + 100
        while not (STATE / 'release').exists():
            if time.monotonic() > until:
                raise TimeoutError('Probe gate exceeded 100s')
            time.sleep(.1)
    return observe(label + '-end')


def scheduled_a():
    return observe('scheduler-a-body')


def scheduled_b():
    return observe('scheduler-b-body')


def initialize():
    os.chdir(BENCH / 'sites')
    STATE.mkdir(exist_ok=True)
    frappe.init(SITE, is_request=True)  # prime the real 60s request cache as a stress condition
    frappe.connect()
    assert frappe.conf.db_name in ('_ht015_sa_a', '_ht015_sa_b')
    frappe.destroy()


def run_worker(kind):
    initialize()
    from rq import Queue, Worker
    from frappe.utils.background_jobs import FrappeWorkerNoFork, get_redis_conn
    conn = get_redis_conn()
    cls = Worker if kind == 'fork' else FrappeWorkerNoFork
    worker = cls([Queue(QUEUE + kind, connection=conn)], connection=conn,
                 name=QUEUE + kind)
    if kind != 'fork':
        # Scheduler is exercised separately, scoped strictly to this probe site.
        worker.start_frappe_scheduler = lambda: None
    (STATE / (kind + '.ready')).touch()
    worker.work(with_scheduler=False, logging_level='WARNING')


def run_scheduler():
    initialize()
    import frappe.utils.background_jobs as bg
    from frappe.utils.scheduler import enqueue_events_for_site
    from rq import Queue
    # Redirect only queue transport; native site initialization, activity/due checks,
    # job selection, ScheduledJobType.enqueue and execute_job remain intact.
    bg.get_queue = lambda *a, **kw: Queue(QUEUE + 'nofork', connection=bg.get_redis_conn())
    real_connect = frappe.connect
    def traced_connect(*args, **kwargs):
        result = real_connect(*args, **kwargs)
        frappe.conf.pause_scheduler = 0
        observe('scheduler-tick-' + tick)
        return result
    frappe.connect = traced_connect
    last = ''
    (STATE / 'scheduler.ready').touch()
    while not (STATE / 'stop').exists():
        command = STATE / 'tick'
        tick = command.read_text() if command.exists() else ''
        if tick and tick != last:
            last = tick
            enqueue_events_for_site(SITE)
            (STATE / ('tick-' + tick + '.done')).touch()
        time.sleep(.05)


if __name__ == '__main__':
    import sys
    if sys.argv[1] == 'scheduler':
        run_scheduler()
    else:
        run_worker(sys.argv[1])
