import pygame

class Item(pygame.sprite.Sprite):
    def __init__(self, name, x, y, width=0, height=0, has_item=False):
        super().__init__()
        self.name = name
        self.image = pygame.image.load(f"images/{name}.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (20, 20))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.position = [x, y]
        self.has_item = has_item
        self.shake_timer = 0
        self.shake_offset = pygame.math.Vector2(0, 0)
