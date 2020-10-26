# -*- coding: utf-8 -*-
# @Author  : xuliang
# @Email   : xuliang@sinap.ac.cn 
# @Time    : 2020/10/26 12:50
from PyQt5.QtCore import QThread
import time,math
from epics import caput

class CurrentThread(QThread):
    def __init__(self,ChannelName,Cycle,Interval,CurrentAmplitude):
        super(CurrentThread, self).__init__()
        self.ChannelName = ChannelName
        self.Interval = Interval
        self.Cycle = Cycle
        self.CurrentAmplitude =CurrentAmplitude

    def run(self):

        t = 0
        while True:

            current = self.CurrentAmplitude * math.sin(t * self.Interval / self.Cycle * 2 * math.pi)
            caput(self.ChannelName,current,timeout=2)
            print(current)
            t += 1
            time.sleep(self.Interval)
