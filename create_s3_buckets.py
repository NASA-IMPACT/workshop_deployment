import boto3
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    except Exception as e:
        logging.error(f"Error creating bucket '{bucket_name}': {e}")

def main():
    if len(sys.argv) != 4:
        logging.error("Usage: python create_buckets.py <region> <bucket_name_prefix> <number_of_buckets>")
        sys.exit(1)
    
    region = sys.argv[1]
    bucket_prefix = sys.argv[2]
    num_buckets = int(sys.argv[3])  # Convert to integer
    project_tag = sys.argv[2]

    for i in range(1, num_buckets + 1):
        bucket_name = f"{bucket_prefix}-{i:03}"
        create_bucket(bucket_name, project_tag, region)

if __name__ == "__main__":
    main()
