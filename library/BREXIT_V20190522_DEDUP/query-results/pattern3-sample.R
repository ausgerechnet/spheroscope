library(tidyverse)

read_tsv("pattern3-query-results.tsv") %>%
  group_by(query) %>%
  sample_n(25) %>%
  print(n = 500) %>%
  write_tsv("pattern3-query-results-sample.tsv")
