def test_hierarchy(client, auth):

    auth.login()
    with client:

        client.get("/")         # initialize session

        # base = desire, slot = formula, slot_pattern = possibility
        base_pattern = 3
        slot = 1
        slot_pattern = 5
        response = client.get(
            "https://localhost/patterns/{base_pattern}/"
            "subquery?slot={slot}&slot_pattern={slot_pattern}".format(
                base_pattern=base_pattern, slot=slot, slot_pattern=slot_pattern
            )
        )
        print(response)

        # base = quotation, slot = formula, slot_pattern = desire
        base_pattern = 0
        slot = 1
        slot_pattern = 3
        response = client.get(
            "https://localhost/patterns/{base_pattern}/"
            "subquery?slot={slot}&slot_pattern={slot_pattern}".format(
                base_pattern=base_pattern, slot=slot, slot_pattern=slot_pattern
            )
        )
        print(response)

        # http://127.0.0.1:5000/patterns/3/subquery?slot=0&slot_pattern=24
        base_pattern = 3
        slot = 0
        slot_pattern = 24
        response = client.get(
            "https://localhost/patterns/{base_pattern}/"
            "subquery?slot={slot}&slot_pattern={slot_pattern}".format(
                base_pattern=base_pattern, slot=slot, slot_pattern=slot_pattern
            )
        )
        print(response)
