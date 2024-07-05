import boto3
import csv
import logging
import sys

# Constants
CSV_FILE = "users.csv"  # Replace with your CSV file name

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def main(region):
    session = boto3.Session(region_name=region)
    sm_client = session.client('sagemaker')
    
    try:
        with open(CSV_FILE, mode='r') as file:
            reader = csv.reader(file)
            rows = list(reader)

            # Extract Sagemaker Domain ID
            sagemaker_domain_id = None
            for row in rows:
                if row[0] == "Sagemaker Domain ID":
                    sagemaker_domain_id = row[1]
                    break

            if not sagemaker_domain_id:
                logging.error("Sagemaker Domain ID not found in CSV file.")
                return

            # Process user profiles
            for row in rows:
                if row[0].startswith("workshop-"):
                    username = row[0]
                    delete_user_profile(sm_client, sagemaker_domain_id, username)
    except FileNotFoundError:
        logging.error(f"CSV file '{CSV_FILE}' not found.")
    except Exception as e:
        logging.error(f"Failed to process CSV file: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <aws-region>")
        sys.exit(1)
    
    aws_region = sys.argv[1]
    main(aws_region)
