import pygame

class Board(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height) 
        
        # 2. The 'UI' Image (The big board that pops up)
        self.ui_image = pygame.image.load("images/board1.png")
        self.ui_rect = self.ui_image.get_rect(center=(pygame.display.get_surface().get_width()//2, 
                                                      pygame.display.get_surface().get_height()//2))
        
        self.open_sound = pygame.mixer.Sound("music/Click.wav")
        self.open = False

    def draw(self, screen):
        if self.open:
            # Draw the UI in the center of the SCREEN, not at the world coordinates
            screen.blit(self.ui_image, self.ui_rect)