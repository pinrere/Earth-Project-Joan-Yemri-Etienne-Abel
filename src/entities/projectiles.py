class ProjectilJoueur:

    def __init__(self,x,y,vitesse):
        self.posx = x
        self.posy = y
        self.vitesse = vitesse

    def avancer(self):
        self.posx += self.vitesse