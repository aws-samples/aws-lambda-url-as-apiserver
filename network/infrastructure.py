from aws_cdk import (
    aws_ec2 as ec2,
)
from constructs import Construct


class Network(Construct):

    def __init__(self, scope: Construct, id_: str, cidr: str) -> None:
        super().__init__(scope, id_)

        self.vpc = ec2.Vpc(
            self,
            "VPC",
            max_azs=2,
            cidr=cidr,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                    name="Private",
                    cidr_mask=24
                )
            ],
            nat_gateways=2,
        )

        # VPC Endpoint for DynamoDB
        self.vpc.add_gateway_endpoint(
            "DynamoDbVPCEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB
        )
