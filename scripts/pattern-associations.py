from ccc import Corpus
from ccc.discoursemes import textual_associations
from pandas import read_csv, DataFrame
from glob import glob

corpus_name = "BREXIT_V20190522_DEDUP"

# all tweets
c = Corpus(corpus_name)
tweets = c.query_s_att("tweet_id")
tweets = tweets.df[['tweet_id']].set_index('tweet_id')
N = len(tweets)

# query results
paths = glob("instance/%s/results/*.tsv" % corpus_name)
for p in paths:

    if p.endswith("summary.tsv"):
        continue
    n = p.split("/")[-1].split(".")[0]
    print(n)

    d = read_csv(p, sep="\t")

    if len(d) > 0:
        d = d[['tweet_id']].drop_duplicates().set_index('tweet_id')
        d[n] = True

    tweets = tweets.join(d).fillna(False)


print("calculating tables")
tables = DataFrame()
for name in tweets.columns:
    table = round(textual_associations(tweets, N, name).reset_index(), 2)
    table['node'] = name
    tables = tables.append(table)

# post-process
tables = tables[
    ['node', 'candidate'] +
    [d for d in tables.columns if d not in ['node', 'candidate']]
]
tables = tables.reset_index().drop('index', axis=1).sort_values(
    by=['node', 'candidate']
)

# save
tables.to_csv("instance/%s/query-association.tsv" % corpus_name, sep="\t")
