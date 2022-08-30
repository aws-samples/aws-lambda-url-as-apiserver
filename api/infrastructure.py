from aws_cdk import (
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_ec2 as ec2,
)
from constructs import Construct


class API(Construct):

    def __init__(self, scope: Construct, id_: str, vpc: ec2.Vpc) -> None:
        super().__init__(scope, id_)

        role = iam.Role(
            self,
            "LambdaURLRole",
            role_name="LambdaURLRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
            ],
            inline_policies={
                "DynamoDBReadWrite": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:PutItem",
                                "dynamodb:Scan"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )

        sg = ec2.SecurityGroup(
            self,
            "SecurityGroup",
            vpc=vpc,
            description="Security Group for Lambda URL",
            security_group_name="LambdaURLSG"
        )

        func = lambda_.Function(
            self,
            "LambdaURLAPIServer",
            function_name="LambdaURLAPIServer",
            handler="lambda_function.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("api/runtime"),
            timeout=Duration.seconds(10),
            role=role,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
            ),
            security_groups=[sg],
            memory_size=128,
        )

        self.func_url = func.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.NONE,
            cors=lambda_.FunctionUrlCorsOptions(
                allowed_origins=["*"],
                allowed_methods=[lambda_.HttpMethod.GET, lambda_.HttpMethod.POST],
            )
        )
