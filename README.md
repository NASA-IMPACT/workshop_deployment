# Welcome to the Workshop Deployment Tool

This tool facilitates the deployment of a Sagemaker workshop with a specified number of users.

## Prerequisites
- Ensure the AWS CLI is installed on your local machine.

## Deployment Steps
1. Run `python ./workshop_builder.py`.
2. Ensure you are signed into your desired AWS account.
3. Enter the AWS region where you want to deploy.
4. Type `create` to initiate the workshop creation process.
5. Choose the VPC where you want to deploy the Sagemaker Domain.
6. Select the subnets for the Sagemaker Domain deployment.
7. Specify the number of workshop users to create.
8. Allow time for the deployment to finish. Details, including sign-in URL and user credentials, will be saved to a `users.csv` file.

## User Sign-In Steps
1. Access the hosted URI provided in the `users.csv` file.
2. Use the username and password from the `users.csv` file to log in.
3. Users will be redirected to the Sagemaker console for workshop access.
