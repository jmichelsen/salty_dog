import os

GPIO_TRIGGER = 18
GPIO_ECHO = 24
SPEED_OF_SOUND = 34300
SALT_LEVEL_REPORTING_THRESHOLD = 100  # number in cm or ft. Must match chosen unit
SALT_LEVEL_ALERT_MESSAGE = 'Heads up! It looks like your salt level has dropped below {} {}'
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
