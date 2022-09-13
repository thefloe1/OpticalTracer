# OpticalTracer
# Work in progress for a simple optical raytraces supporting mirrors, lenses, prisms and gratings
# 13.09.2022, Floery Tobias
# Released under GNU Public License (GPL)

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, \
        QSpinBox, QPushButton, QVBoxLayout, QLabel, QFileDialog, \
        QDoubleSpinBox, QListWidget, QListWidgetItem

from PyQt5 import QtGui, QtCore, QtPrintSupport, QtSvg

QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons

from TraceScene import *
from MyGraphicsView import *
from OpticalElement import *

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__(None)

        self.openFileName = ""

        menuBar = self.menuBar()
        
        fileMenu = menuBar.addMenu("&File")
        
        fileMenu.addAction("&New", lambda: self.newFile())
        fileMenu.addAction("&Open", lambda: self.loadFile())
        fileMenu.addAction("&Save", lambda: self.writeFile())
        fileMenu.addAction("&Save As", lambda: self.writeFile(True))
        fileMenu.addAction("&Export", lambda: self.printView(True))
        fileMenu.addAction("&Print", lambda:self.printView())
        fileMenu.addAction("E&xit", lambda:self.close())
        
        editMenu = menuBar.addMenu("&Edit")
        
        editMenu.addAction("Undo",lambda: self.view.scene().undo(), QtGui.QKeySequence("CTRL+Z"))
        
        sceneMenu = menuBar.addMenu("&Scene")
        sceneMenu.addAction("&Fit", lambda: self.view.scaleToContent())
        sceneMenu.addAction("&Recalculate", lambda: self.resetScene())
        sceneMenu.addAction("&List", lambda: self.view.scene().list())
        
        scene = TraceScene(self, drawLines=True)
        
        self.view = MyGraphicsView(scene, self)
        self.view.setMinimumSize(800,600)
        
        w = QWidget()
        hbox = QHBoxLayout()
        w.setLayout(hbox)

        vbox = QVBoxLayout()

        spin = QSpinBox(w)
        spin.setMinimum(10)
        spin.setMaximum(1000)
        spin.setValue(scene.getGridSize())
        spin.valueChanged.connect(self.gridChange)
        vbox.addWidget(QLabel("Grid"))
        vbox.addWidget(spin)

        sbAngle = QDoubleSpinBox()
        sbAngle.setMinimum(0)
        sbAngle.setMaximum(360)
        sbAngle.setDecimals(1)
        sbAngle.setValue(45)
        sbAngle.valueChanged.connect(self.updteAngleIncrement)

        vbox.addWidget(QLabel("Angle Increment"))
        vbox.addWidget(sbAngle)
        
        btn = QPushButton("undo")
        btn.clicked.connect(lambda x: self.view.scene().undo())
        vbox.addWidget(btn)

        iconSize = QtCore.QSize(48,48)
        lbox = QListWidget()
        lbox.setMinimumWidth(120)

        lbox.setDragEnabled(True)
        lbox.setIconSize(iconSize)
        
        itm = QListWidgetItem(QtGui.QIcon(RayElement(0,0,100,100).getPixmap()), "Ray")
        lbox.addItem(itm)

        itm = QListWidgetItem(QtGui.QIcon(MirrorElement().getPixmap()), "Mirror")
        lbox.addItem(itm)

        itm = QListWidgetItem(QtGui.QIcon(LensElement().getPixmap()), "Lens")
        lbox.addItem(itm)

        itm = QListWidgetItem(QtGui.QIcon(PrismElement().getPixmap()), "Prism")
        lbox.addItem(itm)

        itm = QListWidgetItem(QtGui.QIcon(GratingElement().getPixmap()), "Grating")
        lbox.addItem(itm)

        itm = QListWidgetItem(QtGui.QIcon(BeamBlockElement().getPixmap()), "Beamblock")
        lbox.addItem(itm)

        vbox.addWidget(lbox, 2)

        # vbox.addStretch(1)

        hbox.addLayout(vbox, 0)
        hbox.addWidget(self.view, 2)
        self.setCentralWidget(w)
        # self.setMinimumSize(1000, 700)

        # aoi = 63.6

        # g1 = Grating(lines = 1739.1, rotation=aoi, height=750, material="FS")
        # # g2 = Grating(lines = 870, rotation=aoi, height=750, material="FS", pos = QtCore.QPointF(0,-500) )
        
        # # g2 = Grating(lines = 1739.1, pos = QtCore.QPointF(50,-300), rotation=aoi, material="FS")
        # b = Beamblock( pos = QtCore.QPointF(0,-500))


        # m1 = Mirror(ref1=1, ref2=1, tran1=0, tran2=0, pos = QtCore.QPointF(175,-525), rotation=150)
        # m2 = Mirror(ref1=1, ref2=1, tran1=0, tran2=0, pos = QtCore.QPointF(475,-525), rotation=150)

        # elements = [g1,m1,m2, b]
        # elements = []
        # wl_pts = 5

        # for wl in range(wl_pts):
        #     col = QtGui.QColor().fromHsvF(wl/wl_pts, 1, 1, 0.5)
        #     r = Ray(pos = QtCore.QPointF(-200,0), dir = QtCore.QPointF(1,0), wl = 1.03 + (wl-wl_pts//2)*0.01, color=col)
            
        #     elements.append(r)
        
        # self.view.scene().drawScene(elements)
        
        # self.view.scene().calculateScene()

    def updteAngleIncrement(self, value):
        self.view.angleIncrement = value

    def writeFile(self, newFile = False):

        if self.openFileName is None or newFile:
            fileName,_ = QFileDialog.getSaveFileName(self, "Save Scene", filter="Scene File (*.scn);;All Files (*.*)")
        else:
            fileName = self.openFileName

        if fileName:
            self.view.scene().saveToFile(fileName)
            self.openFileName = fileName
            self.setWindowTitle(self.openFileName)

    def newFile(self):
        self.view.scene().clearScene()
        self.openFileName = None
        self.setWindowTitle("")

    def loadFile(self):
        fileName,_ = QFileDialog.getOpenFileName(self, "Open Scene", filter="Scene File (*.scn);;All Files (*.*)")
        if fileName:
            self.view.scene().loadFromFile(fileName)
            self.view.scaleToContent()
            self.openFileName = fileName
            self.setWindowTitle(self.openFileName)
        
    def resetScene(self):
        # self.view.scene().reset()
        self.view.scene().calculateScene()
        
    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        self.view.scaleToContent()

        return super().showEvent(a0)

    def exportSVG(self, fileName):
        gen = QtSvg.QSvgGenerator()
        gen.setFileName(fileName)
        # gen.setSize()

        br = QtCore.QRectF()

        for itm in self.view.scene().items():
            if isinstance(itm, OpticalElement):
                br = br.united(itm.sceneBoundingRect())

        m = br.width()*0.2

        br = br.marginsAdded(QtCore.QMarginsF(m,m,m,m))

        gen.setSize(QtCore.QSizeF(br.width(), br.height()).toSize())
        gen.setViewBox(QtCore.QRectF(0, 0, br.width(), br.height()).toRect())

        painter = QtGui.QPainter(gen)

        self.view.scene().render(painter, source = br)
        painter.end()

    def printView(self, toFile = False):
        
        self.view.scene().clearSelection()

        printer = None        
        if toFile:

            fileName, _ = QFileDialog.getSaveFileName(self,"'Export","","PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*.*)")

            if fileName:
                if fileName.endswith(".pdf"):
                    printer = QtGui.QPdfWriter(fileName)
                else:
                    self.exportSVG(fileName)

        else:
            dialog = QtPrintSupport.QPrintDialog()
            if dialog.exec_() == QtPrintSupport.QPrintDialog.Accepted:
                printer = dialog.printer()
                    
        if printer is None:
            return

        printer.setPageSize(QtGui.QPagedPaintDevice.A4)
        printer.setResolution(100)
        printer.setPageOrientation(QtGui.QPageLayout.Orientation.Landscape)

        painter = QtGui.QPainter(printer)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        br = QtCore.QRectF()

        for itm in self.view.scene().items():
            if isinstance(itm, OpticalElement):
                br = br.united(itm.sceneBoundingRect())

        m = br.width()*0.2

        br = br.marginsAdded(QtCore.QMarginsF(m,m,m,m))
        
        self.view.scene().render(painter, source=br)
        painter.end()

    def rotateItemsBy(self, d_angle):
        itms = self.view.scene().selectedItems()
        for itm in itms:
            angle = itm.rotation()
            itm.setRotation(angle+d_angle)
            
    def rotateItems(self, angle):
        itms = self.view.scene().selectedItems()
        for itm in itms:
            itm.setRotation(angle)
            
    def scaleChange(self, val):

        newScale = val/100

        self.view.scale(newScale/self.scale, newScale/self.scale)
        self.scale = newScale

    def gridChange(self, val):
        self.view.scene().setGridSize(val)
        self.view.scene().update()

if __name__ == "__main__":
    app = QApplication([])
    w = MainWindow()
    w.show()
    app.exec()
