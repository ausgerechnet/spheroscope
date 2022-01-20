import pytest


@pytest.mark.now
def test_matches(client, auth):

    auth.login()

    with client:

        client.get("/")         # initialize session

        pattern = 3
        response = client.get(
            "https://localhost/patterns/{pattern}/matches".format(
                pattern=pattern
            )
        )
        print(response)


def test_hierarchy_3_1_5(client, auth):

    auth.login()

    with client:

        client.get("/")         # initialize session

        # base = desire, slot = formula, slot_pattern = possibility
        base_pattern = 3
        slot = 1
        slot_pattern = 5

        response = client.get(
            "https://localhost/patterns/{base_pattern}/matches/"
            "subquery?slot={slot}&slot_pattern={slot_pattern}".format(
                base_pattern=base_pattern, slot=slot, slot_pattern=slot_pattern
            )
        )
        print(response)


def test_hierarchy_0_1_3(client, auth):

    auth.login()

    with client:

        client.get("/")         # initialize session

        # http://127.0.0.1:5000/patterns/0/matches/subquery?slot=1&slot_pattern=3
        # base = quotation, slot = formula, slot_pattern = desire
        base_pattern = 0
        slot = 1
        slot_pattern = 3

        response = client.get(
            "https://localhost/patterns/{base_pattern}/matches/"
            "subquery?slot={slot}&slot_pattern={slot_pattern}".format(
                base_pattern=base_pattern, slot=slot, slot_pattern=slot_pattern
            )
        )
        print(response)


def test_hierarchy_3_0_24(client, auth):

    auth.login()

    with client:

        client.get("/")         # initialize session

        # http://127.0.0.1:5000/patterns/3/matches/subquery?slot=0&slot_pattern=24
        # base = desire, slot = entity, slot_pattern = membership
        base_pattern = 3
        slot = 0
        slot_pattern = 24

        response = client.get(
            "https://localhost/patterns/{base_pattern}/matches/"
            "subquery?slot={slot}&slot_pattern={slot_pattern}".format(
                base_pattern=base_pattern, slot=slot, slot_pattern=slot_pattern
            )
        )
        print(response)
