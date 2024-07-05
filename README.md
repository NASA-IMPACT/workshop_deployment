# Welcome to the Workshop Deployment Tool

This tool facilitates the deployment of a Sagemaker workshop with a specified number of users.

## Prerequisites
- Ensure the AWS CLI is installed on your local machine.

## Setting Up a Virtual Environment and Installing Requirements

Before running the deployment script, it's recommended to set up a virtual environment and install the necessary dependencies. Here are the steps:

### Setting Up a Virtual Environment

1. **Install `virtualenv` (if not already installed):**

2. **Create a virtual environment:**

Replace `venv` with your preferred name for the virtual environment.

3. **Activate the virtual environment:**
- On Windows:
  ```
  venv\Scripts\activate
  ```
- On macOS and Linux:
  ```
  source venv/bin/activate
  ```

### Installing Requirements

4. **Install dependencies from `requirements.txt`:**

## Deployment Steps

Once the virtual environment is set up and dependencies are installed, proceed with the deployment steps:

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
