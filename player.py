import pygame
import animation


class PlayerShadow(pygame.sprite.Sprite):
    """Flat ellipse shadow drawn beneath the player while they walk.

    Add this sprite to the pyscroll group at a layer *below* the player so
    pyscroll's camera / zoom handle positioning automatically.
    """

    _ALPHA_WALK = 90   # opacity while moving
    _FRAMES     = 6    # fade-in / fade-out speed (frames per alpha step)

    def __init__(self, player):
        super().__init__()
        self.player = player

        # Shadow dimensions in world-space pixels (pyscroll zooms them up)
        pw          = player.rect.width
        ph          = player.rect.height
        self.sw     = max(int(pw * 0.70), 8)
        self.sh     = max(int(ph * 0.18), 5)

        self._alpha  = 0          # current opacity (animated)
        self._target = 0          # target opacity
        self._tick   = 0

        self.image = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        self.rect  = self.image.get_rect()

    # ------------------------------------------------------------------ #
    def _render(self):
        """Repaint the shadow surface at the current alpha."""
        self.image.fill((0, 0, 0, 0))
        if self._alpha > 0:
            # Soft-edged look: outer ring at half opacity, filled centre full
            outer = (0, 0, 0, self._alpha // 2)
            inner = (0, 0, 0, self._alpha)
            pygame.draw.ellipse(self.image, outer,
                                (0, 0, self.sw, self.sh))
            mx = self.sw // 6
            my = self.sh // 4
            pygame.draw.ellipse(self.image, inner,
                                (mx, my, self.sw - mx * 2, self.sh - my * 2))

    def update(self):
        self._target = self._ALPHA_WALK if self.player.walking else 0

        # Smooth fade in/out every _FRAMES ticks
        self._tick += 1
        if self._tick >= self._FRAMES:
            self._tick = 0
            if self._alpha < self._target:
                self._alpha = min(self._alpha + 15, self._target)
            elif self._alpha > self._target:
                self._alpha = max(self._alpha - 15, self._target)

        self._render()

        # Anchor shadow to the player's feet centre
        self.rect.midbottom = self.player.rect.midbottom


class Player(animation.AnimateSprite):

    def __init__(self, x, y):
        super().__init__()
        self.rect = self.image.get_rect(topleft=(x,y))
        self.image.set_colorkey([255, 255, 255])
        self.position = [x, y]

        self.feet = pygame.Rect(0, 0, self.rect.width * 0.5, 12)
        self.old_position = self.position.copy()
        self.speed = 1.5
        self.canMove = True
        
    def save_location(self):
        self.old_position = self.position.copy()

    def update(self):
        self.rect.topleft = self.position
        self.feet.midbottom = self.rect.midbottom

    def move_back(self):
        self.position = self.old_position
        self.rect.topleft = self.position
        self.feet.midbottom = self.rect.midbottom
    
    def is_on_stairs(self, stairs):
        return self.feet.collidelist(stairs) > -1