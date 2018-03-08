import os
from logging.config import dictConfig

import sys

GPIO_TRIGGER = 18
GPIO_ECHO = 24
SPEED_OF_SOUND = 34300
SALT_LEVEL_ALERT_MESSAGE = 'Heads up! It looks like your salt level has dropped below {0:.2f} {1}'
READS_PER_CHECK = 5
CM_TO_INCHES = 2.54
METRIC = 'metric'
IMPERIAL = 'imperial'
VALID_UNITS = [IMPERIAL, METRIC]

# APIs
TWILIO_PUBLIC_KEY = os.environ.get('TWILIO_PUBLIC_KEY')
TWILIO_SECRET_KEY = os.environ.get('TWILIO_SECRET_KEY')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
REAL_PHONE_NUMBER = os.environ.get('REAL_PHONE_NUMBER')
MESSAGE_TEMPLATE = {'to': REAL_PHONE_NUMBER, 'from_': TWILIO_PHONE_NUMBER, 'body': None}


# Logging setup
PROJECT = os.path.abspath(os.path.split(sys.argv[0])[0])
LOGGING = {
    'version': 1,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S'
        },
        'verbose': {
            'format': 'salty_dog[%(process)d]: %(levelname)s %(name)s[%(module)s] %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'logfile': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '{}/salty_dog.log'.format(PROJECT),
            'when': 'midnight',
            'backupCount': 7,
            'formatter': 'standard',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'syslog': {
            'level': 'INFO',
            'class': 'logging.handlers.SysLogHandler',
            'formatter': 'verbose',
            'address': '/dev/log',
            'facility': 'local2',
        }
    },
    'loggers': {
        'salty_dog': {
            'handlers': ['console', 'logfile', 'syslog'],
            'propagate': False,
            'level': 'DEBUG',
        },
        '': {
            'handlers': ['console', 'logfile', 'syslog'],
            'propagate': True,
            'level': 'DEBUG',
        },
    }
}

dictConfig(LOGGING)
