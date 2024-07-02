from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigatewayv2,
    aws_apigatewayv2_integrations as apigatewayv2_integrations,
    aws_cognito as cognito,
    aws_iam as iam,
    CfnParameter,
    CfnOutput,
    App,
    Duration
)
from constructs import Construct

class WorkshopDeploymentStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Parameters
        region_param = CfnParameter(self, "AWSRegion",
                                    type="String",
                                    description="The AWS region for the resources")

        # Lambda Layer
        requests_layer = _lambda.LayerVersion(self, "RequestsLayer",
                                              code=_lambda.Code.from_asset("lambda_layer/requests_layer.zip"),
                                              compatible_runtimes=[_lambda.Runtime.PYTHON_3_8],
                                              description="A layer for requests library")

        # HTTP API Gateway
        api = apigatewayv2.HttpApi(self, "LambdaApi",
                                   api_name="Lambda API Gateway")

        # Cognito User Pool
        user_pool = cognito.UserPool(self, "UserPool",
                                     self_sign_up_enabled=False,
                                     sign_in_aliases=cognito.SignInAliases(username=True))

        # Generate a unique domain prefix
        user_pool_domain_prefix = f"myapp-{self.stack_name.lower()}"

        # Cognito User Pool Domain
        user_pool_domain = cognito.UserPoolDomain(self, "UserPoolDomain",
                                                  user_pool=user_pool,
                                                  cognito_domain=cognito.CognitoDomainOptions(
                                                      domain_prefix=user_pool_domain_prefix  # Unique domain prefix
                                                  ))

        # Cognito User Pool Client
        user_pool_client = cognito.UserPoolClient(self, "UserPoolClient",
                                                  user_pool=user_pool,
                                                  generate_secret=False,
                                                  o_auth=cognito.OAuthSettings(
                                                      flows=cognito.OAuthFlows(
                                                          authorization_code_grant=True
                                                      ),
                                                      callback_urls=[f"{api.url}invoke"]
                                                  ))

        # Identity Pool
        identity_pool = cognito.CfnIdentityPool(self, "IdentityPool",
                                                allow_unauthenticated_identities=False,
                                                cognito_identity_providers=[
                                                    cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                                                        client_id=user_pool_client.user_pool_client_id,
                                                        provider_name=user_pool.user_pool_provider_name
                                                    )
                                                ])

        # Role for authenticated users
        authenticated_role = iam.Role(self, "CognitoDefaultAuthenticatedRole",
                                      assumed_by=iam.FederatedPrincipal("cognito-identity.amazonaws.com",
                                                                        {
                                                                            "StringEquals": {
                                                                                "cognito-identity.amazonaws.com:aud": identity_pool.ref
                                                                            },
                                                                            "ForAnyValue:StringLike": {
                                                                                "cognito-identity.amazonaws.com:amr": "authenticated"
                                                                            }
                                                                        },
                                                                        "sts:AssumeRoleWithWebIdentity"))

        # Attach policies to the role
        authenticated_role.add_to_policy(iam.PolicyStatement(
            actions=["sagemaker:CreatePresignedDomainUrl"],
            resources=["*"]
        ))

        # Attach the role to the Identity Pool
        cognito.CfnIdentityPoolRoleAttachment(self, "IdentityPoolRoleAttachment",
                                              identity_pool_id=identity_pool.ref,
                                              roles={"authenticated": authenticated_role.role_arn})

        # Lambda Function
        lambda_redirect = _lambda.Function(self, "LambdaRedirect",
                                           runtime=_lambda.Runtime.PYTHON_3_8,
                                           handler="index.lambda_handler",
                                           code=_lambda.Code.from_asset("lambda"),
                                           layers=[requests_layer],
                                           timeout=Duration.seconds(10),
                                           environment={
                                               'CLIENT_ID': user_pool_client.user_pool_client_id,
                                               'COGNITO_DOMAIN': f"{user_pool_domain_prefix}.auth.{region_param.value_as_string}.amazoncognito.com",
                                               'IDENTITY_POOL_ID': identity_pool.ref,
                                               'CUSTOM_AWS_REGION': region_param.value_as_string,
                                               'STUDIO_DOMAIN_ID': 'd-qia0xknhnmu5',  # Update if needed
                                               'USER_POOL_ID': user_pool.user_pool_id,
                                               'REDIRECT_URI': f"{api.url}invoke",
                                           })

        # Add necessary IAM policy statement to the Lambda role
        lambda_redirect.add_to_role_policy(iam.PolicyStatement(
            actions=["sagemaker:CreatePresignedDomainUrl"],
            resources=["*"]
        ))

        # Output the Lambda function ARN
        CfnOutput(self, "LambdaFunctionArn", value=lambda_redirect.function_arn)

        # Integration of API Gateway with Lambda function
        lambda_integration = apigatewayv2_integrations.HttpLambdaIntegration("LambdaIntegration", lambda_redirect)

        # Adding a default route to the API Gateway that integrates with Lambda
        api.add_routes(
            path="/invoke",
            methods=[apigatewayv2.HttpMethod.ANY],
            integration=lambda_integration
        )

        # Output the API endpoint URL
        CfnOutput(self, "ApiEndpoint", value=api.url)

        # Construct the hosted UI URL
        hosted_ui_url = f"https://{user_pool_domain_prefix}.auth.{region_param.value_as_string}.amazoncognito.com/login?client_id={user_pool_client.user_pool_client_id}&response_type=code&scope=aws.cognito.signin.user.admin+openid+profile&redirect_uri={api.url}invoke"

        # Output the Hosted UI URL
        CfnOutput(self, "HostedUIUrl", value=hosted_ui_url)


app = App()
WorkshopDeploymentStack(app, "WorkshopDeploymentStack")
app.synth()
