import boto3
import csv
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_user_profile(sm_client, region, domain_id, username):
    try:
        response = sm_client.create_user_profile(
            DomainId=domain_id,
            UserProfileName=username
        )
        logging.info(f"User profile '{username}' created successfully in region {region}.")
        return response
    except Exception as e:
        logging.error(f"Failed to create user profile '{username}' in region {region}: {e}")
        return None

def main(region, workshop_name):
    sagemaker_domain_id = None

    try:
        with open(f"{workshop_name}-users.csv", mode='r') as file:
            reader = csv.reader(file)
            for _ in range(2):
                next(reader)  # Skip the first 2 rows
            sagemaker_domain_id = next(reader)[1]  # Extract Sagemaker Domain ID from the second row

        if not sagemaker_domain_id:
            logging.error("Missing SageMaker Domain ID in CSV file.")
            sys.exit(1)

    except FileNotFoundError:
        logging.error(f"CSV file '{workshop_name}-users.csv' not found.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Failed to read CSV file: {e}")
        sys.exit(1)

    session = boto3.Session(region_name=region)
    sm_client = session.client('sagemaker')

    try:
        with open(f"{workshop_name}-users.csv", mode='r') as file:
            reader = csv.DictReader(file, fieldnames=["Username", "Password"])
            for _ in range(4):
                next(reader)  # Skip the first 4 rows

            for row in reader:
                username = row.get('Username', '')
                password = row.get('Password', '')

                if username and password:
                    create_user_profile(sm_client, region, sagemaker_domain_id, username)
                else:
                    logging.warning(f"Skipping invalid row: {row}")
    except Exception as e:
        logging.error(f"Failed to process CSV file: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_sagemaker_profiles.py <region> <workshop_name>")
        sys.exit(1)

    region = sys.argv[1]
    workshop_name = sys.argv[2]

    main(region, workshop_name)
