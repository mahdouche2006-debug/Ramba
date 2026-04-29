import pygame

class Inventory:

    # Slot centres measured from inventory1.png (1536×1024)
    # X positions of the 4 column centres (relative to image top-left)
    _SLOT_CX = [249, 603, 941, 1278]
    # Y positions of the 2 row centres (relative to image top-left)
    _SLOT_CY = [366, 727]
    # Item thumbnail size — fits inside the ~200×215 slot interior
    _ITEM_SIZE = 160

    def __init__(self):
        self.size = 8
        self.slots = [None] * self.size
        self.open = False
        self.image = pygame.image.load("images/inventory1.png")
        self.rect = self.image.get_rect()
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
        half = self._ITEM_SIZE // 2

        for i, slot in enumerate(self.slots):
            if slot is None:
                continue

            row = i // 4
            col = i % 4

            # Slot centre on screen
            cx = panel_x + self._SLOT_CX[col]
            cy = panel_y + self._SLOT_CY[row]

            # Use display_image if available (sculptures hide their sprite image on the map)
            src = getattr(slot, 'display_image', slot.image)
            thumb = pygame.transform.smoothscale(src, (self._ITEM_SIZE, self._ITEM_SIZE))
            screen.blit(thumb, (cx - half, cy - half))

