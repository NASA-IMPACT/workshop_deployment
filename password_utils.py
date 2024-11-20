# password_utils.py
import boto3
import csv
import string
import random
import logging
import sys

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

def update_user_passwords(csv_file, region):
    # Read workshop info
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)
        user_pool_id = rows[1][1]  # Get user pool ID from second row
    
    client = boto3.client('cognito-idp', region_name=region)
    
    # Create new CSV content with updated passwords
    new_rows = rows[:4]  # Keep the header rows
    
    # Update each user's password
    for row in rows[4:]:
        username = row[0]
        new_password = generate_safe_password()
        
        try:
            client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=username,
                Password=new_password,
                Permanent=True
            )
            new_rows.append([username, new_password])
            logging.info(f"Updated password for user: {username}")
        except Exception as e:
            logging.error(f"Failed to update password for {username}: {e}")
            new_rows.append(row)  # Keep old password if update fails
    
    # Write updated CSV
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(new_rows)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python password_utils.py <csv_file> <region>")
        sys.exit(1)
    
    update_user_passwords(sys.argv[1], sys.argv[2])