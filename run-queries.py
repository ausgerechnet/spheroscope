from ccc import Corpus
from ccc.queries import cqpy_load, run_query
from glob import glob
import re
import os

corpus_name = "BREXIT_V20190522_DEDUP"

lib_path = os.path.join("library", corpus_name)
corpus = Corpus(corpus_name, lib_path=lib_path)
paths = glob(os.path.join("library", corpus_name, "queries", "*.cqpy"))
paths = [p for p in paths if re.search(r"pattern\d", p)]

dir_out = os.path.join("instance", corpus_name, "queries_matches")


for p in paths:
    print(p)
    query = cqpy_load(p)
    query['query'] = {
        'match_strategy': 'longest',
        's_context': 'tweet',
        's_query': 'tweet',
        'context': None
    }
    query['display'] = {
        'p_show': ['word', 'lemma'],
        'p_slots': 'lemma',
        'p_text': 'word',
        's_show': ['tweet_id']
    }
    corrections_int = dict()
    for k in query['anchors']['corrections'].keys():
        c = query['anchors']['corrections'][k]
        corrections_int[int(k)] = c
    query['anchors']['corrections'] = corrections_int
    dump = run_query(corpus, query)
    try:
        dump = dump.drop('df', axis=1)
        p_out = os.path.join(dir_out, query['meta']['name'] + '.tsv')
        dump.to_csv(p_out, sep="\t")
    except:
        print('error in %s' % p)
