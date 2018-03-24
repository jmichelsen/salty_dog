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
    def __init__(self, force_report=False, unit=settings.METRIC, threshold=0, tank_depth=None):
        self.force_report = force_report
        self.unit = unit if unit in settings.VALID_UNITS else settings.METRIC
        self.notation = 'in' if unit == settings.IMPERIAL else 'cm'
        self.threshold = int(threshold)
        self.tank_depth = self._convert_to_unit(tank_depth or settings.DEFAULT_TANK_DEPTH)

    def check_salt_level(self):
        distance = self.get_average_distance()
        log.info('Salt level is: {} {}'.format(distance, self.notation))
        if distance > self.threshold or self.force_report:
            self.report_salt_level(distance)

    def report_salt_level(self, distance):
        message = settings.MESSAGE_TEMPLATE.copy()
        remaining_salt = self.tank_depth - distance
        message['body'] = settings.SALT_LEVEL_ALERT_MESSAGE.format(remaining_salt, self.notation)
        twilio.messages.create(**message)

    def get_average_distance(self):
        """ used to get an average read since the sensor isn't 100% accurate """
        reads = [self.get_distance() for read in range(settings.READS_PER_CHECK)]
        return sum(reads) / settings.READS_PER_CHECK

    def get_distance(self):
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
        distance = (time_elapsed * settings.SPEED_OF_SOUND) / 2
        return self._convert_to_unit(distance)

    def _convert_to_unit(self, value):
        if self.unit == settings.IMPERIAL:
            return value / settings.CM_TO_INCHES
        return value

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
        'tank_depth': args.tank_depth
    }
    with SaltLevelMonitor(**parsed_kwargs) as monitor:
        monitor.check_salt_level()
