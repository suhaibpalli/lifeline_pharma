#!/usr/bin/env python3
"""Root-only PostgreSQL dump and S3 object backup; never copies a live MinIO data directory."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone

import boto3
from botocore.config import Config as S3Config
from decouple import Config, RepositoryEnv


def main():
    os.umask(0o077)
    config = Config(RepositoryEnv('/home/suhaib/pharma/.env'))
    destination = Path('/home/suhaib/backups/pharma-daily')
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    archive = destination / f'pharma-{stamp}.tar.gz'
    temporary = archive.with_suffix('.partial')
    with tempfile.TemporaryDirectory(prefix='.snapshot-', dir=destination) as folder:
        folder = Path(folder)
        with (folder / 'pharmadb.dump').open('wb') as output:
            subprocess.run(['sudo', '-u', 'postgres', 'pg_dump', '-Fc', config('DB_NAME')],
                           stdout=output, check=True, timeout=120)
        subprocess.run(['pg_restore', '--list', str(folder / 'pharmadb.dump')],
                       stdout=subprocess.DEVNULL, check=True, timeout=30)
        client = boto3.client(
            's3', endpoint_url=config('MINIO_ENDPOINT_URL'),
            aws_access_key_id=config('MINIO_ACCESS_KEY'),
            aws_secret_access_key=config('MINIO_SECRET_KEY'),
            region_name=config('MINIO_REGION_NAME', default='us-east-1'),
            config=S3Config(connect_timeout=5, read_timeout=30, retries={'max_attempts': 3}),
        )
        bucket = config('MINIO_BUCKET_NAME', default='lifeline-media')
        manifest = []
        for page in client.get_paginator('list_objects_v2').paginate(Bucket=bucket):
            for item in page.get('Contents', []):
                key = item['Key']
                target = folder / 'objects' / key
                if not target.resolve().is_relative_to((folder / 'objects').resolve()):
                    raise ValueError('Unsafe object key')
                if key.endswith('/'):
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                # A version/ETag condition prevents silently backing up a changed
                # object under metadata captured by the earlier listing.
                response = client.get_object(Bucket=bucket, Key=key, IfMatch=item['ETag'])
                with response['Body'] as body, target.open('wb') as output:
                    shutil.copyfileobj(body, output)
                if target.stat().st_size != item['Size']:
                    raise RuntimeError('Incomplete object backup')
                manifest.append({'key': key, 'size': item['Size'],
                                 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
        (folder / 'objects.json').write_text(json.dumps(manifest, indent=2))
        (folder / 'bucket-policy.json').write_text(client.get_bucket_policy(Bucket=bucket)['Policy'])
        # SQLite's backup API produces a consistent monitoring/configuration
        # snapshot even while Uptime Kuma is running.
        kuma = Path('/opt/pharma/uptime-kuma-data/kuma.db')
        if kuma.exists():
            with sqlite3.connect(f'file:{kuma}?mode=ro', uri=True) as source:
                with sqlite3.connect(folder / 'kuma.db') as target:
                    source.backup(target)
        with tarfile.open(temporary, 'w:gz') as output:
            output.add(folder, arcname='snapshot')
        with tarfile.open(temporary, 'r:gz') as source:
            assert source.getmember('snapshot/pharmadb.dump').size > 0
        temporary.replace(archive)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.sha256').write_text(f'{checksum}  {archive.name}\n')
    print(f'Verified backup {archive.name}: {len(manifest)} uploaded objects')
    # Preserve at least 14 successful daily snapshots, never the initial relaunch backup.
    for old in sorted(destination.glob('pharma-*.tar.gz'))[:-14]:
        old.unlink()
        old.with_suffix('.sha256').unlink(missing_ok=True)


if __name__ == '__main__':
    main()
