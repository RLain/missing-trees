def missing_trees(event, context):
    return {
        "statusCode": 200,
        "body": "Hello from Serverless Python!"
    }

if __name__ == "__main__":
    response = missing_trees({}, {})
    print(response)
