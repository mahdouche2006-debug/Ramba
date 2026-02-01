import pygame

class Item(pygame.sprite.Sprite):
    def __init__(self, item, x, y):
        super().__init__()
        self.image = pygame.image.load(f"images/{item}.png").convert_alpha()
        self.image = pygame.transform.smoothscale(self.image, (16, 16))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.position = [x, y]