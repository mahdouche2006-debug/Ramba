import pygame

class Inventory:

    def __init__(self):
        self.size = 8
        self.slots = [None] * self.size
        self.slot_size = 64
        self.padding = 15
        self.open = False
        self.image = pygame.image.load("images/inventory.png")
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

        # 1. Center the 850x650 background on screen
        self.rect.center = (screen.get_width() // 2, screen.get_height() // 2)
        screen.blit(self.image, self.rect)

        # 2. Grid Positioning (Relative to the top-left of the inventory image)
        panel_x, panel_y = self.rect.topleft
        
        cols = 4
        # Horizontal distance between octagon centers
        spacing_x = 190
        # Vertical distance between the two rows
        spacing_y = 186
        
        # Starting coordinates for the first item (top-left octagon)
        # Pushed down to start below the "INVENTORY" text
        start_offset_x = 110 
        start_offset_y = 265 

        # 3. Draw the Items
        for i in range(len(self.slots)):
            if self.slots[i]:
                row = i // cols
                col = i % cols

                # Calculate exact screen position
                item_x = panel_x + start_offset_x + (col * spacing_x)
                item_y = panel_y + start_offset_y + (row * spacing_y)

                # Resize to your requested 60x60
                item_image = pygame.transform.smoothscale(self.slots[i].image, (60, 60))
                
                # Blit the item
                screen.blit(item_image, (item_x, item_y))

