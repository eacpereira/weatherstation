#!/usr/bin/env python
from multiprocessing import Manager, Process
from datetime import datetime
import time
import RPi.GPIO as GPIO
import progressbar
import touchphat


from environment_report import EnvironmentReport
from pilconvert import palette_convert
from plot_graphs import plot_graph
from inky_write import show_tpf_image
from speak_information import speak_info, speak_full_info
from weather_report import WeatherReport

@touchphat.on_touch("A")
def handle_a():
    global speak_values
    speak_values = True

@touchphat.on_touch("B")
def handle_b():
    global speak_all_values
    speak_all_values = True

@touchphat.on_touch("Enter")
def handle_enter():
    global screen_change_press
    screen_change_press += 1


class MainProcess:

    def __init__(self, screen_polling_time=60, sleep_time=1, envr_data_polling_time=1, envr_data_limit=60,
                 envr_data_timeout=None, envr_image=None):

        manager = Manager()

        self.cur_screen = manager.list()
        self.cur_screen.append(0)

        if screen_polling_time < 20:
            raise ValueError("Polling time cannot be less 20s, the refresh rate of the screen.")
        if envr_data_polling_time > screen_polling_time:
            raise ValueError("Data must be polled at least once per screen refresh.")
        if screen_polling_time / envr_data_polling_time > 60:
            UserWarning(
                "Data will show the last {} seconds, but only be polled every {} seconds.".format(
                    envr_data_polling_time * 60,
                    screen_polling_time))
        if screen_polling_time / envr_data_polling_time > 180:
            raise ValueError("Too much data will be lost in between screen refreshes (120+ data points).")
        self.polling_time = screen_polling_time

        if sleep_time > 60:
            UserWarning("Sleeping longer than 60s will mean that the screen updates less than once per minute.")
        self.sleep_time = sleep_time

        self.enviro_report = EnvironmentReport(image_file=envr_image, data_polling_time=envr_data_polling_time,
                                               data_limit=envr_data_limit, data_timeout=envr_data_timeout)
        self.weather_report = WeatherReport()

    @staticmethod
    def calculate_led(screen_value):

        if screen_value == 0:
            GPIO.output(23, GPIO.LOW)
            GPIO.output(24, GPIO.LOW)
        elif screen_value == 1:
            GPIO.output(23, GPIO.HIGH)
            GPIO.output(24, GPIO.LOW)
        elif screen_value == 2:
            GPIO.output(23, GPIO.LOW)
            GPIO.output(24, GPIO.HIGH)
        elif screen_value == 3:
            GPIO.output(23, GPIO.HIGH)
            GPIO.output(24, GPIO.HIGH)
        else:
            raise ValueError("Screen number out of range 0-3!")

    def run(self):
        global speak_values
        global speak_all_values
        global screen_change_press

        self.enviro_report.setup()

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(23, GPIO.OUT)
        GPIO.setup(24, GPIO.OUT)
        GPIO.output(23, GPIO.LOW)
        GPIO.output(24, GPIO.LOW)

        time_mark = datetime.now()
        bar = progressbar.ProgressBar(widgets=["Polling: ", progressbar.AnimatedMarker()], max_value=progressbar.UnknownLength)
        while True:

            if screen_change_press >= 1:
                screen_changes = screen_change_press
                screen_change_press = 0

                self.cur_screen.append((self.cur_screen[0] + screen_changes) % 4)
                self.cur_screen.pop(0)

                change_screen_leds = Process(target=self.calculate_led, args=(self.cur_screen[0],), daemon=True)
                change_screen_leds.start()

            if self.cur_screen[0] == 0:
                if speak_values:
                    speak_values = False

                    spk_info = Process(target=speak_info, kwargs=dict(temperature_data=self.enviro_report.temperature_data,
                                                                      pressure_data=self.enviro_report.pressure_data,
                                                                      humidity_data=self.enviro_report.humidity_data), daemon=True)


                    spk_info.start()

                elif speak_all_values:
                    speak_all_values = False

                    spk_all_info = Process(target=speak_full_info, kwargs=dict(temperature_data=self.enviro_report.temperature_data,
                                                                      temperature_statistics=self.enviro_report.temperature_statistics,
                                                                      pressure_data=self.enviro_report.pressure_data,
                                                                      pressure_statistics=self.enviro_report.pressure_statistics,
                                                                      humidity_data=self.enviro_report.humidity_data,
                                                                      humidity_statistics=self.enviro_report.humidity_statistics,
                                                                      data_polling=self.enviro_report.data_polling), daemon=True)

                    spk_all_info.start()

            date_delta = datetime.now() - time_mark
            if date_delta.total_seconds() >= self.polling_time:
                bar.finish()

                time_mark = datetime.now()
                print(time_mark)

                if self.cur_screen[0] == 0:

                    cur_info = "Latest: {0:.2f} F,{1:.2f} hPa,{2:.3f} %RH".format(self.enviro_report.temperature_data[-1],
                                                                                  self.enviro_report.pressure_data[-1],
                                                                                  self.enviro_report.humidity_data[-1])
                    print(cur_info)

                    plot_graph(self.enviro_report.temperature_data, self.enviro_report.pressure_data,
                               self.enviro_report.humidity_data, self.enviro_report.image_file)
                    palette_convert(self.enviro_report.image_file)

                    inky_show = Process(target=show_tpf_image, args=(self.enviro_report.image_file,
                                                                     self.enviro_report.temperature_data,
                                                                     self.enviro_report.pressure_data,
                                                                     self.enviro_report.humidity_data), daemon=True)
                    inky_show.start()
                else:
                    weather_report = Process(target=self.weather_report.run, kwargs=dict(condition_var=self.weather_report.information["condition"],
                                                                                         location_var=self.weather_report.information["location"]),daemon=True)
                    weather_report.start()

                bar.start()

            else:
                bar.update(date_delta.total_seconds())
            time.sleep(self.sleep_time)


if __name__ == "__main__":
    speak_values = False
    speak_all_values = False
    screen_change_press = 0

    while True:
        try:
            long_short = input("Short (1), long (2), or day-long (3) [default: 1]?")

            if long_short == "1" or long_short == "":
                dt_polling_time = 1
                scr_polling_time = 60
                dt_limit = 60
                break
            elif long_short == "2":
                dt_polling_time = 60
                scr_polling_time = 60
                dt_limit = 60
            elif long_short == "3":
                dt_polling_time = 60
                scr_polling_time = 60
                dt_limit = 1440
                break
            else:
                "Select 1, 2, or 3."
        except KeyboardInterrupt:
            pass

    w = MainProcess(envr_image="test.png", envr_data_polling_time=dt_polling_time, screen_polling_time=scr_polling_time, sleep_time=1, envr_data_limit=dt_limit)
    w.run()

