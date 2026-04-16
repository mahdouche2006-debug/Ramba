import pygame


class CountdownTimer:
    def __init__(self, duration):
        self.duration = duration  # total time in seconds
        self.start_time = pygame.time.get_ticks()
        self.remaining_time = duration

        self.font = pygame.font.SysFont("fonts/Pixel Emulator.otf", 70)

        # blinking control
        self.blink = False
        self.blink_timer = 0
        self.blink_interval = 500  # milliseconds

    def update(self):
        # calculate remaining time
        elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
        self.remaining_time = max(self.duration - elapsed, 0)

        # blinking logic when 20 seconds or less
        if self.remaining_time <= 20:
            current_time = pygame.time.get_ticks()
            if current_time - self.blink_timer > self.blink_interval:
                self.blink = not self.blink
                self.blink_timer = current_time

    def draw(self, screen):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60

        time_text = f"{minutes:02}:{seconds:02}"

        # blinking red when <= 20 seconds
        if self.remaining_time <= 20:
            if self.blink:
                text_surface = self.font.render(time_text, True, (255, 0, 0))
            else:
                return  # skip drawing → creates blink effect
        else:
            text_surface = self.font.render(time_text, True, (0, 0, 0))

        screen.blit(text_surface, (10, 10))
