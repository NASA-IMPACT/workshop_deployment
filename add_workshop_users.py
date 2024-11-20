import boto3
import csv
import sys
import logging
from create_cognito_users import create_cognito_user, generate_safe_password
from create_sagemaker_profiles import create_user_profile
from create_s3_buckets import create_bucket

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_workshop_info(csv_file):
    """Read existing workshop information from CSV."""
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        hosted_uri = next(reader)[1]
        user_pool_id = next(reader)[1]
        sagemaker_domain_id = next(reader)[1]
        next(reader)  # Skip header row
        existing_users = [row[0] for row in reader]
    return hosted_uri, user_pool_id, sagemaker_domain_id, existing_users

def get_next_user_number(existing_users):
    """Get the next available user number."""
    if not existing_users:
        return 1
    last_user = existing_users[-1]
    return int(last_user.split('-')[1]) + 1

def add_users(csv_file, num_new_users, region):
    # Read existing workshop information
    hosted_uri, user_pool_id, sagemaker_domain_id, existing_users = read_workshop_info(csv_file)
    
    # Extract workshop name from CSV filename
    workshop_name = csv_file.split('-users.csv')[0]
    
    # Initialize Cognito client
    cognito_client = boto3.client('cognito-idp', region_name=region)
    
    # Get starting user number
    start_num = get_next_user_number(existing_users)
    
    # Open CSV in append mode
    with open(csv_file, 'a', newline='') as file:
        writer = csv.writer(file)
        
        for i in range(num_new_users):
            user_num = start_num + i
            username = f"workshop-{user_num:03}"
            password = generate_safe_password()
            
            # Create Cognito user
            response = create_cognito_user(cognito_client, username, password, user_pool_id)
            if response:
                writer.writerow([username, password])
                logging.info(f"Created user: {username}")
                
                # Create SageMaker profile
                create_user_profile(boto3.client('sagemaker', region_name=region), 
                                 region, 
                                 sagemaker_domain_id, 
                                 username)
                
                # Create S3 bucket
                create_bucket(f"{workshop_name}-{user_num:03}", 
                            workshop_name, 
                            region)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python add_workshop_users.py <csv_file> <num_new_users> <region>")
        sys.exit(1)
        
    csv_file = sys.argv[1]
    num_new_users = int(sys.argv[2])
    region = sys.argv[3]
    
    add_users(csv_file, num_new_users, region)
