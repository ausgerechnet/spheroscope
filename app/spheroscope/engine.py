from ccc.cwb import CWBEngine


def init_engine(config, subcorpus=True):

    print('initializing engine')
    engine = CWBEngine(
        corpus_name=config['CORPUS_NAME'],
        lib_path=config['LIB_PATH'],
        registry_path=config['REGISTRY_PATH'],
        cache_path=config['CACHE_PATH']
    )

    # restrict to subcorpus
    if subcorpus:
        engine.activate_subcorpus(
            "/region[tweet,a] :: (a.tweet_duplicate_status!='1') within tweet;",
            "DEDUP"
        )
        print("switched to subcorpus 'DEDUP'")

    return engine
