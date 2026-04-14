# Copyright (C) 2024 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt, QStandardPaths)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFormLayout, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMenuBar,
    QPushButton, QRadioButton, QSizePolicy, QSpinBox,
    QStackedWidget, QStatusBar, QTabWidget, QVBoxLayout,
    QWidget,QFileDialog,QDialogButtonBox,QDialog)
"""
from PySide6.QtCore import (QThread,Slot,Signal,Qt)
from PySide6.QtWidgets import (QApplication,
    QMainWindow,QFileDialog,QMessageBox)

from vbbui_designer import Ui_MainWindow
#from toolfunction import latest_subdir_by_dir_mtime,copy_latest_subdir_overwrite
#import pyvista as pv
#from ansys.speos.core import project,launcher,speos
#from ansys.speos.core.simulation import SimulationVirtualBSDF

#from dataclasses import dataclass
#from typing import Optional
from setup_data import speos_config
from speos_worker import sim_worker
#from ansys.speos.core.bsdf import AnisotropicBSDF


class vbbwindow(Ui_MainWindow, QMainWindow):
    send_job = Signal(speos_config)
    cancel_job = Signal()
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Virtual BSDF Builder v0.2.2")
        self._simulationTab()
        self._geometryTab()
        self._sourceTab()
        self._sensorTab()
        self._thread: QThread | None = None
        self._worker: sim_worker | None = None
        self.runVBB.clicked.connect(self._on_run_clicked)
        self.stopSimu.clicked.connect(self._on_cancel_clicked)
        self.stopSimu.setEnabled(False)
        self.stopSimu.setVisible(False) # hide stop button for now
    def _simulationTab(self):
        self.roughnessOnly.toggled.connect(self.colorDefi.setDisabled)
        if self.sourceSetGb.isEnabled():
            self.roughnessOnly.toggled.connect(self.sourceSetGb.setDisabled)
        self.roughnessOnly.toggled.connect(self.colorNoViewDirectionRb.setChecked)
        self.roughnessOnly.toggled.connect(lambda checked: self.anisotropicCheck.setChecked(False if checked else False))
        self.roughnessOnly.toggled.connect(lambda checked: self.bsdfBothSideCheck.setChecked(False if checked else False))
        self.roughnessOnly.toggled.connect(lambda checked: self.sensorTypeCombo.setCurrentIndex(1 if checked else 0))
        self.roughnessOnly.toggled.connect(self.sensorTypeCombo.setDisabled)
        self.resultFolderPb.clicked.connect(lambda _: self._select_directory())
        self.wavelengthEnd.setMinimum(self.wavelengthStart.value())
        self.wavelengthStart.valueChanged.connect(lambda val: self.wavelengthEnd.setMinimum(val))

        #self.roughnessOnly.toggled.connect(lambda checked:self.resultTypeLe.setText("Resulting File Type: Unpolished Files(.*unpolished)"))
        self.anisotropicCheck.toggled.connect(lambda checked: self.sourcePhiBox.setVisible(checked))
        if self.anisotropicCheck.isEnabled():
            self.colorViewDirectionRb.toggled.connect(self.anisotropicCheck.setDisabled)
        self.bsdfBothSideCheck.toggled.connect(lambda checked:self.thetaEndLe.setText("180" if checked else "90"))
        #self.bsdfBothSideCheck.toggled.connect(lambda checked:self.resultTypeLe.setText("Resulting File Type: BSDF 180 Files(.*bsdf180)"))
        #if not self.bsdfBothSideCheck.isChecked():
        #    self.anisotropicCheck.toggled.connect(lambda checked:self.resultTypeLe.setText("Resulting File Type: Anisotropic BSDF Files(.*anisotropicbsdf)"))
        self.roughnessOnly.toggled.connect(self._update_line)
        self.allProperty.toggled.connect(self._update_line)
        self.colorNoViewDirectionRb.toggled.connect(self._update_line)
        self.colorViewDirectionRb.toggled.connect(self._update_line)
        self.anisotropicCheck.stateChanged.connect(self._update_line)
        self.bsdfBothSideCheck.stateChanged.connect(self._update_line)
        self._update_line()
    def _update_line(self):
        if self.roughnessOnly.isChecked():
            self.resultTypeLe.setText("Resulting File Type: Unpolished Files(.*unpolished)")
        elif self.bsdfBothSideCheck.isChecked():
                self.resultTypeLe.setText("Resulting File Type: BSDF 180 Files(.*bsdf180)")
        elif self.anisotropicCheck.isChecked():
                self.resultTypeLe.setText("Resulting File Type: Anisotropic BSDF Files(.*anisotropicbsdf)")
        elif self.colorViewDirectionRb.isChecked():
                self.resultTypeLe.setText("Resulting File Type: Complete scattering Files-BRDF(.*brdf)")
        elif self.colorNoViewDirectionRb.isChecked():
                self.resultTypeLe.setText("Resulting File Type: Anisotropic BSDF Files(.*anisotropicbsdf)")
    
    def _select_directory(self):
            
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select directory",       
            "",                      
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        if directory:
            self.resultFolderLe.setText(f"{directory}")
        else:
            self.resultFolderLe.setText("Invalid directory selected.")
    
    def _geometryTab(self):
        self.geoPb.clicked.connect(lambda _: self._open_file_dialog(filetype = "stl (*.stl)",toLineEdit = self.geoAddrLe))
        self.vopPb.clicked.connect(lambda _: self._open_file_dialog(filetype = "vop (*.material)",toLineEdit = self.vopAddrLe))
        vopfiletype:str = """Supported files (*.simplescattering,*.scattering,*.brdf,*.bsdf,*.bsdf180,*.coated,*.anisotropic,*.anisotropicbsdf,*.unpolished);;
        Simple scattering Files (*.simplescattering);;Advanced scattering Files (*.scattering);;
        Complete scattering Files-BRDF (*.brdf);;Simple BSDF Files(*.bsdf);;BSDF 180 Files(*.bsdf180);;Coated Files(*.coated);;Anisotropic scattering Files(*.anisotropic);;
        Anisotropic BSDF Files(*.anisotropicbsdf);;Unpolished Files(*.unpolished);;All File (*)"""
        self.sopPb.clicked.connect(lambda _: self._open_file_dialog(vopfiletype,toLineEdit = self.sopAddrLe))
        self.opaqueCb.toggled.connect(lambda checked: self.vopAddrLe.setDisabled(checked))
        self.opaqueCb.toggled.connect(lambda checked: self.vopPb.setDisabled(checked))
        self.polishedCb.toggled.connect(lambda checked: self.sopAddrLe.setDisabled(checked))
        self.polishedCb.toggled.connect(lambda checked: self.sopPb.setDisabled(checked))
        

    def _open_file_dialog(self,filetype,toLineEdit):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "select geometry file",
            "",  # start path "C:/Users"
            filetype
        )
        if file_path:
            toLineEdit.setText(file_path)  # set selected file path to line edit
    
    def _sourceTab(self):
        self.samplingModeCombo.setCurrentIndex(0)
        self.stackedSourceWidget.setCurrentIndex(0)
        self.samplingModeCombo.currentIndexChanged.connect(self.stackedSourceWidget.setCurrentIndex)
        self.thetaEndLe.setStyleSheet("QLineEdit { color: gray; }")
        self.thetaStartLe.setStyleSheet("QLineEdit { color: gray; }")
        self.thetaStepLe.setStyleSheet("QLineEdit { color: gray; }")
        self.phiEndLe.setStyleSheet("QLineEdit { color: gray; }")
        self.phiStartLe.setStyleSheet("QLineEdit { color: gray; }")
        self.phiStepLe.setStyleSheet("QLineEdit { color: gray; }")
        #set default values for symmetry options
        self.noSymmetryRb.toggled.connect(lambda checked: self.phiEndLe.setText("360"))
        self.symmetryXRb.toggled.connect(lambda checked: self.phiEndLe.setText("180"))
        self.symmetryXYRb.toggled.connect(lambda checked: self.phiEndLe.setText("90"))
        
        #calculate theta step and display
        self.thetaEndLe.textChanged.connect( lambda _:self._update_result(self.thetaEndLe,self.thetaSampleSb,self.thetaStepLe))
        self.thetaSampleSb.valueChanged.connect( lambda _:self._update_result(self.thetaEndLe,self.thetaSampleSb,self.thetaStepLe))
        self._update_result(self.thetaEndLe,self.thetaSampleSb,self.thetaStepLe)
        #calculate phi step and display
        self.phiEndLe.textChanged.connect( lambda _:self._update_result(self.phiEndLe,self.phiSampleSb,self.phiStepLe))
        self.phiSampleSb.valueChanged.connect( lambda _:self._update_result(self.phiEndLe,self.phiSampleSb,self.phiStepLe))
        self._update_result(self.phiEndLe,self.phiSampleSb,self.phiStepLe)
        self.sourceSamplePb.clicked.connect(lambda _: self._open_file_dialog(filetype = "Sample File (*.txt)",toLineEdit = self.sourceSampleAddrLe))
            
    def _sensorTab(self):
        self.sourcePhiBox.setVisible(False)
        #self.samplingModeText.setVisible(False)
        #self.sensorSamplingModeCb.setVisible(False)
        self.sensorThetaGb.setVisible(False)
        self.sensorPhiGb.setVisible(False)
        #self.sensorAutoRb.setChecked(True)
        # 需要先check一次状态以设置初始可见性
        self.sensorAutoRb.toggled.connect(lambda checked: (
            #self.samplingModeText.setVisible(not checked),
            #self.sensorSamplingModeCb.setVisible(not checked),
            #self.sensorSamplingWidget.setVisible(not checked)
            self.sensorThetaGb.setVisible(not checked),
            self.sensorPhiGb.setVisible(not checked)
            ))

        #self.sensorSamplingModeCb.setCurrentIndex(0)
        #self.sensorSamplingWidget.setCurrentIndex(0)
        #self.sensorSamplingModeCb.currentIndexChanged.connect(self.sensorSamplingWidget.setCurrentIndex)
        self.sensorThetaEndLe.setStyleSheet("QLineEdit { color: gray; }")
        self.sensorThetaStartLe.setStyleSheet("QLineEdit { color: gray; }")
        self.sensorThetaStepLe.setStyleSheet("QLineEdit { color: gray; }")
        self.sensorPhiEndLe.setStyleSheet("QLineEdit { color: gray; }")
        self.sensorPhiStartLe.setStyleSheet("QLineEdit { color: gray; }")
        self.sensorPhiStepLe.setStyleSheet("QLineEdit { color: gray; }")
        self.sensorTypeCombo.currentTextChanged.connect(lambda checked:self.sensorThetaEndLe.setText("180" if checked=="Reflection and Transmission" else "90"))
        
        #calculate theta step and display
        self.sensorThetaEndLe.textChanged.connect( lambda _:self._update_result(self.sensorThetaEndLe,self.sensorThetaSampleSb,self.sensorThetaStepLe))
        self.sensorThetaSampleSb.valueChanged.connect( lambda _:self._update_result(self.sensorThetaEndLe,self.sensorThetaSampleSb,self.sensorThetaStepLe))
        self._update_result(self.sensorThetaEndLe,self.sensorThetaSampleSb,self.sensorThetaStepLe)
        #calculate phi step and display
        self.sensorPhiEndLe.textChanged.connect( lambda _:self._update_result(self.sensorPhiEndLe,self.sensorPhiSampleSb,self.sensorPhiStepLe))
        self.sensorPhiSampleSb.valueChanged.connect( lambda _:self._update_result(self.sensorPhiEndLe,self.sensorPhiSampleSb,self.sensorPhiStepLe))
        self._update_result(self.sensorPhiEndLe,self.sensorPhiSampleSb,self.sensorPhiStepLe)
        #self.sampleAddrPb.clicked.connect(lambda _: self._open_file_dialog(filetype = "Sample File (*.txt)",toLineEdit = self.sensorAddrLe))
    
    def _collectJob(self) -> speos_config:
        return speos_config(
            roughness_only = self.roughnessOnly.isChecked(),
            #all_property: bool
            iridescence = self.colorViewDirectionRb.isChecked(),
            #non_iridesense:bool
            anisotropic = self.anisotropicCheck.isChecked(),
            bsdf_180 = self.bsdfBothSideCheck.isChecked(),
            wl_start = self.wavelengthStart.value(),
            wl_end = self.wavelengthEnd.value(),
            wl_sampling = self.wavelengthSampling.value(),
            ray_unit = self.rayUnitCb.currentText().strip(), # "Megarays" or "Gigarays"
            ray_value = self.rayNumSb.value(),
            threads_num = int(self.coreNumSb.value()),          # 线程数
            result_path= self.resultFolderLe.text().strip(),
            #home_path= QStandardPaths.writableLocation(QStandardPaths.HomeLocation),
            hostname= ("localhost" if self.ifLocalhostLe.isChecked()
                        else "remote"),
           # "localhost" or 远端主机名
            grpc_port= int(self.RPCPortLe.text().strip()),
            speos_version= self.speosVersionLe.text().strip(),
            #Geometry
            opaque= self.opaqueCb.isChecked(),
            polished= self.polishedCb.isChecked(),
            geo_path= self.geoAddrLe.text().strip(),
            vop_path= self.vopAddrLe.text().strip(),
            sop_path= self.sopAddrLe.text().strip(),
            x_ratio= self.xRatioSb.value(),
            y_ratio= self.yRatioSb.value(),
            #Source
            sampling_mode= self.samplingModeCombo.currentText().strip(),         # "Adaptive sampling" / "Uniform"
            sampling_file = self.sourceSampleAddrLe.text().strip() if self.samplingModeCombo.currentText().strip() == "Adaptive sampling" else None,
            theta_sampling= int(self.thetaSampleSb.value()),
            phi_sampling = int(self.phiSampleSb.value()),
            symmetry= ("none" if self.noSymmetryRb.isChecked()
                        else "x" if self.symmetryXRb.isChecked()
                        else "xy"),               # "none" / "x" / "xy"
            #Sensor
            sensor_RT= (True if self.sensorTypeCombo.currentText().strip() == "Reflection and Transmission" 
                        else False),
            sensor_auto = self.sensorAutoRb.isChecked(),
            sensor_theta_sample= int(self.sensorThetaSampleSb.value()),
            sensor_phi_sample= int(self.sensorPhiSampleSb.value()),
            integration_angle = self.integratioAngleSb.value()
        )
    
    def _on_run_clicked(self):
        vbb_params = self._collectJob()
        if self._thread is not None:
            QMessageBox.information(self, "Info", "Simulation already running")
            return
        # Simple checks
        if not vbb_params.geo_path:
            QMessageBox.warning(self, "Warning", "Geometry path is empty.")
            return
        if vbb_params.opaque and vbb_params.polished:
            QMessageBox.warning(self, "Warning", "Material can not be opaque and polished")
            return
        if not vbb_params.result_path or vbb_params.result_path == "Invalid directory selected.":
            QMessageBox.warning(self, "Warning", "Save to path is empty or invalid.")
            return
        self._thread = QThread(self)
        self._worker = sim_worker()
        self._worker.moveToThread(self._thread)
        # Connect Signal UI -> Worker
        self.send_job.connect(self._worker.speos_start)
        self.cancel_job.connect(self._worker.speos_cancel, Qt.DirectConnection)
        self.cancel_job.connect(self._worker.speos_cancel)
        # Connect Signal Worker->UI
        self._worker.progress.connect(self._on_progress)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._on_finished)
        # EndThread
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)
        self.runVBB.setEnabled(False)
        #try:
        #    self.stopSimu.setEnabled(True)
        #except Exception:
        #    pass
        self.statusbar.showMessage("Mission Starting...")
        self._thread.start()

        # Send UI to Worker（QueuedConnection）
        self.send_job.emit(vbb_params)
        
    
    def _on_cancel_clicked(self): 
        #print('clicked')
        self.statusbar.showMessage("Cancelling...")
        self.cancel_job.emit()
            #self._thread.join()
            

    # ---- slots ----
    def _on_progress(self, msg: str):
        self.statusbar.showMessage(msg)
        if msg == "Generating...":
            self.stopSimu.setEnabled(True)  # enable stop button when simulation starts

    def _on_error(self, text: str):
        #try:
        #    self.__raise_error(text)  
        #except Exception:
        QMessageBox.critical(self, "Error", text)

    def _on_finished(self, success: bool):
        if success:
            self.statusbar.showMessage(f"Simulation succeeded.")
        else:
            self.statusbar.showMessage(f"Simulation failed/canceled.")

        self.runVBB.setEnabled(True)
        try:
            self.stopSimu.setEnabled(False)
        except Exception:
            pass

    def _on_thread_finished(self): #
        self._thread = None
        self._worker = None
        
        
      
    def _update_result(self,lineTextIn,spinBox,linetoEdit):
        Max:float = float(lineTextIn.text().strip())
        Sample:int = spinBox.value()
        result:flo = Max / (Sample-1)
        formatted:str = f"{result:.3f}".rstrip("0").rstrip(".")
        linetoEdit.setText(formatted)

if __name__ == "__main__":
    app = QApplication([])
    window = vbbwindow()
    window.show()
    app.exec()