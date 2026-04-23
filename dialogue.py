import pygame
import random


# ── Pixel art fleur-de-lis (11 × 15) ──────────────────────────────────────
_FLEUR = [
    [0,0,0,0,0,1,0,0,0,0,0],
    [0,0,0,0,1,1,1,0,0,0,0],
    [0,0,0,0,1,1,1,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0],
    [0,0,1,0,1,1,1,0,1,0,0],
    [0,1,1,1,0,1,0,1,1,1,0],
    [0,0,1,1,1,1,1,1,1,0,0],
    [0,0,0,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,1,1,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0],
    [0,0,0,0,1,1,1,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0],
]

# ── Pixel art small diamond / vine node (7 × 7) ───────────────────────────
_DIAMOND = [
    [0,0,0,1,0,0,0],
    [0,0,1,1,1,0,0],
    [0,1,1,0,1,1,0],
    [1,1,0,0,0,1,1],
    [0,1,1,0,1,1,0],
    [0,0,1,1,1,0,0],
    [0,0,0,1,0,0,0],
]


def _draw_grid(surf, color, step=40):
    """Subtle pixel grid for parchment texture."""
    w, h = surf.get_size()
    for x in range(0, w, step):
        pygame.draw.line(surf, color, (x, 0), (x, h))
    for y in range(0, h, step):
        pygame.draw.line(surf, color, (0, y), (w, y))


def _draw_pixel_art(surf, grid, ox, oy, color, scale=2):
    for r, row in enumerate(grid):
        for c, val in enumerate(row):
            if val:
                pygame.draw.rect(surf, color,
                                 (ox + c*scale, oy + r*scale, scale, scale))


class Dialogue:
    FONT_PATH      = "fonts/Pixel Emulator.otf"
    FONT_SIZE      = 34
    HINT_FONT_SIZE = 18
    TYPE_SPEED     = 3
    BLINK_INTERVAL = 550

    # Dark moyen-âge palette
    C_PARCHMENT  = (22,  14,  6  )   # near-black background
    C_PARCH_DARK = (36,  24,  10 )   # slightly lighter for text box
    C_INK        = (215, 190, 135)   # warm cream — readable on dark bg
    C_DARK_BROWN = (10,  6,   2  )   # near-black outer border
    C_GOLD       = (185, 145, 42 )   # illuminated gold (unchanged)
    C_RED        = (150, 28,  28 )   # heraldic red accent
    C_FLEUR      = (140, 100, 20 )   # slightly muted gold fleur

    def __init__(self, message):
        self.font      = pygame.font.Font(self.FONT_PATH, self.FONT_SIZE)
        self.hint_font = pygame.font.Font(self.FONT_PATH, self.HINT_FONT_SIZE)

        self.dialogues      = message
        self.sound          = pygame.mixer.Sound("music/typingOneChar.mp3")
        self.sound.set_volume(0.5)

        self.dialogue_index = 0
        self.current_length = 0
        self.letter_timer   = 0
        self.active         = False
        self._blink_on      = True
        self._blink_timer   = 0

        self._bg = None   # cached background surface

    # ------------------------------------------------------------------ #
    def _build_bg(self, screen):
        sw, sh = screen.get_width(), screen.get_height()
        surf   = pygame.Surface((sw, sh))
        surf.fill(self.C_PARCHMENT)

        # dark pixel noise (very subtle on near-black bg)
        rng = random.Random(42)
        for _ in range(sw * sh // 60):
            nx = rng.randint(0, sw - 1)
            ny = rng.randint(0, sh - 1)
            v  = rng.randint(-8, 12)
            c  = tuple(max(0, min(255, self.C_PARCHMENT[i] + v)) for i in range(3))
            surf.set_at((nx, ny), c)

        # very dark grid lines — barely visible on black
        _draw_grid(surf, (32, 22, 10), step=44)

        # ── border system ─────────────────────────────────────────────
        bo = 10   # outer dark brown
        bg = 5    # gold
        br = 3    # red

        # outer dark brown
        pygame.draw.rect(surf, self.C_DARK_BROWN, (0,       0,       sw,    bo))
        pygame.draw.rect(surf, self.C_DARK_BROWN, (0,       sh-bo,   sw,    bo))
        pygame.draw.rect(surf, self.C_DARK_BROWN, (0,       0,       bo,    sh))
        pygame.draw.rect(surf, self.C_DARK_BROWN, (sw-bo,   0,       bo,    sh))

        # gold band
        o = bo
        pygame.draw.rect(surf, self.C_GOLD, (o,      o,       sw-o*2, bg))
        pygame.draw.rect(surf, self.C_GOLD, (o,      sh-o-bg, sw-o*2, bg))
        pygame.draw.rect(surf, self.C_GOLD, (o,      o,       bg,     sh-o*2))
        pygame.draw.rect(surf, self.C_GOLD, (sw-o-bg,o,       bg,     sh-o*2))

        # red accent line
        o = bo + bg
        pygame.draw.rect(surf, self.C_RED, (o,      o,       sw-o*2, br))
        pygame.draw.rect(surf, self.C_RED, (o,      sh-o-br, sw-o*2, br))
        pygame.draw.rect(surf, self.C_RED, (o,      o,       br,     sh-o*2))
        pygame.draw.rect(surf, self.C_RED, (sw-o-br,o,       br,     sh-o*2))

        # ── diamond vine pattern along gold band ──────────────────────
        dw = len(_DIAMOND[0]) * 2   # 14px per diamond
        dh = len(_DIAMOND)    * 2   # 14px

        # top gold band
        gy_top = bo + (bg - dh) // 2
        for x in range(bo + bg + 8, sw - bo - bg - 8 - dw, dw + 10):
            _draw_pixel_art(surf, _DIAMOND, x, gy_top, self.C_DARK_BROWN, scale=2)

        # bottom gold band
        gy_bot = sh - bo - bg + (bg - dh) // 2
        for x in range(bo + bg + 8, sw - bo - bg - 8 - dw, dw + 10):
            _draw_pixel_art(surf, _DIAMOND, x, gy_bot, self.C_DARK_BROWN, scale=2)

        # left gold band
        gx_left = bo + (bg - dw) // 2
        for y in range(bo + bg + 8, sh - bo - bg - 8 - dh, dh + 10):
            _draw_pixel_art(surf, _DIAMOND, gx_left, y, self.C_DARK_BROWN, scale=2)

        # right gold band
        gx_right = sw - bo - bg + (bg - dw) // 2
        for y in range(bo + bg + 8, sh - bo - bg - 8 - dh, dh + 10):
            _draw_pixel_art(surf, _DIAMOND, gx_right, y, self.C_DARK_BROWN, scale=2)

        # ── fleur-de-lis in each corner ───────────────────────────────
        fw = len(_FLEUR[0]) * 3   # 33px
        fh = len(_FLEUR)     * 3   # 45px
        margin = 4
        corners = [
            (margin,          margin),
            (sw - fw - margin, margin),
            (margin,           sh - fh - margin),
            (sw - fw - margin, sh - fh - margin),
        ]
        for cx, cy in corners:
            _draw_pixel_art(surf, _FLEUR, cx, cy, self.C_FLEUR, scale=3)

        # ── heavy vignette — edges fade to pure black ─────────────────
        vign   = pygame.Surface((sw, sh), pygame.SRCALPHA)
        layers = 160
        for i in range(layers):
            # quadratic falloff: outermost layer is nearly opaque (alpha~220)
            alpha = int(220 * (1 - i / layers) ** 2)
            pygame.draw.rect(vign, (0, 0, 0, alpha), (i, i, sw - i*2, sh - i*2), 1)
        surf.blit(vign, (0, 0))

        return surf

    # ------------------------------------------------------------------ #
    def start(self):
        self.active         = True
        self.dialogue_index = 0
        self.current_length = 0
        self.letter_timer   = 0
        self._bg            = None   # rebuild for new screen state

    def handle_event(self, event):
        if not self.active:
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            current = self.dialogues[self.dialogue_index]
            if self.current_length < len(current):
                self.current_length = len(current)   # skip typing
            elif self.dialogue_index < len(self.dialogues) - 1:
                self.dialogue_index += 1
                self.current_length  = 0
                self.letter_timer    = 0
            else:
                self.active = False

    def update(self):
        if not self.active:
            return
        self.letter_timer += 1
        current = self.dialogues[self.dialogue_index]
        if self.letter_timer % self.TYPE_SPEED == 0 and self.current_length < len(current):
            self.current_length += 1
            self.sound.play()

    # ------------------------------------------------------------------ #
    def _draw_hint(self, screen, done):
        now = pygame.time.get_ticks()
        if now - self._blink_timer >= self.BLINK_INTERVAL:
            self._blink_on    = not self._blink_on
            self._blink_timer = now
        if done and not self._blink_on:
            return

        label = self.hint_font.render("[ SPACE ]  continue", False, self.C_INK)
        lx    = screen.get_width()  // 2 - label.get_width()  // 2
        ly    = screen.get_height() - label.get_height() - 28
        screen.blit(label, (lx, ly))

    # ------------------------------------------------------------------ #
    def draw(self, screen):
        if not self.active:
            return

        sw, sh = screen.get_width(), screen.get_height()

        # build parchment background once
        if self._bg is None:
            self._bg = self._build_bg(screen)
        screen.blit(self._bg, (0, 0))

        # ── text (no box) ─────────────────────────────────────────────
        current = self.dialogues[self.dialogue_index]
        text    = current[:self.current_length]
        done    = self.current_length >= len(current)

        text_surf = self.font.render(text, False, self.C_INK)
        tw, th    = text_surf.get_size()
        tx        = sw // 2 - tw // 2
        ty        = sh // 2 - th // 2

        # blinking cursor while still typing
        if not done and (pygame.time.get_ticks() // 350) % 2 == 0:
            pygame.draw.rect(screen, self.C_INK, (tx + tw + 3, ty, 3, th))

        screen.blit(text_surf, (tx, ty))

        # ── hint ──────────────────────────────────────────────────────
        self._draw_hint(screen, done)
