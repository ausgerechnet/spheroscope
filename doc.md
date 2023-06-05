# short implementation documentation

## modules

### auth.py

- load_logged_in_user()
- @login_required

- /register (GET, POST) → register()
- /login (GET, POST) → login()
- /logout (GET) → logout()

### database.py

- User
- WordList
- Macro
- Query
- Pattern
- Corpus

- init_db()
- read_patterns(path)
- import_library()

- CLI: init-db → init_db_command()
- CLI: import-lib → import_lib_command()

### corpora.py

- load_default()
- read_config(cwb_id, init)
- init_corpus(corpus_config)

- / (GET, POST) → choose()
- /<cwb_id> (GET, POST) → corpus_config(cwb_id)

### macros.py

- get_frequencies(cwb_id, macro)
- get_defined_macros(cwb_id)

- / (GET) → index()
- /<int:id>/delete (POST) → delete_cmd(id)
- /create (GET, POST) → create()
- /<int:id>/update (GET, POST) → update(id)
- /<int:id>/frequencies (GET) → frequencies(id)

### wordlists.py

- get_frequencies(cwb_id, words, p_att)
- get_similar_ones(cwb_id, words, p_att, number)

- / (GET) → index()
- /<int:id>/delete (POST) → delete_cmd(id)
- /create (GET, POST) → create()
- /<int:id>/update (GET, POST) → update()
- /<int:id>/frequencies (GET) → frequencies(id)
- /<int:id>/similar (GET) → similar(id)

### queries.py

- query_corpus(query, cwb_id)
- patch_query_result(result)
- add_gold(result, cwb_id, pattern)

- / (GET) → index()
- /create (GET, POST) → create()
- /<int:id>/update (GET, POST) → update(id)
- /<int:id>/delete (POST) → delete_cmd(id)
- /<int:id>/run (GET, POST) → run_cmd(id)

- CLI: query → query_command(pattern, dir_out, cwb_id)

### patterns.py

- run_queries(corpus_config, queries, slot)

- / (GET) → index()
- /api → patterns()
- /<int(signed=True):id> (GET, POST) → pattern(id)
- /<int:id>/subquery (GET, POST) → run_subquery(id)

### remote.py

#### methods
- connect(port)
- get_tables(con)
- get_gold(con)
- get_patterns(con)
- set_query_results(con)

#### CLI
- push_results
