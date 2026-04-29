import pygame

class Inventory:

    # Slot centres measured from inventory1.png at full 1536×1024 resolution
    _SLOT_CX_BASE = [249, 603, 941, 1278]
    _SLOT_CY_BASE = [366, 727]
    # Display scale — 0.6 makes the panel roughly 922×614, comfortable on 1920×1080
    _SCALE = 0.6

    def __init__(self):
        self.size = 8
        self.slots = [None] * self.size
        self.open = False

        # Load and scale down the inventory image
        _raw = pygame.image.load("images/inventory1.png")
        _w   = int(_raw.get_width()  * self._SCALE)
        _h   = int(_raw.get_height() * self._SCALE)
        self.image = pygame.transform.smoothscale(_raw, (_w, _h))
        self.rect  = self.image.get_rect()

        # Scale slot centres to match the displayed image size
        self._slot_cx  = [int(x * self._SCALE) for x in self._SLOT_CX_BASE]
        self._slot_cy  = [int(y * self._SCALE) for y in self._SLOT_CY_BASE]
        self._item_size = int(160 * self._SCALE)   # ~96 px — fits the scaled slot

        self.open_sound = pygame.mixer.Sound("music/Click.wav")
        self.open_sound.set_volume(0.5)

    def add_item(self, item):
        for i, slot in enumerate(self.slots):
            if slot is None:
                self.slots[i] = item
                return True
        return False

    def remove_item(self, item_name):
        for i, slot in enumerate(self.slots):
            if slot and slot.name == item_name:
                self.slots[i] = None
                return True
        return False

    def draw(self, screen):
        if not self.open:
            return

        # Centre the inventory panel on screen
        self.rect.center = (screen.get_width() // 2, screen.get_height() // 2)
        screen.blit(self.image, self.rect)

        panel_x, panel_y = self.rect.topleft
        half = self._item_size // 2

        for i, slot in enumerate(self.slots):
            if slot is None:
                continue

            row = i // 4
            col = i % 4

            # Slot centre on screen
            cx = panel_x + self._slot_cx[col]
            cy = panel_y + self._slot_cy[row]

            # Use display_image if available (sculptures hide their sprite image on the map)
            src = getattr(slot, 'display_image', slot.image)
            thumb = pygame.transform.smoothscale(src, (self._item_size, self._item_size))
            screen.blit(thumb, (cx - half, cy - half))

