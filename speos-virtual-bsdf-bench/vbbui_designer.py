# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'vbbUIv2uwuZgG.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFormLayout, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLayout, QLineEdit,
    QMainWindow, QMenuBar, QPushButton, QRadioButton,
    QSizePolicy, QSpinBox, QStackedWidget, QStatusBar,
    QTabWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(600, 720)
        MainWindow.setMinimumSize(QSize(600, 720))
        MainWindow.setMaximumSize(QSize(600, 720))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.stackedSensorWidget = QTabWidget(self.centralwidget)
        self.stackedSensorWidget.setObjectName(u"stackedSensorWidget")
        self.stackedSensorWidget.setGeometry(QRect(20, 10, 561, 641))
        self.Simulation = QWidget()
        self.Simulation.setObjectName(u"Simulation")
        self.wavelengthGb = QGroupBox(self.Simulation)
        self.wavelengthGb.setObjectName(u"wavelengthGb")
        self.wavelengthGb.setGeometry(QRect(20, 320, 111, 185))
        self.verticalLayout_3 = QVBoxLayout(self.wavelengthGb)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label = QLabel(self.wavelengthGb)
        self.label.setObjectName(u"label")

        self.verticalLayout_3.addWidget(self.label)

        self.wavelengthStart = QSpinBox(self.wavelengthGb)
        self.wavelengthStart.setObjectName(u"wavelengthStart")
        self.wavelengthStart.setMinimum(350)
        self.wavelengthStart.setMaximum(800)
        self.wavelengthStart.setSingleStep(10)
        self.wavelengthStart.setValue(400)

        self.verticalLayout_3.addWidget(self.wavelengthStart)

        self.label_2 = QLabel(self.wavelengthGb)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_3.addWidget(self.label_2)

        self.wavelengthEnd = QSpinBox(self.wavelengthGb)
        self.wavelengthEnd.setObjectName(u"wavelengthEnd")
        self.wavelengthEnd.setMinimum(350)
        self.wavelengthEnd.setMaximum(800)
        self.wavelengthEnd.setSingleStep(10)
        self.wavelengthEnd.setValue(700)

        self.verticalLayout_3.addWidget(self.wavelengthEnd)

        self.label_3 = QLabel(self.wavelengthGb)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout_3.addWidget(self.label_3)

        self.wavelengthSampling = QSpinBox(self.wavelengthGb)
        self.wavelengthSampling.setObjectName(u"wavelengthSampling")
        self.wavelengthSampling.setMinimum(5)
        self.wavelengthSampling.setMaximum(1000)
        self.wavelengthSampling.setValue(13)

        self.verticalLayout_3.addWidget(self.wavelengthSampling)

        self.rayNumberGb = QGroupBox(self.Simulation)
        self.rayNumberGb.setObjectName(u"rayNumberGb")
        self.rayNumberGb.setGeometry(QRect(150, 350, 291, 120))
        self.rayNumberGb.setCheckable(False)
        self.label_4 = QLabel(self.rayNumberGb)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(10, 80, 231, 16))
        self.layoutWidget = QWidget(self.rayNumberGb)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(10, 40, 190, 28))
        self.horizontalLayout = QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.rayNumSb = QSpinBox(self.layoutWidget)
        self.rayNumSb.setObjectName(u"rayNumSb")
        self.rayNumSb.setMinimum(1)
        self.rayNumSb.setMaximum(1000)
        self.rayNumSb.setSingleStep(10)
        self.rayNumSb.setValue(10)

        self.horizontalLayout.addWidget(self.rayNumSb)

        self.rayUnitCb = QComboBox(self.layoutWidget)
        self.rayUnitCb.addItem("")
        self.rayUnitCb.addItem("")
        self.rayUnitCb.setObjectName(u"rayUnitCb")

        self.horizontalLayout.addWidget(self.rayUnitCb)

        self.resultTypeLe = QLineEdit(self.Simulation)
        self.resultTypeLe.setObjectName(u"resultTypeLe")
        self.resultTypeLe.setGeometry(QRect(150, 320, 351, 21))
        self.resultTypeLe.setReadOnly(True)
        self.layoutWidget1 = QWidget(self.Simulation)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.layoutWidget1.setGeometry(QRect(10, 20, 491, 291))
        self.verticalLayout_6 = QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.formatDesc = QGroupBox(self.layoutWidget1)
        self.formatDesc.setObjectName(u"formatDesc")
        self.layoutWidget2 = QWidget(self.formatDesc)
        self.layoutWidget2.setObjectName(u"layoutWidget2")
        self.layoutWidget2.setGeometry(QRect(20, 30, 253, 56))
        self.verticalLayout = QVBoxLayout(self.layoutWidget2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.allProperty = QRadioButton(self.layoutWidget2)
        self.allProperty.setObjectName(u"allProperty")
        self.allProperty.setChecked(True)

        self.verticalLayout.addWidget(self.allProperty)

        self.roughnessOnly = QRadioButton(self.layoutWidget2)
        self.roughnessOnly.setObjectName(u"roughnessOnly")
        self.roughnessOnly.setChecked(False)

        self.verticalLayout.addWidget(self.roughnessOnly)


        self.verticalLayout_6.addWidget(self.formatDesc)

        self.colorDefi = QGroupBox(self.layoutWidget1)
        self.colorDefi.setObjectName(u"colorDefi")
        self.layoutWidget3 = QWidget(self.colorDefi)
        self.layoutWidget3.setObjectName(u"layoutWidget3")
        self.layoutWidget3.setGeometry(QRect(20, 20, 281, 61))
        self.verticalLayout_2 = QVBoxLayout(self.layoutWidget3)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.colorViewDirectionRb = QRadioButton(self.layoutWidget3)
        self.colorViewDirectionRb.setObjectName(u"colorViewDirectionRb")

        self.verticalLayout_2.addWidget(self.colorViewDirectionRb)

        self.colorNoViewDirectionRb = QRadioButton(self.layoutWidget3)
        self.colorNoViewDirectionRb.setObjectName(u"colorNoViewDirectionRb")
        self.colorNoViewDirectionRb.setChecked(True)

        self.verticalLayout_2.addWidget(self.colorNoViewDirectionRb)


        self.verticalLayout_6.addWidget(self.colorDefi)

        self.sourceSetGb = QGroupBox(self.layoutWidget1)
        self.sourceSetGb.setObjectName(u"sourceSetGb")
        self.layoutWidget4 = QWidget(self.sourceSetGb)
        self.layoutWidget4.setObjectName(u"layoutWidget4")
        self.layoutWidget4.setGeometry(QRect(20, 10, 231, 61))
        self.verticalLayout_5 = QVBoxLayout(self.layoutWidget4)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.anisotropicCheck = QCheckBox(self.layoutWidget4)
        self.anisotropicCheck.setObjectName(u"anisotropicCheck")

        self.verticalLayout_5.addWidget(self.anisotropicCheck)

        self.bsdfBothSideCheck = QCheckBox(self.layoutWidget4)
        self.bsdfBothSideCheck.setObjectName(u"bsdfBothSideCheck")

        self.verticalLayout_5.addWidget(self.bsdfBothSideCheck)


        self.verticalLayout_6.addWidget(self.sourceSetGb)

        self.layoutWidget5 = QWidget(self.Simulation)
        self.layoutWidget5.setObjectName(u"layoutWidget5")
        self.layoutWidget5.setGeometry(QRect(30, 520, 346, 82))
        self.gridLayout_2 = QGridLayout(self.layoutWidget5)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_16 = QLabel(self.layoutWidget5)
        self.label_16.setObjectName(u"label_16")

        self.gridLayout_2.addWidget(self.label_16, 0, 0, 1, 1)

        self.speosVersionLe = QLineEdit(self.layoutWidget5)
        self.speosVersionLe.setObjectName(u"speosVersionLe")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.speosVersionLe.sizePolicy().hasHeightForWidth())
        self.speosVersionLe.setSizePolicy(sizePolicy)

        self.gridLayout_2.addWidget(self.speosVersionLe, 0, 1, 1, 1)

        self.label_18 = QLabel(self.layoutWidget5)
        self.label_18.setObjectName(u"label_18")

        self.gridLayout_2.addWidget(self.label_18, 0, 2, 1, 1)

        self.label_17 = QLabel(self.layoutWidget5)
        self.label_17.setObjectName(u"label_17")

        self.gridLayout_2.addWidget(self.label_17, 1, 0, 1, 1)

        self.RPCPortLe = QLineEdit(self.layoutWidget5)
        self.RPCPortLe.setObjectName(u"RPCPortLe")

        self.gridLayout_2.addWidget(self.RPCPortLe, 1, 1, 1, 1)

        self.ifLocalhostLe = QCheckBox(self.layoutWidget5)
        self.ifLocalhostLe.setObjectName(u"ifLocalhostLe")
        self.ifLocalhostLe.setChecked(True)

        self.gridLayout_2.addWidget(self.ifLocalhostLe, 1, 2, 1, 1)

        self.label_19 = QLabel(self.layoutWidget5)
        self.label_19.setObjectName(u"label_19")

        self.gridLayout_2.addWidget(self.label_19, 2, 0, 1, 1)

        self.coreNumSb = QSpinBox(self.layoutWidget5)
        self.coreNumSb.setObjectName(u"coreNumSb")
        self.coreNumSb.setMinimum(1)
        self.coreNumSb.setMaximum(1000)
        self.coreNumSb.setSingleStep(1)
        self.coreNumSb.setValue(4)

        self.gridLayout_2.addWidget(self.coreNumSb, 2, 1, 1, 1)

        self.layoutWidget6 = QWidget(self.Simulation)
        self.layoutWidget6.setObjectName(u"layoutWidget6")
        self.layoutWidget6.setGeometry(QRect(151, 481, 351, 28))
        self.horizontalLayout_2 = QHBoxLayout(self.layoutWidget6)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label00 = QLabel(self.layoutWidget6)
        self.label00.setObjectName(u"label00")

        self.horizontalLayout_2.addWidget(self.label00)

        self.resultFolderLe = QLineEdit(self.layoutWidget6)
        self.resultFolderLe.setObjectName(u"resultFolderLe")

        self.horizontalLayout_2.addWidget(self.resultFolderLe)

        self.resultFolderPb = QPushButton(self.layoutWidget6)
        self.resultFolderPb.setObjectName(u"resultFolderPb")
        self.resultFolderPb.setIconSize(QSize(16, 16))

        self.horizontalLayout_2.addWidget(self.resultFolderPb)

        self.horizontalLayout_2.setStretch(0, 1)
        self.horizontalLayout_2.setStretch(1, 20)
        self.horizontalLayout_2.setStretch(2, 1)
        self.stackedSensorWidget.addTab(self.Simulation, "")
        self.Geometries = QWidget()
        self.Geometries.setObjectName(u"Geometries")
        self.groupBox_5 = QGroupBox(self.Geometries)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.groupBox_5.setGeometry(QRect(20, 220, 231, 141))
        self.layoutWidget7 = QWidget(self.groupBox_5)
        self.layoutWidget7.setObjectName(u"layoutWidget7")
        self.layoutWidget7.setGeometry(QRect(20, 20, 189, 108))
        self.formLayout = QFormLayout(self.layoutWidget7)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.label_7 = QLabel(self.layoutWidget7)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_7)

        self.xRatioSb = QDoubleSpinBox(self.layoutWidget7)
        self.xRatioSb.setObjectName(u"xRatioSb")
        self.xRatioSb.setMinimum(10.000000000000000)
        self.xRatioSb.setMaximum(100.000000000000000)
        self.xRatioSb.setSingleStep(10.000000000000000)
        self.xRatioSb.setValue(80.000000000000000)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.xRatioSb)

        self.label_9 = QLabel(self.layoutWidget7)
        self.label_9.setObjectName(u"label_9")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_9)

        self.lineEdit_3 = QLineEdit(self.layoutWidget7)
        self.lineEdit_3.setObjectName(u"lineEdit_3")
        self.lineEdit_3.setEnabled(False)
        self.lineEdit_3.setReadOnly(True)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.lineEdit_3)

        self.label_8 = QLabel(self.layoutWidget7)
        self.label_8.setObjectName(u"label_8")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_8)

        self.yRatioSb = QDoubleSpinBox(self.layoutWidget7)
        self.yRatioSb.setObjectName(u"yRatioSb")
        self.yRatioSb.setMinimum(10.000000000000000)
        self.yRatioSb.setMaximum(100.000000000000000)
        self.yRatioSb.setSingleStep(10.000000000000000)
        self.yRatioSb.setValue(80.000000000000000)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.yRatioSb)

        self.label_10 = QLabel(self.layoutWidget7)
        self.label_10.setObjectName(u"label_10")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_10)

        self.lineEdit_4 = QLineEdit(self.layoutWidget7)
        self.lineEdit_4.setObjectName(u"lineEdit_4")
        self.lineEdit_4.setEnabled(False)
        self.lineEdit_4.setReadOnly(True)

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.lineEdit_4)

        self.layoutWidget8 = QWidget(self.Geometries)
        self.layoutWidget8.setObjectName(u"layoutWidget8")
        self.layoutWidget8.setGeometry(QRect(22, 52, 511, 92))
        self.gridLayout = QGridLayout(self.layoutWidget8)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.layoutWidget8)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 0, 0, 1, 1)

        self.geoAddrLe = QLineEdit(self.layoutWidget8)
        self.geoAddrLe.setObjectName(u"geoAddrLe")

        self.gridLayout.addWidget(self.geoAddrLe, 0, 1, 1, 1)

        self.geoPb = QPushButton(self.layoutWidget8)
        self.geoPb.setObjectName(u"geoPb")
        self.geoPb.setIconSize(QSize(16, 16))

        self.gridLayout.addWidget(self.geoPb, 0, 2, 1, 1)

        self.label_6 = QLabel(self.layoutWidget8)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 1, 0, 1, 1)

        self.vopAddrLe = QLineEdit(self.layoutWidget8)
        self.vopAddrLe.setObjectName(u"vopAddrLe")
        self.vopAddrLe.setMaxLength(399998)

        self.gridLayout.addWidget(self.vopAddrLe, 1, 1, 1, 1)

        self.vopPb = QPushButton(self.layoutWidget8)
        self.vopPb.setObjectName(u"vopPb")

        self.gridLayout.addWidget(self.vopPb, 1, 2, 1, 1)

        self.label_14 = QLabel(self.layoutWidget8)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout.addWidget(self.label_14, 2, 0, 1, 1)

        self.sopAddrLe = QLineEdit(self.layoutWidget8)
        self.sopAddrLe.setObjectName(u"sopAddrLe")
        self.sopAddrLe.setMaxLength(399998)

        self.gridLayout.addWidget(self.sopAddrLe, 2, 1, 1, 1)

        self.sopPb = QPushButton(self.layoutWidget8)
        self.sopPb.setObjectName(u"sopPb")

        self.gridLayout.addWidget(self.sopPb, 2, 2, 1, 1)

        self.layoutWidget9 = QWidget(self.Geometries)
        self.layoutWidget9.setObjectName(u"layoutWidget9")
        self.layoutWidget9.setGeometry(QRect(20, 150, 123, 56))
        self.verticalLayout_4 = QVBoxLayout(self.layoutWidget9)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.opaqueCb = QCheckBox(self.layoutWidget9)
        self.opaqueCb.setObjectName(u"opaqueCb")
        self.opaqueCb.setAutoExclusive(False)

        self.verticalLayout_4.addWidget(self.opaqueCb)

        self.polishedCb = QCheckBox(self.layoutWidget9)
        self.polishedCb.setObjectName(u"polishedCb")
        self.polishedCb.setAutoExclusive(False)

        self.verticalLayout_4.addWidget(self.polishedCb)

        self.stackedSensorWidget.addTab(self.Geometries, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.label_11 = QLabel(self.tab_4)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setGeometry(QRect(30, 20, 84, 26))
        self.samplingModeCombo = QComboBox(self.tab_4)
        self.samplingModeCombo.addItem("")
        self.samplingModeCombo.addItem("")
        self.samplingModeCombo.setObjectName(u"samplingModeCombo")
        self.samplingModeCombo.setGeometry(QRect(260, 20, 148, 26))
        self.stackedSourceWidget = QStackedWidget(self.tab_4)
        self.stackedSourceWidget.setObjectName(u"stackedSourceWidget")
        self.stackedSourceWidget.setEnabled(True)
        self.stackedSourceWidget.setGeometry(QRect(10, 80, 491, 441))
        self.stackedSourceWidget.setFrameShape(QFrame.Shape.Box)
        self.page_3 = QWidget()
        self.page_3.setObjectName(u"page_3")
        self.sourceThetaBox = QGroupBox(self.page_3)
        self.sourceThetaBox.setObjectName(u"sourceThetaBox")
        self.sourceThetaBox.setGeometry(QRect(50, 10, 400, 161))
        self.layoutWidget_2 = QWidget(self.sourceThetaBox)
        self.layoutWidget_2.setObjectName(u"layoutWidget_2")
        self.layoutWidget_2.setGeometry(QRect(10, 30, 196, 106))
        self.formLayout_3 = QFormLayout(self.layoutWidget_2)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.formLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_20 = QLabel(self.layoutWidget_2)
        self.label_20.setObjectName(u"label_20")

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_20)

        self.thetaStartLe = QLineEdit(self.layoutWidget_2)
        self.thetaStartLe.setObjectName(u"thetaStartLe")
        self.thetaStartLe.setEnabled(True)
        self.thetaStartLe.setReadOnly(True)

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.FieldRole, self.thetaStartLe)

        self.label_21 = QLabel(self.layoutWidget_2)
        self.label_21.setObjectName(u"label_21")

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_21)

        self.thetaEndLe = QLineEdit(self.layoutWidget_2)
        self.thetaEndLe.setObjectName(u"thetaEndLe")
        self.thetaEndLe.setEnabled(True)
        self.thetaEndLe.setReadOnly(True)

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.FieldRole, self.thetaEndLe)

        self.label_22 = QLabel(self.layoutWidget_2)
        self.label_22.setObjectName(u"label_22")

        self.formLayout_3.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_22)

        self.thetaSampleSb = QSpinBox(self.layoutWidget_2)
        self.thetaSampleSb.setObjectName(u"thetaSampleSb")
        self.thetaSampleSb.setMinimum(2)
        self.thetaSampleSb.setMaximum(999)
        self.thetaSampleSb.setSingleStep(1)
        self.thetaSampleSb.setValue(9)

        self.formLayout_3.setWidget(2, QFormLayout.ItemRole.FieldRole, self.thetaSampleSb)

        self.label_23 = QLabel(self.layoutWidget_2)
        self.label_23.setObjectName(u"label_23")

        self.formLayout_3.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_23)

        self.thetaStepLe = QLineEdit(self.layoutWidget_2)
        self.thetaStepLe.setObjectName(u"thetaStepLe")
        self.thetaStepLe.setEnabled(True)
        self.thetaStepLe.setReadOnly(True)

        self.formLayout_3.setWidget(3, QFormLayout.ItemRole.FieldRole, self.thetaStepLe)

        self.sourcePhiBox = QGroupBox(self.page_3)
        self.sourcePhiBox.setObjectName(u"sourcePhiBox")
        self.sourcePhiBox.setGeometry(QRect(50, 170, 400, 251))
        self.layoutWidget_3 = QWidget(self.sourcePhiBox)
        self.layoutWidget_3.setObjectName(u"layoutWidget_3")
        self.layoutWidget_3.setGeometry(QRect(10, 30, 196, 106))
        self.formLayout_4 = QFormLayout(self.layoutWidget_3)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.formLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label_24 = QLabel(self.layoutWidget_3)
        self.label_24.setObjectName(u"label_24")

        self.formLayout_4.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_24)

        self.phiStartLe = QLineEdit(self.layoutWidget_3)
        self.phiStartLe.setObjectName(u"phiStartLe")
        self.phiStartLe.setEnabled(True)
        self.phiStartLe.setReadOnly(True)

        self.formLayout_4.setWidget(0, QFormLayout.ItemRole.FieldRole, self.phiStartLe)

        self.label_25 = QLabel(self.layoutWidget_3)
        self.label_25.setObjectName(u"label_25")

        self.formLayout_4.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_25)

        self.phiEndLe = QLineEdit(self.layoutWidget_3)
        self.phiEndLe.setObjectName(u"phiEndLe")
        self.phiEndLe.setEnabled(True)
        self.phiEndLe.setReadOnly(True)

        self.formLayout_4.setWidget(1, QFormLayout.ItemRole.FieldRole, self.phiEndLe)

        self.label_26 = QLabel(self.layoutWidget_3)
        self.label_26.setObjectName(u"label_26")

        self.formLayout_4.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_26)

        self.phiSampleSb = QSpinBox(self.layoutWidget_3)
        self.phiSampleSb.setObjectName(u"phiSampleSb")
        self.phiSampleSb.setMinimum(2)
        self.phiSampleSb.setMaximum(999)
        self.phiSampleSb.setSingleStep(1)
        self.phiSampleSb.setValue(36)

        self.formLayout_4.setWidget(2, QFormLayout.ItemRole.FieldRole, self.phiSampleSb)

        self.label_27 = QLabel(self.layoutWidget_3)
        self.label_27.setObjectName(u"label_27")

        self.formLayout_4.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_27)

        self.phiStepLe = QLineEdit(self.layoutWidget_3)
        self.phiStepLe.setObjectName(u"phiStepLe")
        self.phiStepLe.setEnabled(True)
        self.phiStepLe.setReadOnly(True)

        self.formLayout_4.setWidget(3, QFormLayout.ItemRole.FieldRole, self.phiStepLe)

        self.noSymmetryRb = QRadioButton(self.sourcePhiBox)
        self.noSymmetryRb.setObjectName(u"noSymmetryRb")
        self.noSymmetryRb.setGeometry(QRect(10, 150, 98, 24))
        self.noSymmetryRb.setChecked(True)
        self.symmetryXYRb = QRadioButton(self.sourcePhiBox)
        self.symmetryXYRb.setObjectName(u"symmetryXYRb")
        self.symmetryXYRb.setGeometry(QRect(10, 210, 311, 24))
        self.symmetryXRb = QRadioButton(self.sourcePhiBox)
        self.symmetryXRb.setObjectName(u"symmetryXRb")
        self.symmetryXRb.setGeometry(QRect(10, 180, 261, 24))
        self.stackedSourceWidget.addWidget(self.page_3)
        self.Adaptive_sampling = QWidget()
        self.Adaptive_sampling.setObjectName(u"Adaptive_sampling")
        self.groupBox_6 = QGroupBox(self.Adaptive_sampling)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.groupBox_6.setGeometry(QRect(50, 20, 400, 261))
        self.groupBox_6.setFlat(False)
        self.groupBox_6.setCheckable(False)
        self.layoutWidget10 = QWidget(self.groupBox_6)
        self.layoutWidget10.setObjectName(u"layoutWidget10")
        self.layoutWidget10.setGeometry(QRect(11, 41, 381, 28))
        self.horizontalLayout_4 = QHBoxLayout(self.layoutWidget10)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label_15 = QLabel(self.layoutWidget10)
        self.label_15.setObjectName(u"label_15")

        self.horizontalLayout_4.addWidget(self.label_15)

        self.sourceSampleAddrLe = QLineEdit(self.layoutWidget10)
        self.sourceSampleAddrLe.setObjectName(u"sourceSampleAddrLe")

        self.horizontalLayout_4.addWidget(self.sourceSampleAddrLe)

        self.sourceSamplePb = QPushButton(self.layoutWidget10)
        self.sourceSamplePb.setObjectName(u"sourceSamplePb")
        self.sourceSamplePb.setIconSize(QSize(16, 16))

        self.horizontalLayout_4.addWidget(self.sourceSamplePb)

        self.stackedSourceWidget.addWidget(self.Adaptive_sampling)
        self.stackedSensorWidget.addTab(self.tab_4, "")
        self.Sensor = QWidget()
        self.Sensor.setObjectName(u"Sensor")
        self.label_12 = QLabel(self.Sensor)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setGeometry(QRect(40, 20, 101, 26))
        self.integration_angleLb = QLabel(self.Sensor)
        self.integration_angleLb.setObjectName(u"integration_angleLb")
        self.integration_angleLb.setGeometry(QRect(40, 50, 111, 26))
        self.sensorTypeCombo = QComboBox(self.Sensor)
        self.sensorTypeCombo.addItem("")
        self.sensorTypeCombo.addItem("")
        self.sensorTypeCombo.setObjectName(u"sensorTypeCombo")
        self.sensorTypeCombo.setGeometry(QRect(260, 20, 191, 26))
        self.integratioAngleSb = QDoubleSpinBox(self.Sensor)
        self.integratioAngleSb.setObjectName(u"integratioAngleSb")
        self.integratioAngleSb.setGeometry(QRect(260, 50, 84, 23))
        self.integratioAngleSb.setMinimum(0.200000000000000)
        self.integratioAngleSb.setMaximum(10.000000000000000)
        self.integratioAngleSb.setSingleStep(0.200000000000000)
        self.integratioAngleSb.setValue(2.000000000000000)
        self.sensorAutoRb = QRadioButton(self.Sensor)
        self.sensorAutoRb.setObjectName(u"sensorAutoRb")
        self.sensorAutoRb.setGeometry(QRect(40, 80, 181, 24))
        self.sensorAutoRb.setChecked(True)
        self.sensorPhiGb = QGroupBox(self.Sensor)
        self.sensorPhiGb.setObjectName(u"sensorPhiGb")
        self.sensorPhiGb.setGeometry(QRect(40, 310, 400, 161))
        self.layoutWidget_7 = QWidget(self.sensorPhiGb)
        self.layoutWidget_7.setObjectName(u"layoutWidget_7")
        self.layoutWidget_7.setGeometry(QRect(10, 30, 196, 106))
        self.formLayout_7 = QFormLayout(self.layoutWidget_7)
        self.formLayout_7.setObjectName(u"formLayout_7")
        self.formLayout_7.setContentsMargins(0, 0, 0, 0)
        self.label_37 = QLabel(self.layoutWidget_7)
        self.label_37.setObjectName(u"label_37")

        self.formLayout_7.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_37)

        self.sensorPhiStartLe = QLineEdit(self.layoutWidget_7)
        self.sensorPhiStartLe.setObjectName(u"sensorPhiStartLe")
        self.sensorPhiStartLe.setEnabled(True)
        self.sensorPhiStartLe.setReadOnly(True)

        self.formLayout_7.setWidget(0, QFormLayout.ItemRole.FieldRole, self.sensorPhiStartLe)

        self.label_38 = QLabel(self.layoutWidget_7)
        self.label_38.setObjectName(u"label_38")

        self.formLayout_7.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_38)

        self.sensorPhiEndLe = QLineEdit(self.layoutWidget_7)
        self.sensorPhiEndLe.setObjectName(u"sensorPhiEndLe")
        self.sensorPhiEndLe.setEnabled(True)
        self.sensorPhiEndLe.setReadOnly(True)

        self.formLayout_7.setWidget(1, QFormLayout.ItemRole.FieldRole, self.sensorPhiEndLe)

        self.label_39 = QLabel(self.layoutWidget_7)
        self.label_39.setObjectName(u"label_39")

        self.formLayout_7.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_39)

        self.sensorPhiSampleSb = QSpinBox(self.layoutWidget_7)
        self.sensorPhiSampleSb.setObjectName(u"sensorPhiSampleSb")
        self.sensorPhiSampleSb.setMinimum(2)
        self.sensorPhiSampleSb.setMaximum(999)
        self.sensorPhiSampleSb.setSingleStep(5)
        self.sensorPhiSampleSb.setValue(36)

        self.formLayout_7.setWidget(2, QFormLayout.ItemRole.FieldRole, self.sensorPhiSampleSb)

        self.label_40 = QLabel(self.layoutWidget_7)
        self.label_40.setObjectName(u"label_40")

        self.formLayout_7.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_40)

        self.sensorPhiStepLe = QLineEdit(self.layoutWidget_7)
        self.sensorPhiStepLe.setObjectName(u"sensorPhiStepLe")
        self.sensorPhiStepLe.setEnabled(True)
        self.sensorPhiStepLe.setReadOnly(True)

        self.formLayout_7.setWidget(3, QFormLayout.ItemRole.FieldRole, self.sensorPhiStepLe)

        self.sensorThetaGb = QGroupBox(self.Sensor)
        self.sensorThetaGb.setObjectName(u"sensorThetaGb")
        self.sensorThetaGb.setGeometry(QRect(40, 140, 400, 161))
        self.layoutWidget_8 = QWidget(self.sensorThetaGb)
        self.layoutWidget_8.setObjectName(u"layoutWidget_8")
        self.layoutWidget_8.setGeometry(QRect(10, 30, 196, 106))
        self.formLayout_8 = QFormLayout(self.layoutWidget_8)
        self.formLayout_8.setObjectName(u"formLayout_8")
        self.formLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_41 = QLabel(self.layoutWidget_8)
        self.label_41.setObjectName(u"label_41")

        self.formLayout_8.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_41)

        self.sensorThetaStartLe = QLineEdit(self.layoutWidget_8)
        self.sensorThetaStartLe.setObjectName(u"sensorThetaStartLe")
        self.sensorThetaStartLe.setEnabled(True)
        self.sensorThetaStartLe.setReadOnly(True)

        self.formLayout_8.setWidget(0, QFormLayout.ItemRole.FieldRole, self.sensorThetaStartLe)

        self.label_42 = QLabel(self.layoutWidget_8)
        self.label_42.setObjectName(u"label_42")

        self.formLayout_8.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_42)

        self.sensorThetaEndLe = QLineEdit(self.layoutWidget_8)
        self.sensorThetaEndLe.setObjectName(u"sensorThetaEndLe")
        self.sensorThetaEndLe.setEnabled(True)
        self.sensorThetaEndLe.setAutoFillBackground(False)
        self.sensorThetaEndLe.setReadOnly(True)

        self.formLayout_8.setWidget(1, QFormLayout.ItemRole.FieldRole, self.sensorThetaEndLe)

        self.label_43 = QLabel(self.layoutWidget_8)
        self.label_43.setObjectName(u"label_43")

        self.formLayout_8.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_43)

        self.sensorThetaSampleSb = QSpinBox(self.layoutWidget_8)
        self.sensorThetaSampleSb.setObjectName(u"sensorThetaSampleSb")
        self.sensorThetaSampleSb.setMinimum(2)
        self.sensorThetaSampleSb.setMaximum(999)
        self.sensorThetaSampleSb.setSingleStep(1)
        self.sensorThetaSampleSb.setValue(11)

        self.formLayout_8.setWidget(2, QFormLayout.ItemRole.FieldRole, self.sensorThetaSampleSb)

        self.label_44 = QLabel(self.layoutWidget_8)
        self.label_44.setObjectName(u"label_44")

        self.formLayout_8.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_44)

        self.sensorThetaStepLe = QLineEdit(self.layoutWidget_8)
        self.sensorThetaStepLe.setObjectName(u"sensorThetaStepLe")
        self.sensorThetaStepLe.setEnabled(True)
        self.sensorThetaStepLe.setReadOnly(True)

        self.formLayout_8.setWidget(3, QFormLayout.ItemRole.FieldRole, self.sensorThetaStepLe)

        self.stackedSensorWidget.addTab(self.Sensor, "")
        self.layoutWidget11 = QWidget(self.centralwidget)
        self.layoutWidget11.setObjectName(u"layoutWidget11")
        self.layoutWidget11.setGeometry(QRect(20, 660, 561, 41))
        self.horizontalLayout_3 = QHBoxLayout(self.layoutWidget11)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.runVBB = QPushButton(self.layoutWidget11)
        self.runVBB.setObjectName(u"runVBB")

        self.horizontalLayout_3.addWidget(self.runVBB)

        self.stopSimu = QPushButton(self.layoutWidget11)
        self.stopSimu.setObjectName(u"stopSimu")

        self.horizontalLayout_3.addWidget(self.stopSimu)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 600, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.stackedSensorWidget.setCurrentIndex(0)
        self.rayUnitCb.setCurrentIndex(0)
        self.stackedSourceWidget.setCurrentIndex(0)
        self.sensorTypeCombo.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.wavelengthGb.setTitle(QCoreApplication.translate("MainWindow", u"Wavelength", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"End", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Sampling", None))
        self.rayNumberGb.setTitle(QCoreApplication.translate("MainWindow", u"Ray number", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"(Per analysis configuration)", None))
        self.rayUnitCb.setItemText(0, QCoreApplication.translate("MainWindow", u"Megarays", None))
        self.rayUnitCb.setItemText(1, QCoreApplication.translate("MainWindow", u"Gigarays", None))

        self.rayUnitCb.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Rays", None))
        self.formatDesc.setTitle(QCoreApplication.translate("MainWindow", u"Format Description", None))
        self.allProperty.setText(QCoreApplication.translate("MainWindow", u"BSDF depends on all properties", None))
        self.roughnessOnly.setText(QCoreApplication.translate("MainWindow", u"BSDF depends on surface roughness only", None))
        self.colorDefi.setTitle("")
        self.colorViewDirectionRb.setText(QCoreApplication.translate("MainWindow", u"Color depends on viewing direction", None))
        self.colorNoViewDirectionRb.setText(QCoreApplication.translate("MainWindow", u"Color does not depends on viewing direction", None))
        self.sourceSetGb.setTitle("")
        self.anisotropicCheck.setText(QCoreApplication.translate("MainWindow", u"Anisotropic", None))
        self.bsdfBothSideCheck.setText(QCoreApplication.translate("MainWindow", u"BSDF depends on light incident side", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", u"Speos Version", None))
        self.speosVersionLe.setText(QCoreApplication.translate("MainWindow", u"252", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow", u"e.g. Speos 25R2 = 252", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow", u"Speos RPC Port", None))
        self.RPCPortLe.setText(QCoreApplication.translate("MainWindow", u"50098", None))
        self.ifLocalhostLe.setText(QCoreApplication.translate("MainWindow", u"LocalHost", None))
        self.label_19.setText(QCoreApplication.translate("MainWindow", u"Core Number", None))
        self.label00.setText(QCoreApplication.translate("MainWindow", u"Save to", None))
        self.resultFolderPb.setText(QCoreApplication.translate("MainWindow", u"...", None))
        self.stackedSensorWidget.setTabText(self.stackedSensorWidget.indexOf(self.Simulation), QCoreApplication.translate("MainWindow", u"Simulation", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", u"Analysis area", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"X Ratio                ", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"X Size", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Y Ratio", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Y Size", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Geometry", None))
        self.geoPb.setText(QCoreApplication.translate("MainWindow", u"...", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"VOP         ", None))
        self.vopPb.setText(QCoreApplication.translate("MainWindow", u"...", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"SOP", None))
        self.sopAddrLe.setText("")
        self.sopPb.setText(QCoreApplication.translate("MainWindow", u"...", None))
        self.opaqueCb.setText(QCoreApplication.translate("MainWindow", u"Opaque material", None))
        self.polishedCb.setText(QCoreApplication.translate("MainWindow", u"Optical Polished", None))
        self.stackedSensorWidget.setTabText(self.stackedSensorWidget.indexOf(self.Geometries), QCoreApplication.translate("MainWindow", u"Geometries", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Sampling Mode", None))
        self.samplingModeCombo.setItemText(0, QCoreApplication.translate("MainWindow", u"Uniform", None))
        self.samplingModeCombo.setItemText(1, QCoreApplication.translate("MainWindow", u"Adaptive sampling", None))

        self.samplingModeCombo.setCurrentText(QCoreApplication.translate("MainWindow", u"Uniform", None))
        self.sourceThetaBox.setTitle(QCoreApplication.translate("MainWindow", u"Theta", None))
        self.label_20.setText(QCoreApplication.translate("MainWindow", u"start                           ", None))
        self.thetaStartLe.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.thetaStartLe.setPlaceholderText(QCoreApplication.translate("MainWindow", u"0", None))
        self.label_21.setText(QCoreApplication.translate("MainWindow", u"End", None))
        self.thetaEndLe.setText(QCoreApplication.translate("MainWindow", u"90", None))
        self.thetaEndLe.setPlaceholderText(QCoreApplication.translate("MainWindow", u"90", None))
        self.label_22.setText(QCoreApplication.translate("MainWindow", u"Sampling", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow", u"step", None))
        self.thetaStepLe.setPlaceholderText("")
        self.sourcePhiBox.setTitle(QCoreApplication.translate("MainWindow", u"phi", None))
        self.label_24.setText(QCoreApplication.translate("MainWindow", u"start                           ", None))
        self.phiStartLe.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.phiStartLe.setPlaceholderText(QCoreApplication.translate("MainWindow", u"0", None))
        self.label_25.setText(QCoreApplication.translate("MainWindow", u"End", None))
        self.phiEndLe.setText(QCoreApplication.translate("MainWindow", u"360", None))
        self.phiEndLe.setPlaceholderText(QCoreApplication.translate("MainWindow", u"360", None))
        self.label_26.setText(QCoreApplication.translate("MainWindow", u"Sampling", None))
        self.label_27.setText(QCoreApplication.translate("MainWindow", u"step", None))
        self.noSymmetryRb.setText(QCoreApplication.translate("MainWindow", u"No symmetry", None))
        self.symmetryXYRb.setText(QCoreApplication.translate("MainWindow", u"Symmetry to planes 0-180 90-270", None))
        self.symmetryXRb.setText(QCoreApplication.translate("MainWindow", u"Symmetry to plane 0-180", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("MainWindow", u"Adaptive Sampling", None))
        self.label_15.setText(QCoreApplication.translate("MainWindow", u"File", None))
        self.sourceSamplePb.setText(QCoreApplication.translate("MainWindow", u"...", None))
        self.stackedSensorWidget.setTabText(self.stackedSensorWidget.indexOf(self.tab_4), QCoreApplication.translate("MainWindow", u"Source", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Sensor Type", None))
        self.integration_angleLb.setText(QCoreApplication.translate("MainWindow", u"Integration angle", None))
        self.sensorTypeCombo.setItemText(0, QCoreApplication.translate("MainWindow", u"Reflection and Transmission", None))
        self.sensorTypeCombo.setItemText(1, QCoreApplication.translate("MainWindow", u"Reflection only", None))

        self.sensorAutoRb.setText(QCoreApplication.translate("MainWindow", u"Automated Sampling", None))
        self.sensorPhiGb.setTitle(QCoreApplication.translate("MainWindow", u"phi", None))
        self.label_37.setText(QCoreApplication.translate("MainWindow", u"start                           ", None))
        self.sensorPhiStartLe.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.sensorPhiStartLe.setPlaceholderText(QCoreApplication.translate("MainWindow", u"0", None))
        self.label_38.setText(QCoreApplication.translate("MainWindow", u"End", None))
        self.sensorPhiEndLe.setText(QCoreApplication.translate("MainWindow", u"360", None))
        self.sensorPhiEndLe.setPlaceholderText(QCoreApplication.translate("MainWindow", u"360", None))
        self.label_39.setText(QCoreApplication.translate("MainWindow", u"Sampling", None))
        self.label_40.setText(QCoreApplication.translate("MainWindow", u"step", None))
        self.sensorThetaGb.setTitle(QCoreApplication.translate("MainWindow", u"Theta", None))
        self.label_41.setText(QCoreApplication.translate("MainWindow", u"start                           ", None))
        self.sensorThetaStartLe.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.sensorThetaStartLe.setPlaceholderText(QCoreApplication.translate("MainWindow", u"0", None))
        self.label_42.setText(QCoreApplication.translate("MainWindow", u"End", None))
        self.sensorThetaEndLe.setText(QCoreApplication.translate("MainWindow", u"180", None))
        self.sensorThetaEndLe.setPlaceholderText("")
        self.label_43.setText(QCoreApplication.translate("MainWindow", u"Sampling", None))
        self.label_44.setText(QCoreApplication.translate("MainWindow", u"step", None))
        self.stackedSensorWidget.setTabText(self.stackedSensorWidget.indexOf(self.Sensor), QCoreApplication.translate("MainWindow", u"Sensor", None))
        self.runVBB.setText(QCoreApplication.translate("MainWindow", u"Generate VBB", None))
        self.stopSimu.setText(QCoreApplication.translate("MainWindow", u"Stop Generation", None))
    # retranslateUi

