
class UndoRedoType:
    elementAdded = 1
    elementDeleted = 2
    elementParamChanged = 3
    
class UndoRedoItem:
    def __init__(self, element, type : UndoRedoType, param = None, value = None):
        self.element = element
        self.type = type
        self.param = param
        self.value = value
        
    def getParam(self):
        return self.param
    
    def getValue(self):
        return self.value
    
    def getType(self) -> UndoRedoType:
        return self.type
    
    def getElement(self):
        return self.element
    