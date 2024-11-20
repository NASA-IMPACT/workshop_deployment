import boto3
import csv
import random
import string
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_safe_password():
    """Generate a password that works reliably with Cognito."""
    # Use a more limited set of special characters that are less likely to cause issues
    special_chars = "!@#$%^&*"
    
    # Ensure at least one of each required character type
    password = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice(special_chars)
    ]
    
    # Fill remaining length with random chars (avoiding problematic ones)
    chars = string.ascii_letters + string.digits + special_chars
    password.extend(random.choice(chars) for _ in range(8))  # Adding 8 more for 12 total
    
    # Shuffle the password
    random.shuffle(password)
    return ''.join(password)

def create_cognito_user(client, username, temporary_password, user_pool_id):
    try:
        response = client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            TemporaryPassword=temporary_password,
            MessageAction='SUPPRESS'
        )
        logging.info(f"Created user: {username}")
    except client.exceptions.UsernameExistsException:
        logging.warning(f"User {username} already exists.")
        return None
    except Exception as e:
        logging.error(f"Failed to create user {username}: {str(e)}")
        return None

    try:
        client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=temporary_password,
            Permanent=True
        )
        logging.info(f"Set permanent password for user: {username}")
    except Exception as e:
        logging.error(f"Failed to set permanent password for user {username}: {str(e)}")
        return None

    return response

def main(num_users, user_pool_id, sagemaker_domain_id, hosted_uri, region, workshop_name):
    client = boto3.client('cognito-idp', region_name=region)

    # Write user pool id, sagemaker domain id, and hosted URI at the top of CSV
    with open(f"{workshop_name}-users.csv", mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Hosted URI", hosted_uri])
        writer.writerow(["User Pool ID", user_pool_id])
        writer.writerow(["Sagemaker Domain ID", sagemaker_domain_id])
        writer.writerow(["Username", "Password"])

        for i in range(1, num_users + 1):
            username = f"workshop-{i:03}"
            temporary_password = generate_safe_password()

            response = create_cognito_user(client, username, temporary_password, user_pool_id)

            if response:
                writer.writerow([username, temporary_password])

    logging.info(f"Users created and details saved to {workshop_name}-users.csv")

if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Usage: python create_cognito_users.py <num_users> <user_pool_id> <sagemaker_domain_id> <hosted_uri> <region> <workshop_name>")
        sys.exit(1)
    
    num_users = int(sys.argv[1])
    user_pool_id = sys.argv[2]
    sagemaker_domain_id = sys.argv[3]
    hosted_uri = sys.argv[4]
    region = sys.argv[5]
    workshop_name = sys.argv[6]

    main(num_users, user_pool_id, sagemaker_domain_id, hosted_uri, region, workshop_name)
