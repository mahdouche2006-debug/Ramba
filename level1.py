import pygame
import pytmx
import pyscroll
import game
import math

from player import Player
from item import Item
from dialogue import Dialogue
from inventory import Inventory
from board import Board


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

        # Load the image
        original_e = pygame.image.load("images/e.png").convert_alpha()

        # Scale it to 32x32 pixels
        self.e_image = pygame.transform.scale(original_e, (16, 16))

        # Create the E prompt as a Sprite
        self.e_sprite = pygame.sprite.Sprite()
        self.e_sprite.image = self.e_image
        self.e_sprite.rect = self.e_image.get_rect()

        # Start it off-screen so it's hidden
        self.e_sprite.rect.topleft = (-100, -100)

        # Add it to the group so it moves with the camera
        self.group.add(self.e_sprite)
        
        # lists
        self.walls = []
        self.items = []
        self.items_with_item = ["wood_chest_with_item", "gold_chest"]
        self.items_with_no_item = ["wood_chest_with_no_item", "little_gold_chest"]

        self.sculptures = []

        for obj in tmx_data.objects:

            if obj.type == "obj":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

            elif obj.type == "item":
                item = Item(obj.name, obj.x, obj.y, False)

                self.items.append(item)
                self.group.add(item)
            
            elif obj.type == "sculpture":
                item = Item(obj.name, obj.x, obj.y, False)
                self.sculptures.append(item)
                self.group.add(item)

            if obj.name == "board":
                self.board = Board(obj.x, obj.y, obj.width, obj.height)

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

        if self.inventory.open or self.board.open:
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

        self.board.draw(self.screen)

        # Draw a red box around the board hitbox
        pygame.draw.rect(self.screen, (255, 0, 0), self.board.rect.move(-self.group._map_layer.view_rect.x, -self.group._map_layer.view_rect.y), 2)

        # Draw a blue box around the player's feet hitbox
        pygame.draw.rect(self.screen, (0, 0, 255), self.player.feet.move(-self.group._map_layer.view_rect.x, -self.group._map_layer.view_rect.y), 2)

        if self.check_collision_with_list(self.walls):
            self.player.move_back()

        # 1. Get a shifting offset based on time
        # pygame.time.get_ticks() gives us the time in milliseconds
        # We divide by 200 to control the speed of the bobbing
        bobbing_offset = math.sin(pygame.time.get_ticks() / 200) * 8

        near_sculpture = self.get_colliding_item(self.sculptures)
        near_board = self.player.feet.colliderect(self.board.rect)
        if near_board or near_sculpture:
            # Position the E sprite relative to the player's WORLD coordinates
            # Pyscroll will automatically scale this by 3x and offset it for the camera
            self.e_sprite.rect.midbottom = (
                self.player.rect.centerx + bobbing_offset, 
                self.player.rect.top - 10
            )
        else:
            # Hide it when not near anything
            self.e_sprite.rect.topleft = (-500, -500)

        for event in pygame.event.get():

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()

                if event.key == pygame.K_e and not self.inventory.open:
                    sculpture = self.get_colliding_item(self.sculptures)
                    if sculpture:
                        print("Interacting with sculpture:", sculpture.name if sculpture else "None")

                    if self.player.feet.colliderect(self.board.rect):
                        self.board.open_sound.play()
                        self.board.open = not self.board.open

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
