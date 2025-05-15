# AWS SageMaker Workshop Deployment Tool

This tool automates the process of creating and destroying AWS workshops, including the setup of Cognito users, SageMaker profiles, and S3 buckets.

## Prerequisites

- Python 3.8 or higher
- Ensure you have the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) installed.
- AWS CDK installed
- Ensure that your AWS account has been bootstrapped for CDK. Run `cdk bootstrap`

## Installation

1. Clone this repository: `git clone <repository-url>` & `cd <repository-directory>`

2. Create and activate a virtual environment:

For macOS and Linux: `python3 -m venv venv` & `source venv/bin/activate`

For Windows: `python -m venv venv` & `.\venv\Scripts\activate`

3. Install the required Python packages: `pip install -r requirements.txt`

4. Ensure AWS CDK is installed and bootstrapped in your account: `npm install -g aws-cdk` & `cdk bootstrap`

## Usage

Ensure your virtual environment is activated, then run the main script: `python workshop_builder.py`

Follow the prompts to either create or destroy a workshop.

### Creating a Workshop

1. Sign in to your AWS account when prompted.
2. Select or confirm the AWS region.
3. Choose a VPC and subnet(s) for deployment.
4. Enter the number of users to create.
5. Provide a unique workshop name.

The script will:
- Deploy the CDK stack
- Create Cognito users
- Set up SageMaker profiles
- Create S3 buckets

A CSV file with user login information will be generated.

### Destroying a Workshop

1. Sign in to your AWS account when prompted.
2. Select or confirm the AWS region.
3. Choose the workshop to destroy from the list of existing workshops.

The script will:
- Delete SageMaker spaces
- Remove SageMaker user profiles
- Delete Cognito users
- Remove S3 buckets
- Destroy the CDK stack

## File Structure

- `workshop_builder.py`: Main script for creating/destroying workshops
- `create_cognito_users.py`: Script to create Cognito users
- `create_sagemaker_profiles.py`: Script to create SageMaker profiles
- `create_s3_buckets.py`: Script to create S3 buckets
- `delete_spaces.py`: Script to delete SageMaker spaces
- `delete_sagemaker_profiles.py`: Script to delete SageMaker profiles
- `delete_cognito_users.py`: Script to delete Cognito users
- `delete_s3_buckets.py`: Script to delete S3 buckets

## Notes

- Ensure you have the necessary AWS permissions to create and destroy resources.
- The tool will create a CSV file with user login information for each workshop.
- Be cautious when destroying workshops, as this action is irreversible.

## Troubleshooting

If you encounter any issues:
1. Ensure your AWS CLI is properly configured.
2. Check that you have the necessary permissions in your AWS account.
3. Verify that all dependencies are correctly installed.

For further assistance, please open an issue in the repository.