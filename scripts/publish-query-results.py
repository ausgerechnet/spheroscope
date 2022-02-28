from glob import glob
from pandas import read_csv, DataFrame, concat
from argparse import ArgumentParser


def main(glob_in):

    paths = glob(glob_in)
    results = list()
    for p in paths:
        query = p.split("/")[-1].split(".")[0]
        df = read_csv(p, sep="\t")
        df = DataFrame(
            index=list(set(df['tweet_id'])),
            data={'query': query}
        )
        results.append(df)
    df = concat(results)
    df.index.name = 'tweet_id'

    return df


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('pattern',
                        type=str)
    args = parser.parse_args()

    glob_in = (
        "instance/BREXIT_V20190522_DEDUP/results/"
        "pattern%s_*.tsv" % args.pattern
    )

    df = main(glob_in)

    df.to_csv(
        'library/BREXIT_V20190522_DEDUP/query-results/'
        'pattern%s-query-results.tsv' % args.pattern, sep="\t"
    )
