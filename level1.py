import pygame
import pytmx
import pyscroll
import game

from player import Player
from item import Item
from dialogue import Dialogue
from inventory import Inventory


class Level1:
    def __init__(self, timer):
        # cree la fenetre du jeu
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("RAMBA")

        # charger la carte (tmx)
        tmx_data = pytmx.util_pygame.load_pygame('one chamber.tmx')
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 3

        # generer un joueur
        player_position = tmx_data.get_object_by_name("player")
        self.player = Player(player_position.x, player_position.y)
        
        # dessiner le groupe de calque
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=3)
        self.group.add(self.player) 

        self.e_image = pygame.image.load("images/e.png").convert_alpha()
        
        # lists
        self.walls = []
        self.items = []
        self.items_with_item = ["wood_chest_with_item", "gold_chest"]
        self.items_with_no_item = ["wood_chest_with_no_item", "little_gold_chest"]

        for obj in tmx_data.objects:

            if obj.type == "obj":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

            elif obj.type == "item":
                item = Item(obj.name, obj.x, obj.y, False)

                self.items.append(item)
                self.group.add(item)

        for item in self.items:
            if item.name in self.items_with_item:
                item.has_item = True
        
        self.group.change_layer(self.player, 4)  # Assure que le joueur est au-dessus des items et des murs

        # counter for items collected
        self.items_collected = 0

        # timer creation
        self.timer = timer

        # font
        self.font = pygame.font.SysFont("fonts/Pixel Emulator.otf", 70)

        # inventory creation
        self.inventory = Inventory()

        # change the soud of the footsteps
        self.player.walk_sounds = [
            pygame.mixer.Sound("music/woodWalk1.wav"),
            pygame.mixer.Sound("music/woodWalk2.wav"),
            pygame.mixer.Sound("music/woodWalk3.wav")
        ]

        for sound in self.player.walk_sounds:
            sound.set_volume(0.3)
        
    def handle_input(self):
        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        if self.inventory.open:
            return

        # prevent movement while attacking
        if self.player.attacking:
            self.player.animate()
            return

        self.player.walking = False

        # movement
        if keys[pygame.K_UP]:
            dy -= 1
            self.player.direction = "up"
            self.player.walking = True

        elif keys[pygame.K_DOWN]:
            dy += 1
            self.player.direction = "down"
            self.player.walking = True

        if keys[pygame.K_LEFT]:
            dx -= 1
            self.player.direction = "left"
            self.player.walking = True

        elif keys[pygame.K_RIGHT]:
            dx += 1
            self.player.direction = "right"
            self.player.walking = True

        direction = pygame.math.Vector2(dx, dy)

        if direction.length() > 0:
            direction = direction.normalize()

        self.player.save_location()

        self.player.position[0] += direction.x * self.player.speed
        self.player.position[1] += direction.y * self.player.speed

        self.player.animate()
    
    def remove_item_from_lists(self, item):
        self.group.remove(item)
        self.items.remove(item)

    def get_colliding_item(self, list):
        for item in list:
            if self.player.feet.colliderect(item.rect):
                return item
        return None

    def check_collision_with_list(self, obj):
        # verification collision
        return self.player.feet.collidelist(obj) > -1
    
    def draw_counter(self):
        text = self.font.render(f"{self.items_collected}/10", True, (255, 255, 255))
        self.screen.blit(text, (self.screen.get_width()*92/100, 0))

    def ending_the_level(self, message):
        dialogue = Dialogue(message)
        dialogue.start()
        self.screen.fill((0, 0, 0)) 
        while dialogue.active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        pygame.quit()
                    if event.key == pygame.K_c:
                        self.screen.fill((0, 0, 0)) 

                dialogue.handle_event(event)
            dialogue.update()
            dialogue.draw(self.screen)
            pygame.display.flip()

    def remove_item(self, item):
        if item:
            if item.name == "apple":
                self.items_collected += 1
                self.remove_item_from_lists(item)
                self.inventory.add_item(item)

            elif item.name in self.items_with_item or item.name in self.items_with_no_item:
                
                # animate attack
                self.player.attacking = True
                self.player.frame_index = 0
                self.player.animate()

                if item.has_item:
                    self.generate_new_item(item, "apple")

                self.remove_item_from_lists(item)
    
    def generate_new_item(self, item, item_name):
        new_apple = Item(item_name, item.rect.x, item.rect.y)
        self.items.append(new_apple)
        self.group.add(new_apple)

    def run(self):
        self.player.save_location()
        self.handle_input()

        self.group.update()
        self.group.center(self.player.rect)
        self.group.draw(self.screen)
        self.draw_counter()

        self.timer.update()
        self.timer.draw(self.screen)

        self.inventory.draw(self.screen)
        if self.check_collision_with_list(self.walls):
            self.player.move_back()

        if self.get_colliding_item(self.items):
            self.screen.blit(self.e_image, (self.screen.get_width() - self.e_image.get_width(), self.screen.get_height() - self.e_image.get_height()))

        for event in pygame.event.get():

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()

                if event.key == pygame.K_e and not self.inventory.open:
                    item = self.get_colliding_item(self.items)
                    self.remove_item(item)

                if event.key == pygame.K_i:
                    self.inventory.open_sound.play()
                    self.inventory.open = not self.inventory.open
        
        # return to world when all items are collected
        if self.items_collected == 8:
            self.ending_the_level(["You found all the items!", "Press c to return to world map..."])
            game.Game().map = "world"
            game.Game().run()

        if self.timer.remaining_time <= 0:
            self.ending_the_level(["Time's up! Returning to world map..."])
            game.Game().map = "world"
            game.Game().run() # Return to world map (adjust as needed)
