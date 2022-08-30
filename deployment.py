from aws_cdk import Stage, Stack, Tags, Environment
from constructs import Construct

from network.infrastructure import Network
from database.infrastructure import Database
from api.infrastructure import API
from compute.infrastructure import Compute


class LambdaURL(Stage):
    def __init__(self, scope: Construct, id_: str, env: Environment, tags: dict, **kwargs) -> None:
        super().__init__(scope, id_, **kwargs)
        """
        Stateful  : The resources that are going to lose the data, if it is deleted, or persistent infrastructure like a VPC
        Stateless : The resources that are not going to lose the data, even if it is deleted.
        """

        stateful = Stack(self, "Stateful", env=env)
        for k, v in tags.items():
            Tags.of(stateful).add(k, v)

        cidr = "172.50.0.0/16"
        vpc = Network(
            stateful,
            "VPC",
            cidr=cidr
        )

        Database(
            stateful,
            "DynamoDB"
        )

        stateless = Stack(self, "Stateless", env=env)
        for k, v in tags.items():
            Tags.of(stateless).add(k, v)

        api = API(
            stateless,
            "LambdaFunc",
            vpc=vpc.vpc
        )

        Compute(
            stateless,
            "EC2",
            vpc=vpc.vpc,
            lambda_url=api.func_url.url
        )


