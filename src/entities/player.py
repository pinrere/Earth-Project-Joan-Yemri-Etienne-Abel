class Player:

    def __init__(self, pv, speed, x, y):
        self.pv = pv
        self.speed = speed
        self.posx = x
        self.posy = y
        self.orientation = 1

    def moveRight(self):
        self.posx += self.speed
        self.orientation = 1

    def moveLeft(self):
        self.posx -= self.speed
        self.orientation = -1

    def jump(self):
        self.posy -= 100