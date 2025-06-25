from handler import missing_trees

def test_missing_trees():
    response = missing_trees({}, {})
    assert response['statusCode'] == 200
    assert response['body'] == "Hello from Serverless Python!"
