import pygame
import animation


class Player(animation.AnimateSprite):

    def __init__(self, x, y):
        super().__init__()
        self.rect = self.image.get_rect(topleft=(x,y))
        self.image.set_colorkey([255, 255, 255])
        self.position = [x, y]

        self.feet = pygame.Rect(0, 0, self.rect.width * 0.5, 12)
        self.old_position = self.position.copy()
        self.speed = 1.5
        
    def save_location(self):
        self.old_position = self.position.copy()

    def update(self):
        self.rect.topleft = self.position
        self.feet.midbottom = self.rect.midbottom

    def move_back(self):
        self.position = self.old_position
        self.rect.topleft = self.position
        self.feet.midbottom = self.rect.midbottom
    
    def is_on_stairs(self, stairs):
        return self.feet.collidelist(stairs) > -1