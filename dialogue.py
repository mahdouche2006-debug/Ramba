import pygame

class Dialogue:
    
    def __init__(self, message):
        self.font = pygame.font.SysFont("fonts/Pixel Emulator.otf", 70)
        
        self.dialogues = message # message should be a list
        self.sound = pygame.mixer.Sound("music/typingOneChar.mp3")
        self.sound.set_volume(0.6)

        self.dialogue_index = 0
        self.current_length = 0
        self.letter_timer = 0
        
        self.active = False

    def start(self):
        self.active = True
        self.dialogue_index = 0
        self.current_length = 0
        self.letter_timer = 0

    def handle_event(self, event):
        if not self.active:
            return
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_c:

            if self.current_length == len(self.dialogues[self.dialogue_index]):
                if self.dialogue_index < len(self.dialogues) - 1:
                    self.dialogue_index += 1
                    self.current_length = 0
                    self.letter_timer = 0

                else:
                    self.active = False

    def update(self):
        if not self.active:
            return

        self.letter_timer += 1
        if self.letter_timer % 35 == 0 and self.current_length < len(self.dialogues[self.dialogue_index]):
            self.current_length += 1
            self.sound.play()

    def draw(self, screen):
        if not self.active:
            return

        text = self.dialogues[self.dialogue_index][:self.current_length]
        text_surface = self.font.render(text, False, (255, 255, 255))
        screen.fill((0, 0, 0))
        screen.blit(pygame.image.load("images/c.png"), (screen.get_width() - 120, screen.get_height() - 120))
        screen.blit(text_surface, (screen.get_width() // 2 - text_surface.get_width()//2, screen.get_height() // 2 - text_surface.get_height()//2))