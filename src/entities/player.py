if __name__ == "__main__":
    import projectiles as pr
else:
    import entities.projectiles as pr

class Player:

    def __init__(self, pv, speed, x, y, size):
        self.pv = pv
        self.speed = speed
        self.posx = x
        self.posy = y
        self.size = size
        self.orientation = 1

    def moveRight(self):
        self.posx += self.speed
        self.orientation = 1

    def moveLeft(self):
        self.posx -= self.speed
        self.orientation = -1

    def jump(self):
        self.posy -= 50

    def tirer(self):
        return pr.ProjectilJoueur(self.posx + self.size + 10,self.posy + 10,self.orientation)