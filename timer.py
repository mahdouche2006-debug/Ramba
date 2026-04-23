import pygame


class CountdownTimer:
    FONT_PATH         = "fonts/Pixel Emulator.otf"
    FONT_SIZE         = 36    # matches the item counter font size
    WARNING_THRESHOLD = 20
    BLINK_INTERVAL    = 500
    PAD               = 8
    MARGIN            = 12   # distance from screen edge

    def __init__(self, duration):
        self.duration       = duration
        self.start_time     = pygame.time.get_ticks()
        self.remaining_time = duration

        self.font = pygame.font.Font(self.FONT_PATH, self.FONT_SIZE)

        self.blink        = False
        self.blink_timer  = 0
        self._was_warning = False

    def update(self):
        elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
        self.remaining_time = max(self.duration - elapsed, 0)

        if self.remaining_time <= self.WARNING_THRESHOLD:
            if not self._was_warning:
                self.blink        = True
                self.blink_timer  = pygame.time.get_ticks()
                self._was_warning = True
            now = pygame.time.get_ticks()
            if now - self.blink_timer >= self.BLINK_INTERVAL:
                self.blink       = not self.blink
                self.blink_timer = now

    def is_expired(self):
        return self.remaining_time <= 0

    def _lerp(self, a, b, t):
        t = max(0.0, min(1.0, t))
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    def _get_color(self):
        ratio = self.remaining_time / max(self.duration, 1)
        if ratio > 0.5:
            return self._lerp((80, 220, 100), (240, 210, 0), (1.0 - ratio) * 2.0)
        elif ratio > 0.25:
            return self._lerp((240, 210, 0), (255, 100, 0), (0.5 - ratio) * 4.0)
        else:
            return self._lerp((255, 100, 0), (255, 20, 20), (0.25 - ratio) * 4.0)

    def draw(self, screen):
        if self.remaining_time <= self.WARNING_THRESHOLD and not self.blink:
            return

        color = self._get_color()

        minutes   = self.remaining_time // 60
        seconds   = self.remaining_time % 60
        label     = self.font.render(f"{minutes:02}:{seconds:02}", False, color)

        box_w = label.get_width()  + self.PAD * 2
        box_h = label.get_height() + self.PAD * 2

        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        screen.blit(bg,    (self.MARGIN, self.MARGIN))
        screen.blit(label, (self.MARGIN + self.PAD, self.MARGIN + self.PAD))
