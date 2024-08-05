import boto3
import csv
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def list_user_profiles(sm_client, domain_id):
    try:
        user_profiles = []
        paginator = sm_client.get_paginator('list_user_profiles')
        for page in paginator.paginate(DomainIdEquals=domain_id):
            user_profiles.extend(page['UserProfiles'])
        return user_profiles
    except Exception as e:
        logging.error(f"Failed to list user profiles: {e}")
        return []

def delete_user_profile(sm_client, domain_id, username):
    try:
        response = sm_client.delete_user_profile(
            DomainId=domain_id,
            UserProfileName=username
        )
        logging.info(f"User profile '{username}' deleted successfully.")
        return response
    except sm_client.exceptions.ResourceNotFound:
        logging.warning(f"User profile '{username}' not found.")
    except Exception as e:
        logging.error(f"Failed to delete user profile '{username}': {e}")
        return None

def get_domain_id_from_csv(csv_file):
    try:
        with open(csv_file, mode='r') as file:
            reader = csv.reader(file)
            rows = list(reader)

            for row in rows:
                if row[0] == "Sagemaker Domain ID":
                    return row[1]
            logging.error("Sagemaker Domain ID not found in CSV file.")
            return None
    except FileNotFoundError:
        logging.error(f"CSV file '{csv_file}' not found.")
        return None
    except Exception as e:
        logging.error(f"Failed to process CSV file: {e}")
        return None

def main(csv_file, region):
    session = boto3.Session(region_name=region)
    sm_client = session.client('sagemaker')
    
    domain_id = get_domain_id_from_csv(csv_file)
    if not domain_id:
        logging.error("Failed to get Sagemaker Domain ID from CSV. Exiting.")
        return

    logging.info(f"Using Sagemaker Domain ID: {domain_id}")

    # List all user profiles
    user_profiles = list_user_profiles(sm_client, domain_id)
    
    if not user_profiles:
        logging.info("No user profiles found in the domain.")
        return

    # Delete all user profiles
    for profile in user_profiles:
        username = profile['UserProfileName']
        delete_user_profile(sm_client, domain_id, username)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python delete_sagemaker_profiles.py <csv_file> <region>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    region = sys.argv[2]
    main(csv_file, region)