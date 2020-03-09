import pandas as pd
from collections import Counter


def format_query_result(query_result):

    # init result
    result = dict()
    result['query'] = query_result['query']
    result['pattern'] = query_result['pattern']
    result['nr_matches'] = query_result['result']['nr_matches']

    # format anchors
    anchors = pd.DataFrame(query_result['anchors'])
    if not anchors.empty:
        anchors.columns = ['number', 'correction', 'hole', 'clear name']
        result['anchors'] = anchors.to_html(escape=False, index=False)
    else:
        result['anchors'] = None

    # format regions
    regions = pd.DataFrame(query_result['regions'])
    if not regions.empty:
        regions.columns = ['start', 'end', 'hole', 'clear name']
        result['regions'] = regions.to_html(escape=False, index=False)
    else:
        result['regions'] = None

    # matches
    result['matches'] = list()

    for match in query_result['result']['matches']:

        df_dict = match.pop('df')
        df_dict.pop('offset')

        # format anchor column
        df = pd.DataFrame(df_dict, dtype=str)
        df.fillna(-1, inplace=True)
        df['anchor'] = df['anchor'].apply(pd.to_numeric, downcast='integer')
        df = df.replace(-1, "")

        match['df'] = df.to_html(
            escape=False, index_names='cpos', bold_rows=False
        )

        result['matches'].append(match)

    # frequency count of holes
    counts = dict()
    for key in query_result['result']['holes'].keys():
        df = pd.DataFrame.from_dict(
            Counter(query_result['result']['holes'][key]), orient='index'
        ).sort_values(by=0, ascending=False)
        df.columns = ['freq']
        df.index.name = key
        counts[key] = df.to_html(escape=False, index_names=True, bold_rows=False)
    result['holes'] = counts

    # return
    return result
