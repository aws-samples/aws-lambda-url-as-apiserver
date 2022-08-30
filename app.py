#!/usr/bin/env python3
import os
import aws_cdk as cdk

from deployment import LambdaURL

app = cdk.App()

LambdaURL(
    app,
    "LambdaURL",
    env=cdk.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"]),
    tags={"Owner": "lambda-url"}
)


app.synth()

