# Material.py
# Class for storing refractive index of different materials
# 13.09.2022, Floery Tobias
# Released under GNU Public License (GPL)

class Materials:
    def __init__(self):

        self.materials = {
            "FS":     lambda x: (1+0.6961663/(1-(0.0684043/x)**2)+0.4079426/(1-(0.1162414/x)**2)+0.8974794/(1-(9.896161/x)**2))**.5,
            "BK7":      lambda x: (1+1.03961212/(1-0.00600069867/x**2)+0.231792344/(1-0.0200179144/x**2)+1.01046945/(1-103.560653/x**2))**.5,
            "SF10":     lambda x: (1+1.62153902/(1-0.0122241457/x**2)+0.256287842/(1-0.0595736775/x**2)+1.64447552/(1-147.468793/x**2))**.5,
            "CaF2":     lambda x: (1+0.5675888/(1-(0.050263605/x)**2)+0.4710914/(1-(0.1003909/x)**2)+3.8484723/(1-(34.649040/x)**2))**.5,
            "Air":      lambda x: 1+0.05792105/(238.0185-x**-2)+0.00167917/(57.362-x**-2),
        }

    def getMaterial(self, name):
        if name in self.materials:
            return self.materials[name]
        else:
            raise NameError(f"Material {name} not found in list")

    def listMaterials(self):
        return self.materials.keys()
        
if __name__ == "__main__":
    m = Materials()

    caf2 = m.getMaterial("CaF2")
    bk7 = m.getMaterial("BK7")


    print(bk7(0.5),bk7(1.0), bk7(1.5))