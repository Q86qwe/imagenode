"""nodehealth: network and system stability classes

Copyright (c) 2017 by Jeff Bass.
License: MIT, see LICENSE for more details.
"""

import os
import psutil
import logging
import platform
import threading
import multiprocessing
import numpy as np
from tools.utils import interval_timer

class HealthMonitor:
    """ Methods and attributes to measure and tune network and system stability

    Provides methods to send network heartbeat messages, determine system type
    (e.g., Raspberry Pi vs. Mac), and fix problems.

    Mostly a few example methods so far; send_heartbeat() has been very helpful
    in fixing some odd WiFi networking problems.

    Parameters:
        settings (Settings object): settings object created from YAML file
        send_q (list): queue of (text, image) messages to send to imagehub
    """
    def __init__(self, settings, send_q):
        self.send_q = send_q
        self.sys_type = self.get_sys_type()
        self.tiny_image = np.zeros((3,3), dtype="uint8")  # tiny blank image
        self.heartbeat_event_text = ' |'.join([settings.nodename, 'Heartbeat'])
        if settings.heartbeat:
            threading.Thread(daemon=True,
                target=lambda: interval_timer(
                    settings.heartbeat, self.send_heartbeat)).start()
        if True:  # later change this to stall_watcher settings value test
            pid = os.getpid()
            timing_thread = multiprocessing.Process(daemon=True,
                               args=((pid,)),
                               target=self.stall_watcher)

    def send_heartbeat(self):
        """ send a heartbeat message to imagehub
        """
        text = self.heartbeat_event_text
        text_and_image = (text, self.tiny_image)
        self.send_q.append(text_and_image)

    def stall_watcher(pid):
        p = psutil.Process(pid)
        main_time = p.cpu_times().user
        sleep_time = 10
        sleep(sleep_time)
        while True:
            last_main_time = main_time
            main_time = p.cpu_times().user
            delta_time = round(abs(main_time - last_main_time))
            if delta_time < 1:
                os.kill(pid, signal.SIGTERM) # p.terminate() # or os.kill(pid, signal.SIGTERM)
                sys.exit()
            sleep(sleep_time)

    def get_sys_type(self):
        """ determine system type, e.g., RPi or Mac
        """
        uname = platform.uname()
        if uname.system == 'Darwin':
            return 'Mac'
        elif uname.system == 'Linux':
            with open('/etc/os-release') as f:
                osrelease = f.read()
                if 'raspbian' in osrelease.lower():
                    return 'RPi'
                elif 'ubuntu' in osrelease.lower():
                    return 'Ubuntu'
                else:
                    return 'Linux'
        else:
            return 'Unknown'

    def reboot_this_computer(self):
        if self.sys_type == 'RPi':  # reboot only if RPi
            print('This is a mock reboot.')

    def check_ping(self, address='192.168.1.1'):
        return 'OK'  # for testing

def main():
    settings = None
    health = HealthMonitor(settings)
    print('This computer is ', health.sys_type)
    ping_OK = health.check_ping()
    print('Ping Check is ', ping_OK)
    health.reboot_this_computer()

if __name__ == '__main__' :
    main()
