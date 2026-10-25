#!/usr/bin/env python3
"""Publish the existing Uptime Kuma page. Run only while Kuma is stopped."""
from pathlib import Path
import sqlite3
import subprocess

if subprocess.check_output(['docker', 'inspect', '-f', '{{.State.Running}}', 'pharma_uptime'], text=True).strip() != 'false':
    raise RuntimeError('Stop pharma_uptime before updating its SQLite configuration')

path = Path('/opt/pharma/uptime-kuma-data/kuma.db')
db = sqlite3.connect(path)
with db:
    page = db.execute("SELECT id FROM status_page WHERE slug='main'").fetchone()
    if page is None:
        cursor = db.execute(
            "INSERT INTO status_page (slug,title,icon,theme) VALUES ('main',?,'/icon.svg','auto')",
            ('Lifeline Healthcare Status',),
        )
        page_id = cursor.lastrowid
    else:
        page_id = page[0]
    db.execute(
        'UPDATE status_page SET title=?,description=?,published=1,password=NULL,modified_date=CURRENT_TIMESTAMP WHERE id=?',
        ('Lifeline Healthcare Status',
         'Current service availability. Monitoring was repaired on 26 October 2026; earlier history includes monitoring configuration failures.',
         page_id),
    )
    mapping = db.execute('SELECT id FROM status_page_cname WHERE domain=?', ('status.lifelinehealthcare.in',)).fetchone()
    if mapping:
        db.execute('UPDATE status_page_cname SET status_page_id=? WHERE id=?', (page_id, mapping[0]))
    else:
        db.execute('INSERT INTO status_page_cname (status_page_id,domain) VALUES (?,?)', (page_id, 'status.lifelinehealthcare.in'))
    group = db.execute('SELECT id FROM "group" WHERE status_page_id=? AND public=1', (page_id,)).fetchone()
    if group:
        group_id = group[0]
    else:
        group_id = db.execute('INSERT INTO "group" (name,public,active,status_page_id) VALUES (?,1,1,?)', ('Services', page_id)).lastrowid
    db.execute("UPDATE monitor SET name='Website',url='https://lifelinehealthcare.in/',type='keyword',keyword='Your Health',invert_keyword=0,timeout=12,maxretries=2,ignore_tls=0 WHERE id=1")
    db.execute("UPDATE monitor SET name='Application Health',url='https://lifelinehealthcare.in/health/',type='http',timeout=12,maxretries=2,ignore_tls=0 WHERE id=5")
    for monitor_id in (1, 5):
        if not db.execute('SELECT id FROM monitor WHERE id=?', (monitor_id,)).fetchone():
            raise RuntimeError('Expected production monitor is missing')
        if not db.execute('SELECT id FROM monitor_group WHERE monitor_id=? AND group_id=?', (monitor_id, group_id)).fetchone():
            db.execute('INSERT INTO monitor_group (monitor_id,group_id,weight,send_url) VALUES (?,?,?,0)', (monitor_id, group_id, monitor_id))
        db.execute('UPDATE monitor_group SET send_url=0 WHERE monitor_id=? AND group_id=?', (monitor_id, group_id))
db.close()
print('Published the public status page; the management dashboard still requires login.')
