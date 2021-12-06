from glob import glob
from pandas import read_csv, DataFrame, concat


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
    glob_in = (
        "instance/BREXIT_V20190522_DEDUP/results/"
        "pattern3_*.tsv"
    )
    df = main(glob_in)
    df.to_csv(
        'library/BREXIT_V20190522_DEDUP/gold/'
        'pattern3-query-results.tsv', sep="\t"
    )
