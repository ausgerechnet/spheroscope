import sys
import os
from logging.config import dictConfig

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, dir_path)

from spheroscope import create_app

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.handlers.RotatingFileHandler',
        "formatter": "default",
        "filename": os.path.join(dir_path, "instance", "app.log"),
        "maxBytes": 1000000,
        "backupCount": 10,
        "delay": "True",
        "level": "DEBUG"
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

application = create_app()
