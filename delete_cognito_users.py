import boto3
import csv
import logging
import sys

def delete_cognito_user(user_pool_id, username, region):
    client = boto3.client('cognito-idp', region_name=region)

    try:
        client.admin_delete_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        logging.info(f"Deleted user: {username}")
    except client.exceptions.UserNotFoundException:
        logging.warning(f"User {username} not found, skipping deletion.")
    except Exception as e:
        logging.error(f"Failed to delete user {username}: {str(e)}")

def main(csv_file, region):
    try:
        with open(csv_file, mode='r') as file:
            reader = csv.reader(file)
            rows = list(reader)

            # Find User Pool ID
            user_pool_id = None
            for row in rows:
                if row[0] == "User Pool ID":
                    user_pool_id = row[1]
                    break

            if not user_pool_id:
                logging.error("User Pool ID not found in CSV file.")
                return

            # Process usernames for deletion
            for row in rows:
                if row[0].startswith("workshop-"):
                    username = row[0]
                    delete_cognito_user(user_pool_id, username, region)
    except FileNotFoundError:
        logging.error(f"CSV file '{csv_file}' not found.")
    except Exception as e:
        logging.error(f"Failed to process CSV file: {str(e)}")

    logging.info("User deletion process complete.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <csv_file> <aws-region>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    aws_region = sys.argv[2]
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main(csv_file, aws_region)
