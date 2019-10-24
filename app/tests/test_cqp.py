import pytest
from spheroscope.cqp import CWBEngine
from spheroscope.cqp import load_macro


REGISTRY_PATH = '/usr/local/cwb-3.4.16/share/cwb/registry/'


t = {
    'items1': ['mother', 'father'],

    'corpus_settings': {
        'name': 'BREXIT_V20190522',
        'registry_path': REGISTRY_PATH
    },

    'analysis_settings': {
        'p_query': 'lemma',
        's_break': 'tweet',
        'max_window_size': 10
    },

    'concordance_settings': {
        'order': 'random',
        'cut_off': 10
    },

    'collocate_settings': {
        'order': 'random',
        'cut_off': 10
    }
}


@pytest.mark.cwb
def test_CWB_df_node():
    engine = CWBEngine(t['corpus_settings'])
    df_node = engine.prepare_df_node(
        t['analysis_settings']['p_query'],
        t['analysis_settings']['s_break'],
        t['items1']
    )
    # print(df_node)
    assert len(df_node) > 1


@pytest.mark.cwb
def test_CWB_lexicalize_positions():

    engine = CWBEngine(t['corpus_settings'])
    tokens = engine.lexicalize_positions([501, 502])
    lemmas = engine.lexicalize_positions([501, 502],
                                         t['analysis_settings']['p_query'])
    assert tokens == ['be', 'trusted'] and lemmas == ['be', 'trust']


@pytest.mark.macros
def test_load_macro():
    t = load_macro("x_will_y_if_brexit.txt")
    print(t)
