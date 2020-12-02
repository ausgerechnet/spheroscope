class DevConfig:

    DEBUG = False
    TESTING = False
    SECRET_KEY = "dev"

    DB_NAME = "spheroscope.sqlite"  # relative to instance folder
    DB_USERNAME = "admin"
    DB_PASSWORD = "0000"

    SESSION_COOKIE_SECURE = True

    REGISTRY_PATH = "/path/to/your/cwb/registry"
    CACHE_PATH = "/tmp/spheroscope-cache"
    # FILLFORM = "fillform-static"
