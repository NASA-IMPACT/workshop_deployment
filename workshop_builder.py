import subprocess
import boto3
import os
import re

VALID_AWS_REGIONS = [
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'af-south-1', 'ap-east-1', 'ap-south-1', 'ap-northeast-1',
    'ap-northeast-2', 'ap-northeast-3', 'ap-southeast-1',
    'ap-southeast-2', 'ca-central-1', 'cn-north-1', 'cn-northwest-1',
    'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3',
    'eu-north-1', 'eu-south-1', 'me-south-1', 'sa-east-1'
]

def aws_sign_in():
    print("Please ensure you have AWS CLI configured with 'aws configure'.")
    try:
        sts_client = boto3.client('sts')
        caller_identity = sts_client.get_caller_identity()
        account_id = caller_identity.get('Account')
        print(f"Signed into AWS account: {account_id}")
        confirmation = input("Is this the correct account? (yes/no): ").strip().lower()
        if confirmation not in ['yes', 'y']:
            print("Please configure the correct AWS account and try again.")
            exit(1)
        print("AWS credentials are configured correctly.")
    except Exception as e:
        print(f"Error: {e}")
        print("Please run 'aws configure' to set up your credentials.")
        exit(1)

def set_aws_region():
    while True:
        region = input("Please enter the AWS region to use (e.g., us-west-2): ").strip()
        if region in VALID_AWS_REGIONS:
            os.environ['AWS_DEFAULT_REGION'] = region
            os.environ['AWS_REGION'] = region
            try:
                subprocess.run(["aws", "configure", "set", "region", region], check=True)
                print(f"AWS region set to {region}.")
                return region
            except subprocess.CalledProcessError as e:
                print(f"Error setting AWS region: {e}")
        else:
            print("Invalid AWS region. Please enter a valid AWS region.")

def get_available_vpcs():
    ec2_client = boto3.client('ec2')
    response = ec2_client.describe_vpcs()
    vpcs = response['Vpcs']
    return vpcs

def get_available_subnets(vpc_id):
    ec2_client = boto3.client('ec2')
    response = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    subnets = response['Subnets']
    return subnets

def select_vpc():
    vpcs = get_available_vpcs()
    print("Available VPCs:")
    for index, vpc in enumerate(vpcs, start=1):
        print(f"{index}. VPC ID: {vpc['VpcId']}")
    
    vpc_index = int(input("Choose VPC (enter number): ")) - 1
    return vpcs[vpc_index]['VpcId']

def gather_parameters(region):
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

def deploy_cdk_stack(params):
    print("Deploying the CDK stack... Please wait")

    os.environ['VPCID'] = params['VPCID']
    os.environ['AWSRegion'] = params['AWSRegion']
    os.environ['SubnetIDs'] = ','.join(params['SubnetIDs'])

    cdk_params = f"--parameters AWSRegion={params['AWSRegion']} " \
                 f"--parameters VPCID={params['VPCID']} " \
                 f"--parameters SubnetIDs={','.join(params['SubnetIDs'])}" \
                 " --require-approval never"

    try:
        result = subprocess.run(f"cdk deploy {cdk_params} 2>&1", shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)

        if result.returncode == 0:
            print("CDK stack deployed successfully.")
        else:
            print("CDK stack deployment failed.")
        
        return result.stdout

    except subprocess.CalledProcessError as e:
        print(f"CDK deployment error: {e}")
        print(e.stderr)

        return None

def extract_outputs(deploy_output):
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
        result = subprocess.run(["python", script_name, *args], capture_output=True, text=True, check=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Script execution error: {e}")

if __name__ == "__main__":
    aws_sign_in()
    region = set_aws_region()

    while True:
        action = input("Would you like to create or destroy a workshop? (create/destroy): ").strip().lower()
        if action in ['create', 'destroy']:
            break
        else:
            print("Invalid action. Please enter 'create' or 'destroy'.")

    if action == 'create':
        parameters = gather_parameters(region)
        num_users = input("Enter the number of users to create: ").strip()
        deploy_output = deploy_cdk_stack(parameters)

        if deploy_output:
            cognito_domain_id, sagemaker_id, hosted_uri = extract_outputs(deploy_output)
            if cognito_domain_id and sagemaker_id and hosted_uri:
                print("Creating Cognito Users...")
                execute_script('create_cognito_users.py', num_users, cognito_domain_id, sagemaker_id, hosted_uri, region)
                print("Created Cognito Users")
                print("Creating Sagemaker Profiles...")
                execute_script('create_sagemaker_profiles.py', region)
                print("Created Sagemaker Users")
                print('View users.csv file for sign in information')
            else:
                print("Failed to extract Cognito Domain ID and/or SageMaker ID from the CDK deploy output.")
        else:
            print("CDK deployment failed. Exiting.")

    if action == 'destroy':
        print('Deleting spaces...')
        execute_script('delete_spaces.py', region)
        print('Deleted spaces')
        print('Deleting Sagemaker Users...')
        execute_script('delete_sagemaker_profiles.py', region)
        print('Deleted Sagemaker Users')
        print('Deleting Cognito Users...')
        execute_script('delete_cognito_users.py', region)
        print('Deleted Cognito Users')
        
        try:
            subprocess.run(["cdk", "destroy", "--force"], check=True, capture_output=True, text=True)
            print('Fully deleted workshop')
        except subprocess.CalledProcessError as e:
            print(f"Error destroying CDK stack: {e}")
