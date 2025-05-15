#!/usr/bin/env python3

import subprocess
import json
import logging
import time
import csv
import sys

# Constants
WAIT_TIME = 5  # Time in seconds to wait between checks
MAX_WAIT_ITERATIONS = 60  # Maximum number of iterations to wait

def list_spaces(domain_id, region):
    command = ["aws", "sagemaker", "list-spaces", "--domain-id", domain_id, "--region", region]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        spaces = json.loads(result.stdout).get('Spaces', [])
        return spaces
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to list spaces. Error: {e}")
        return []

def list_apps(domain_id, region):
    command = ["aws", "sagemaker", "list-apps", "--domain-id", domain_id, "--region", region]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        apps = json.loads(result.stdout).get('Apps', [])
        return apps
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to list apps. Error: {e}")
        return []

def delete_app(domain_id, app_name, app_type, region, user_profile_name=None, space_name=None):
    if user_profile_name:
        delete_command = ["aws", "sagemaker", "delete-app", "--domain-id", domain_id, "--user-profile-name", user_profile_name, "--app-name", app_name, "--app-type", app_type, "--region", region]
    elif space_name:
        delete_command = ["aws", "sagemaker", "delete-app", "--domain-id", domain_id, "--space-name", space_name, "--app-name", app_name, "--app-type", app_type, "--region", region]
    else:
        logging.error(f"Neither UserProfileName nor SpaceName provided for app: {app_name}. Skipping deletion.")
        return
    
    try:
        result = subprocess.run(delete_command, check=False, capture_output=True, text=True)
        
        # Check if the error is about the app already being deleted
        if result.returncode != 0:
            if "App [default] has already been deleted" in result.stderr:
                logging.info(f"App: {app_name} of type: {app_type} from user profile: {user_profile_name} or space: {space_name} was already deleted.")
                return
            else:
                # If it's a different error, raise it
                subprocess.run(delete_command, check=True)
                
        logging.info(f"Initiated deletion of app: {app_name} of type: {app_type} from user profile: {user_profile_name} or space: {space_name}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to delete app: {app_name} of type: {app_type} from user profile: {user_profile_name} or space: {space_name}. Error: {e}")

def delete_all_apps(domain_id, region):
    logging.info(f"Starting deletion of all apps for domain ID: {domain_id}")
    
    # List all apps
    apps = list_apps(domain_id, region)
    if not apps:
        logging.info("No apps found to delete.")
        return
    
    # Delete each app
    for app in apps:
        app_name = app['AppName']
        app_type = app['AppType']
        user_profile_name = app.get('UserProfileName')
        space_name = app.get('SpaceName')
        delete_app(domain_id, app_name, app_type, region, user_profile_name, space_name)

def delete_space(domain_id, space_name, region):
    delete_command = ["aws", "sagemaker", "delete-space", "--domain-id", domain_id, "--space-name", space_name, "--region", region]
    
    try:
        subprocess.run(delete_command, check=True)
        logging.info(f"Initiated deletion of space: {space_name}")
        
        # Custom wait loop
        for _ in range(MAX_WAIT_ITERATIONS):
            time.sleep(WAIT_TIME)
            if not space_exists(domain_id, space_name, region):
                logging.info(f"Successfully deleted space: {space_name}")
                return
        logging.error(f"Failed to delete space: {space_name} within the allotted time.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to delete space: {space_name}. Error: {e}")

def space_exists(domain_id, space_name, region):
    spaces = list_spaces(domain_id, region)
    for space in spaces:
        if space['SpaceName'] == space_name:
            return True
    return False

def get_domain_id_from_csv(csv_file):
    try:
        with open(csv_file, mode='r') as file:
            reader = csv.reader(file)
            rows = list(reader)

            # Find Sagemaker Domain ID
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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Fetch domain ID from CSV
    domain_id = get_domain_id_from_csv(csv_file)
    if not domain_id:
        logging.error("Failed to fetch Sagemaker Domain ID from CSV. Exiting.")
        sys.exit(1)
    
    logging.info(f"Starting deletion process for domain ID: {domain_id} in region: {region}")

    # Delete all apps first
    delete_all_apps(domain_id, region)
    
    # List all spaces after apps are deleted
    spaces = list_spaces(domain_id, region)
    if not spaces:
        logging.info("No spaces found to delete.")
        exit()
    
    # Delete each space
    for space in spaces:
        space_name = space['SpaceName']
        delete_space(domain_id, space_name, region)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <csvs_file> <aws-region>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    aws_region = sys.argv[2]
    main(csv_file, aws_region)
