# Lifeline production operations

Production runs Django/Gunicorn under `pharma.service`, PostgreSQL 16 on the
host, and Redis/MinIO/Uptime Kuma in Docker. The optional Compose Django service
is behind the `backend` profile. Never run it alongside the systemd backend.

Before deployment, create and verify a PostgreSQL custom-format dump and a copy
of uploaded objects. Retain an off-server copy. Take a filesystem snapshot of
MinIO only while it is stopped; live backups use the authenticated S3 API.

## Runtime configuration

The host `.env` must have `DEBUG=False`, `DB_HOST=localhost`,
`MINIO_ENDPOINT_URL=http://127.0.0.1:9000`,
`MINIO_PUBLIC_ENDPOINT_URL=https://media.lifelinehealthcare.in`,
`REDIS_URL=redis://127.0.0.1:6379/1`, `SECURE_SSL_REDIRECT=True`,
`EMAIL_VALIDATE_CERTS=True`, the exact public hosts and HTTPS CSRF origins.
Preserve real keys and passwords; do not replace `.env` with the example.

The `gunicorn.conf.py` default is two synchronous workers with request-count
recycling. systemd bounds the group at 1.5 GiB; measure memory under actual
traffic before changing worker counts. Images above 12 megapixels are rejected
before decoding/EXIF transforms can allocate large buffers.
The optional Gunicorn control socket is disabled: systemd owns reload/shutdown,
and the protected home directory must remain read-only.

## Validation and deployment

```bash
venv/bin/python manage.py check
venv/bin/python manage.py check --deploy
venv/bin/python manage.py test --settings=pharma_ecommerce.test_settings --noinput
venv/bin/python manage.py makemigrations --check --dry-run
venv/bin/python manage.py migrate --noinput
venv/bin/python manage.py collectstatic --noinput
```

The test settings isolate SQLite, cache, storage and email from production.
Storage-only migrations change the storage backend, not existing object keys.
Keep `/home/suhaib/pharma/staticfiles` and `/opt/pharma/staticfiles` aligned
(the production installation uses a symlink).

Install the unit files into `/etc/systemd/system/`, `pharma-health` into
`/usr/local/sbin/`, and `pharma-backup.py` into `/usr/local/libexec/`, owned by
root. Install the logrotate rule as `/etc/logrotate.d/pharma`.
Use `install -o root -g root -m 0644` for unit, nginx and logrotate
configuration files (logrotate rejects group-writable rules), and mode 0750
for the health and backup executables. For example:

```bash
sudo install -o root -g root -m 0644 deploy/pharma.logrotate /etc/logrotate.d/pharma
sudo install -o root -g root -m 0750 deploy/pharma-health /usr/local/sbin/pharma-health
```

Copy the nginx site/proxy/log-format templates into their corresponding nginx
directories, run `nginx -t`, then reload. Do not return HTTP 200 for maintenance.
Enable `pharma-dependencies.service`, `pharma.service`, `pharma-health.timer`
and `pharma-backup.timer`. Remove the old password-dependent user restart cron.
Set host `vm.overcommit_memory=1` for Redis persistence, with the application
and container memory limits retained.

Run `venv/bin/python deploy/configure-storage.py` after backing up the old
bucket policy. Public access is read-only for catalogue prefixes; profiles and
prescriptions use five-minute signed URLs and bypass nginx's shared cache.
The media proxy blocks browser uploads/deletes; the application uses the
internal S3 endpoint with credentials. Verify anonymous PUT/DELETE/ListBucket
are denied and signed private reads work before reopening.

Update Uptime Kuma's backend target to the public `/health/` endpoint; the old
`pharma_django` target is invalid. Do this through its UI or edit its SQLite
database only while the container is stopped, after taking a backup.
`deploy/configure-status.py` publishes the existing page through Kuma's native
custom-domain mapping for `status.lifelinehealthcare.in`. Run it while the
container is stopped, then start Kuma. `/dashboard` remains authenticated;
the root domain shows public service health. Preserve historical heartbeats.

### Uptime Kuma upgrades

The monitoring image is pinned to stable 2.5.7 and its published manifest digest.
Upgrade only `uptime-kuma`, using `docker compose up -d --no-deps uptime-kuma`;
the Django/systemd backend and other containers can continue running.

Before a major upgrade, stop Kuma alone and archive its complete
`/opt/pharma/uptime-kuma-data` directory, record the old image/configuration, verify
SQLite integrity and the archive checksum, and keep an off-server copy. Rehearse
the upgrade against a separate copy with networking and monitors disabled. Never
interrupt the v1-to-v2 aggregation migration. A rollback requires restoring the
pre-upgrade data directory along with the old image, not running v1 against the
migrated database. See the official
[migration guide](https://github.com/louislam/uptime-kuma/wiki/Migration-From-v1-To-v2).
The default image runs as root: keep its host data directory owned by root with
mode 0700 and `kuma.db` mode 0600, since the database contains SMTP credentials.

Verify the dashboard login, custom-domain public page, monitors, history and
notification assignments after upgrading. SMTP custom templates in v2 use Liquid;
use `[Lifeline] {{status}} - {{name}}` and retain STARTTLS/certificate validation.
After backing up and stopping Kuma, `python3 deploy/upgrade-status-notifications.py`
updates the existing Lifeline email channel without changing its recipients or
credentials; it refuses to edit a running instance's database.
Test mail to the configured recipients through Kuma after checking the rendered
subject. Kuma's 512 MiB limit allows headroom for its migration and aggregation.

## Daily backups and recovery

`pharma-backup.timer` runs at 02:30 IST, with missed runs caught on startup.
It creates a PostgreSQL dump and authenticated copies of all bucket objects,
records object hashes and the bucket policy, and retains 14 successful daily
archives under `/home/suhaib/backups/pharma-daily`. These archives contain
private data; directory/file permissions must remain 0700/0600. Copy them
off-server regularly; a VPS-only backup is not disaster recovery.

For a recovery drill, create a separate PostgreSQL database and feed the dump
to `sudo -u postgres pg_restore --no-owner --exit-on-error -d TEMP_DATABASE`.
Compare record counts, then drop only that temporary database. For the daily
object backup, restore `snapshot/objects/` through the authenticated S3 API;
do not copy these plain objects directly into MinIO's internal data directory.

Inspect `journalctl -u pharma-backup.service`, `pharma-health.service`, and
`pharma.service`. Django file logs and separate nginx per-site logs rotate for
90 days. Nginx logging omits query strings so signed document URLs and tokens
are not recorded.

## Maintenance

Create `/run/pharma-maintenance`, stop `pharma-health.timer`, then stop
`pharma.service` for deliberate maintenance. Leave nginx serving an HTTP 503
maintenance page and preserve PostgreSQL/uploads. To restore, start dependencies
and backend, confirm `/health/` returns 200 with all checks `ok`, remove the
maintenance flag, and start the health timer. Never stop the shared Docker/nginx
daemons just to stop this application.
