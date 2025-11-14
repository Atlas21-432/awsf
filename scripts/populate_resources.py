#!/usr/bin/env python3
"""
AWS Resource Populator
======================

Fetches resources from multiple AWS services and stores them in a searchable format.

This script connects to your AWS account and retrieves information about resources
across multiple services, storing them in a JSON file for fast searching.

Services supported:
- AWS Lambda
- Amazon S3
- Amazon SQS
- Amazon Kinesis
- Amazon DynamoDB
- Amazon RDS
- Amazon API Gateway

Requirements:
- AWS CLI configured (aws configure)
- Python boto3 library (pip install boto3)
- Appropriate IAM permissions for listing resources

Usage:
    python3 populate_resources.py
    python3 populate_resources.py --region us-west-2
    python3 populate_resources.py --profile myprofile
"""

import boto3
import json
import sys
import os
from botocore.exceptions import ClientError, NoCredentialsError

# Get the directory paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config", "config.json")

def load_config():
    """Load configuration from JSON file"""
    default_config = {
        "aws_region": "us-east-1",
        "aws_profile": None,
        "console_base_url": "https://console.aws.amazon.com"
    }
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except (FileNotFoundError, json.JSONDecodeError):
        return default_config

def get_session(profile=None):
    """Create boto3 session"""
    try:
        if profile:
            session = boto3.Session(profile_name=profile)
            print(f"Using AWS profile: {profile}")
        elif os.getenv('AWS_ACCESS_KEY_ID'):
            session = boto3.Session()
            print("Using AWS environment variables for authentication")
        else:
            session = boto3.Session()
            print("Using default AWS credentials")
        
        return session
    except Exception as e:
        print(f"❌ Error creating AWS session: {e}")
        return None

def fetch_lambda_functions(session, region):
    """Fetch Lambda functions"""
    try:
        client = session.client('lambda', region_name=region)
        paginator = client.get_paginator('list_functions')
        
        functions = {}
        for page in paginator.paginate():
            for func in page.get('Functions', []):
                name = func['FunctionName']
                arn = func['FunctionArn']
                
                # Generate console URL
                console_url = f"https://{region}.console.aws.amazon.com/lambda/home?region={region}#/functions/{name}?tab=configuration"
                
                functions[name] = {
                    'service': 'lambda',
                    'type': 'function',
                    'arn': arn,
                    'url': console_url,
                    'runtime': func.get('Runtime', 'unknown'),
                    'last_modified': func.get('LastModified', ''),
                    'region': region
                }
        
        print(f"   ✅ Found {len(functions)} Lambda functions")
        return functions
        
    except ClientError as e:
        print(f"   ❌ Error fetching Lambda functions: {e}")
        return {}

def fetch_s3_buckets(session, region):
    """Fetch S3 buckets"""
    try:
        client = session.client('s3')
        response = client.list_buckets()
        
        buckets = {}
        for bucket in response.get('Buckets', []):
            name = bucket['Name']
            
            # Generate console URL  
            console_url = f"https://s3.console.aws.amazon.com/s3/buckets/{name}?region={region}"
            
            buckets[name] = {
                'service': 's3',
                'type': 'bucket',
                'url': console_url,
                'creation_date': bucket.get('CreationDate', '').isoformat() if bucket.get('CreationDate') else '',
                'region': region
            }
        
        print(f"   ✅ Found {len(buckets)} S3 buckets")
        return buckets
        
    except ClientError as e:
        print(f"   ❌ Error fetching S3 buckets: {e}")
        return {}

def fetch_sqs_queues(session, region):
    """Fetch SQS queues"""
    try:
        client = session.client('sqs', region_name=region)
        response = client.list_queues()
        
        queues = {}
        for queue_url in response.get('QueueUrls', []):
            queue_name = queue_url.split('/')[-1]
            
            # Generate console URL
            console_url = f"https://{region}.console.aws.amazon.com/sqs/v2/home?region={region}#/queues/{queue_url.replace('://', '%3A//')}"
            
            queues[queue_name] = {
                'service': 'sqs',
                'type': 'queue',
                'url': console_url,
                'queue_url': queue_url,
                'region': region
            }
        
        print(f"   ✅ Found {len(queues)} SQS queues")
        return queues
        
    except ClientError as e:
        print(f"   ❌ Error fetching SQS queues: {e}")
        return {}

def fetch_kinesis_streams(session, region):
    """Fetch Kinesis streams"""
    try:
        client = session.client('kinesis', region_name=region)
        paginator = client.get_paginator('list_streams')
        
        streams = {}
        for page in paginator.paginate():
            for stream_name in page.get('StreamNames', []):
                # Get stream details
                try:
                    stream_details = client.describe_stream(StreamName=stream_name)
                    stream_info = stream_details['StreamDescription']
                    
                    # Generate console URL
                    console_url = f"https://{region}.console.aws.amazon.com/kinesis/home?region={region}#/streams/details/{stream_name}/monitoring"
                    
                    streams[stream_name] = {
                        'service': 'kinesis',
                        'type': 'stream',
                        'url': console_url,
                        'arn': stream_info.get('StreamARN', ''),
                        'status': stream_info.get('StreamStatus', 'unknown'),
                        'shard_count': len(stream_info.get('Shards', [])),
                        'region': region
                    }
                except ClientError:
                    # Skip streams we can't access
                    continue
        
        print(f"   ✅ Found {len(streams)} Kinesis streams")
        return streams
        
    except ClientError as e:
        print(f"   ❌ Error fetching Kinesis streams: {e}")
        return {}

def fetch_dynamodb_tables(session, region):
    """Fetch DynamoDB tables"""
    try:
        client = session.client('dynamodb', region_name=region)
        paginator = client.get_paginator('list_tables')
        
        tables = {}
        for page in paginator.paginate():
            for table_name in page.get('TableNames', []):
                # Get table details
                try:
                    table_details = client.describe_table(TableName=table_name)
                    table_info = table_details['Table']
                    
                    # Generate console URL
                    console_url = f"https://{region}.console.aws.amazon.com/dynamodbv2/home?region={region}#table?name={table_name}"
                    
                    tables[table_name] = {
                        'service': 'dynamodb',
                        'type': 'table',
                        'url': console_url,
                        'arn': table_info.get('TableArn', ''),
                        'status': table_info.get('TableStatus', 'unknown'),
                        'item_count': table_info.get('ItemCount', 0),
                        'region': region
                    }
                except ClientError:
                    # Skip tables we can't access
                    continue
        
        print(f"   ✅ Found {len(tables)} DynamoDB tables")
        return tables
        
    except ClientError as e:
        print(f"   ❌ Error fetching DynamoDB tables: {e}")
        return {}

def fetch_rds_resources(session, region):
    """Fetch RDS instances and clusters"""
    try:
        client = session.client('rds', region_name=region)
        resources = {}
        
        # Fetch RDS instances
        try:
            paginator = client.get_paginator('describe_db_instances')
            for page in paginator.paginate():
                for instance in page.get('DBInstances', []):
                    name = instance['DBInstanceIdentifier']
                    
                    # Generate console URL
                    console_url = f"https://{region}.console.aws.amazon.com/rds/home?region={region}#database:id={name};is-cluster=false"
                    
                    resources[name] = {
                        'service': 'rds',
                        'type': 'instance',
                        'url': console_url,
                        'arn': instance.get('DBInstanceArn', ''),
                        'engine': instance.get('Engine', 'unknown'),
                        'status': instance.get('DBInstanceStatus', 'unknown'),
                        'region': region
                    }
        except ClientError as e:
            print(f"   ⚠️  Error fetching RDS instances: {e}")
        
        # Fetch RDS clusters
        try:
            paginator = client.get_paginator('describe_db_clusters')
            for page in paginator.paginate():
                for cluster in page.get('DBClusters', []):
                    name = cluster['DBClusterIdentifier']
                    
                    # Generate console URL
                    console_url = f"https://{region}.console.aws.amazon.com/rds/home?region={region}#database:id={name};is-cluster=true"
                    
                    resources[name] = {
                        'service': 'rds',
                        'type': 'cluster',
                        'url': console_url,
                        'arn': cluster.get('DBClusterArn', ''),
                        'engine': cluster.get('Engine', 'unknown'),
                        'status': cluster.get('Status', 'unknown'),
                        'region': region
                    }
        except ClientError as e:
            print(f"   ⚠️  Error fetching RDS clusters: {e}")
        
        print(f"   ✅ Found {len(resources)} RDS resources")
        return resources
        
    except ClientError as e:
        print(f"   ❌ Error fetching RDS resources: {e}")
        return {}

def fetch_api_gateway_apis(session, region):
    """Fetch API Gateway APIs"""
    try:
        client = session.client('apigateway', region_name=region)
        response = client.get_rest_apis()
        
        apis = {}
        for api in response.get('items', []):
            name = api['name']
            api_id = api['id']
            
            # Generate console URL
            console_url = f"https://{region}.console.aws.amazon.com/apigateway/home?region={region}#/apis/{api_id}"
            
            apis[name] = {
                'service': 'apigateway',
                'type': 'rest_api',
                'url': console_url,
                'api_id': api_id,
                'description': api.get('description', ''),
                'created_date': api.get('createdDate', '').isoformat() if api.get('createdDate') else '',
                'region': region
            }
        
        print(f"   ✅ Found {len(apis)} API Gateway APIs")
        return apis
        
    except ClientError as e:
        print(f"   ❌ Error fetching API Gateway APIs: {e}")
        return {}

def main():
    """Main execution function"""
    # Parse command line arguments
    region = None
    profile = None
    
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg in ['--region', '-r'] and i < len(sys.argv) - 1:
            region = sys.argv[i + 1]
        elif arg in ['--profile', '-p'] and i < len(sys.argv) - 1:
            profile = sys.argv[i + 1]
        elif arg in ['--help', '-h']:
            print(__doc__)
            return
    
    # Load configuration
    config = load_config()
    if not region:
        region = config.get('aws_region', 'us-east-1')
    if not profile:
        profile = config.get('aws_profile')
    
    print("🚀 AWS Resource Fetcher")
    print("=" * 50)
    print(f"Region: {region}")
    
    # Create session
    session = get_session(profile)
    if not session:
        return 1
    
    # Test credentials
    try:
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"Account: {identity.get('Account', 'unknown')}")
        print(f"User/Role: {identity.get('Arn', 'unknown').split('/')[-1]}")
    except (ClientError, NoCredentialsError) as e:
        print(f"❌ AWS credential error: {e}")
        print("💡 Make sure AWS is configured (aws configure) or environment variables are set")
        return 1
    
    print()
    
    # Fetch resources from all services
    all_resources = {}
    
    print("🔍 Fetching Lambda functions...")
    all_resources.update(fetch_lambda_functions(session, region))
    
    print("🔍 Fetching S3 buckets...")
    all_resources.update(fetch_s3_buckets(session, region))
    
    print("🔍 Fetching SQS queues...")
    all_resources.update(fetch_sqs_queues(session, region))
    
    print("🔍 Fetching Kinesis streams...")
    all_resources.update(fetch_kinesis_streams(session, region))
    
    print("🔍 Fetching DynamoDB tables...")
    all_resources.update(fetch_dynamodb_tables(session, region))
    
    print("🔍 Fetching RDS instances and clusters...")
    all_resources.update(fetch_rds_resources(session, region))
    
    print("🔍 Fetching API Gateway APIs...")
    all_resources.update(fetch_api_gateway_apis(session, region))
    
    # Save to file
    os.makedirs(DATA_DIR, exist_ok=True)
    output_file = os.path.join(DATA_DIR, "aws_resources.json")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_resources, f, indent=2, default=str)
        print(f"\n✅ Successfully saved {len(all_resources)} resources to {output_file}")
    except (OSError, IOError) as e:
        print(f"\n❌ Error saving resources: {e}")
        return 1
    
    # Summary by service
    print("\n📊 Resource Summary:")
    service_counts = {}
    for resource in all_resources.values():
        service = resource.get('service', 'unknown').upper()
        service_counts[service] = service_counts.get(service, 0) + 1
    
    for service in sorted(service_counts.keys()):
        print(f"   {service:<12}: {service_counts[service]:>4} resources")
    
    print(f"\n🎉 Resource collection complete! Use 'awsf' to search.")
    return 0

if __name__ == "__main__":
    sys.exit(main())