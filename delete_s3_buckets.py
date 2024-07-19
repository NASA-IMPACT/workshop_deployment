import boto3
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def empty_bucket(bucket_name, region):
    """
    Empty an S3 bucket by deleting all objects inside.
    """
    s3 = boto3.resource('s3', region_name=region)
    bucket = s3.Bucket(bucket_name)
    
    try:
        bucket.objects.all().delete()
        logging.info(f"All objects deleted from bucket '{bucket_name}'.")
    except Exception as e:
        logging.error(f"Error deleting objects from bucket '{bucket_name}': {e}")

def delete_bucket(bucket_name, region):
    """
    Delete an S3 bucket with the specified name.
    """
    s3 = boto3.client('s3', region_name=region)
    try:
        empty_bucket(bucket_name, region)  # Empty the bucket first
        response = s3.delete_bucket(Bucket=bucket_name)
        logging.info(f"Bucket '{bucket_name}' deleted successfully.")
    except Exception as e:
        logging.error(f"Error deleting bucket '{bucket_name}': {e}")

def main():
    if len(sys.argv) != 4:
        logging.error("Usage: python delete_buckets.py <region> <bucket_name_prefix> <number_of_buckets>")
        sys.exit(1)
    
    region = sys.argv[1]
    bucket_prefix = sys.argv[2]
    num_buckets = int(sys.argv[3])  # Convert to integer

    for i in range(1, num_buckets + 1):
        bucket_name = f"{bucket_prefix}-{i:03}"
        delete_bucket(bucket_name, region)

if __name__ == "__main__":
    main()
