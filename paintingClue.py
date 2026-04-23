import pygame
import sys


# Pixel art corner ornament (15x15 grid, 1 = filled pixel)
_CORNER = [
    [1,0,0,0,1,0,0,1,0,0,1,0,0,0,1],
    [0,1,0,0,0,0,1,0,1,0,0,0,0,1,0],
    [0,0,1,0,0,0,0,1,0,0,0,0,1,0,0],
    [0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
    [1,0,0,0,1,0,0,0,0,0,1,0,0,0,1],
    [0,0,0,0,0,1,0,0,0,1,0,0,0,0,0],
    [0,1,0,0,0,0,1,0,1,0,0,0,0,1,0],
    [1,0,1,0,0,0,0,1,0,0,0,0,1,0,1],
    [0,1,0,0,0,0,1,0,1,0,0,0,0,1,0],
    [0,0,0,0,0,1,0,0,0,1,0,0,0,0,0],
    [1,0,0,0,1,0,0,0,0,0,1,0,0,0,1],
    [0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
    [0,0,1,0,0,0,0,1,0,0,0,0,1,0,0],
    [0,1,0,0,0,0,1,0,1,0,0,0,0,1,0],
    [1,0,0,0,1,0,0,1,0,0,1,0,0,0,1],
]

# Pixel art scroll icon drawn in the center top (11x7)
_SCROLL = [
    [0,1,1,1,1,1,1,1,1,1,0],
    [1,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,0,1,0,1,0,1,0,1],
    [1,0,0,1,0,1,0,1,0,0,1],
    [1,0,1,0,1,0,1,0,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,1],
    [0,1,1,1,1,1,1,1,1,1,0],
]


class PaintingClue:
    # colours
    C_BG         = (195, 182, 162, 210)  # warm greige, slightly transparent
    C_DARK       = (75,  52,  30 )       # dark brown border
    C_GOLD       = (180, 140, 80 )       # golden middle border
    C_CREAM      = (220, 205, 178)       # light cream inner border
    C_ORNAMENT   = (110, 75,  40 )       # pixel art details
    C_TEXT       = (55,  40,  25 )       # text

    BORDER_OUTER = 7
    BORDER_GOLD  = 5
    BORDER_CREAM = 4
    CORNER_SIZE  = 15   # matches _CORNER grid
    PIXEL        = 2    # scale factor for corner ornament pixels

    def __init__(self, screen, game_instance=None, message=[]):
        self.screen   = screen
        self.game     = game_instance

        self.screen_w, self.screen_h = self.screen.get_size()
        self.box_height = int(self.screen_h * 0.12)

        font_size = int(self.screen_w * 0.02)
        try:
            self.font = pygame.font.Font("fonts/Pixel Emulator.otf", font_size)
        except:
            self.font = pygame.font.SysFont("Arial", font_size)

        self.dialogues            = message
        self.current_dialogue_idx = 0
        self.text_index           = 0
        self.text_speed           = 3
        self.frame_count          = 0
        self.is_finished          = False

        self.cached_lines = self.wrap_text(self.dialogues[self.current_dialogue_idx])

        # pre-bake the background + border surface
        self._build_box_surface()

    # ------------------------------------------------------------------ #
    def _build_box_surface(self):
        sw = self.screen_w
        bh = self.box_height
        cs = self.CORNER_SIZE * self.PIXEL   # rendered corner size in px

        surf = pygame.Surface((sw, bh), pygame.SRCALPHA)

        # background fill
        surf.fill(self.C_BG)

        bo = self.BORDER_OUTER
        bg = self.BORDER_GOLD
        bc = self.BORDER_CREAM

        # --- outer dark border ---
        pygame.draw.rect(surf, self.C_DARK, (0,      0,      sw,    bo))   # top
        pygame.draw.rect(surf, self.C_DARK, (0,      bh-bo,  sw,    bo))   # bottom
        pygame.draw.rect(surf, self.C_DARK, (0,      0,      bo,    bh))   # left
        pygame.draw.rect(surf, self.C_DARK, (sw-bo,  0,      bo,    bh))   # right

        # --- golden middle border ---
        o = bo
        pygame.draw.rect(surf, self.C_GOLD, (o,      o,      sw-o*2, bg))
        pygame.draw.rect(surf, self.C_GOLD, (o,      bh-o-bg,sw-o*2, bg))
        pygame.draw.rect(surf, self.C_GOLD, (o,      o,      bg,     bh-o*2))
        pygame.draw.rect(surf, self.C_GOLD, (sw-o-bg,o,      bg,     bh-o*2))

        # --- cream inner border ---
        o = bo + bg
        pygame.draw.rect(surf, self.C_CREAM, (o,      o,       sw-o*2, bc))
        pygame.draw.rect(surf, self.C_CREAM, (o,      bh-o-bc, sw-o*2, bc))
        pygame.draw.rect(surf, self.C_CREAM, (o,      o,       bc,     bh-o*2))
        pygame.draw.rect(surf, self.C_CREAM, (sw-o-bc,o,       bc,     bh-o*2))

        # --- repeating dot pattern along top & bottom gold border ---
        dot_y_top    = bo + 1
        dot_y_bottom = bh - bo - bg
        for x in range(cs + 4, sw - cs - 4, 10):
            pygame.draw.rect(surf, self.C_DARK, (x, dot_y_top,    2, bg))
            pygame.draw.rect(surf, self.C_DARK, (x, dot_y_bottom, 2, bg))

        # --- pixel art corner ornaments (all four corners) ---
        p = self.PIXEL
        corners = [
            (0, 0),                        # top-left
            (sw - cs*p, 0),                # top-right
            (0, bh - cs*p),                # bottom-left
            (sw - cs*p, bh - cs*p),        # bottom-right
        ]
        for ox, oy in corners:
            for row_i, row in enumerate(_CORNER):
                for col_i, val in enumerate(row):
                    if val:
                        pygame.draw.rect(surf, self.C_ORNAMENT,
                                         (ox + col_i*p, oy + row_i*p, p, p))

        # --- small scroll icon centered at top border ---
        icon_w = len(_SCROLL[0]) * p
        icon_x = (sw - icon_w) // 2
        icon_y = (bo - p) // 2           # centered in outer border
        for row_i, row in enumerate(_SCROLL):
            for col_i, val in enumerate(row):
                if val:
                    pygame.draw.rect(surf, self.C_CREAM,
                                     (icon_x + col_i*p, icon_y + row_i*p, p, p))

        self.box_surface = surf

    # ------------------------------------------------------------------ #
    def wrap_text(self, text):
        max_width = self.screen_w - (self.screen_w * 0.15)
        words     = text.split(" ")
        lines, current_line = [], ""
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
        self.text_index  = 0
        self.frame_count = 0

    # ------------------------------------------------------------------ #
    def draw(self):
        box_y = self.screen_h - self.box_height
        self.screen.blit(self.box_surface, (0, box_y))

        current_full_text = self.dialogues[self.current_dialogue_idx]
        displayed_text    = current_full_text[:self.text_index]
        visible_lines     = self.wrap_text(displayed_text)

        line_spacing = int(self.font.get_height() * 1.2)
        x = self.screen_w * 0.07
        y = box_y + (self.box_height * 0.22)

        for line in visible_lines:
            text_surface = self.font.render(line, True, self.C_TEXT)
            self.screen.blit(text_surface, (x, y))
            y += line_spacing

    def update(self):
        self.frame_count += 1
        current_full_text = self.dialogues[self.current_dialogue_idx]
        if self.frame_count % self.text_speed == 0:
            if self.text_index < len(current_full_text):
                self.text_index += 1
        self.draw()
