from glob import glob
from ccc.queries import load_query_json, cqpy_dump


paths = glob("library/BREXIT_V20190522_DEDUP/queries/*.query")


for p in paths:
    p_out = p.replace(".query", ".cqpy")
    query = load_query_json(p)
    print(p_out)
    with open(p_out, "wt") as f:
        f.write(cqpy_dump(query))
