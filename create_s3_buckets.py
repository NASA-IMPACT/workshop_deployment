import boto3
import logging
import sys
import uuid
import random
import string
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_random_string(length=6):
    """
    Generate a random string of lowercase letters and numbers.
    """
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def create_bucket(bucket_name, project_tag, region):
    """
    Create an S3 bucket with the specified name and region.
    """
    s3 = boto3.client('s3', region_name=region)
    try:
        location = {'LocationConstraint': region}
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration=location if region != 'us-east-1' else {}
        )
        logging.info(f"Bucket '{bucket_name}' created successfully in region '{region}'.")
        
        # Get the current time
        creation_date = datetime.now().strftime("%Y-%m-%d")
        
        s3.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={
                'TagSet': [
                    {'Key': 'project', 'Value': "cmt-workshop"},
                    {'Key': 'workshop', 'Value': project_tag},
                    {'Key': 'creation-date', 'Value': creation_date}
                ]
            }
        )
        logging.info(f"Tag added to bucket '{bucket_name}': Project={project_tag}.")
        return True
    except Exception as e:
        logging.error(f"Error creating bucket '{bucket_name}': {e}")
        return False

def main():
    if len(sys.argv) != 4:
        logging.error("Usage: python create_buckets.py <region> <bucket_name_prefix> <number_of_buckets>")
        sys.exit(1)
    
    region = sys.argv[1]
    original_prefix = sys.argv[2]
    project_tag = original_prefix  # Keep original for tagging
    bucket_prefix = original_prefix.lower()  # Convert to lowercase for bucket names
    num_buckets = int(sys.argv[3])  # Convert to integer
    
    # Generate a random suffix to make bucket names more unique
    # Using both a UUID part and a timestamp to reduce collision probability
    timestamp = datetime.now().strftime("%m%d%H%M")
    random_suffix = generate_random_string(6)
    
    successful_buckets = []
    for i in range(1, num_buckets + 1):
        # Create bucket name with randomization
        bucket_name = f"{bucket_prefix}-{timestamp}-{random_suffix}-{i:03}"
        
        # Ensure bucket name doesn't exceed 63 characters
        if len(bucket_name) > 63:
            # Truncate the prefix if needed
            max_prefix_length = 63 - len(f"-{timestamp}-{random_suffix}-{i:03}")
            bucket_name = f"{bucket_prefix[:max_prefix_length]}-{timestamp}-{random_suffix}-{i:03}"
        
        if create_bucket(bucket_name, project_tag, region):
            successful_buckets.append(bucket_name)
    
    # Print summary
    logging.info(f"Successfully created {len(successful_buckets)} out of {num_buckets} buckets")
    for bucket in successful_buckets:
        logging.info(f"Created: {bucket}")

if __name__ == "__main__":
    main()