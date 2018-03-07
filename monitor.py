import os
import time

from twilio.rest import Client

import settings
import RPi.GPIO as GPIO

twilio = Client(settings.TWILIO_PUBLIC_KEY, settings.TWILIO_SECRET_KEY)


class SaltLevelMonitor(object):
    def check_salt_level(self):
        print('checking salt level')
        distance = self.get_average_distance()
        if distance > settings.SALT_LEVEL_REPORTING_THRESHOLD:
            self.report_salt_level(distance)

    @staticmethod
    def report_salt_level(distance):
        print('reporting salt level')
        message = settings.MESSAGE_TEMPLATE.copy()
        message['body'] = settings.SALT_LEVEL_ALERT_MESSAGE.format(distance)
        twilio.messages.create(**message)

    def get_average_distance(self):
        print('getting average distance')
        reads = [self.get_distance() for read in range(settings.READS_PER_CHECK)]
        return sum(reads) / settings.READS_PER_CHECK

    @staticmethod
    def get_distance():
        print('getting single distance')
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

    def __enter__(self):
        print('entering context manager')
        GPIO.setmode(GPIO.BCM)

        # set GPIO direction (IN / OUT)
        GPIO.setup(settings.GPIO_TRIGGER, GPIO.OUT)
        GPIO.setup(settings.GPIO_ECHO, GPIO.IN)

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('exiting context manager')
        GPIO.cleanup()


if __name__ == '__main__':
    print('starting up')
    with SaltLevelMonitor() as monitor:
        monitor.check_salt_level()
