# MyGraphicsView.py
# Extending QGraphicsView to handle mouse & keypresses, drag & drop, ...
# 13.09.2022, Floery Tobias
# Released under GNU Public License (GPL)

from PyQt5.QtWidgets import QGraphicsView, QMenu
from PyQt5 import QtCore, QtGui

from OpticalElement import *

class MyGraphicsView(QGraphicsView):
    def __init__(self, scene, parent = None):
        super(MyGraphicsView, self).__init__(scene, parent)
        
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)

        self.setAcceptDrops(True)
        self.angleIncrement = 45.0
        
    
    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        # return super().mouseDoubleClickEvent(event)
        itm = self.itemAt(event.pos())
        
        if itm is not None:
            self.scene().showElementEditor(itm)
        else:        
            return super().mouseDoubleClickEvent(event)
        
    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        pos = event.pos()
        element = self.itemAt(pos)
        
        if element is not None: # and element.isSelected():
            menu = QMenu(self)
            menu.addAction("Porperties", lambda: self.scene().showElementEditor(element))
            menu.addAction("Delete", lambda: self.scene().removeElement(element))
            menu.exec(event.globalPos())
            # return super().contextMenuEvent(event)

        return super().contextMenuEvent(event)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        # print("drag enter view")


        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
        
            event.accept()
            event.acceptProposedAction()
        # else:
        # return super().dragEnterEvent(event)
    
    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        # print("drop")

        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            data = event.mimeData()
            source_item = QtGui.QStandardItemModel()
            source_item.dropMimeData(data, QtCore.Qt.CopyAction, 0,0, QtCore.QModelIndex())
            item = source_item.item(0, 0) 

            pos = self.mapToScene(event.pos())
            
            if item.text() == "Mirror":
                x = MirrorElement()
            elif item.text() == "Lens":
                x = LensElement()
            elif item.text() == "Prism":
                x = PrismElement()
            elif item.text() == "Grating":
                x = GratingElement()
            elif item.text() == "Beamblock":
                x = BeamBlockElement()
            elif item.text() == "Ray":
                x = RayElement(0,0,2000,0)
                x.setWavelength([0.8,0.9,1.0,1.1,1.2])
                
            else:
                return

            x.setPos(pos)
            self.scene().addElement(x)
            

            # return super().dropEvent(event)
    
    def scaleToContent(self):
        br = QtCore.QRectF()

        for itm in self.scene().items():
            if isinstance(itm, OpticalElement):
                br = br.united(itm.sceneBoundingRect())

        m = br.width()*0.1

        br = br.marginsAdded(QtCore.QMarginsF(m,m,m,m))

        self.fitInView(br, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        # self.update()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        key = event.key()
        mod = event.modifiers()
        ctrl =  mod & QtCore.Qt.KeyboardModifier.ControlModifier
                    
        
        # if key == QtCore.Qt.Key.Key_Z:
        #     if ctrl:
        #         self.scene().undo()
        #     event.accept()
        #     return

        itms = self.scene().selectedItems()
        
        if key == QtCore.Qt.Key.Key_C:
            if ctrl:
                self.copyItems = [x.getState() for x in itms]
                self.copyPos = self.mapFromGlobal(QtGui.QCursor().pos())

        if key == QtCore.Qt.Key.Key_X:
            if ctrl:
                self.copyItems = [x.getState() for x in itms]
                self.copyPos = self.mapFromGlobal(QtGui.QCursor().pos())
                for itm in itms:
                    self.scene().removeElement(itm)
                
        if key == QtCore.Qt.Key.Key_V:
            if ctrl:
                pastePos = self.mapFromGlobal(QtGui.QCursor().pos())
                delta = pastePos - self.copyPos

                if self.copyItems is not None:
                    for itm in self.copyItems:
                        el = self.scene().createElementFromState(itm)
                        el.setPos(el.pos()+delta)
                        self.scene().addElement(el)
                        

        if len(itms) == 0:
            return super().keyPressEvent(event)

        for itm in itms:
            if not isinstance(itm, OpticalElement) and not isinstance(itm, RayElement):
                continue
            
            ### only act on parent rays
            if isinstance(itm, RayElement) and itm.parent is not None:
                continue
            # print("here")

            
            step = self.scene().getGridSize()

            snap = itm.getSnap()

            if ctrl:
                step = 1
                itm.setSnap(False)

            if key == QtCore.Qt.Key.Key_Left:
                itm.moveBy(-step,0)
            elif key == QtCore.Qt.Key.Key_Right:
                itm.moveBy(step,0)
            elif key == QtCore.Qt.Key.Key_Up:
                itm.moveBy(0,-step)
            elif key == QtCore.Qt.Key.Key_Down:
                itm.moveBy(0,step)
            elif key == QtCore.Qt.Key.Key_R:
                
                angle = self.angleIncrement
                
                if ctrl:
                    angle = self.angleIncrement/10.0

                if mod & QtCore.Qt.KeyboardModifier.ShiftModifier:
                    angle *= -1

                itm.setRotation(itm.rotation() + angle)
            elif key == QtCore.Qt.Key.Key_Delete:

                self.scene().removeElement(itm)
                
            elif key == QtCore.Qt.Key.Key_I:
                print(itm.boundingRect().size())

            ### restore snap state
            itm.setSnap(snap)

        return

    def wheelEvent(self, event: QtGui.QWheelEvent):

        mod = event.modifiers()
        if mod & QtCore.Qt.KeyboardModifier.ShiftModifier:  
            ### move left - right
            move = 25

            if event.angleDelta().y() > 0:
                move *= -1

            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + move)
        elif mod & QtCore.Qt.KeyboardModifier.ControlModifier:
            ### move up - down
            move = 25

            if event.angleDelta().y() > 0:
                move *= -1

            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + move)

        else:
            zoom = 1.25

            # Save the scene pos
            oldPos = self.mapToScene(event.pos())

            # Zoom
            if event.angleDelta().y() > 0:
                zoomFactor = zoom
            else:
                zoomFactor = 1/zoom
                
            self.scale(zoomFactor, zoomFactor)

            # Get the new position
            newPos = self.mapToScene(event.pos())

            # Move scene to old position
            delta = newPos - oldPos
            self.translate(delta.x(), delta.y())

        event.accept()
        # return super().wheelEvent(event)
