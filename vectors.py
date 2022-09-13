# vectors.py
# Helper functions for vector math
# 13.09.2022, Floery Tobias
# Released under GNU Public License (GPL)

import math
from PyQt5.QtCore import QPointF

def rotate(p1: QPointF, alpha):
    return QPointF(p1.x()*math.cos(alpha) - p1.y()*math.sin(alpha), p1.x()*math.sin(alpha) + p1.y()*math.cos(alpha))

def mirrorX(p1 : QPointF, center : QPointF = QPointF()):
    return QPointF(2*center.x()-p1.x(), p1.y())

def invert(p1 : QPointF):
    return p1*-1

def crossP(p1: QPointF, p2: QPointF):
    return p1.x()*p2.y() - p1.y()*p2.x()

def dotP(p1: QPointF, p2: QPointF):
    return p1.x()*p2.x()+ p1.y()*p2.y()

def project(p1: QPointF, p2: QPointF):
    k = dotP(p1, p2) / dotP(p2, p2)
    return k*p2

def distance(p1: QPointF, p2: QPointF = QPointF(0,0)):
    return  math.sqrt((p2.x()-p1.x())**2 + (p2.y()-p1.y())**2)

def angle(v1: QPointF, v2 : QPointF):
    #return math.acos(dotP(v1, v2)/(distance(v1)*distance(v2)))
    return math.asin(crossP(v1, v2)/(distance(v1)*distance(v2)))

def angleOfDirection(dir: QPointF):
    return math.atan(dir.y()/dir.x())
    
def normalize(p1: QPointF):
    return p1 / distance(p1, QPointF(0,0))

def normalVector(p1: QPointF, p2: QPointF):
    d = p2-p1    
    return (QPointF(-d.y(), d.x()), QPointF(d.y(), -d.x()))

def normalDir(p1: QPointF, p2: QPointF):
    d = p2-p1    
    return normalize(QPointF(d.y(), -d.x()))

def LineCircle(p1: QPointF, p2: QPointF, c: QPointF, r):
    
    if r < 0:
        r *= -1
        
    dir = normalize(p2-p1)

    # print(dir)

    t = dir.x() * (c.x()-p1.x()) + dir.y() * (c.y() - p1.y())

    # print(t)

    E = t * dir + p1

    lec = distance(E, c)
    
    # print(lec)

    if lec < r:
        dt = math.sqrt(r**2 - lec**2)
        F = (t-dt) * dir + p1
        G = (t+dt) * dir + p1
        return [F, G]
    elif lec == r:
        return [E]
    else:
        return None

def LineLine(p1: QPointF, p2: QPointF, p3: QPointF, p4: QPointF):
    # print("Checking Intersection")

    p = p1
    r = p2-p1

    q = p3
    s = p4-p3

    if crossP(r, s) == 0:
        return None

    else:
        t = crossP(q-p, s) / crossP(r, s)
        u = crossP(p-q, r) / crossP(s, r)
        # print(t)
        # print(u)
        if t>=0 and t<=1 and u>=0 and u<=1:
            return (r * t) + p
        else:
            return None

if __name__ == "__main__":
    p1 = QPointF(0,0)
    p2 = QPointF(100, 0)


    p3 = QPointF(200,0 )

    print(dotP(p3-p1, p2-p3), dotP(p3-p1, p2-p1))
    # p3 = QPointF(50,50)
    # p4 = QPointF(50,-50)


    # # print(LineLine(p1,p2,p3,p4))

    # c = QPointF(50, 50)

    # print(LineCircle(p1,p2, c, 50))



