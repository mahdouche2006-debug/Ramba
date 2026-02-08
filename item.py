import pygame

class Item(pygame.sprite.Sprite):
    def __init__(self, name, x, y, has_item=False):
        super().__init__()
        self.name = name
        self.image = pygame.image.load(f"images/{name}.png")
        self.rect = self.image.get_rect(topleft=(x, y))
        self.position = [x, y]
        self.has_item = has_item
