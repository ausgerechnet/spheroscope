from spheroscope.macros import (delete, lib2db, read_from_db, read_from_path,
                                write)


def test_read():
    path = (
        "/home/ausgerechnet/repositories/spheroscope/library/"
        "BREXIT_V20190522_DEDUP/macros/macro_prepositional_np.txt"
    )
    macro = read_from_path(path)
    print(macro)


def test_write(app):

    user_id = 1
    path = (
        "/home/ausgerechnet/repositories/spheroscope/library/"
        "BREXIT_V20190522_DEDUP/macros/macro_prepositional_np.txt"
    )
    macro = read_from_path(path)
    macro['user_id'] = user_id
    with app.app_context():
        write(macro)


def test_read_from_db_all(app):

    user_id = 1
    path = (
        "/home/ausgerechnet/repositories/spheroscope/library/"
        "BREXIT_V20190522_DEDUP/macros/macro_prepositional_np.txt"
    )
    macro = read_from_path(path)
    macro['user_id'] = user_id
    with app.app_context():
        write(macro)
        macros = read_from_db()

    print(macros)


def test_read_from_db_one(app):

    user_id = 1
    path = (
        "/home/ausgerechnet/repositories/spheroscope/library/"
        "BREXIT_V20190522_DEDUP/macros/macro_prepositional_np.txt"
    )
    macro = read_from_path(path)
    macro['user_id'] = user_id
    with app.app_context():
        write(macro)
        macros = read_from_db([1])

    print(macros)


def test_delete(app):

    user_id = 1
    path = (
        "/home/ausgerechnet/repositories/spheroscope/library/"
        "BREXIT_V20190522_DEDUP/macros/macro_prepositional_np.txt"
    )
    macro = read_from_path(path)
    macro['user_id'] = user_id
    with app.app_context():
        write(macro)
        delete(1)


def test_lib2db(app):
    with app.app_context():
        lib2db()
        macros = read_from_db()
    print(macros)
