import boto3
import logging
import sys
import os
import json
import csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def empty_bucket(bucket_name, region):
    """
    Empty an S3 bucket by deleting all objects inside.
    """
    s3 = boto3.resource('s3', region_name=region)
    bucket = s3.Bucket(bucket_name)
    
    try:
        # Delete objects
        bucket.objects.all().delete()
        logging.info(f"All objects deleted from bucket '{bucket_name}'.")
        
        # Delete object versions if bucket has versioning enabled
        bucket.object_versions.all().delete()
        logging.info(f"All object versions deleted from bucket '{bucket_name}'.")
    except Exception as e:
        logging.error(f"Error deleting objects from bucket '{bucket_name}': {e}")
        return False
    return True

def delete_bucket(bucket_name, region):
    """
    Delete an S3 bucket with the specified name.
    """
    s3 = boto3.client('s3', region_name=region)
    try:
        if empty_bucket(bucket_name, region):  # Empty the bucket first
            s3.delete_bucket(Bucket=bucket_name)
            logging.info(f"Bucket '{bucket_name}' deleted successfully.")
            return True
    except Exception as e:
        logging.error(f"Error deleting bucket '{bucket_name}': {e}")
    return False

def list_matching_buckets(region, bucket_prefix):
    """
    List all buckets that start with the given prefix.
    """
    s3 = boto3.client('s3', region_name=region)
    try:
        response = s3.list_buckets()
        bucket_prefix_lower = bucket_prefix.lower()
        matching_buckets = [bucket['Name'] for bucket in response['Buckets'] 
                            if bucket['Name'].startswith(bucket_prefix_lower)]
        return matching_buckets
    except Exception as e:
        logging.error(f"Error listing buckets: {e}")
        return []

def get_bucket_list_from_csv(csv_file, workshop_name, region):
    """
    Try to get bucket information from the workshop CSV file.
    """
    bucket_names = []
    try:
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            for row in reader:
                # Skip rows until we find bucket info
                if len(row) >= 3 and 's3' in row[2].lower():
                    bucket_names.append(row[2].split('/')[-1])
    except Exception as e:
        logging.error(f"Error reading bucket info from CSV: {e}")
    
    # If no buckets found in CSV, try the default naming pattern
    if not bucket_names:
        logging.warning("No bucket info found in CSV, falling back to default naming pattern")
        # Try to find buckets with the workshop name prefix
        bucket_names = list_matching_buckets(region, workshop_name)
    
    return bucket_names

def main():
    if len(sys.argv) != 4:
        logging.error("Usage: python delete_s3_buckets.py <region> <workshop_name> <number_of_buckets>")
        sys.exit(1)
    
    region = sys.argv[1]
    workshop_name = sys.argv[2]
    num_buckets = int(sys.argv[3])  # Convert to integer
    
    # Check if a CSV file exists for this workshop
    csv_file = f"{workshop_name}-users.csv"
    bucket_names = []
    
    if os.path.exists(csv_file):
        logging.info(f"Found workshop CSV file: {csv_file}")
        bucket_names = get_bucket_list_from_csv(csv_file, workshop_name, region)  # Pass region parameter here
    
    # If no buckets found from CSV, fall back to searching by prefix
    if not bucket_names:
        logging.info(f"Searching for buckets with prefix: {workshop_name}")
        bucket_names = list_matching_buckets(region, workshop_name.lower())
    
    # If still no buckets found, try the old naming pattern
    if not bucket_names:
        logging.warning("No matching buckets found by prefix search. Trying sequential bucket naming.")
        for i in range(1, num_buckets + 1):
            bucket_name = f"{workshop_name.lower()}-{i:03}"
            bucket_names.append(bucket_name)
    
    logging.info(f"Found {len(bucket_names)} buckets to delete")
    
    # Delete the buckets
    deleted_count = 0
    for bucket_name in bucket_names:
        if delete_bucket(bucket_name, region):
            deleted_count += 1
    
    logging.info(f"Successfully deleted {deleted_count} out of {len(bucket_names)} buckets")

if __name__ == "__main__":
    main()