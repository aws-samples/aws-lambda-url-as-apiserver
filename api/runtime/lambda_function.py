import json
import boto3
import base64

from urllib.parse import parse_qsl

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Users")


def get_handler(event) -> dict:
    raw_path = event["rawPath"]

    if raw_path == "/sample":
        kwargs = {
            "ConsistentRead": True,
        }
        response = table.scan(**kwargs)
        print(response)
        body = response["Items"]
    else:
        body = {"msg": "This is GET method"}

    return body


def post_handler(event) -> dict:
    raw_path = event["rawPath"]
    decoded = base64.b64decode(event["body"])
    data = dict(parse_qsl(decoded.decode("UTF-8")))
    print(data)

    if raw_path == "/sample":
        new_item = {
            "name": data["name"],
            "location": data["location"]
        }
        table.put_item(
            Item=new_item
        )
        body = {"msg": "Data Inserted"}
    else:
        body = {"msg": "This is POST method"}

    return body


def lambda_handler(event, context):
    http_info = event["requestContext"]["http"]
    http_path = http_info["path"]
    http_method = http_info["method"]

    print(http_path, http_method)

    if http_method == "GET":
        status_code = 200
        body = get_handler(event)
    elif http_method == "POST":
        status_code = 200
        body = post_handler(event)
    else:
        status_code = 400
        body = {"msg": f"{http_method} is not allowed"}

    response = {
        "statusCode": status_code,
        "body": json.dumps(body)
    }

    return response
