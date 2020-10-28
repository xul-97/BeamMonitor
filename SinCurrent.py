# -*- coding: utf-8 -*-
# @Author  : xuliang
# @Email   : xuliang@sinap.ac.cn 
# @Time    : 2020/10/26 12:50
from PyQt5.QtCore import QThread, pyqtSlot
import time,math
from epics import caput

class CurrentThread(QThread):
    def __init__(self):
        super(CurrentThread, self).__init__()
        self.ChannelName = "xuliang"
        self.Interval = 0
        self.Cycle = 1
        self.CurrentAmplitude = 0
        self.keepRunning = True

    def stop(self):
        self.keepRunning = False

    def run(self):

        t = 0
        while self.keepRunning:

            current = self.CurrentAmplitude * math.sin(t * self.Interval / self.Cycle * 2 * math.pi)
            caput(self.ChannelName,current,timeout=2)
            t += 1
            print("QM",[t,current])
            time.sleep(self.Interval)

        self.keepRunning = True

    @pyqtSlot(str,float,float,float)
    def receiveParameters(self,ChannelName,Cycle,Interval,CurrentAmplitude):
        self.ChannelName = ChannelName
        self.Interval = Interval
        self.Cycle = Cycle
        self.CurrentAmplitude = CurrentAmplitude

