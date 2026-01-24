import pygame


class AnimateSprite(pygame.sprite.Sprite):
    def __init__(self, sprite_name):
        super().__init__()
        self.image = pygame.image.load(f'{sprite_name}/{sprite_name}_stop_down.png')
        self.animation = False
        self.current_image = 0
        self.walkLeft = [pygame.image.load('player/playerleft2.png'),
                         pygame.image.load('player/player_stop_left.png'),
                         pygame.image.load('player/playerleft1.png'),
                         pygame.image.load('player/player_stop_left.png')]
        self.walkRight = [pygame.image.load('player/playerright2.png'),
                          pygame.image.load('player/player_stop_right.png'),
                          pygame.image.load('player/playerright1.png'),
                          pygame.image.load('player/player_stop_right.png')]
        self.walkUp = [pygame.image.load('player/playerup1.png'),
                       pygame.image.load('player/player_stop_up.png'),
                       pygame.image.load('player/playerup2.png'),
                       pygame.image.load('player/player_stop_up.png')]
        self.walkDown = [pygame.image.load('player/playerdown1.png'),
                         pygame.image.load('player/player_stop_down.png'),
                         pygame.image.load('player/playerdown2.png'),
                         pygame.image.load('player/player_stop_down.png')]
        self.walkCount = 0
        self.walkCount1 = 0
        self.walkCount2 = 0
        self.right = False
        self.left = False
        self.up = False
        self.down = False
        """
        moving without animation
        self.images = {
            'down': pygame.image.load('player/playerdown1.png'),
            'left': pygame.image.load('player/playerleft1.png'),
            'right': pygame.image.load('player/playerright1.png'),
            'up': pygame.image.load('player/playerup1.png')
        }
        """

    def moving_right_left(self):
        if self.walkCount + 1 >= 8:
            self.walkCount = 0

        if self.left:
            self.image = self.walkLeft[self.walkCount//2]
            self.walkCount += 1

        elif self.right:
            self.image = self.walkRight[self.walkCount//2]
            self.walkCount += 1
        else:
            self.walkCount = 0

    def moving_up(self):
        if self.walkCount1 + 1 >= 8:
            self.walkCount1 = 0

        if self.up:
            self.image = self.walkUp[self.walkCount1//2]
            self.walkCount1 += 1

        else:
            self.walkCount1 = 0

    def moving_down(self):
        if self.walkCount2 + 1 >= 8:
            self.walkCount2 = 0

        if self.down:
            self.image = self.walkDown[self.walkCount2//2]
            self.walkCount2 += 1

        else:
            self.walkCount2 = 0
