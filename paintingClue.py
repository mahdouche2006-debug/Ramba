import pygame
import sys

class PaintingClue:
    def __init__(self, screen, game_instance=None, message=[]):
        self.screen = screen
        self.game = game_instance
        
        self.screen_w, self.screen_h = self.screen.get_size()
        self.box_height = int(self.screen_h * 0.22)
        
        # Sizing font for fullscreen
        font_size = int(self.screen_w * 0.02) 
        try:
            self.font = pygame.font.Font("fonts/Pixel Emulator.otf", font_size)
        except:
            self.font = pygame.font.SysFont("Arial", font_size)

        self.dialogues = message

        self.current_dialogue_idx = 0
        
        try:
            raw_box = pygame.image.load("images/bm.png").convert_alpha()
            self.dialogue_box_img = pygame.transform.scale(raw_box, (self.screen_w, self.box_height))
        except:
            self.dialogue_box_img = pygame.Surface((self.screen_w, self.box_height))
            self.dialogue_box_img.fill((50, 50, 50))

        self.text_index = 0
        self.text_speed = 3  
        self.frame_count = 0
        self.is_finished = False
        
        self.cached_lines = self.cached_lines = self.wrap_text(self.dialogues[self.current_dialogue_idx])

    def wrap_text(self, text):
        max_width = self.screen_w - (self.screen_w * 0.15)
        words = text.split(" ")
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if self.font.size(test_line)[0] < max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)
        return lines

    def reset_text(self):
        self.text_index = 0
        self.frame_count = 0

    def draw(self):
        box_y = self.screen_h - self.box_height
        self.screen.blit(self.dialogue_box_img, (0, box_y))

        current_full_text = self.dialogues[self.current_dialogue_idx]
        displayed_text = current_full_text[:self.text_index]
        visible_lines = self.wrap_text(displayed_text)

        line_spacing = int(self.font.get_height() * 1.2)
        x = self.screen_w * 0.07
        y = box_y + (self.box_height * 0.2)

        for line in visible_lines:
            text_surface = self.font.render(line, True, (0,0, 0))
            self.screen.blit(text_surface, (x, y))
            y += line_spacing

    def update(self):

        self.frame_count += 1
        current_full_text = self.dialogues[self.current_dialogue_idx]
        if self.frame_count % self.text_speed == 0:
            if self.text_index < len(current_full_text):
                self.text_index += 1

        self.draw()

