def test_hierarchy(client, auth):

    base_pattern = 3
    slot = 1
    slot_pattern = 5

    auth.login()
    with client:
        client.get("/")         # initialize session
        response = client.get(
            "https://localhost/patterns/{base_pattern}/"
            "subquery?slot={slot}&slot_pattern={slot_pattern}".format(
                base_pattern=base_pattern, slot=slot, slot_pattern=slot_pattern
            )
        )

    print(response)
