import argparse
import time

import sys
from twilio.rest import Client

import settings
import RPi.GPIO as GPIO

twilio = Client(settings.TWILIO_PUBLIC_KEY, settings.TWILIO_SECRET_KEY)


class SaltLevelMonitor(object):
    def __init__(self, force_report=False, unit=settings.METRIC):
        self.force_report = force_report
        self.unit = unit if unit in settings.VALID_UNITS else settings.METRIC
        self.threshold = settings.SALT_LEVEL_REPORTING_THRESHOLD * settings.CM_TO_INCHES \
            if unit == settings.IMPERIAL else self.threshold * 1

    def check_salt_level(self):
        distance = self.get_average_distance()
        if distance > self.threshold or self.force_report:
            self.report_salt_level(distance)

    @staticmethod
    def report_salt_level(distance):
        message = settings.MESSAGE_TEMPLATE.copy()
        message['body'] = settings.SALT_LEVEL_ALERT_MESSAGE.format(distance)
        twilio.messages.create(**message)

    def get_average_distance(self):
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
        if self.unit == settings.IMPERIAL:
            return distance * settings.CM_TO_INCHES
        return distance

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
    parser.add_argument('--unit',
                        action='store_true',
                        dest='unit',
                        default='metric',
                        help='Unit of measure used in reporting')
    parser.add_argument('--force-report',
                        action='store_true',
                        dest='force_report',
                        default=False,
                        help='Force Salty Dog to send SMS regardless of salt level measured')
    args = parser.parse_args(sys.argv[1:])
    with SaltLevelMonitor(force_report=args.force_report, unit=args.unit) as monitor:
        monitor.check_salt_level()
