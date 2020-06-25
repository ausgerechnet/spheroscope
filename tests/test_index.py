def test_index(client, auth):
    response = client.get("/")
    print(response.data)

    auth.login()
    response = client.get("/")
    print(response.data)
