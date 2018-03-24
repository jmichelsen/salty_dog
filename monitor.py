import argparse
import logging
import time

import sys
from twilio.rest import Client

import settings
import RPi.GPIO as GPIO

twilio = Client(settings.TWILIO_PUBLIC_KEY, settings.TWILIO_SECRET_KEY)
log = logging.getLogger(__name__)


class SaltLevelMonitor(object):
    def __init__(self, force_report=False, unit=settings.METRIC, threshold=0,
                 tank_depth=settings.DEFAULT_TANK_DEPTH):
        self.force_report = force_report
        self.unit = unit if unit in settings.VALID_UNITS else settings.METRIC
        self.notation = 'inches' if unit == settings.IMPERIAL else 'centimeters'
        self.threshold = float(threshold)
        self.tank_depth = float(tank_depth)
        self.distance = None
        self.remaining_salt = None

    def check_salt_level(self):
        self.distance = self.get_average_distance()
        self._convert_units()
        message = self._get_report_message()
        log.info(message['body'])
        if self.remaining_salt < self.threshold or self.force_report:
            self.report_salt_level(message)

    def get_average_distance(self):
        """ used to get an average read since the sensor isn't 100% accurate """
        reads = [self.get_distance() for _ in range(settings.READS_PER_CHECK)]
        return sum(reads) / settings.READS_PER_CHECK

    @staticmethod
    def get_distance():
        """ returns distance in centimeters """
        # set Trigger to HIGH
        GPIO.output(settings.GPIO_TRIGGER, True)

        # set Trigger after 0.01ms to LOW
        time.sleep(0.00001)
        GPIO.output(settings.GPIO_TRIGGER, False)

        start_time = time.time()
        stop_time = time.time()

        # save StartTime
        while GPIO.input(settings.GPIO_ECHO) == 0:
            start_time = time.time()

        # save time of arrival
        while GPIO.input(settings.GPIO_ECHO) == 1:
            stop_time = time.time()

        # time difference between start and arrival
        time_elapsed = stop_time - start_time
        return (time_elapsed * settings.SPEED_OF_SOUND) / 2

    def _convert_units(self):
        """
        convert distance to inches if IMPERIAL or convert tank_depth and threshold to centimeters
        """
        if self.unit == settings.IMPERIAL:
            self.distance = self.distance / settings.CM_TO_INCHES
        else:
            self.tank_depth = self.tank_depth * settings.CM_TO_INCHES
            self.threshold = self.threshold * settings.CM_TO_INCHES

    def _get_report_message(self):
        message = settings.MESSAGE_TEMPLATE.copy()
        self.remaining_salt = self.tank_depth - self.distance
        message['body'] = settings.SALT_LEVEL_ALERT_MESSAGE.format(
            self.remaining_salt, self.notation)
        return message

    @staticmethod
    def report_salt_level(message):
        twilio.messages.create(**message)

    def __enter__(self):
        GPIO.setmode(GPIO.BCM)

        # set GPIO direction (IN / OUT)
        GPIO.setup(settings.GPIO_TRIGGER, GPIO.OUT)
        GPIO.setup(settings.GPIO_ECHO, GPIO.IN)
        return self

    def __exit__(self, *args):
        GPIO.cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Salty Dog')
    parser.add_argument('-u',
                        '--unit',
                        action='store',
                        dest='unit',
                        default='metric',
                        help='Unit of measure used in reporting')
    parser.add_argument('-t',
                        '--threshold',
                        action='store',
                        dest='threshold',
                        help='Threshold for reporting in inches or cm (must match --unit)')
    parser.add_argument('-d',
                        '--tank-depth',
                        action='store',
                        dest='tank_depth',
                        help='Total depth of your salt tank in inches or cm (must match --unit)')
    parser.add_argument('-f',
                        '--force-report',
                        action='store_true',
                        dest='force_report',
                        default=False,
                        help='Force Salty Dog to send SMS regardless of salt level measured')
    args = parser.parse_args(sys.argv[1:])
    parsed_kwargs = {
        'force_report': args.force_report,
        'unit': args.unit,
        'threshold': args.threshold,
        'tank_depth': args.tank_depth,
    }
    with SaltLevelMonitor(**parsed_kwargs) as monitor:
        monitor.check_salt_level()
