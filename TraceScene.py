# TraceScene.py
# Class for drawing, printing and exporting a scnene and calculating the rays, still very simple
# 13.09.2022, Floery Tobias
# Released under GNU Public License (GPL)


from PyQt5.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent
from PyQt5 import QtCore, QtGui

from OpticalElement import *
import json

from UndoRedo import UndoRedoItem, UndoRedoType

class TraceScene(QGraphicsScene):
    def __init__(self, parent = None, gridSize = 50, drawLines = False):
        super(TraceScene, self).__init__(parent)

        self.gridSize = gridSize
        self.drawLines = drawLines

        self.setSceneRect(QtCore.QRectF(-5000,-5000,10000,10000))
        # self.setItemIndexMethod(QGraphicsScene.NoIndex)
        
        self.checkCount = 0
        self.intensityThreshold : float = 0.05
        
        self.history : list[UndoRedoItem] = []
        self.movingItem = None
        self.oldPos = None
        
        self.selectionChanged.connect(self.selChange)

    def dragMoveEvent(self, e):
        e.acceptProposedAction()
        
    def undo(self):
        if len(self.history) < 1:
            return
        
        # print("undo: ", len(self.history))
        
        item = self.history.pop()
        
        if item.getType() == UndoRedoType.elementAdded:
            self.removeElement(item.getElement(), addHistory=False)
        elif item.getType() == UndoRedoType.elementDeleted:
            self.addElement(item.getElement(), snap=False,addHistory=False)
        elif item.getType() == UndoRedoType.elementParamChanged:
            param = item.getParam()
            value = item.getValue()
            element = item.getElement()
            print("param changed: ", element, param, value)
            if  param ==  "pos":
                element.setPos(value)
                self.history.pop()
            elif param == "rot":
                element.setRotation(value)
                self.history.pop()
            pass
        
    def list(self):
        
        for i, itm in enumerate(self.items()):
            if isinstance(itm, OpticalElement):
                print(i, itm)
            elif isinstance(itm, RayElement):
                print(i, itm, itm.intensity, itm.wl, itm.line().length(), itm.handled)
            else:
                print(i, itm, "XXX")
        
        # ray_dict = {}

        # for ray in self.rays:
        #     wl = ray.wl
        #     l = ray.getLength()

        #     if wl in ray_dict:
        #         ray_dict[wl] = ray_dict[wl] + l
        #     else:
        #         ray_dict[wl] = l
        
        # distances = 0
        # for d in ray_dict.values():
        #     distances += d
        # mean_d = distances/len(ray_dict)

        # print("="*40)
        # print("Dispersion:")
        # for k,v in ray_dict.items():
        #     print(f"wl: {k:.3f} um, len: {v/10.0:.3f} mm, ({(v-mean_d)/10.0:.3f} mm)")
            
    def setGridSize(self, gridSize):
        if gridSize < 10:
            return
        
        self.gridSize = gridSize

    def getGridSize(self):        
        return self.gridSize

    def drawBackground(self, painter: QtGui.QPainter, rect: QtCore.QRectF) -> None:
        painter.setPen(QtGui.QPen(QtGui.QColor(100,100,100, 200), 0.5))
        xs = int(rect.left()) - (int(rect.left()) % self.gridSize)
        ys = int(rect.top()) - (int(rect.top()) % self.gridSize)

        points = []

        x = xs
        y = ys

        if self.drawLines:
            lines = []
            while x < rect.right():
                lines.append(QtCore.QLineF(x, rect.top(), x, rect.bottom()))
                x += self.gridSize

            while y < rect.bottom():
                lines.append(QtCore.QLineF(rect.left(), y, rect.right(), y))
                y += self.gridSize

            painter.drawLines(lines)
        else:
            while x < rect.right():
                y = ys
                while y < rect.bottom():
                    points.append(QtCore.QPointF(x,y))
                    y += self.gridSize
                x += self.gridSize

            painter.drawPoints(points)

        return super().drawBackground(painter, rect)
    
    
    def showElementEditor(self, element):
        # print("show: ", element)
        if isinstance(element, RayElement):
            if element.parent is not None:
                ### find the parent ray
                pr = list(element.getParents())
                element = pr[0]

        dlg = element.getDialog()
        ret = dlg.exec_()

        if ret == QDialog.DialogCode.Accepted:
            element.setState(dlg.state)
            self.calculateScene()
            # print("accpted: ", dlg.state)

    def selChange(self) -> None:
        itms = self.selectedItems()
        
        if len(itms) == 1:
            if isinstance(itms[0], RayElement):
                pr = list(itms[0].getParents(True))
                for ray in pr:
                    ray.setSelected(True)
                

    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        pos = event.buttonDownScenePos(QtCore.Qt.MouseButton.LeftButton)
        itms = self.items(pos)

        if len(itms) > 0:
            self.movingItem = itms[0]
        else:
            self.movingItem = None
            
        if self.movingItem is not None and event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.oldPos = self.movingItem.pos()

        # print(self.movingItem, self.oldPos)
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        if self.movingItem is not None and event.button() == QtCore.Qt.MouseButton.LeftButton:
            if self.oldPos != self.movingItem.pos():
                hi = UndoRedoItem(self.movingItem, UndoRedoType.elementParamChanged,"pos", self.oldPos)
                self.history.append(hi)

            self.movingItem = None
        return super().mouseReleaseEvent(event)
                        
    def addElement(self, element, snap = True, addHistory = True):
        # self.initial_elements.append(element)
        
        self.clearSelection()
        
        if isinstance(element, RayElement):

            if snap:
                pos = element.getSnapPos(element.pos(), self.gridSize)
                element.setPos(pos)
                element.handled = False

            self.addItem(element)
            
            if addHistory:
                self.history.append(UndoRedoItem(element, UndoRedoType.elementAdded))
                            
            element.itemMovedOrRotated.connect(self.calculateScene)
            
        elif isinstance(element, OpticalElement):

            if snap:
                pos = element.getSnapPos(element.pos(), self.gridSize)
                element.setPos(pos)

            
            self.addItem(element)
            if addHistory:
                self.history.append(UndoRedoItem(element, UndoRedoType.elementAdded))
            element.itemMovedOrRotated.connect(self.calculateScene)

            ### remove all children rays and update primary rays....
            
            itms = element.collidingItems(QtCore.Qt.ItemSelectionMode.IntersectsItemBoundingRect)

            rays = [x for x in itms if isinstance(x, RayElement)]

            for ray in rays:
                ray.removeChildren()

                if ray.parent is not None:
                    ray.parent.handled = False
                    ray.parent.setLength(2000)
                    ray.parent.removeChildren()
                else:
                    ray.handled = False

        self.calculateScene()

    def removeElement(self, element, addHistory=True):
        if isinstance(element, OpticalElement):
            rays = element.rays
            for ray in rays:
                ray.removeChildren()

                if ray.parent is not None:
                    ray.parent.handled = False
                    ray.parent.setLength(2000)
                    ray.parent.removeChildren()
                    
            self.removeItem(element)
            if addHistory:
                self.history.append(UndoRedoItem(element, UndoRedoType.elementDeleted))

        elif isinstance(element, RayElement):
            pr = list(element.getParents(True))            
            element = pr[-1]

            element.removeChildren()
            # print("x")
            self.removeItem(element)
            if addHistory and element.parent is None:
                element.setSelected(False)
                self.history.append(UndoRedoItem(element, UndoRedoType.elementDeleted))

        # del(element)
        self.calculateScene()

    def calculateScene(self):
        # print("calc")
        processedRays = 0
        # print("Check: ", self.checkCount)
        # self.checkCount += 1

        # if self.cbSingleStep:
        #     singleStep = self.cbSingleStep.isChecked()

        # if not singleStep:
        #     self.reset()

        ### remove all but parent rays
        for itm in self.items():
            if isinstance(itm, RayElement):
                if itm.parent is None:
                    itm.handled = False
                    itm.removeChildren()

            if isinstance(itm, OpticalElement):
                itm.rays = []

        loops = 0
        abort = False
        ray_len = math.sqrt(self.sceneRect().width()**2 + self.sceneRect().height()**2)

        # print("calculate scene")

        while loops < 100:
            # print("="*80)
            # print(loops)
            loops += 1

            # print("-"*80)

            newRays = []

            rays = [x for x in self.items() if isinstance(x, RayElement)]
            
            # print("Handling: ", len(rays), " rays")

            for ray in rays: # self.rays
                # print("Ray: ",ray, ray.handled)
                if ray.handled:
                    continue
        
                ### make ray long
                ray.setLength(ray_len)

                ray_p1 = ray.mapToScene(ray.line().p1())
                ray_p2 = ray.mapToScene(ray.line().p2())

                lst = ray.collidingItems(QtCore.Qt.ItemSelectionMode.IntersectsItemBoundingRect)
                ### only check interference with Materials
                lst = [x for x in lst if isinstance(x, OpticalElement)]

                hits = []
                # print("Colliding: ", len(lst))
                if len(lst) > 0:

                    for itm in lst:
                        ret = itm.getIntersections(itm.mapFromScene(ray_p1), itm.mapFromScene(ray_p2))
                        if len(ret) > 0:
                            hits.append((itm, ret[0]))

                if len(hits) > 0:

                    ### sort hits on all elements by distance from ray start
                    x = sorted(hits, key = lambda x: vectors.distance(x[1][0], x[0].mapFromScene(ray_p1)))                 

                    ### unpack closest hit
                    itm , (pt, n, iface) = x[0]
                    # print(f"Item: {itm}, pt: {pt}, n: {n}, iface: {iface}")

                    hit_pos = itm.mapToScene(pt)
                    ray.setEndPoint(hit_pos)

                    ### get surface normal in scene coordinates
                    n_rot = vectors.rotate(n, itm.rotation() / 180.0 * math.pi)

                    ### check if ray starts in optical element
                    ### this checks could be removed for rays created in the "check loop"
                    sitm = self.items(ray_p1, QtCore.Qt.ItemSelectionMode.IntersectsItemShape)
                    sitm = [x for x in sitm if isinstance(x, OpticalElement)]

                    wls = ray.wl

                    if not isinstance(ray.wl, list):
                        wls = [ray.wl]

                    for idx, wl in enumerate(wls):
                        
                        n_rotR = n_rot
                        ### assign refractive indices
                        if len(sitm) == 0:
                            n1 = 1
                            n2 = itm.getRefractiveIndex(wl)                        
                        else:
                            n1 = itm.getRefractiveIndex(wl)
                            n2 = 1

                        
                        ### angle between ray and surface normal
                        angle = vectors.angle(ray_p2-ray_p1, n_rotR) 

                        # print(wl, n1, n2, angle*180/math.pi)
                        
                        # print("Angle: ", angle*180/math.pi)
                        # print(iface.t, iface.r, n1, n2)

                        r = iface.r

                        if ray.intensity * iface.t > self.intensityThreshold:
                            ### we have transmission on the surface    

                            try:
                                if iface.lines is None:
                                    # print(angle*180/math.pi, n1, n2)

                                    angle_out = math.asin(n1/n2*math.sin(angle))

                                    # print(angle_out*180/math.pi)
                                else:
                                    # print("Grating: ", angle*180/math.pi, iface.lines, n1,n2)
                                    m = -1
                                    
                                    # angle_out = math.asin(math.sin(angle/180.0*math.pi) - m * ray.wl*1e6 / d)
                                    angle_out = math.asin((n1*math.sin(angle) - m * wl*1e-6 * iface.lines*1e3)/n2)

                                    # print(angle*180/math.pi, angle_out*180/math.pi)

                                if n2 < n1:
                                    angle_out *= -1

                                ### let the surface normal point into the same direction as incoming ray
                                if vectors.dotP(n_rotR, ray_p2-ray_p1) < 0:
                                    n_rotR = vectors.invert(n_rotR)
                                

                                t_dir = vectors.rotate(n_rotR, angle_out)

                                t_pos=hit_pos

                                # t_ray = RayElement(t_pos.x() + t_dir.x(), t_pos.y() + t_dir.y(), t_pos.x() + t_dir.x() * ray_len, t_pos.y() + t_dir.y() * ray_len, intensity = ray.intensity*iface.t, wl = ray.wl, color=ray.color, parent=ray)                            
                                t_ray = RayElement(t_dir.x(), t_dir.y(), t_dir.x() * ray_len, t_dir.y() * ray_len, intensity = ray.intensity*iface.t, wl = [wl], color=ray.color[idx], showArrow=ray.showArrow,parent=ray)
                                t_ray.setPos(t_pos)
                                newRays.append(t_ray)
                                itm.rays.append(t_ray)
                            
                            except ValueError:
                                # print("error in calculating angle")
                                ### if it cannot be tranmitted, reflect it ;)
                                r = 1.0
                                # pass

                        if ray.intensity * r > self.intensityThreshold:
                            try:

                                ### let the surface normal point into different direction as incoming ray
                                if vectors.dotP(n_rotR, ray_p2-ray_p1) > 0:
                                    n_rotR = vectors.invert(n_rotR)

                                angle_out = angle

                                if iface.lines is None:
                                    if n2 < n1:
                                        angle_out *= -1
                                else:
                                    m = -1
                                    # angle_out = math.asin(math.sin(angle/180.0*math.pi) - m * ray.wl*1e6 / d)
                                    angle_out = math.asin(math.sin(angle) - m * wl*1e-6 * iface.lines*1e3)

                                # print(angle)

                                t_dir = vectors.rotate(n_rotR, -angle_out)

                                t_pos=hit_pos

                                # t_ray = RayElement(t_pos.x() + t_dir.x(), t_pos.y() + t_dir.y(), t_pos.x() + t_dir.x() * ray_len, t_pos.y() + t_dir.y() * ray_len, intensity = ray.intensity * r, wl = ray.wl, color=ray.color, parent=ray)
                                t_ray = RayElement(t_dir.x(), t_dir.y(), t_dir.x() * ray_len, t_dir.y() * ray_len, intensity = ray.intensity * r, wl = [wl], color=ray.color[idx], showArrow=ray.showArrow, parent=ray)
                                t_ray.setPos(t_pos)

                                newRays.append(t_ray)
                                itm.rays.append(t_ray)                      
                            except ValueError:
                                # if ray not in itm.rays:
                                #     itm.rays.append(ray)
                                pass
                            # print("Refl: ",t_dir, n_rot)  
                        # else:
                        #     print("Ray <- ", ray.intensity, iface.t)
                        # itm.markers.append(pt)
                        # itm.normals.append((pt-n*15,pt+n*15))
                                                    ### keep ray in item for updates
                        if ray not in itm.rays:
                            itm.rays.append(ray)

                ray.handled = True

            processedRays += len(newRays)
            # self.rays.extend(newRays)
            
            for ray in newRays:
                self.addItem(ray)

            # if singleStep or abort:
            if abort:
                self.update(self.sceneRect())
                break

            if len(newRays)==0:
                abort = True
                
        # if not singleStep:
        #     print("Finished in",loops, "iterations")

        # self.view.scene().update()
        # print("loops: ", loops, " processed rays ", processedRays)                

    def saveToFile(self, filename):
        with open(filename, 'w') as writer:
            
            data = []
            for itm in self.items():
                if isinstance(itm, RayElement):
                    # only save parent rays
                    if itm.parent is None:
                        data.append(itm.getState())
                elif isinstance(itm, OpticalElement):
                    data.append(itm.getState())

            json.dump(data, writer, indent=2)

    def clearScene(self):
        # self.clear()
        self.history.clear()

        for itm in self.items():
            self.removeItem(itm)

    def createElementFromState(self, state) -> QGraphicsObject:
        x=globals()[state["type"]]
        z=x()
        z.setState(state)
        return z
                
    def loadFromFile(self, filename):

        self.clearScene()

        with open(filename, 'r') as reader:
            data = json.load(reader)
            # print(data)

            for itm in data:
                # try:
                el = self.createElementFromState(itm)
                self.addElement(el, snap = False)
                # except Exception as ex:
                #     print("Error parsing: ", itm, ex)
                #     pass
            
            # self.drawScene(elements)
            self.calculateScene()
