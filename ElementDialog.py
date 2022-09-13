# ElementDialog.py
# Class for editing element parameters
# 13.09.2022, Floery Tobias
# Released under GNU Public License (GPL)

from PyQt5.QtWidgets import QDialog, QFormLayout, QComboBox, QListWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
        QWidget, QLabel, QColorDialog, QDoubleSpinBox, QShortcut, QListWidgetItem, QCheckBox

from PyQt5 import QtGui, QtCore
from OpticalElement import *

class ColorButton(QPushButton):
    colorChanged = QtCore.pyqtSignal(object)

    def __init__(self, *args, color=None, **kwargs):
        super(ColorButton, self).__init__(*args, **kwargs)

        self._color = color
        self.pressed.connect(self.onColorPicker)
        self.setObjectName("ColorChooserButton")

        # Set the initial/default state.
        self.setColor(self._color)

    def setColor(self, color):
        if color != self._color:
            self._color = color
            self.colorChanged.emit(color)

        if self._color:
            self.setStyleSheet("QPushButton#ColorChooserButton {background-color: %s;}" % self._color.name())
        else:
            self.setStyleSheet("QPushButton#ColorChooserButton {}")

    def color(self):
        return self._color

    def onColorPicker(self):

        dlg = QColorDialog(self)
        dlg.setOption(QColorDialog.ShowAlphaChannel, on=True)

        if self._color:
            dlg.setCurrentColor(self._color)

        if dlg.exec_():
            self.setColor(dlg.currentColor())

class ColorBoxFloatListItem(QListWidgetItem):

    def __init__(self, label, color = None):
        super(ColorBoxFloatListItem, self).__init__(label)
        self.setColor(color)

    def setColor(self, color : QtGui.QColor):
        
        self.color = color
        pm = self.createColorPixmap(color)
        self.setIcon(QtGui.QIcon(pm))

    def createColorPixmap(self, color):
        pm = QtGui.QPixmap(64,64)
        pm.fill(QtCore.Qt.GlobalColor.transparent)
        if color is not None:
            color.setAlphaF(1.0)

            painter = QtGui.QPainter(pm) 
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            painter.setBrush(QtGui.QBrush(color))
            painter.drawRect(0,0,64,64)
            painter.end()
        return pm
    
    def __lt__(self, other):
        
        try:
            return float(self.text()) < float(other.text())
        except Exception:
            return QListWidgetItem.__lt__(self, other)        
    
class ElementDialog(QDialog):
    def __init__(self, element, parent = None):
        super(ElementDialog, self).__init__(parent)
        
        # self.scaledKeys = ["r1", "r2", "height", "thickness"]
        
        self.changes = {}

        self.setWindowTitle(element.__class__.__name__)

        self.element = element
        self.istate = element.getState()
        self.state = self.istate.copy()

        if "color" in self.state:
            self.colors = [QtGui.QColor().fromRgb(*x) for x in self.state["color"]]

        layout = QVBoxLayout()
        self.mainWidget = QWidget()
        
        # layout.addWidget(self.mainWidget)
        fLayout = QFormLayout()
        self.createFields(fLayout)
        layout.addLayout(fLayout)

        buttonBox = QHBoxLayout()
        self.okButton = QPushButton("OK")
        self.okButton.setDefault(True)
        self.okButton.clicked.connect(self.accept)
        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.reject)
        buttonBox.addWidget(self.okButton)
        buttonBox.addWidget(self.cancelButton)
        layout.addLayout(buttonBox)

        self.setLayout(layout)

    def createFields(self, layout):
        # print(self.state)
        
        for k,v in self.state.items():
            
            if k == "type":
                continue

            # print(type(v))
            
            elif k == "arrows":
                cb = QCheckBox("show Arrows")
                cb.setChecked(self.state["arrows"])
                cb.stateChanged.connect(self.arrowChanged)
                layout.addRow("", cb)

            elif k == "color":
            #     color = QtGui.QColor().fromRgb(*self.state["color"])
            #     btn = ColorButton()
            #     btn.colorChanged.connect(self.colorChanged)
            #     layout.addRow("Color", btn)
                pass
            elif k == "pos":
                hbox = QHBoxLayout()
                
                
                x,y = self.state["pos"]
                
                hbox.addWidget(QLabel("x"))
                
                self.sbX = QDoubleSpinBox()
                self.sbX.setDecimals(1)
                self.sbX.setMinimum(-10000)
                self.sbX.setMaximum(10000)
                self.sbX.setValue(x)
                self.sbX.valueChanged.connect(self.posChanged)
                hbox.addWidget(self.sbX)
                
                
                hbox.addWidget(QLabel("y"))

                self.sbY = QDoubleSpinBox()
                self.sbY.setDecimals(1)
                self.sbY.setMinimum(-10000)
                self.sbY.setMaximum(10000)
                self.sbY.setValue(y)
                self.sbY.valueChanged.connect(self.posChanged)
                hbox.addWidget(self.sbY)

                layout.addRow("Position", hbox)
            elif k == "rot":
                sbRot = QDoubleSpinBox()
                sbRot.setMinimum(-360.0*4)
                sbRot.setMaximum(360.0*4)
                sbRot.setDecimals(1)
                sbRot.setValue(self.state["rot"])
                sbRot.valueChanged.connect(self.rotChanged)
                layout.addRow("Rotation", sbRot)
            elif k == "intensity":
                sbInt = QDoubleSpinBox()
                sbInt.setMinimum(0.0)
                sbInt.setMaximum(100.0)
                sbInt.setSingleStep(0.1)
                sbInt.setDecimals(1)
                sbInt.setValue(self.state["intensity"])
                sbInt.valueChanged.connect(self.intChanged)
                layout.addRow("Intensity", sbInt)
            elif k == "wl":
                vbox = QVBoxLayout()
                
            
                self.lwWL = QListWidget()
                # self.lwWL.setIconSize(QtCore.QSize(32,32))
                self.lwWL.setSortingEnabled(True)

                for idx, wl in enumerate(self.state["wl"]):
                    if len(self.colors) == len(self.state["wl"]):
                        col = self.colors[idx]
                    else:
                        col = self.colors[0]

                    itm = ColorBoxFloatListItem(f"{wl:.3f}", col)

                    self.lwWL.addItem(itm)
                    
                # self.lwWL.addItems(wls)
                self.lwWL.setFixedWidth(150)

                vbox.addWidget(self.lwWL)
                
                hbox = QHBoxLayout()
                # self.leNewWL = QLineEdit("")
                # hbox.addWidget(self.leNewWL)
                self.sbWL = QDoubleSpinBox()
                self.sbWL.setMinimum(0.001)
                self.sbWL.setValue(1.03)
                self.sbWL.setMaximum(20.0)
                self.sbWL.setDecimals(3)
                self.sbWL.setSingleStep(0.1)
                hbox.addWidget(self.sbWL)
                btn = QPushButton("+")
                btn.clicked.connect(self.addWLEntry)
                hbox.addWidget(btn)
                btn = QPushButton("-")
                btn.clicked.connect(self.delWLEntry)                
                hbox.addWidget(btn)
                
                                
                vbox.addLayout(hbox)
                layout.addRow("Wavelength", vbox)
                
                sc = QShortcut(QtCore.Qt.Key.Key_Delete, self.lwWL)
                sc.activated.connect(self.delWLEntry)
                
                
                # le = QLineEdit(str(self.state["wl"])[1:-1])
                # layout.addRow("Wavelength", le)
            elif k == "mat":
                self.cbMat = QComboBox()
                self.cbMat.addItems(Materials().listMaterials())
                self.cbMat.setCurrentText(self.state["mat"])
                self.cbMat.currentIndexChanged.connect(self.matChanged)
                layout.addRow("Material", self.cbMat)
            else:
                sbEdit = QDoubleSpinBox()
                sbEdit.setMinimum(-10000)
                sbEdit.setMaximum(10000)
                sbEdit.setDecimals(2)
                sbEdit.setSingleStep(0.1)
                if v is None:
                    v = 0
                sbEdit.setValue(v)
                # sbEdit.setData()
                sbEdit.valueChanged.connect(lambda x,k=k: self.valChange(x, k))
                layout.addRow(k, sbEdit)
                # break
                # layout.addRow(k, QLineEdit(str(v)))
                

    def arrowChanged(self, state):
        self.state["arrows"] = state
        
    def valChange(self, value, key):
        if key == "r1" or key == "r2":
            if value == 0:
                value = None
                
        # print(key, value)
        self.state[key] = value
                
    def matChanged(self, idx):
        self.state["mat"] = self.cbMat.currentText()
        
        
    def delWLEntry(self):
        itms = self.lwWL.selectedItems()
        for itm in itms:
            self.lwWL.takeItem(self.lwWL.row(itm))
            
        self.updateWavelength()
        
    def addWLEntry(self):
        itm = ColorBoxFloatListItem(f"{self.sbWL.value():.3f}")

        out = self.lwWL.findItems(itm.text(), QtCore.Qt.MatchFlag.MatchExactly)
        
        if len(out) < 1:
            self.lwWL.addItem(itm)
            
        self.updateWavelength()
        
    def updateWavelength(self):
        wls =  [float(self.lwWL.item(i).text()) for i in range(self.lwWL.count())]
        # print(wls)
        self.state["wl"] = wls
        colors = self.element.getColors(wls)
        # QtGui.QColor().getRgbF()

        self.state["color"] = [x.getRgb() for x in colors]

        for i in range(self.lwWL.count()):
            itm = self.lwWL.item(i)
            itm.setColor(colors[i])
        
    def intChanged(self, val):
        self.state["intensity"] = val
        
    def rotChanged(self, val):
        self.state["rot"] = val
        
        
    def posChanged(self, val):        
        self.state["pos"] = [self.sbX.value(), self.sbY.value()]
        
    def colorChanged(self, color):
        self.state["color"] = color.getRgb()

    def reject(self) -> None:
        # print("reject")
        self.state = self.istate
        return super().reject()

    def accept(self) -> None:
        # print("accept")
        changed = False
        for k,v in self.state.items():
            if self.istate[k] != v:
                # print("changed: ",k,v, " was ", self.istate[k])
                changed = True
                self.changes[k] = v
        # if not changed:
            # print("no changes")
        return super().accept()

    def done(self, a0: int) -> None:
        # print("done")
        return super().done(a0)

    
class RayDialog(ElementDialog):
    def __init__(self, element):
        super(RayDialog, self).__init__(element)



        # layout = QVBoxLayout()


        # layout.addWidget(QLabel("Ray"))

        # self.mainWidget.setLayout(layout)
