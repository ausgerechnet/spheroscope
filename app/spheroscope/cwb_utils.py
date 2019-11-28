from collections import defaultdict
from ccc.concordances import df_anchor_to_concordance
from ccc.cwb import CWBEngine


corpus_settings = {
    'name': 'BREXIT_V20190522',
    'registry_path': '/home/ausgerechnet/corpora/cwb/registry',
    'lib_path': '/home/ausgerechnet/projects/spheroscope/app/instance/lib'
}

concordance_settings = {
    'order': 'first',
    'cut_off': None,
    'p_query': 'lemma',
    's_break': 'tweet',
    'match_strategy': 'longest'
}


def apply_correction(row, correction):
    value, lower_bound, upper_bound = row
    value += correction
    if value < lower_bound or value > upper_bound:
        value = -1
    return value


def apply_corrections(df_anchor, anchors):
    corrections = list()
    for anchor in anchors:
        if anchor[1] != 0:
            anchors.append((anchor[0], anchor[1]))
    for correction in corrections:
        if correction[0] in df_anchor.columns:
            df_anchor[correction[0]] = df_anchor[
                [correction[0], 's_start', 's_end']
            ].apply(lambda x: apply_correction(x, correction[1]), axis=1)
    return df_anchor


def anchor_query(query, anchors, regions):

    engine = CWBEngine(corpus_settings)
    engine.read_lib(corpus_settings['lib_path'])

    df_anchor = engine.df_anchor_from_query(
        query,
        s_break=concordance_settings['s_break'],
        match_strategy=concordance_settings['match_strategy']
    )

    out = dict()

    # fill for each concordance line
    out['concordance'] = dict()

    # fill for each anchor / region
    out['anchor_words'] = defaultdict(list)
    out['regions_words'] = defaultdict(list)

    # if query is empty
    if df_anchor.empty:
        out['nr_matches'] = 0
        return out

    # retrieve concordance
    df_anchor = apply_corrections(df_anchor, anchors)
    concordance = df_anchor_to_concordance(engine, df_anchor)
    out['nr_matches'] = len(concordance)

    # loop through concordances
    for key in concordance.keys():

        # fill concordance line
        out['concordance'][key] = concordance[key].to_dict()

        # fill anchor words
        for row in concordance[key].iterrows():
            if len(row[1]['role']) > 0:
                for role in row[1]['role']:
                    out['anchor_words'][str(role)].append(row[1]['word'])

        # fill region words
        for region in regions:
            r = list()
            append = False
            for row in concordance[key].iterrows():
                if region[0] in row[1]['role']:
                    append = True
                if append:
                    r.append(row[1]['word'])
                if region[1] in row[1]['role']:
                    append = False
                    out['regions_words'][str(region)].append(r)

    return out
