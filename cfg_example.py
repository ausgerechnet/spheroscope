class DevConfig:

    DEBUG = False               # show interactive debugger?
    TESTING = False             # propagate exceptions?
    SECRET_KEY = "dev"          # change in production!
    SESSION_COOKIE_SECURE = False  # only send cookies via https? (disable for development server)

    DB_NAME = "spheroscope.sqlite"  # path to database (relative to instance folder)
    DB_USERNAME = "admin"           # local database username
    DB_PASSWORD = "0000"            # local database password

    REMOTE_NAME = "galois.informatik.uni-erlangen.de"  # remote database URL
    REMOTE_USERNAME = "USER"  # username @ galois.informatik.uni-erlangen.de
    REMOTE_PASSWORD = "PASSWORD"  # password @ galois.informatik.uni-erlangen.de

    REGISTRY_PATH = "/usr/local/share/cwb/registry/"  # path to your CWB registry
    CACHE_PATH = "/tmp/spheroscope-cache"  # path for CQP dumps and cwb-ccc data
