# -*- coding: utf-8 -*-
# @Author  : xuliang
# @Email   : xuliang@sinap.ac.cn 
# @Time    : 2020/10/23 16:33
'''
读取EPICS上BPM的束流位置信息，并在matplotlib中画出随时间变化的曲线
改变BPM前面四极铁前面的矫正子电流大小，并观察BPM中位置信息如何改变
'''
import sys
from PyQt5.Qt import QApplication,QWidget, QVBoxLayout, QTimer, QMessageBox, QFileDialog, pyqtSlot, pyqtSignal
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
from epics import caget, caput
import mainwindow
import SinCurrent
import DMCurrent

class BeamMonitor(QWidget):

    AmplitudeSender = pyqtSignal(list)
    QMSetParameters = pyqtSignal(str,float,float,float)

    def __init__(self):
        super(BeamMonitor, self).__init__()
        self.timer =  QTimer(self)
        self.timer.timeout.connect(self.getDatafromEPICS)
        self.InitUI()

        self.QMCurrent = SinCurrent.CurrentThread()
        self.QMSetParameters.connect(self.QMCurrent.receiveParameters)


    def InitUI(self):
        global QMCurrentAmplitude, QMCycle, QMInterval,QMChannelName,DMCurrentAmplitude,DMInterval,DMChannelName

        self.BPMChannelName_X = "xuliang"
        self.BPMChannelName_Y= "xuliang"
        DMChannelName = "xuliang"
        QMChannelName = "xuliang"
        QMCurrentAmplitude = 0
        QMCycle = 1
        QMInterval = 0
        DMCurrentAmplitude = 0
        DMInterval = 0
        self.FilePath = ["",""]
        self.error_X = []
        self.error_Y = []
        self.sinCurrentRun = False
        self.DMCurrentRun = False
        self.BPMChannelRight = False
        self.QMChannelRight = False
        self.DMChannelRight = False


        self.ui = mainwindow.Ui_Form()
        self.ui.setupUi(self)
        self.ui.SetSaveInfo.hide()
        self.ui.FilePath.setReadOnly(True)

        self.ui.isSaveCheckBox.stateChanged.connect(self.on_isSaveCheckBox_slot)
        self.ui.BPMChannel_X.textChanged.connect(self.getChannelName)
        self.ui.BPMChannel_Y.textChanged.connect(self.getChannelName)
        self.ui.QMChannel.textChanged.connect(self.getChannelName)
        self.ui.DMChannel.textChanged.connect(self.getChannelName)
        self.ui.StartBtn.clicked.connect(self.on_StartBtn_slot)
        self.ui.StopBtn.clicked.connect(self.on_StopBtn_slot)
        self.ui.QMPutBtn.clicked.connect(self.QMCurrent_set)
        self.ui.DMPutBtn.clicked.connect(self.DMCurrent_set)
        self.ui.FilePathBtn.clicked.connect(self.getFilePath)
        self.ui.QM_A.valueChanged.connect(self.getValue)
        self.ui.QM_C.valueChanged.connect(self.getValue)
        self.ui.QM_I.valueChanged.connect(self.getValue)
        self.ui.DM_C.valueChanged.connect(self.getValue)
        self.ui.DM_I.valueChanged.connect(self.getValue)

        self.XLine = XOnBPM()
        self.VLayout = QVBoxLayout()
        self.VLayout.addWidget(self.XLine)
        self.ui.XFigure.setLayout(self.VLayout)

        self.t = 0

    def on_StartBtn_slot(self):
        #每0.5秒读取一次BPM的数据
        self.timer.start(500)
        self.ui.StartBtn.setEnabled(False)
        self.ui.isSaveCheckBox.setEnabled(False)
        self.ui.BPMChannel_X.setReadOnly(True)
        self.ui.BPMChannel_Y.setReadOnly(True)

    def on_StopBtn_slot(self):
        self.timer.stop()
        self.t = 0
        self.XLine.TimeAndX = np.empty((0,3))
        self.ui.StartBtn.setEnabled(True)
        self.ui.isSaveCheckBox.setEnabled(True)
        self.ui.BPMChannel_X.setReadOnly(False)
        self.ui.BPMChannel_Y.setReadOnly(False)

    def on_isSaveCheckBox_slot(self):
        '''
        是否保存数据，保存则显示设置文件名，文件路径
        :return:
        '''
        if self.ui.isSaveCheckBox.isChecked():
            self.ui.SetSaveInfo.show()
            if self.FilePath[0] == "":
                self.ui.StartBtn.setEnabled(False)
        else:
            self.ui.SetSaveInfo.hide()
            self.ui.StartBtn.setEnabled(True)

    def getDatafromEPICS(self):
        '''
        从EPICS系统中读取数据
        :return:
        '''
        global QMCycle
        if not self.BPMChannelRight:
            if (not caget(self.BPMChannelName_X, timeout = 1)) or (not caget(self.BPMChannelName_Y, timeout = 1)):
                QMessageBox.information(self, "提示", "无法连接到通道，请检查是否有误!")
                self.timer.stop()
                self.t = 0
                self.XLine.TimeAndX = np.empty((0,3))
                self.ui.StartBtn.setEnabled(True)
                self.ui.isSaveCheckBox.setEnabled(True)
                self.ui.BPMChannel_X.setReadOnly(False)
                self.ui.BPMChannel_Y.setReadOnly(False)
            else:
                self.BPMChannelRight = True
        if self.BPMChannelRight:
            current_X = caget(self.BPMChannelName_X)
            current_Y = caget(self.BPMChannelName_Y)
            print([self.t * 0.5, current_X, current_Y])

            if self.XLine.TimeAndX.shape[0] < 80:

                self.XLine.TimeAndX = np.vstack((self.XLine.TimeAndX,[self.t * 0.5,current_X,current_Y]))
                if self.ui.isSaveCheckBox.isChecked():
                    with open(self.FilePath[0], 'ab') as f:
                        np.savetxt(f, np.array([[self.t * 0.5, current_X, current_Y]]))
            else:
                self.XLine.TimeAndX = np.delete(self.XLine.TimeAndX, 0, axis = 0)
                self.XLine.TimeAndX = np.vstack((self.XLine.TimeAndX,[self.t * 0.5,current_X,current_Y]))
                if self.ui.isSaveCheckBox.isChecked():
                    with open(self.FilePath[0], 'ab') as f:
                        np.savetxt(f, np.array([[self.t * 0.5, current_X,current_Y]]))

            if (self.t + 1) % (QMCycle * 2) == 0:
                if len(self.error_X) < 2:
                    self.error_X.append(max(self.XLine.TimeAndX[(self.t + 1 - QMCycle * 2):self.t + 1,1]) -
                                        min(self.XLine.TimeAndX[(self.t + 1 - QMCycle * 2):self.t + 1,1]))
                    self.error_Y.append(max(self.XLine.TimeAndX[(self.t + 1 - QMCycle * 2):self.t + 1, 2]) -
                                        min(self.XLine.TimeAndX[(self.t + 1 - QMCycle * 2):self.t + 1, 2]))
                else:
                    del self.error_X[0]
                    del self.error_Y[0]
                    if self.t < 80:
                        self.error_X.append(max(self.XLine.TimeAndX[(self.t + 1 - QMCycle * 2):self.t + 1, 1]) -
                                            min(self.XLine.TimeAndX[(self.t + 1 - QMCycle * 2):self.t + 1, 1]))
                        self.error_Y.append(max(self.XLine.TimeAndX[(self.t + 1 - QMCycle * 2):self.t + 1, 2]) -
                                            min(self.XLine.TimeAndX[(self.t + 1 - QMCycle * 2):self.t + 1, 2]))
                    else:
                        self.error_X.append(max(self.XLine.TimeAndX[(80 - QMCycle * 2):80, 1]) -
                                            min(self.XLine.TimeAndX[(80 - QMCycle * 2):80, 1]))
                        self.error_Y.append(max(self.XLine.TimeAndX[(80 - QMCycle * 2):80, 2]) -
                                            min(self.XLine.TimeAndX[(80 - QMCycle * 2):80, 2]))

                                      
                    

                self.ui.errorDisplay_X.setText("X " + str(self.error_X))
                self.ui.errorDisplay_Y.setText("Y " + str(self.error_Y))
                self.AmplitudeSender.emit(self.error_X)

            
            self.XLine.update_figure()

            self.t += 1

    def ChannelTest_slot(self,channelName):
        '''
        检测通道名是否有效
        目前作废函数
        :return:
        '''
        if not caget(channelName,timeout=1): # 尝试是否可以连接到通道并读取数据
            QMessageBox.information(self,"提示", "无法连接到通道，请检查是否有误")

    def getChannelName(self):
        '''
        获取用户设置的通道名
        :return:
        '''
        global QMChannelName, DMChannelName
        lineEdit = self.sender()
        if lineEdit.objectName() == "BPMChannel_X":
            self.BPMChannelName_X =  self.ui.BPMChannel_X.text()
            self.BPMChannelRight = False
        elif lineEdit.objectName() == "QMChannel":
            QMChannelName = self.ui.QMChannel.text()
            self.QMChannelRight = False
        elif lineEdit.objectName() == "DMChannel":
            DMChannelName = self.ui.DMChannel.text()
            self.DMChannelRight = False
        elif lineEdit.objectName() == "BPMChannel_Y":
            self.BPMChannelName_Y = self.ui.BPMChannel_Y.text()
            self.BPMChannelRight = False

    def QMCurrent_set(self):
        global QMInterval,QMCycle,QMChannelName,QMCurrentAmplitude

        if not self.QMChannelRight:
            if not caget(QMChannelName,timeout=0.5): # 尝试是否可以连接到通道并读取数据
                QMessageBox.information(self,"提示", "无法连接到通道，请检查是否有误!")
            else:
                self.QMChannelRight = True

        if self.QMChannelRight:
            if QMInterval == 0:
                caput(QMChannelName,QMCurrentAmplitude)
            else:
                # 为四极铁添加周期性电流（创建子线程文件）
                if self.sinCurrentRun:
                    self.ui.QMPutBtn.setText("Put")
                    self.sinCurrentRun = not self.sinCurrentRun
                    # 线程停止并销毁
                    self.QMCurrent.stop()
                    self.ui.QM_I.setReadOnly(False)
                else:
                    self.ui.QMPutBtn.setText("Stop")
                    self.sinCurrentRun = not self.sinCurrentRun
                    #创建线程并开启
                    self.QMCurrent.start()
                    self.QMSetParameters.emit(QMChannelName, QMCycle, QMInterval, QMCurrentAmplitude)
                    self.ui.QM_I.setReadOnly(True)

    def DMCurrent_set(self):
        global DMInterval,DMChannelName, DMCurrentAmplitude
        if not self.DMChannelRight:
            if not caget(DMChannelName, timeout=0.5):  # 尝试是否可以连接到通道并读取数据
                QMessageBox.information(self, "提示", "无法连接到通道，请检查是否有误!")
            else:
                self.DMChannelRight = True

        if self.DMChannelRight:
            if DMInterval == 0:
                caput(DMChannelName, DMCurrentAmplitude)
            else:
                if self.DMCurrentRun:
                    self.ui.DMPutBtn.setText("Put")
                    self.DMCurrentRun = not self.DMCurrentRun
                    # 线程停止并销毁
                    self.DMCurrent.stop()
                    self.ui.DM_I.setReadOnly(False)
                else:
                    self.ui.DMPutBtn.setText("Stop")
                    self.DMCurrentRun = not self.DMCurrentRun
                    #创建线程并开启
                    self.DMCurrent = DMCurrent.DMCurrentThread(DMChannelName,DMInterval,DMCurrentAmplitude)
                    self.DMCurrent.CurrentSignal.connect(self.receiveDMCurrent)
                    self.QMCurrent.sendData.connect(self.DMCurrent.receiveError)
                    self.DMCurrent.start()
                    self.ui.DM_I.setReadOnly(True)

    def getFilePath(self):
        self.FilePath = QFileDialog.getSaveFileName(filter ="Text Files (*.txt)")
        self.ui.FilePath.setText(self.FilePath[0])
        if self.FilePath[0] == "":
            self.ui.StartBtn.setEnabled(False)
        else:
            self.ui.StartBtn.setEnabled(True)

    def getValue(self):
        global QMCurrentAmplitude, QMCycle, QMInterval, DMCurrentAmplitude, DMInterval
        SpinBox = self.sender()
        if SpinBox.objectName() == "QM_A":
            QMCurrentAmplitude = SpinBox.value()
        elif SpinBox.objectName() == "QM_C":
            QMCycle = SpinBox.value()
        elif SpinBox.objectName() == "QM_I":
            QMInterval = SpinBox.value()
        elif SpinBox.objectName() == "DM_C":
            DMCurrentAmplitude = SpinBox.value()
        elif SpinBox.objectName() == "DM_I":
            DMInterval = SpinBox.value()

    @pyqtSlot(float)
    def receiveDMCurrent(self,current):
        self.ui.DM_C.setValue(current)

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
        yLine, = plt.plot([i for i in range(10)], [9,0,3,5,7,2,3,6,8,5], 'b', marker="o", markersize=4)
        self.ax.set_xlim(-1, 10)
        self.ax.tick_params(labelsize=7)
        plt.legend([xLine,yLine], ["X","Y"], loc=2, fontsize=6)

        self.TimeAndX = np.empty((0,3))

    def update_figure(self):
        # self.x = [random.randint(0, 10) for i in range(4)]
        self.ax.cla()

        self.ax.tick_params(labelsize=7)
        self.ax.yaxis.get_major_formatter().set_powerlimits((0, 1))
        self.ax.set_ylabel("x/y")
        self.ax.grid()
        xLine, = self.ax.plot(self.TimeAndX[:,0],self.TimeAndX[:,1],'r', marker = "o", markersize = 4)
        yLine, = self.ax.plot(self.TimeAndX[:, 0], self.TimeAndX[:, 2], 'b', marker="o", markersize=4)
        #添加图例显示
        self.ax.legend([xLine,yLine],["X","Y"], loc = 2, fontsize = 6)
        self.draw()





if  __name__ == "__main__":
    app = QApplication(sys.argv)

    w = BeamMonitor()
    w.show()
    w.setWindowTitle("Beam Monitor")

    sys.exit(app.exec_())
