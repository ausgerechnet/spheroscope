library(tidyverse)

pattern_ <- '3'

random1000 <- read_tsv(
  "library/BREXIT-2016-RAND/gold/tweetsets.tsv", 
  col_types = cols(.default = 'c')
  ) %>% 
  filter(set_name == 'random1000') %>% 
  rename(tweet_id = tweets)

matches <- read_tsv(
  paste0("instance/BREXIT-2016-RAND/query-results/pattern", pattern_, ".tsv.gz"),
  col_types = cols(.default = 'c')
  )

gold <- read_tsv(
  "library/BREXIT-2016-RAND/gold/adjudicated.tsv",
  col_types = cols(.default = 'c')
  ) %>% 
  filter(pattern == pattern_) %>% 
  rename(tweet_id = tweet) %>% 
  mutate(tweet_id = str_sub(tweet_id, 2)) %>% 
  select(- c("...1", "pattern"))

d <- random1000 %>%
  left_join(gold, by = 'tweet_id') %>% 
  left_join(matches, by = 'tweet_id', relationship = "many-to-many")

d %>% filter(annotation == "True") %>%
  print(n = 100)
