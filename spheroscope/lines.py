from ccc import Corpus


def get_lines():
    corpus = Corpus()
    result = corpus.query()
    concordance = corpus.concordance(result)
    lines = concordance.lines('extended')
    return lines


def show_line(one_line):
    corpus = Corpus()
    dump_line = DataFrame(index=one_line[['match', 'matchend']]
    concordance = corpus.concordance(one_line)
    line = concordance.lines(form='df')
    df = line['df']
    return df
