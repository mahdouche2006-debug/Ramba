import math
import pygame

class PaintingUI:
    def __init__(self, painting_image):
        # 1. Background & Setup
        self.template = pygame.image.load("images/PaintingUI.png").convert_alpha()
        self.rect = self.template.get_rect(center=(pygame.display.get_surface().get_width()//2, 
                                                   pygame.display.get_surface().get_height()//2))
        
        self.painting_img = painting_image
        self.painting_img = pygame.transform.scale(self.painting_img, (600, 350)) # Scale to fit nicely in the UI
        self.font = pygame.font.Font("fonts/Pixel Emulator.otf", 25)
        
        # 2. Buttons: 0 = "This is it", 1 = "Go Back"
        offset_y = 630
        self.button_rects = [
            # 1. "Confirm" (Left Box) - Align over frame
            pygame.Rect(self.rect.x + 200, self.rect.y + offset_y, 300, 100), 
            
            # 2. "Exit" (Right Box) - Corrected to align further right
            pygame.Rect(self.rect.x + 500, self.rect.y + offset_y, 300, 100) 
        ]
        self.options = ["Choose", "Go Back"]
        
        # 3. Animation State
        self.clicked_index = None
        self.shake_timer = 0
        self.shake_offset = 0
        self.is_correct = False
        
        # 4. Colors
        self.default_brown = [60, 40, 30]
        self.target_gold = [218, 165, 32]
        self.current_colors = [[60, 40, 30] for _ in range(2)]

    def trigger_feedback(self, index, correct=False):
        self.clicked_index = index
        self.is_correct = correct
        self.shake_timer = pygame.time.get_ticks()

    def draw(self, screen):
        should_close = False
        mouse_pos = pygame.mouse.get_pos()

        # Handle Shaking Logic
        if self.clicked_index is not None:
            elapsed = pygame.time.get_ticks() - self.shake_timer
            if elapsed < 800:
                self.shake_offset = math.sin(elapsed * 0.03) * 15
            else:
                should_close = True # Tell Level to close after animation

        # Draw UI
        screen.blit(self.template, self.rect)
        
        # Center the painting in the main box
        img_pos = self.painting_img.get_rect(center=(self.rect.centerx, self.rect.centery - 80))
        screen.blit(self.painting_img, img_pos)

        # Draw Buttons
        for i, name in enumerate(self.options):
            if i == self.clicked_index:
                color = (0, 180, 50) if self.is_correct else (220, 20, 60)
            else:
                is_hover = self.button_rects[i].collidepoint(mouse_pos) and self.clicked_index is None
                target = self.target_gold if is_hover else self.default_brown
                for j in range(3):
                    self.current_colors[i][j] += (target[j] - self.current_colors[i][j]) * 0.15
                color = tuple(self.current_colors[i])

            text_surf = self.font.render(name, True, color)
            btn_rect = self.button_rects[i].copy()
            if i == self.clicked_index:
                btn_rect.x += self.shake_offset
            
            screen.blit(text_surf, text_surf.get_rect(center=btn_rect.center))
        
        return should_close