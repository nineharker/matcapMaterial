# -*- coding: utf-8 -*-
from maya import OpenMayaUI, cmds
from PySide2 import QtCore, QtWidgets
#import shiboken
from shiboken2 import wrapInstance


class ToolWidget(QtWidgets.QWidget):
    applied = QtCore.Signal()
    closed  = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super(ToolWidget, self).__init__(*args, **kwargs)
        mainLayout = QtWidgets.QGridLayout(self)
        self.setLayout(mainLayout)

        self.__scrollWidget = QtWidgets.QScrollArea(self)
        self.__scrollWidget.setWidgetResizable(True)
        self.__scrollWidget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__scrollWidget.setMinimumHeight(1)
        mainLayout.addWidget(self.__scrollWidget, 0, 0, 1, 3)

        self.__actionBtn = QtWidgets.QPushButton(self)
        self.__actionBtn.setText('Apply and Close')
        self.__actionBtn.clicked.connect(self.action)
        mainLayout.addWidget(self.__actionBtn, 1, 0)

        applyBtn = QtWidgets.QPushButton(self)
        applyBtn.setText('Apply')
        applyBtn.clicked.connect(self.apply)
        mainLayout.addWidget(applyBtn, 1, 1)

        closeBtn = QtWidgets.QPushButton(self)
        closeBtn.setText('Close')
        closeBtn.clicked.connect(self.close)
        mainLayout.addWidget(closeBtn, 1, 2)

    def action(self):
        self.apply()
        self.close()

    def apply(self):
        self.applied.emit()

    def close(self):
        self.closed.emit()

    def setActionName(self, name):
        self.__actionBtn.setText(name)

    def setOptionWidget(self, widget):
        self.__scrollWidget.setWidget(widget)

class Callback(object):
    def __init__(self, func, *args, **kwargs):
        self.__func   = func
        self.__args   = args
        self.__kwargs = kwargs

    def __call__(self):
        cmds.undoInfo(openChunk=True)
        try:
            return self.__func(*self.__args, **self.__kwargs)

        except:
            raise

        finally:
            cmds.undoInfo(closeChunk=True)

def getMayaWindow():
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    #widget = shiboken.wrapInstance(long(ptr), QtWidgets.QWidget)
    widget = wrapInstance(long(ptr), QtWidgets.QWidget)
    return widget
