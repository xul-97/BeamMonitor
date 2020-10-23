# -*- coding: utf-8 -*-
# @Author  : xuliang
# @Email   : xuliang@sinap.ac.cn 
# @Time    : 2020/10/23 16:33
'''
读取EPICS上BPM的束流位置信息，并在matplotlib中画出随时间变化的曲线
改变BPM前面四极铁前面的矫正子电流大小，并观察BPM中位置信息如何改变
'''
import sys
from PyQt5.Qt import QApplication,QWidget, QVBoxLayout, QTimer
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
from epics import caget, caput
import mainwindow

class BeamMonitor(QWidget):
    def __init__(self):
        super(BeamMonitor, self).__init__()
        self.timer =  QTimer(self)
        self.timer.timeout.connect(self.getDatafromEPICS)
        self.InitUI()

    def InitUI(self):

        self.ui = mainwindow.Ui_Form()
        self.ui.setupUi(self)
        self.ui.SetSaveInfo.hide()
        self.ui.FilePath.setReadOnly(True)

        self.ui.isSaveCheckBox.stateChanged.connect(self.on_isSaveCheckBox_slot)
        self.ui.ChannelTestBtn.clicked.connect(self.ChannelTest_slot)
        self.ui.BPMChannel.textChanged.connect(self.getChannelName)

        self.XLine = XOnBPM()
        self.VLayout = QVBoxLayout()
        self.VLayout.addWidget(self.XLine)
        self.ui.XFigure.setLayout(self.VLayout)

        self.t = 0

    def on_StartBtn_slot(self):
        # 0.5秒读取一次数据
        # self.timer.start(500)

    def on_isSaveCheckBox_slot(self):
        '''
        是否保存数据，保存则显示设置文件名，文件路径
        :return:
        '''
        if self.ui.isSaveCheckBox.isChecked():
            self.ui.SetSaveInfo.show()
        else:
            self.ui.SetSaveInfo.hide()

    def getDatafromEPICS(self):
        '''
        从EPICS系统中读取数据
        :return:
        '''
        if len(self.XLine.x) < 80:
            self.XLine.x.append(caget(self.ChannelName))
            self.XLine.time.append(self.t * 0.5)
        else:
            del self.XLine.x[0]
            del self.XLine.time[0]
            self.XLine.x.append(caget(self.ChannelName))
            self.XLine.time.append(self.t * 0.5)

        self.t += 1

    def ChannelTest_slot(self):
        '''
        检测通道名是否有效
        :return:
        '''
        try:
            self.ChannelName #尝试是否输入了通道名
            caget(self.ChannelName) # 尝试是否可以连接到通道并读取数据
        except Exception as e:
            print(e)

    def getChannelName(self):
        '''
        获取用户设置的通道名
        :return:
        '''
        self.ChannelName =  self.ui.BPMChannel.text()




class XOnBPM(FigureCanvas):
    def __init__(self):
        self.figure = plt.figure(figsize=(10, 5), frameon=False)
        plt.subplots_adjust(left=0.09, right=0.95, bottom=0.15, top=0.9)
        plt.grid()
        plt.ylabel("x/y")
        plt.ylim(0, 10)
        self.ax = self.figure.add_subplot()

        FigureCanvas.__init__(self, self.figure)
        FigureCanvas.updateGeometry(self)

        xLine, = plt.plot([i for i in range(10)], [1, 2, 0, 4, 6, 8, 2, 6, 8, 9], 'r', marker="o", markersize=4)
        self.ax.set_xlim(-1, 10)
        self.ax.tick_params(labelsize=7)
        plt.legend([xLine], ["X"], loc=2, fontsize=6)

        self.x = []
        self.time = []

    def update_figure(self):
        # self.x = [random.randint(0, 10) for i in range(4)]
        self.ax.cla()

        self.ax.tick_params(labelsize=7)
        self.ax.yaxis.get_major_formatter().set_powerlimits((0, 1))
        #将x轴坐标刻度设置为文字
        self.ax.set_ylabel("x/y")
        self.ax.grid()
        xLine, = self.ax.plot(self.time,self.x,'r', marker = "o", markersize = 4)
        #添加图例显示
        self.ax.legend([xLine],["X"], loc = 2, fontsize = 6)
        self.draw()










if  __name__ == "__main__":
    app = QApplication(sys.argv)

    w = BeamMonitor()
    w.show()

    sys.exit(app.exec_())