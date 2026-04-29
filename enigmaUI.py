import math

import pygame

class EnigmaUI:
    def __init__(self, sculpture_image, artist_names, correct_index):
        # 1. Load the background template you just drew
        self.template = pygame.image.load("images/EnigmaUI.png").convert_alpha()
        self.rect = self.template.get_rect(center=(pygame.display.get_surface().get_width()//2, 
                                                   pygame.display.get_surface().get_height()//2))
        
        # 2. Sculpture-specific data
        self.sculpture_img = sculpture_image # A pre-loaded surface of the actual statue
        self.options = artist_names          # List of 3 strings: ["Rodin", "Donatello", "Bernini"]
        self.correct_index = correct_index   # 0, 1, or 2
        
        self.font = pygame.font.Font("fonts/Pixel Emulator.otf", 25)
        
        # 3. Define Clickable Rects (Coordinates relative to the SCREEN)
        # The Y-offset from the top of the template to the top of the button boxes
        # Based on your image, the buttons are quite low
        offset_y = 615 

        self.button_rects = [
            # Box 1 (Left)
            pygame.Rect(self.rect.x + 45,  self.rect.y + offset_y, 285, 135), 
            # Box 2 (Middle)
            pygame.Rect(self.rect.x + 365, self.rect.y + offset_y, 285, 135), 
            # Box 3 (Right)
            pygame.Rect(self.rect.x + 685, self.rect.y + offset_y, 285, 135), 
        ]

        self.clicked_index = None
        self.shake_timer = 0
        self.shake_offset = 0
        self.is_correct = False # Tracks if we should show Green or Red

        # Initialize 3 colors (one for each button) starting at your default dark brown
        self.current_colors = [[60, 40, 30] for _ in range(3)]
        self.target_gold = [218, 165, 32]
        self.default_brown = [60, 40, 30]

        # Keyboard navigation — which button is currently focused
        self.selected_index = 0

    def trigger_shake_anim(self, index, correct = False):
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
        screen.blit(self.sculpture_img, (self.rect.centerx - self.sculpture_img.get_width() // 2, self.rect.centery - self.sculpture_img.get_height() // 2 - 100))

        mouse_pos = pygame.mouse.get_pos()

        for i, name in enumerate(self.options):
            color = (60, 40, 30) # A dark brown usually looks better than pure black on that parchment

            if i == self.clicked_index:
                color = (0, 180, 0) if self.is_correct else (200, 0, 0)

            else:
                # Gold-highlight if mouse is hovering OR this is the keyboard-selected button
                is_highlighted = (
                    self.clicked_index is None and
                    (self.button_rects[i].collidepoint(mouse_pos) or i == self.selected_index)
                )
                target = self.target_gold if is_highlighted else self.default_brown

                # Transition each RGB channel slowly (Lerp)
                for j in range(3):
                    diff = target[j] - self.current_colors[i][j]
                    self.current_colors[i][j] += diff * 0.15

                color = tuple(self.current_colors[i])

            text_surf = self.font.render(name, True, color)

            # Apply shake_offset only to the clicked button
            current_rect = self.button_rects[i].copy()
            if i == self.clicked_index:
                current_rect.x += self.shake_offset

            text_rect = text_surf.get_rect(center=current_rect.center)
            screen.blit(text_surf, text_rect)

            # Draw a gold outline around the keyboard-selected button
            if i == self.selected_index and self.clicked_index is None:
                pygame.draw.rect(screen, (255, 215, 0), current_rect.inflate(6, 6), width=3, border_radius=6)

        return is_done_shaking