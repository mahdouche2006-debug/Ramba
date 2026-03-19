import pygame

class EnigmaUI:
    def __init__(self, sculpture_image, artist_names, correct_index):
        # 1. Load the background template you just drew
        self.template = pygame.image.load("images/sculptureImage.png").convert_alpha()
        self.rect = self.template.get_rect(center=(pygame.display.get_surface().get_width()//2, 
                                                   pygame.display.get_surface().get_height()//2))
        
        # 2. Sculpture-specific data
        self.sculpture_img = sculpture_image # A pre-loaded surface of the actual statue
        self.options = artist_names          # List of 3 strings: ["Rodin", "Donatello", "Bernini"]
        self.correct_index = correct_index   # 0, 1, or 2
        
        self.font = pygame.font.Font("fonts/Pixel Emulator.otf", 20)
        
        # 3. Define Clickable Rects (Coordinates relative to the SCREEN)
        # You will need to adjust these numbers based on where your boxes are in your image
        offset_y = 950
        self.button_rects = [
            pygame.Rect(self.rect.x + 20,  self.rect.y + offset_y, 200, 80), # Box 1
            pygame.Rect(self.rect.x + 240, self.rect.y + offset_y, 200, 80), # Box 2
            pygame.Rect(self.rect.x + 460, self.rect.y + offset_y, 200, 80), # Box 3
        ]

    def draw(self, screen):
        # Draw background template
        screen.blit(self.template, self.rect)
        
        # Draw the sculpture image in the top big box
        screen.blit(self.sculpture_img, (self.rect.x + 100, self.rect.y + 50))
        
        # Draw the 3 artist names on top of the button boxes
        for i, name in enumerate(self.options):
            text_surf = self.font.render(name, True, (255, 255, 255))
            # Center the text in its specific button rect
            text_rect = text_surf.get_rect(center=self.button_rects[i].center)
            screen.blit(text_surf, text_rect)