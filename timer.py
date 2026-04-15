import pygame


class CountdownTimer:
    FONT_PATH = "fonts/Pixel Emulator.otf"
    FONT_SIZE = 70
    PADDING = 16          # pixels around text for the background pill
    WARNING_THRESHOLD = 20  # seconds at which blinking/red kicks in
    BLINK_INTERVAL = 500   # milliseconds per blink half-cycle

    COLOR_NORMAL  = (255, 255, 255)
    COLOR_WARNING = (255,  50,  50)
    COLOR_BG      = (0,    0,   0, 160)  # semi-transparent black

    def __init__(self, duration):
        self.duration = duration          # total time in seconds
        self.start_time = pygame.time.get_ticks()
        self.remaining_time = duration

        self.font = pygame.font.Font(self.FONT_PATH, self.FONT_SIZE)

        # blinking control
        self.blink = False
        self.blink_timer = 0
        self._was_warning = False         # tracks first entry into warning mode

    def update(self):
        elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
        self.remaining_time = max(self.duration - elapsed, 0)

        if self.remaining_time <= self.WARNING_THRESHOLD:
            # reset blink state on first entry so the timer is always visible first
            if not self._was_warning:
                self.blink = True
                self.blink_timer = pygame.time.get_ticks()
                self._was_warning = True

            now = pygame.time.get_ticks()
            if now - self.blink_timer >= self.BLINK_INTERVAL:
                self.blink = not self.blink
                self.blink_timer = now

    def is_expired(self):
        return self.remaining_time <= 0

    def draw(self, screen):
        # skip drawing when blinking and in the "off" phase
        if self.remaining_time <= self.WARNING_THRESHOLD and not self.blink:
            return

        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        time_text = f"{minutes:02}:{seconds:02}"

        color = self.COLOR_WARNING if self.remaining_time <= self.WARNING_THRESHOLD else self.COLOR_NORMAL
        text_surface = self.font.render(time_text, True, color)

        screen_w = screen.get_width()
        text_w, text_h = text_surface.get_size()

        # center horizontally, fixed distance from top
        x = (screen_w - text_w) // 2
        y = 20

        # draw semi-transparent background pill
        bg_rect = pygame.Rect(
            x - self.PADDING,
            y - self.PADDING // 2,
            text_w + self.PADDING * 2,
            text_h + self.PADDING,
        )
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surface.fill(self.COLOR_BG)
        screen.blit(bg_surface, bg_rect.topleft)

        screen.blit(text_surface, (x, y))
