from spheroscope.corpora import read_config


def test_read_config(app):
    path = "instance/corpus_defaults.yaml"
    t = read_config(path)
    from pprint import pprint
    pprint(t)
