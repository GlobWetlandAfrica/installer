# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'componentInstructionsDialog.ui'
#
# Created: Tue May 06 09:09:39 2014
#      by: PyQt4 UI code generator 4.10.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(570, 464)
        self.continueButton = QtGui.QPushButton(Dialog)
        self.continueButton.setGeometry(QtCore.QRect(380, 420, 75, 23))
        self.continueButton.setObjectName(_fromUtf8("continueButton"))
        self.logoLabel = QtGui.QLabel(Dialog)
        self.logoLabel.setGeometry(QtCore.QRect(420, 60, 131, 51))
        self.logoLabel.setText(_fromUtf8(""))
        self.logoLabel.setPixmap(QtGui.QPixmap(_fromUtf8("../images/GWA_logo.png")))
        self.logoLabel.setScaledContents(True)
        self.logoLabel.setObjectName(_fromUtf8("logoLabel"))
        self.topLabel = QtGui.QLabel(Dialog)
        self.topLabel.setGeometry(QtCore.QRect(20, 70, 401, 41))
        self.topLabel.setWordWrap(True)
        self.topLabel.setObjectName(_fromUtf8("topLabel"))
        self.instructionsFooterLabel = QtGui.QLabel(Dialog)
        self.instructionsFooterLabel.setGeometry(QtCore.QRect(30, 330, 501, 21))
        self.instructionsFooterLabel.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedKingdom))
        self.instructionsFooterLabel.setWordWrap(True)
        self.instructionsFooterLabel.setObjectName(_fromUtf8("instructionsFooterLabel"))
        self.line = QtGui.QFrame(Dialog)
        self.line.setGeometry(QtCore.QRect(20, 140, 531, 16))
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.cancelButton = QtGui.QPushButton(Dialog)
        self.cancelButton.setGeometry(QtCore.QRect(470, 420, 75, 23))
        self.cancelButton.setObjectName(_fromUtf8("cancelButton"))
        self.instructionsHeaderLabel = QtGui.QLabel(Dialog)
        self.instructionsHeaderLabel.setGeometry(QtCore.QRect(20, 150, 101, 41))
        self.instructionsHeaderLabel.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedKingdom))
        self.instructionsHeaderLabel.setWordWrap(True)
        self.instructionsHeaderLabel.setObjectName(_fromUtf8("instructionsHeaderLabel"))
        self.bottomLabel = QtGui.QLabel(Dialog)
        self.bottomLabel.setGeometry(QtCore.QRect(20, 380, 511, 31))
        self.bottomLabel.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedKingdom))
        self.bottomLabel.setWordWrap(True)
        self.bottomLabel.setObjectName(_fromUtf8("bottomLabel"))
        self.line_2 = QtGui.QFrame(Dialog)
        self.line_2.setGeometry(QtCore.QRect(20, 360, 531, 16))
        self.line_2.setFrameShape(QtGui.QFrame.HLine)
        self.line_2.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_2.setObjectName(_fromUtf8("line_2"))
        self.instructionsMainLabel = QtGui.QLabel(Dialog)
        self.instructionsMainLabel.setGeometry(QtCore.QRect(30, 160, 511, 131))
        self.instructionsMainLabel.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedKingdom))
        self.instructionsMainLabel.setWordWrap(True)
        self.instructionsMainLabel.setObjectName(_fromUtf8("instructionsMainLabel"))

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "GWA Toolbox Installation", None))
        self.continueButton.setText(_translate("Dialog", "Continue", None))
        self.topLabel.setText(_translate("Dialog", "BEAM is a software for analysing optical and thermal data derived with satellites operated by Europen Space Agency (ESA) and other organisation.", None))
        self.instructionsFooterLabel.setText(_translate("Dialog", "Afterwards click \"Continue\".", None))
        self.cancelButton.setText(_translate("Dialog", "Cancel", None))
        self.instructionsHeaderLabel.setText(_translate("Dialog", "Instructions:", None))
        self.bottomLabel.setText(_translate("Dialog", "If you would like to abandon the installation altogether, click \"Cancel\". The GWA Toolbox components that were already installed will remain on your computer.", None))
        self.instructionsMainLabel.setText(_translate("Dialog", "You need to activate BEAM plugins. To do that start BEAM, select \"Plugins\" from main menu and ...", None))

