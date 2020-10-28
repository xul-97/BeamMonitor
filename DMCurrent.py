# -*- coding: utf-8 -*-
# @Author  : xuliang
# @Email   : xuliang@sinap.ac.cn 
# @Time    : 2020/10/28 12:33
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
import time,math
from epics import caput

class DMCurrentThread(QThread):
    CurrentSignal = pyqtSignal(float)
    def __init__(self,ChannelName,Interval,Current):
        super(DMCurrentThread, self).__init__()
        self.ChannelName = ChannelName
        self.Interval = Interval
        self.Current = Current
        self.keepRunning = True
        self.error = []
        self.isBigger = True

    def stop(self):
        self.keepRunning = False

    def run(self):

        t = 0
        count = 0
        while self.keepRunning:

            if len(self.error) == 1:
                self.Current -= 0.2
            elif len(self.error) == 2:
                if count == 0:
                    if self.error[1] - self.error[0] > 0:
                        self.isBigger = True
                    else:
                        self.isBigger = False
                    count += 1
                if self.isBigger:
                    if count < 2:
                        self.Current += 0.2
                    else:
                        if self.error[1] - self.error[0] < 0:
                            self.Current += 0.2
                        else:
                            self.Current -= 0.2
                else:
                    if self.error[1] - self.error[0] > 0:
                        self.Current += 0.2
                    else:
                        self.Current -= 0.2

            # caput(self.ChannelName,current,timeout=2)
            t += 1
            self.CurrentSignal.emit(self.Current)
            print("DM",t,"  ",self.Current,self.error)
            time.sleep(self.Interval)

        self.keepRunning = True

    @pyqtSlot(list)
    def receiveError(self,error):
        self.error = error

