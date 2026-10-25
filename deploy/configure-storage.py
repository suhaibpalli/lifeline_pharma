#!/usr/bin/env python3
"""Expose catalogue objects for read only; keep all other uploads private."""
import json
import boto3
from decouple import Config, RepositoryEnv

config = Config(RepositoryEnv('/home/suhaib/pharma/.env'))
bucket = config('MINIO_BUCKET_NAME', default='lifeline-media')
client = boto3.client(
    's3', endpoint_url=config('MINIO_ENDPOINT_URL'),
    aws_access_key_id=config('MINIO_ACCESS_KEY'), aws_secret_access_key=config('MINIO_SECRET_KEY'),
    region_name=config('MINIO_REGION_NAME', default='us-east-1'),
)
resources = [f'arn:aws:s3:::{bucket}/{prefix}/*' for prefix in
             ['products', 'carousel', 'categories', 'manufacturers', 'catalogues']]
# Preserve existing root-level public videos without a wildcard that would
# accidentally expose similarly named files inside private profile folders.
for page in client.get_paginator('list_objects_v2').paginate(Bucket=bucket):
    resources.extend(f'arn:aws:s3:::{bucket}/{obj["Key"]}' for obj in page.get('Contents', [])
                     if '/' not in obj['Key'] and obj['Key'].lower().endswith('.mp4'))
policy = {'Version': '2012-10-17', 'Statement': [{
    'Effect': 'Allow', 'Principal': {'AWS': ['*']},
    'Action': ['s3:GetObject'], 'Resource': resources,
}]}
client.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
print('Applied public-read-only catalogue policy; private documents require signed URLs.')
