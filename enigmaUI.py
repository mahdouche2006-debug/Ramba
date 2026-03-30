import math

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
        
        self.font = pygame.font.Font("fonts/Pixel Emulator.otf", 25)
        
        # 3. Define Clickable Rects (Coordinates relative to the SCREEN)
        # You will need to adjust these numbers based on where your boxes are in your image
        offset_y = 650
        self.button_rects = [
            pygame.Rect(self.rect.x + 90,  self.rect.y + offset_y, 200, 80), # Box 1
            pygame.Rect(self.rect.x + 420, self.rect.y + offset_y, 200, 80), # Box 2
            pygame.Rect(self.rect.x + 700, self.rect.y + offset_y, 200, 80), # Box 3
        ]

        self.clicked_index = None
        self.shake_timer = 0
        self.shake_offset = 0
        self.is_correct = False # Tracks if we should show Green or Red

    def trigger_wrong_anim(self, index, correct = False):
        self.clicked_index = index
        self.is_correct = correct
        self.shake_timer = pygame.time.get_ticks()

    def draw(self, screen):
        is_done_shaking = False
    
        if self.clicked_index is not None:
            elapsed = pygame.time.get_ticks() - self.shake_timer
            if elapsed < 800: # Increased to 800ms to see the slow shake better
                # --- SLOWER SHAKE MATH ---
                # Changed 0.1 to 0.03 to make it oscillate slower
                # Changed 10 to 15 to make the sway wider/more visible
                self.shake_offset = math.sin(elapsed * 0.03) * 10
            else:
                # Animation is finished!
                self.clicked_index = None
                self.shake_offset = 0
                is_done_shaking = True # Signal that we can close now

        # Draw background
        screen.blit(self.template, self.rect)
        screen.blit(self.sculpture_img, (self.rect.x + 100, self.rect.y + 50))

        for i, name in enumerate(self.options):
            color = (0, 0, 0) # Default Black
            if i == self.clicked_index:
                color = (0, 200, 0) if self.is_correct else (255, 0, 0)
            
            text_surf = self.font.render(name, True, color)
            
            # Apply shake_offset only to the X of the wrong button
            current_rect = self.button_rects[i].copy()
            if i == self.clicked_index:
                current_rect.x += self.shake_offset
                
            text_rect = text_surf.get_rect(center=current_rect.center)
            screen.blit(text_surf, text_rect)

        return is_done_shaking