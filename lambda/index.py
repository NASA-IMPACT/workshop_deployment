import json
import logging
import os
import requests
import boto3
import base64

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CLIENT_ID = os.environ['CLIENT_ID']
REDIRECT_URI = os.environ['REDIRECT_URI']
TOKEN_ENDPOINT = f"https://{os.environ['COGNITO_DOMAIN']}/oauth2/token"
IDENTITY_POOL_ID = os.environ['IDENTITY_POOL_ID']
CUSTOM_AWS_REGION = os.environ['CUSTOM_AWS_REGION']
STUDIO_DOMAIN_ID = os.environ['STUDIO_DOMAIN_ID']
USER_POOL_ID = os.environ['USER_POOL_ID']

def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event, indent=2))

    try:
        # Get the authorization code from the query parameters
        query_params = event.get('queryStringParameters', {})
        code = query_params.get('code')

        if not code:
            logger.error("Authorization code missing")
            return {
                'statusCode': 400,
                'body': 'Authorization code missing'
            }

        # Exchange the authorization code for tokens
        payload = {
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'code': code,
            'redirect_uri': REDIRECT_URI
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(TOKEN_ENDPOINT, data=payload, headers=headers)
        if response.status_code != 200:
            logger.error("Error exchanging authorization code for tokens: %s", response.text)
            return {
                'statusCode': 500,
                'body': f"Error exchanging authorization code for tokens: {response.text}"
            }

        tokens = response.json()
        logger.info("Tokens: %s", tokens)

        # Extract the ID token
        id_token = tokens.get('id_token')
        if not id_token:
            return {
                'statusCode': 500,
                'body': 'ID token not found in the response'
            }

        # Decode the ID token to extract the username
        token_parts = id_token.split('.')
        payload_part = token_parts[1]
        payload_part += '=' * (4 - len(payload_part) % 4)  # Padding for base64 decoding
        user_info = json.loads(base64.urlsafe_b64decode(payload_part).decode('utf-8'))
        username = user_info.get('cognito:username', user_info.get('email', 'default_username'))

        # Get temporary AWS credentials from the Cognito Identity Pool
        credentials = get_aws_credentials(id_token)
        if not credentials:
            return {
                'statusCode': 500,
                'body': 'Failed to get AWS credentials'
            }

        # Generate the presigned URL for SageMaker Studio
        presigned_url = generate_presigned_domain_url(CUSTOM_AWS_REGION, STUDIO_DOMAIN_ID, username)

        if not presigned_url:
            return {
                'statusCode': 500,
                'body': 'Failed to generate presigned URL'
            }

        return {
            'statusCode': 302,
            'headers': {
                'Location': presigned_url
            },
            'body': f'Redirecting to {presigned_url} now...'
        }

    except Exception as e:
        logger.error("An error occurred: %s", str(e))
        return {
            'statusCode': 500,
            'body': f"Internal server error: {str(e)}"
        }

def get_aws_credentials(id_token):
    client = boto3.client('cognito-identity', region_name=CUSTOM_AWS_REGION)
    try:
        identity_response = client.get_id(
            IdentityPoolId=IDENTITY_POOL_ID,
            Logins={
                f'cognito-idp.{CUSTOM_AWS_REGION}.amazonaws.com/{USER_POOL_ID}': id_token
            }
        )
        identity_id = identity_response['IdentityId']
        
        credentials_response = client.get_credentials_for_identity(
            IdentityId=identity_id,
            Logins={
                f'cognito-idp.{CUSTOM_AWS_REGION}.amazonaws.com/{USER_POOL_ID}': id_token
            }
        )
        return credentials_response['Credentials']
    except Exception as e:
        logger.error("Failed to get AWS credentials: %s", str(e))
        return None

def generate_presigned_domain_url(region_name, domain_id, user_profile_name, expiration=3600):
    """
    Generate a presigned URL for AWS SageMaker Studio domain access.

    Parameters:
    - region_name: AWS region name (e.g., 'us-west-2').
    - domain_id: The ID of the SageMaker Studio domain.
    - user_profile_name: The name of the user profile.
    - expiration: Expiration time in seconds for the presigned URL (default: 3600 seconds).

    Returns:
    - Presigned URL as a string.
    """
    sagemaker_client = boto3.client('sagemaker', region_name=region_name)
    
    try:
        response = sagemaker_client.create_presigned_domain_url(
            DomainId=domain_id,
            UserProfileName=user_profile_name,
            SessionExpirationDurationInSeconds=expiration
        )
        return response['AuthorizedUrl']
    except boto3.exceptions.Boto3Error as e:
        logger.error(f"Error generating presigned URL: {e}")
        return None
