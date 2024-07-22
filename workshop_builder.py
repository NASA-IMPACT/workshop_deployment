import subprocess
import boto3
import os
import re
import time
import glob
import pandas as pd
import csv
from tqdm import tqdm
import sys

VALID_AWS_REGIONS = [
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'af-south-1', 'ap-east-1', 'ap-south-1', 'ap-northeast-1',
    'ap-northeast-2', 'ap-northeast-3', 'ap-southeast-1',
    'ap-southeast-2', 'ca-central-1', 'cn-north-1', 'cn-northwest-1',
    'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3',
    'eu-north-1', 'eu-south-1', 'me-south-1', 'sa-east-1'
]

def aws_sign_in():
    """Verify AWS CLI configuration and account."""
    print("Please ensure you have AWS CLI configured with 'aws configure'.")
    try:
        sts_client = boto3.client('sts')
        caller_identity = sts_client.get_caller_identity()
        account_id = caller_identity.get('Account')
        print(f"Signed into AWS account: {account_id}")
        confirmation = input("Is this the correct account? (yes/no) [yes]: ").strip().lower()
        if confirmation not in ['yes', 'y', '']:
            print("Please configure the correct AWS account and try again.")
            exit(1)
        print("AWS credentials are configured correctly.")
    except Exception as e:
        print(f"Error: {e}")
        print("Please run 'aws configure' to set up your credentials.")
        exit(1)

def set_aws_region():
    """Query the current AWS region and ask if the user wants to change it."""
    # Get the current region
    session = boto3.Session()
    current_region = session.region_name

    if current_region:
        print(f"Current AWS region: {current_region}")
        change_region = input("Would you like to change the region? (yes/no) [no]: ").strip().lower()
        if change_region not in ['yes', 'y']:
            return current_region
    else:
        print("No AWS region currently set.")
        change_region = 'yes'

    while True:
        if change_region in ['yes', 'y']:
            new_region = input("Please enter the AWS region to use (e.g. us-west-2): ").strip()
            if new_region in VALID_AWS_REGIONS:
                os.environ['AWS_DEFAULT_REGION'] = new_region
                os.environ['AWS_REGION'] = new_region
                try:
                    subprocess.run(["aws", "configure", "set", "region", new_region], check=True)
                    print(f"AWS region set to {new_region}.")
                    return new_region
                except subprocess.CalledProcessError as e:
                    print(f"Error setting AWS region: {e}")
            else:
                print("Invalid AWS region. Please enter a valid AWS region.")
        else:
            return current_region

def get_available_vpcs():
    """Retrieve available VPCs in the selected region."""
    ec2_client = boto3.client('ec2')
    response = ec2_client.describe_vpcs()
    return response['Vpcs']

def get_available_subnets(vpc_id):
    """Retrieve available subnets for a given VPC."""
    ec2_client = boto3.client('ec2')
    response = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    return response['Subnets']

def select_vpc():
    """Allow user to select a VPC from available options."""
    vpcs = get_available_vpcs()
    print("Available VPCs:")
    for index, vpc in enumerate(vpcs, start=1):
        print(f"{index}. VPC ID: {vpc['VpcId']}")
    
    vpc_index = int(input("Choose VPC (enter number): ")) - 1
    return vpcs[vpc_index]['VpcId']

def gather_parameters(region):
    """Collect necessary parameters for deployment."""
    vpc_id = select_vpc()
    
    subnets = get_available_subnets(vpc_id)
    print(f"Available Subnets for VPC {vpc_id}:")
    for index, subnet in enumerate(subnets, start=1):
        print(f"{index}. Subnet ID: {subnet['SubnetId']} ({subnet['AvailabilityZone']})")
    
    subnet_indices = input("Choose Subnet IDs (comma-separated numbers): ").strip().split(',')
    subnet_ids = [subnets[int(index) - 1]['SubnetId'] for index in subnet_indices]

    return {
        "AWSRegion": region,
        "VPCID": vpc_id,
        "SubnetIDs": subnet_ids
    }

def deploy_cdk_stack(params, workshop_name):
    print("Deploying the CDK stack... Please wait")

    # Set environment variables for CDK deployment
    os.environ['VPCID'] = params['VPCID']
    os.environ['AWSRegion'] = params['AWSRegion']
    os.environ['SubnetIDs'] = ','.join(params['SubnetIDs'])
    os.environ['WORKSHOP_NAME'] = workshop_name

    cdk_params = f"--parameters AWSRegion={params['AWSRegion']} " \
                 f"--parameters VPCID={params['VPCID']} " \
                 f"--parameters SubnetIDs={','.join(params['SubnetIDs'])} " \
                 f"--context workshop_name={workshop_name} " \
                 f"--require-approval never"

    command = f"cdk deploy {cdk_params}"

    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

        output = []
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
            sys.stdout.flush()
            output.append(line)

        process.stdout.close()
        return_code = process.wait()

        if return_code == 0:
            print("\nCDK stack deployed successfully.")
            return ''.join(output)
        else:
            print("\nCDK stack deployment failed.")
            return None
    except subprocess.CalledProcessError as e:
        print(f"CDK deployment error: {e}")
        return None

def destroy_cdk_stack(stack_name, workshop_name):
    try:
        command = f"cdk destroy {stack_name}-WorkshopDeploymentStack --context workshop_name={workshop_name} --force"
        
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

        for line in iter(process.stdout.readline, ''):
            print(line, end='')
            sys.stdout.flush()

        process.stdout.close()
        return_code = process.wait()

        if return_code == 0:
            print(f"\nCDK stack {stack_name} destroyed successfully.")
        else:
            print(f"\nCDK stack {stack_name} destroy failed.")

    except subprocess.CalledProcessError as e:
        print(f"Error destroying CDK stack {stack_name}: {e}")

def extract_outputs(deploy_output):
    """Extract important outputs from CDK deployment."""
    cognito_domain_id = None
    sagemaker_id = None
    hosted_uri = None

    cognito_regex = r"WorkshopDeploymentStack\.CognitoUserPoolID\s+=\s+(.*)"
    sagemaker_regex = r"WorkshopDeploymentStack\.SageMakerDomainID\s+=\s+(.*)"
    hosted_uri_regex = r"WorkshopDeploymentStack\.HostedUIUrl\s+=\s+(.*)"

    cognito_match = re.search(cognito_regex, deploy_output)
    sagemaker_match = re.search(sagemaker_regex, deploy_output)
    hosted_uri_match = re.search(hosted_uri_regex, deploy_output)

    if cognito_match:
        cognito_domain_id = cognito_match.group(1).strip()
    else:
        print("Failed to find Cognito Domain ID in the CDK deploy output.")

    if sagemaker_match:
        sagemaker_id = sagemaker_match.group(1).strip()
    else:
        print("Failed to find SageMaker ID in the CDK deploy output.")

    if hosted_uri_match:
        hosted_uri = hosted_uri_match.group(1).strip()
    else:
        print("Failed to find Hosted URI in the CDK deploy output.")

    return cognito_domain_id, sagemaker_id, hosted_uri

def execute_script(script_name, *args):
    try:
        # Convert all args to strings to avoid TypeError
        str_args = [str(arg) for arg in args]
        
        with tqdm(total=0, desc=f"Running {script_name}", bar_format='{desc}: {elapsed}') as pbar:
            result = subprocess.Popen(["python", script_name, *str_args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            while result.poll() is None:
                pbar.update(1)
                time.sleep(1)

        stdout, stderr = result.communicate()

        if result.returncode == 0:
            print(f"\n{script_name} completed successfully.")
            print(stdout)
        else:
            print(f"\n{script_name} execution failed.")
            print(stderr)
    except subprocess.CalledProcessError as e:
        print(f"Script execution error: {e}")

def select_csv_file(region):
    """Select a CSV file for an existing workshop in the given region."""
    csv_files = glob.glob("*-users.csv")
    if not csv_files:
        print("No existing workshops found.")
        return None

    valid_files = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            if df.apply(lambda row: row.astype(str).str.contains(region, na=False).any(), axis=1).any():
                valid_files.append(file)
        except Exception as e:
            print(f"Error reading {file}: {e}")

    if not valid_files:
        print(f"No existing workshops found in the '{region}' region.")
        return None

    print("Workshops available to delete:")
    for index, file in enumerate(valid_files, start=1):
        print(f"{index}. {file}")
    
    file_index = int(input("Choose a CSV file (enter number): ")) - 1
    return valid_files[file_index]

def extract_stack_name_from_csv(csv_file):
    """Extract the stack name from the CSV file name."""
    stack_name = csv_file.split('-users.csv')[0]
    return stack_name

def count_csv_rows(csv_file):
    """Count the number of rows in a CSV file."""
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        num_rows = sum(1 for row in reader)
    return num_rows

def get_existing_workshop_names():
    """Get a list of existing workshop names from CSV files."""
    csv_files = glob.glob("*-users.csv")
    return [os.path.splitext(file)[0].replace('-users', '') for file in csv_files]

def get_unique_workshop_name():
    """Prompt for a unique workshop name that doesn't exist in current CSV files."""
    existing_names = get_existing_workshop_names()
    while True:
        workshop_name = input("Please enter the workshop name: ").strip()
        if workshop_name in existing_names:
            print(f"A workshop named '{workshop_name}' already exists. Please choose a different name.")
        else:
            return workshop_name

if __name__ == "__main__":
    aws_sign_in()
    region = set_aws_region()

    while True:
        action = input("Would you like to create or destroy a workshop? (create/destroy) [create]: ").strip().lower()
        if action in ['create', 'destroy', '']:
            if action == '':
                action = 'create'
            break
        else:
            print("Invalid action. Please enter 'create' or 'destroy'.")

    if action == 'create':
        parameters = gather_parameters(region)
        num_users = input("Enter the number of users to create: ").strip()
        workshop_name = get_unique_workshop_name()
        deploy_output = deploy_cdk_stack(parameters, workshop_name)

        if deploy_output:
            cognito_domain_id, sagemaker_id, hosted_uri = extract_outputs(deploy_output)
            if cognito_domain_id and sagemaker_id and hosted_uri:
                print("Creating Cognito users...")
                execute_script('create_cognito_users.py', num_users, cognito_domain_id, sagemaker_id, hosted_uri, region, workshop_name)
                print("Creating Sagemaker Profiles...")
                execute_script('create_sagemaker_profiles.py', region, workshop_name)
                print("Creating S3 buckets...")
                execute_script('create_s3_buckets.py', region, workshop_name, num_users)
                print(f'View {workshop_name}-users.csv file for sign in information')
            else:
                print("Failed to extract Cognito Domain ID and/or SageMaker ID from the CDK deploy output.")
        else:
            print("CDK deployment failed. Exiting.")

    if action == 'destroy':
        csv_file = select_csv_file(region)
        if csv_file:
            workshop_name = extract_stack_name_from_csv(csv_file)
            num_rows = count_csv_rows(csv_file)
            num_users = num_rows - 4  # Adjust num_users as specified

            print('Deleting spaces...')
            execute_script('delete_spaces.py', csv_file, region)
            print('Deleting Sagemaker users...')
            execute_script('delete_sagemaker_profiles.py', csv_file, region)
            print('Deleting Cognito users...')
            execute_script('delete_cognito_users.py', csv_file, region)
            print('Deleting S3 buckets...')
            execute_script('delete_s3_buckets.py', region, workshop_name, num_users)

            stack_name = extract_stack_name_from_csv(csv_file)
            
            # Extract workshop name from the stack name
            workshop_name = stack_name.split('-')[0]
            
            destroy_cdk_stack(stack_name, workshop_name)

            try:
                os.remove(csv_file)
                print(f"Deleted the file: {csv_file}")
            except Exception as e:
                print(f"Failed to delete the file {csv_file}: {e}")
