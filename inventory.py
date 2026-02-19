import pygame

class Inventory:

    def __init__(self):
        self.size = 8
        self.slots = [None] * self.size
        self.slot_size = 64
        self.padding = 15
        self.open = False

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

        screen_width, screen_height = screen.get_size()

        # ---- INVENTORY PANEL SIZE (85% of screen) ----
        panel_width = int(screen_width * 0.85)
        panel_height = int(screen_height * 0.85)

        panel_x = (screen_width - panel_width) // 2
        panel_y = (screen_height - panel_height) // 2

        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

        # ---- DRAW BACKGROUND PANEL ----
        pygame.draw.rect(
            screen,
            (25, 25, 25),
            panel_rect,
            border_radius=20
        )

        pygame.draw.rect(
            screen,
            (180, 180, 180),
            panel_rect,
            4,
            border_radius=20
        )

        # ---- GRID SETTINGS ----
        cols = 4
        rows = 2

        padding_x = panel_width * 0.08
        padding_y = panel_height * 0.1

        available_width = panel_width - 2 * padding_x
        available_height = panel_height - 2 * padding_y

        slot_size = min(
            available_width / cols,
            available_height / rows
        ) * 0.8

        spacing_x = available_width / cols
        spacing_y = available_height / rows

        # ---- DRAW SLOTS ----
        for i in range(self.size):

            row = i // cols
            col = i % cols

            x = panel_x + padding_x + col * spacing_x + (spacing_x - slot_size) / 2
            y = panel_y + padding_y + row * spacing_y + (spacing_y - slot_size) / 2

            rect = pygame.Rect(x, y, slot_size, slot_size)

            # Slot background
            pygame.draw.rect(
                screen,
                (50, 50, 50),
                rect,
                border_radius=int(slot_size * 0.2)
            )

            # Slot border
            pygame.draw.rect(
                screen,
                (220, 220, 220),
                rect,
                3,
                border_radius=int(slot_size * 0.2)
            )

            # Draw item if exists
            if self.slots[i]:
                item_size = int(slot_size * 0.7)
                item_image = pygame.transform.smoothscale(
                    self.slots[i].image,
                    (item_size, item_size)
                )

                screen.blit(
                    item_image,
                    (
                        rect.centerx - item_size // 2,
                        rect.centery - item_size // 2
                    )
                )

