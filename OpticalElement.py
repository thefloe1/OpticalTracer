# OpticalElement.py
# Classes for optical elements, their representation and some of their math
# 13.09.2022, Floery Tobias
# Released under GNU Public License (GPL)

from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsItem, \
        QStyleOptionGraphicsItem, QStyle, QGraphicsObject

from PyQt5 import QtGui, QtCore

from PyQt5.QtWidgets import QApplication

import math
from Material import Materials
import vectors

from UndoRedo import UndoRedoItem, UndoRedoType
from ElementDialog import *

def blendColors(color1 : QtGui.QColor, color2: QtGui.QColor, ratio : float = 0.5):
    r0,g0,b0,a0 = color1.getRgbF()
    r1,g1,b1,a1 = color2.getRgbF()

    # a01 = (1 - ratio)*a1 + ratio*a0
    # r01 = ((1 - ratio)*a1*r1 + ratio*r0) / a01
    # g01 = ((1 - ratio)*a1*g1 + ratio*g0) / a01
    # b01 = ((1 - ratio)*a1*b1 + ratio*b0) / a01
    a01 = a1 * a0
    r01 = r1 * r0
    g01 = g1 * g0
    b01 = b1 * b0

    return QtGui.QColor().fromRgbF(r01,g01,b01,a01)

class RayElement(QGraphicsObject):
    itemMovedOrRotated = QtCore.pyqtSignal()

    def __init__(self, x1=0, y1=0, x2=2000, y2=0, intensity = 1.0, wl=[1.03], color = None, showArrow = False, parent = None):
        super(RayElement, self).__init__()

        self._line = QtCore.QLineF(x1,y1,x2,y2)
        # self.setCacheMode(QGraphicsObject.CacheMode.ItemCoordinateCache)

        self.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.setCacheMode(QGraphicsObject.CacheMode.NoCache)
        
        self.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable)
        
        if parent is None:            
            self.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsMovable)

        self.handled = False
        self.intensity = intensity

        self.parent = parent

        self.children = []

        # self.color = color
        self.setWavelength(wl)

        if color is not None:
            self.color = [color]

        self.linewidth = 2
        
        self.showArrow = showArrow

        self.snap = True
        self.brMargin = QtCore.QMarginsF(10,10,10,10)

        if self.parent is not None:
            self.parent.addChild(self)

    def setWavelength(self, wl):
        self.wl = wl
        self.color = self.getColors()
        # print(self.wl, self.color)
            
    def getColors(self, wl = None):
        if wl is None:
            wl = self.wl
        return [QtGui.QColor().fromHslF((1-((x+1)/(len(wl))))*0.9, 0.95, 0.5, 0.75) for x in range(len(wl))]

    def getPixmap(self, pix_size = QtCore.QSize(200,200)):

        pm = QtGui.QPixmap(pix_size)
        pm.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pm) 
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtGui.QPen(QtGui.QColor("black"),2))
        painter.drawLine(QtCore.QLineF(pix_size.width()/4,pix_size.height()/2,pix_size.width()*3/4,pix_size.height()/4))
        painter.drawLine(QtCore.QLineF(pix_size.width()/4,pix_size.height()/2,pix_size.width()*3/4,pix_size.height()/2))
        painter.drawLine(QtCore.QLineF(pix_size.width()/4,pix_size.height()/2,pix_size.width()*3/4,pix_size.height()*3/4))
        painter.end()

        return pm

    def getState(self):
        state_dict = {
            "type": self.__class__.__name__,
            "pos": [self.pos().x(), self.pos().y()],
            "rot": self.rotation(),
            "intensity": self.intensity,
            "wl": self.wl,
            "arrows": self.showArrow
        }

        state_dict["color"] = None
        if self.color is not None:
            state_dict["color"] = [x.getRgb() for x in self.color]

        return state_dict

    def setState(self, state_dict):

        
                
        try:
            pos = state_dict["pos"]
            self.setPos(QtCore.QPointF(pos[0], pos[1]))
        except KeyError:
            pass        
        
        try:
            self.setRotation(state_dict["rot"])
        except KeyError:
            pass
        
        try:
            self.intensity = state_dict["intensity"]
        except KeyError:
            pass
        
        try:
            self.setWavelength(state_dict["wl"])
        except KeyError:
            pass
        try:
            self.showArrow = state_dict["arrows"]
        except KeyError:
            pass
        
        ### load colors
        colors = state_dict["color"]
        if colors is not None:
            self.color = [QtGui.QColor().fromRgb(*x) for x in colors]

    def getDialog(self):
        # dlg = QDialog()
        # layout = QFormLayout()

        # layout.addRow("Pos", QLineEdit(f"{self.pos().x():.1f},{self.pos().y():.1f}"))
        # layout.addRow("Angle", QLineEdit(f"{self.rotation():.2f}"))
        # layout.addRow("Intensity", QLineEdit(f"{self.intensity:.2f}"))

        # self.lwWl = QListWidget()
        # wls = [f"{x:.3f}" for x in self.wl]
        # self.lwWl.addItems(wls)
        # layout.addRow("Wavelength (um)", self.lwWl)
        # # layout.addRow("Wavelength (um)", QLineEdit(f"{str(self.wl):.3f}"))
        # r,g,b,a = self.color.getRgb()
        # layout.addRow("Color (R,G,B,A)", QLineEdit(f"{r},{g},{b},{a}"))

        # dlg.setLayout(layout)

        dlg = RayDialog(self)
        
        return dlg

    def getParents(self, first = False):
        if self.parent is not None:
            for ray in self.parent.getParents():
                yield ray
        
        yield self

    def setLine(self, line):
        self._line = line

    def line(self) -> QtCore.QLineF:
        return self._line

    def shape(self) -> QtGui.QPainterPath:
        path = QtGui.QPainterPath(self.line().p1())
        path.lineTo(self.line().p2())
        path.closeSubpath()
        
        stroker = QtGui.QPainterPathStroker()
        stroker.setWidth(self.linewidth+10)
        stroker.setJoinStyle(QtCore.Qt.PenJoinStyle.MiterJoin)
        cpath = (stroker.createStroke(path) + path).simplified()

            
        return cpath
        # return super().shape()

    def boundingRect(self) -> QtCore.QRectF:
        rect = QtCore.QRectF(self.line().p1(), self.line().p2())
        return rect.marginsAdded(self.brMargin)

    def addChild(self, child):
        self.children.append(child)
        
    def getChildren(self):
        return self.children

    def removeChildren(self):
        for child in self.children:
            child.removeChildren()

            if self.scene() is not None:
                self.scene().removeItem(child)

        self.children = []

    def setEndPoint(self, p:QtCore.QPointF):
        line = self.line()
        p = self.mapFromScene(p)
        line.setP2(p)
        self.setLine(line)

    def getLength(self):
        return self.line().length()

    def setLength(self, length):
        line = self.line()
        line.setLength(length)
        self.setLine(line)

    def setColor(self, color):
        self.color = color

    def getColor(self):
        return self.color

    def setLinewidth(self, lw):
        self.linewidth = lw

    def getLinewidth(self):
        return self.linewidth

    def setSnap(self, state):
        self.snap = state

    def getSnap(self):
        return self.snap
    
    def getSnapPos(self, point, step = None):
        if step is None:
            step = self.scene().getGridSize()
        # p = QtCore.QPointF(point.x() - point.x() % step - self.boundingRect().height()/2, point.y() - point.y() % step)
        p = QtCore.QPointF(round(point.x() / step)*step, round(point.y() / step)*step)
        # print(point, p)
        return p

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):

        if self.scene() is None:
            return super().itemChange(change, value)
        
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            
            mod = QApplication.keyboardModifiers()
            
            ctrl = mod & QtCore.Qt.KeyboardModifier.ControlModifier

            delta = value - self.pos()
            
            if self.snap and not ctrl:
                delta = self.getSnapPos(delta)

            return self.pos() + delta

        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged or change == QGraphicsItem.GraphicsItemChange.ItemRotationHasChanged:
            self.removeChildren()

            if self.parent is not None:
                self.parent.handled = False
                self.parent.setLength(2000)
                self.parent.removeChildren()
            else:
                self.handled = False
            
            self.itemMovedOrRotated.emit()

        return super().itemChange(change, value)

    def drawArror(self, painter : QtGui.QPainter, point : QtCore.QPointF(), dir: QtCore.QPointF(), arrowWidth=10, arrowHeight=8, centered = True):
        ndir = vectors.normalDir(point, point+dir)
        
        scale = self.scene().views()[0].transform().m11()
        if arrowWidth / scale > arrowWidth:
            arrowWidth /= scale
        
        if arrowHeight / scale > arrowHeight:
            arrowHeight /= scale
        
        if centered:
            painter.drawLine(point + dir * arrowWidth/2, point - dir * arrowWidth/2 + ndir * arrowHeight/2)
            painter.drawLine(point + dir * arrowWidth/2, point - dir * arrowWidth/2 - ndir * arrowHeight/2)
        else:
            painter.drawLine(point, point - dir * arrowWidth + ndir * arrowHeight/2)
            painter.drawLine(point, point - dir * arrowWidth - ndir * arrowHeight/2)
            
    def paint(self, painter: QtGui.QPainter, option: QStyleOptionGraphicsItem, widget):

        scale = self.scene().views()[0].transform().m11()
        lw = int(self.linewidth / scale)
        
        if lw < self.linewidth:
            lw = self.linewidth
        # self.linewidth = 6

        # print([x.name() for x in self.color])

        col = self.color[0]
        num = len(self.color)
        
        for c in self.color[1:]:
            col = blendColors(col, c)

        pen = QtGui.QPen(QtGui.QBrush(col), lw, QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap, QtCore.Qt.PenJoinStyle.RoundJoin)
        # pen = self.pen()

        if option.state & QStyle.StateFlag.State_Selected:
            #pen.setStyle(QtCore.Qt.PenStyle.DashDotLine)
            pen.setWidth(lw*2)
            
        # pen.setStyle(QtCore.Qt.PenStyle.DashDotLine)

        r,g,b,a = pen.color().getRgbF()

        comp = 0.3

        ### compress intensity a bit
        i = math.sin(a*self.intensity*math.pi/2)*(1-comp)+comp
        pen.setColor(QtGui.QColor().fromRgbF(r,g,b,i))
        
        # self.setPen(pen)

        painter.setPen(pen)

        painter.drawLine(self.line())
        
        if self.showArrow:
            marker_dist = 500
            
            marker_dist /= scale
            
            ll = self.line().length()
            ndir = vectors.normalize(self.line().p2() - self.line().p1())
            
            if ll < 1000:
                # painter.drawEllipse(self.line().center(), 5, 5)
                self.drawArror(painter, self.line().center(), ndir, centered=False)
            else:
                num = int(ll / marker_dist)
                if num <=7:
                    num=7
                if num >= 200:
                    num=200

                    
                dl = ll / num
                for i in range(num):
                    
                    point = self.line().p1() + (i+0.5) * dl * ndir
                    self.drawArror(painter, point, ndir, centered=False)


    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.pos()} {self.line()}>"

                        
class Interface(QtGui.QPainterPath):
    def __init__(self, t = 1.0, r = 0.0, lines = None, pen = None):
        super(Interface, self).__init__()
        self.t = t
        self.r = r
        self.lines = lines

        if self.r == 0 and self.t == 0:
            pen = QtGui.QPen(QtGui.QColor("black"), 4)
            
        self.pen = pen
        

class OpticalElement(QGraphicsObject):

    itemMovedOrRotated = QtCore.pyqtSignal()

    def __init__(self, material): #iface1 : Interface, iface2 : Interface
        super(OpticalElement, self).__init__(None)

        # self.setCacheMode(QGraphicsObject.CacheMode.ItemCoordinateCache)
        # self.setCacheMode(QGraphicsObject.CacheMode.DeviceCoordinateCache)
        self.setCacheMode(QGraphicsObject.CacheMode.NoCache)

        self.setMaterial(material)

        # self.updateInterfaces(ifaces)
        
        self.pen = QtGui.QPen(QtGui.QBrush(QtGui.QColor("black")), 1)

        self.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor("black")), 2, QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap, QtCore.Qt.PenJoinStyle.RoundJoin))

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.markers = []
        self.normals = []
        
        self.normalScaleLength = 20
        self.brMargin = QtCore.QMarginsF(10,10,10,10)

        self.rays = []
        self.setZValue(100)

        self.snap = True
        self.ctrl_pressed = False
        
        self.oldPos = QtCore.QPointF()        

        self.update()

    def getState(self):
        state_dict = {
            "type": self.__class__.__name__,
            'pos': [self.pos().x(), self.pos().y()],
            'rot': self.rotation(),
            'mat': self.material
        }

        return state_dict

    def setState(self, state_dict):
        pos = state_dict["pos"]
        self.setPos( QtCore.QPointF(pos[0], pos[1]))
        self.setRotation(state_dict["rot"])

        self.setMaterial(state_dict["mat"])
        self.update()

    def getDialog(self):
        # dlg = QDialog()
        # layout = QFormLayout()

        # cb = QComboBox()
        # cb.addItems(Materials().listMaterials())
        # cb.setCurrentText(self.getMaterial())
        # layout.addRow("Material", cb)
        # layout.addRow("Pos", QLineEdit(f"{self.pos().x():.1f},{self.pos().y():.1f}"))
        # layout.addRow("Rotation", QLineEdit(f"{self.rotation():.1f}"))
        # dlg.setLayout(layout)
        
        # return dlg

        dlg = ElementDialog(self)
        
        return dlg
    
    def getPixmap(self, pix_size = QtCore.QSize(100,100)):

        size = self.boundingRect().size().toSize()

        sq = size.width()
        if size.height() > sq:
            sq = size.height()

        size = QtCore.QSize(sq,sq)

        pm = QtGui.QPixmap(size)
        pm.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pm) 
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        

        center = QtCore.QPointF(size.width()/2, size.height()/2)
        painter.translate(center)

        opt = QStyleOptionGraphicsItem()
        self.paint(painter, opt, None)
        painter.end()

        return pm

    def update(self):
        # self.ifaces = ifaces

        self.createInterfaces()

        self.path = QtGui.QPainterPath()
        
        if self.ifaces is not None:

            for iface in self.ifaces:
                self.path.connectPath(iface)
            
    def createInterfaces(self):
        self.ifaces = []

    def setMaterial(self, material):
        try:
            self.n = Materials().getMaterial(material)
        except NameError:
            self.n = material
        self.material = material

    def getMaterial(self):
        return self.material
        
    def getSnapPos(self, point, step = None):
        if step is None:
            step = self.scene().getGridSize()
        # p = QtCore.QPointF(point.x() - point.x() % step, point.y() - point.y() % step)
        p = QtCore.QPointF(round(point.x() / step)*step, round(point.y() / step)*step)

        # print(point, p)
        return p
        
        
    def getRefractiveIndex(self, wl = 1.03):
        if callable(self.n):
            return self.n(wl)
        
        return self.n

    def setSnap(self, state):
        self.snap = state

    def getSnap(self):
        return self.snap
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):

        if self.scene() is None:
            return super().itemChange(change, value)

        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:            
            mod = QApplication.keyboardModifiers()
            # print("move: ", self.pos(), value)
            ctrl = mod & QtCore.Qt.KeyboardModifier.ControlModifier
            
            delta = value - self.pos()

            if self.snap and not ctrl:
                delta = self.getSnapPos(delta)
                            
            path = self.mapToScene(self.shape())

            stroker = QtGui.QPainterPathStroker()
            stroker.setWidth(4)
            stroker.setJoinStyle(QtCore.Qt.PenJoinStyle.MiterJoin)
            cpath = (stroker.createStroke(path) + path).simplified()

            cpath.translate(delta)

            itms = self.scene().items(cpath, QtCore.Qt.ItemSelectionMode.IntersectsItemShape)
            itms = [x for x in itms if isinstance(x, OpticalElement) and x is not self]

            if len(itms) > 0:
                # print("done: ", self.oldPos)
                return self.oldPos

            hi = UndoRedoItem(self, UndoRedoType.elementParamChanged,"pos", self.pos())
                
            ### if last entry in history is the same, update the value there
            hist = self.scene().history
                
            if not (len(hist) > 0 and hist[-1].getElement() == self and hist[-1].getType() == hi.getType()):
                hist.append(hi)
                            
            value = self.pos() + delta
            self.oldPos = value
            # print("done: ", self.oldPos)
            return value
        elif change == QGraphicsItem.GraphicsItemChange.ItemRotationChange:
            hi = UndoRedoItem(self, UndoRedoType.elementParamChanged, "rot", self.rotation())
                
            ### if last entry in history is the same, update the value there
            hist = self.scene().history
                
            if not (len(hist) > 0 and hist[-1].getElement() == self and hist[-1].getType() == hi.getType()):
                hist.append(hi)
                            

        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged or change == QGraphicsItem.GraphicsItemChange.ItemRotationHasChanged:
            itms = self.collidingItems(QtCore.Qt.ItemSelectionMode.IntersectsItemBoundingRect)

            rays = [x for x in itms if isinstance(x, RayElement)]
            rays.extend(self.rays)

            for ray in rays:

                ray.removeChildren()

                if ray.parent is not None:
                    ray.parent.handled = False
                    ray.parent.setLength(2000)
                    ray.parent.removeChildren()
                else:
                    ray.handled = False

                # if self.scene() is not None and ray in self.scene().rays:
                #     print("removing ray from scene.rays")
                #     self.scene().rays.remove(ray)

                
            self.itemMovedOrRotated.emit()

        return super().itemChange(change, value)


    def setPen(self, pen : QtGui.QPen):
        self.pen = pen

    def paint(self, painter: QtGui.QPainter, option: QStyleOptionGraphicsItem, widget):
        painter.setPen(self.pen)
        col = self.pen.color()
        col.setAlpha(25)
        # painter.setBrush(col)
    
        for iface in self.ifaces:
            if iface.pen is not None:
                painter.setPen(iface.pen)
            else:
                painter.setPen(self.pen)
                
            painter.drawPath(iface)
        painter.fillPath(self.path, col)

        # painter.drawPath(self.path)
        # painter.drawRect(self.path.boundingRect())

        painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor("green")), 1))
        painter.setBrush(QtGui.QBrush())        
                    
        for marker in self.markers:
            painter.drawEllipse(marker, 6, 6)
            
        painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor("black")), 1))
        
        for p1, p2 in self.normals:
            painter.drawEllipse(p1, 3, 3)
            painter.drawLine(p1, p2)
            
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(QtGui.QPen(QtGui.QColor("black"), 1.5 , QtCore.Qt.PenStyle.DashLine))
            painter.drawRect(self.boundingRect())

        # painter.end()
        # super().paint(painter, option, widget)

    def shape(self) -> QtGui.QPainterPath:
        return self.path
        # return super().shape()

    def boundingRect(self) -> QtCore.QRectF:
        return self.path.boundingRect().marginsAdded(self.brMargin)
        #return QtCore.QRectF(-120,-120,240,240)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: ({self.pos().x():.1f},{self.pos().y():.1f}) @ {self.rotation():.1f}°>"
    
class LensElement(OpticalElement):
    def __init__(self, material = "BK7", r1=1000, r2=1000, thickness=20, height=254, ref1 = 0, tran1=1.0, ref2=0, tran2=1.0):
        self.r1 = r1
        self.r2 = r2
        self.thickness = thickness
        self.height = height
            
        self.ref1 = ref1
        self.tran1 = tran1
        self.ref2 = ref2
        self.tran2 = tran2
        super(LensElement, self).__init__(material = material)

        # self.update()

    def createInterfaces(self):
        
        if self.r1 is not None and math.fabs(self.r1) <= self.height/2:
            self.r1 /= math.fabs(self.r1)*self.height/2
            
        if self.r2 is not None and math.fabs(self.r2) <= self.height/2:
            self.r2 /= math.fabs(self.r2)*self.height/2       
        
        # print(self.r1, self.r2)        
        
        ifac1 = Interface(self.tran1, self.ref1)

        if self.r1 is None:
            ifac1.moveTo(0, self.height/2)
            ifac1.lineTo(self.thickness/2, self.height/2)
            ifac1.lineTo(self.thickness/2, -self.height/2)
            ifac1.lineTo(0, -self.height/2)            
        else:
            alpha1 = math.asin(self.height/(2*self.r1))
            alpha1_deg = alpha1 * 180.0 / math.pi
            delta1 = self.r1*math.cos(alpha1)
            self.delta1 = delta1

            ifac1.moveTo(0, -self.height/2)
            ifac1.lineTo(self.thickness/2, -self.height/2)
            ifac1.arcTo(-self.r1-delta1+self.thickness/2,-self.r1, 2*self.r1,2*self.r1, alpha1_deg, -alpha1_deg*2)
            ifac1.lineTo(0, self.height/2)

            self.center1 = QtCore.QPointF(-self.delta1+self.thickness/2,0)

        ifac2 = Interface(self.tran2, self.ref2)
        if self.r2 is None:
            ifac2.moveTo(0, self.height/2)
            ifac2.lineTo(-self.thickness/2, self.height/2)
            ifac2.lineTo(-self.thickness/2, -self.height/2)
            ifac2.lineTo(0, -self.height/2)
        else:
            r2 = self.r2
            

            alpha2 = math.asin(self.height/(2*r2))
            alpha2_deg = alpha2 * 180.0 / math.pi
            delta2 = r2*math.cos(alpha2)
            self.delta2 = delta2
            ifac2.moveTo(0, -self.height/2)
            ifac2.lineTo(-self.thickness/2, -self.height/2)
            ifac2.arcTo(+self.r2+delta2-self.thickness/2,-self.r2, -2*self.r2,2*self.r2, alpha2_deg, -alpha2_deg*2)
            ifac2.lineTo(0, self.height/2)
            
            self.center2 = QtCore.QPointF(self.delta2-self.thickness/2,0)

        self.ifaces = [ifac1, ifac2]

    def getState(self):
        dict = super().getState()
        dict["r1"] = self.r1
        dict["r2"] = self.r2
        dict["thickness"] = self.thickness
        dict["height"] = self.height

        return dict

    def setState(self, state_dict):
        self.r1 = state_dict["r1"]
        self.r2 = state_dict["r2"]
        self.thickness = state_dict["thickness"]
        self.height = state_dict["height"]

        return super().setState(state_dict)

    # def getDialog(self):
    #     dlg = super().getDialog()
    #     layout = dlg.layout()

    #     layout.addRow("Thickness (mm): ", QLineEdit(f"{self.thickness/10:.1f}"))
    #     layout.addRow("Height (mm): ", QLineEdit(f"{self.height/10:.1f}"))


    #     if self.r1 is None:
    #         layout.addRow("R1 (mm):", QLineEdit("None"))
    #     else:
    #         layout.addRow("R1 (mm):", QLineEdit(f"{self.r1/10:.1f}"))

    #     if self.r2 is None:
    #         layout.addRow("R2 (mm):", QLineEdit("None"))
    #     else:
    #         layout.addRow("R2 (mm):", QLineEdit(f"{self.r2/10:.1f}"))

    #     layout.addRow("r1", QLineEdit(f"{self.ref1:.2f}"))
    #     layout.addRow("t1", QLineEdit(f"{self.tran1:.2f}"))
    #     layout.addRow("r2", QLineEdit(f"{self.ref2:.2f}"))
    #     layout.addRow("t2", QLineEdit(f"{self.tran2:.2f}"))
        
    #     return dlg


    def getIntersections(self, p1 : QtCore.QPointF, p2 : QtCore.QPointF):

        # print("getIntersections ", p1, p2)

        hits = []
        if self.r1 is not None:
            # check for intersection with curved surface
                
            ret = vectors.LineCircle(p1, p2, self.center1, self.r1)
            if ret is not None:
                for pts in ret:
                    # only points within the height of the object are valid, TODO take projected height
                    if vectors.distance(pts, QtCore.QPointF()) < self.height/2:
                        nd = vectors.normalize(pts-self.center1)
                        if self.r1 < 0:
                            nd = vectors.invert(nd)                        
                        hits.append((pts, nd, self.ifaces[0]))
        else:
            # check for intersection with flat surface
            ret = vectors.LineLine(p1, p2, QtCore.QPointF(self.thickness/2, self.height/2), QtCore.QPointF(self.thickness/2, -self.height/2))
            if ret is not None:
                nd = vectors.normalDir(QtCore.QPointF(self.thickness/2, -self.height/2), QtCore.QPointF(self.thickness/2, self.height/2))
                hits.append((ret,nd, self.ifaces[0]))

        if self.r2 is not None:
            # check for intersection with curved surface

            
            ret = vectors.LineCircle(p1, p2, self.center2, self.r2)
            if ret is not None:
                for pts in ret:
                    # only points within the height of the object are valid, TODO take projected height
                    if vectors.distance(pts, QtCore.QPointF()) < self.height/2:
                        nd = vectors.normalize(pts-self.center2)
                        if self.r2 < 0:
                            nd = vectors.invert(nd)
                            
                        hits.append((pts, nd, self.ifaces[1]))
                        # print(pts, nd)
        else:
            # check for intersection with flat surface
            ret = vectors.LineLine(p1, p2, QtCore.QPointF(-self.thickness/2, self.height/2), QtCore.QPointF(-self.thickness/2, -self.height/2))
            if ret is not None:                
                nd = vectors.normalDir(QtCore.QPointF(-self.thickness/2, self.height/2), QtCore.QPointF(-self.thickness/2, -self.height/2))
                hits.append((ret,nd, self.ifaces[1]))
        
        ### check top and bottom edges
        
        ret = vectors.LineLine(p1, p2, QtCore.QPointF(-self.thickness/2, self.height/2), QtCore.QPointF(self.thickness/2, self.height/2))
        if ret is not None:
            nd = vectors.normalDir(QtCore.QPointF(-self.thickness/2, self.height/2), QtCore.QPointF(self.thickness/2, self.height/2))
            nd = vectors.invert(nd)
            hits.append((ret,nd, Interface(0,0)))
            
        ret = vectors.LineLine(p1, p2, QtCore.QPointF(-self.thickness/2, -self.height/2), QtCore.QPointF(self.thickness/2, -self.height/2))
        if ret is not None:
            nd = vectors.normalDir(QtCore.QPointF(-self.thickness/2, -self.height/2), QtCore.QPointF(self.thickness/2, -self.height/2))
            hits.append((ret,nd, Interface(0,0)))
                    
        
        ### only take points in ray direction
        hits = [(x,y,z) for x,y,z in hits if vectors.dotP(p2-p1, x-p1) > 0]
        
        # print(len(hits))
        
        ### sort by distance
        hits = sorted(hits, key = lambda x: vectors.distance(p1, x[0]))

        return hits

class MirrorElement(LensElement):
    def __init__(self, material="BK7", r1=None, r2=None, height=254, thickness=30, ref1=1.0, ref2=1.0, tran1=0.0, tran2=0.0):
        super(MirrorElement, self).__init__(material = material, r1 = r1, r2 = r2, ref1 = ref1, ref2 = ref2, tran1=tran1, tran2=tran2, height=height, thickness=thickness )
        # self.thickness = thickness

    def setState(self, state_dict):
        self.ref1 = state_dict["ref1"]
        self.ref2 = state_dict["ref2"]
        self.tran1 = state_dict["tran1"]
        self.tran2= state_dict["tran2"]
        # self.thickness = state_dict["thickness"]
        self.height = state_dict["height"]
        self.r1 = state_dict["r1"]
        self.r2 = state_dict["r2"]
        super().setState(state_dict)


    def getState(self):
        dict = super().getState()
        dict["ref1"] = self.ref1
        dict["ref2"] = self.ref2
        dict["tran1"] = self.tran1
        dict["tran2"] = self.tran2
        # dict["thickness"] = self.thickness
        dict["height"] = self.height
        dict["r1"] = self.r1
        dict["r2"] = self.r2
        return dict

    # def getDialog(self):
    #     dlg = super().getDialog()
    #     layout = dlg.layout()

    #     layout.addRow("Thickness (mm): ", QLineEdit(f"{self.thickness/10:.1f}"))
    #     layout.addRow("Height (mm): ", QLineEdit(f"{self.height/10:.1f}"))


    #     if self.r1 is None:
    #         layout.addRow("R1 (mm):", QLineEdit("None"))
    #     else:
    #         layout.addRow("R1 (mm):", QLineEdit(f"{self.r1/10:.1f}"))

    #     if self.r2 is None:
    #         layout.addRow("R2 (mm):", QLineEdit("None"))
    #     else:
    #         layout.addRow("R2 (mm):", QLineEdit(f"{self.r2/10:.1f}"))

    #     layout.addRow("r1", QLineEdit(f"{self.ref1:.2f}"))
    #     layout.addRow("t1", QLineEdit(f"{self.tran1:.2f}"))
    #     layout.addRow("r2", QLineEdit(f"{self.ref2:.2f}"))
    #     layout.addRow("t2", QLineEdit(f"{self.tran2:.2f}"))
        
    #     return dlg

class BeamBlockElement(MirrorElement):
    def __init__(self, height=254, thickness=30):
        super(BeamBlockElement, self).__init__(height=height, thickness=thickness, ref1=0.0, tran1=0.0, ref2=0.0, tran2=0.0)

    # def getDialog(self):
    #     dlg = super().getDialog()
    #     layout = dlg.layout()

    #     layout.addRow("Thickness (mm): ", QLineEdit(f"{self.thickness/10:.1f}"))
    #     layout.addRow("Height (mm): ", QLineEdit(f"{self.height/10:.1f}"))

    #     return dlg


        
class PolygonElement(OpticalElement):
    def __init__(self, material):
        self.polygon = QtGui.QPolygonF()
        super(PolygonElement, self).__init__(material)

    def createInterfaces(self):
        ifaces = [Interface(r=0.05, t=0.95) for x in self.polygon]
        
        cnt = self.polygon.count()-1

        for i in range(cnt):
            ifaces[i].moveTo(self.polygon[i])
            ifaces[i].lineTo(self.polygon[i+1])
            
        ifaces[cnt].moveTo(self.polygon[cnt])
        ifaces[cnt].lineTo(self.polygon[0])
        self.ifaces = ifaces
    
    def getIntersections(self, p1 : QtCore.QPointF, p2 : QtCore.QPointF):
        
        cnt = self.polygon.count()
        hits = []
        
        rng = list(range(cnt))
        rng.append(0)
        rng.reverse()
        
        for k,i in enumerate(range(cnt)):
            ret = vectors.LineLine(p1, p2, self.polygon[rng[i]], self.polygon[rng[i+1]])
            
            if ret is not None:
                
                nd = vectors.normalDir(self.polygon[rng[i]], self.polygon[rng[i+1]])
                hits.append((ret,nd, self.ifaces[k]))
                # self.markers.append(ret)
                # self.normals.append((ret-20*nd, ret+20*nd))

        ### only take points in ray direction
        hits = [(x,y,z) for x,y,z in hits if vectors.dotP(p2-p1, x-p1) > 0]
        
        # print(len(hits))
        
        ### sort by distance
        hits = sorted(hits, key = lambda x: vectors.distance(p1, x[0]))

        return hits

class PrismElement(PolygonElement):
    def __init__(self, material = "BK7", base=100, apex=60.0):
        self.base = base
        self.apex = apex
        super(PrismElement, self).__init__(material)

        # p = PolygonElement(self.material, QtGui.QPolygonF(pts), pid = id(self))

    def createInterfaces(self):
        r = self.base / (2*math.sin(self.apex / 180.0 * math.pi))
        h = math.sqrt(r**2-(self.base/2)**2)
        
        pts = [
            QtCore.QPointF (-self.base/2, h),
            QtCore.QPointF (self.base/2, h),
            QtCore.QPointF (0, -r)
        ]
        # print("Prism", self.base, self.apex )
        
        self.polygon = QtGui.QPolygonF(pts)
        super().createInterfaces()

    def getState(self):
        dict = super().getState()
        dict["base"] = self.base
        dict["apex"] = self.apex

        return dict

    def setState(self, state_dict):
        self.base = state_dict["base"]
        self.apex = state_dict["apex"]
        super().setState(state_dict)

    # def getDialog(self):
    #     dlg = super().getDialog()
    #     layout = dlg.layout()

    #     layout.addRow("Base (mm)", QLineEdit(f"{self.base/10:.1f}"))
    #     layout.addRow("Apex", QLineEdit(f"{self.apex:.2f}"))
    #     return dlg

        
class GratingElement(OpticalElement):
    def __init__(self, material = "BK7", lines=600, height=254, thickness=60):

        self.height = height
        self.thickness = thickness
        self.lines = lines
        super(GratingElement, self).__init__(material)


    def createInterfaces(self):
        ifac1 = Interface()

        ifac1.moveTo(-self.thickness/2, self.height/2)
        ifac1.lineTo(self.thickness/2, self.height/2)
        ifac1.lineTo(self.thickness/2, -self.height/2)
        ifac1.lineTo(-self.thickness/2, -self.height/2)       

        pen = QtGui.QPen(QtGui.QColor("green"), 2)
        steps = int(self.height * self.lines / 10000)
        # print(self.lines, steps)
        dist = self.height/steps
                
        pen.setDashPattern([dist, 4])
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        ifac2 = Interface(lines = self.lines, pen = pen)
        
        
        ifac2.moveTo(-self.thickness/2, self.height/2)
        ifac2.lineTo(-self.thickness/2, -self.height/2)
            
        self.ifaces = [ifac1, ifac2]
    
    def getState(self):
        dict = super().getState()
        dict["lines"] = self.lines
        dict["height"] = self.height
        dict["thickness"] = self.thickness
        return dict

    def setState(self, state_dict):
        self.lines = state_dict["lines"]
        self.height = state_dict["height"]
        self.thickness = state_dict["thickness"]

        super().setState(state_dict)

    # def getDialog(self):
    #     dlg = super().getDialog()
    #     layout = dlg.layout()

    #     layout.addRow("Thickness (mm): ", QLineEdit(f"{self.thickness/10:.1f}"))
    #     layout.addRow("Height (mm): ", QLineEdit(f"{self.height/10:.1f}"))
    #     layout.addRow("Lines/mm: ", QLineEdit(f"{self.lines:.1f}"))

    #     return dlg


    def getIntersections(self, p1 : QtCore.QPointF, p2 : QtCore.QPointF):
        
        hits = []

        # check for intersection with flat surface
        ret = vectors.LineLine(p1, p2, QtCore.QPointF(self.thickness/2, self.height/2), QtCore.QPointF(self.thickness/2, -self.height/2))
        if ret is not None:
            nd = vectors.normalDir(QtCore.QPointF(self.thickness/2, -self.height/2), QtCore.QPointF(self.thickness/2, self.height/2))
            hits.append((ret,nd, self.ifaces[0]))

        ret = vectors.LineLine(p1, p2, QtCore.QPointF(-self.thickness/2, self.height/2), QtCore.QPointF(-self.thickness/2, -self.height/2))
        if ret is not None:                
            nd = vectors.normalDir(QtCore.QPointF(-self.thickness/2, self.height/2), QtCore.QPointF(-self.thickness/2, -self.height/2))
            hits.append((ret,nd, self.ifaces[1]))
    
        ### check top and bottom edges
        
        ret = vectors.LineLine(p1, p2, QtCore.QPointF(-self.thickness/2, self.height/2), QtCore.QPointF(self.thickness/2, self.height/2))
        if ret is not None:
            nd = vectors.normalDir(QtCore.QPointF(-self.thickness/2, self.height/2), QtCore.QPointF(self.thickness/2, self.height/2))
            nd = vectors.invert(nd)
            hits.append((ret,nd, Interface(0,0)))
            
        ret = vectors.LineLine(p1, p2, QtCore.QPointF(-self.thickness/2, -self.height/2), QtCore.QPointF(self.thickness/2, -self.height/2))
        if ret is not None:
            nd = vectors.normalDir(QtCore.QPointF(-self.thickness/2, -self.height/2), QtCore.QPointF(self.thickness/2, -self.height/2))
            hits.append((ret,nd, Interface(0,0)))

        ### only take points in ray direction
        hits = [(x,y,z) for x,y,z in hits if vectors.dotP(p2-p1, x-p1) > 0]
        
        # print(len(hits))
        
        ### sort by distance
        hits = sorted(hits, key = lambda x: vectors.distance(p1, x[0]))

        return hits

    def __repr__(self):
        return f"<Grating, {self.pos()}, {self.rotation()}>"
    

# class LensDialog(QDialog):
#     def __init__(self, element : OpticalElement, parent = None):
#         super(LensDialog, self).__init__(parent)

#         layout = QFormLayout()

#         # r1, r2, thickness, height, ref1 = 0, tran1=1.0, ref2=0, tran2=1.0

#         cb = QComboBox()
#         cb.addItems(Materials().listMaterials())
#         cb.setCurrentText(element.getMaterial())
#         layout.addRow("Material", cb)
        
#         le = QLineEdit()
#         if element.r1 is None:
#             le.setText(f"None")
#         else:
#             le.setText(f"{element.r1/10:.1f}")
#         layout.addRow("R1 (mm)", le)
#         le = QLineEdit()
#         if element.r2 is None:
#             le.setText(f"None")
#         else:
#             le.setText(f"{element.r2/10:.1f}")
#         layout.addRow("R2 (mm)", le)
#         le = QLineEdit()
#         le.setText(f"{element.thickness/10:.1f}")
#         layout.addRow("Edge Thickness (mm)", le)
#         le = QLineEdit()
#         le.setText(f"{element.height/10:.1f}")
#         layout.addRow("Height (mm)", le)
#         print(element.ifaces)
#         for i, iface in enumerate(element.ifaces):
#             le = QLineEdit(f"{iface.r:.2f}")
#             layout.addRow(f"r{i+1} =", le)
#             le = QLineEdit(f"{iface.t:.2f}")
#             layout.addRow(f"t{i+1} =", le)

#         self.setLayout(layout)

