#! /usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser

from pandas import read_csv


def main(path_in, path_out):

    df = read_csv(path_in, sep="\t")[['tweet_id', 'query']]
    df = df.drop_duplicates()

    df.to_csv(path_out, sep="\t", index=False)


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('pattern', type=int)
    parser.add_argument("--corpus_name", default="BREXIT_V20190522_DEDUP")
    args = parser.parse_args()

    path_in = "instance/%s/query-results/pattern%d.tsv.gz" % (args.corpus_name, args.pattern)
    path_out = "library/%s/query-results/pattern%d.tsv" % (args.corpus_name, args.pattern)

    main(path_in, path_out)
