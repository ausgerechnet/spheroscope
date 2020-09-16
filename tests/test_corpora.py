from spheroscope.corpora import read_config2


def test_read_config():
    path = "instance/corpus_defaults.yaml"
    t = read_config2(path)
    from pprint import pprint
    pprint(t)
