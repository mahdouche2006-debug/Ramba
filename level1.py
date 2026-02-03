import pygame
import pytmx
import pyscroll

from player import Player
from item import Item

class Level1:
    def __init__(self):
        # cree la fenetre du jeu
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("RAMBA")

        # charger la carte (tmx)
        tmx_data = pytmx.util_pygame.load_pygame('one chamber.tmx')
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 5

        self.map = "level1"
    
        # generer un joueur
        player_position = tmx_data.get_object_by_name("player")
        self.player = Player(player_position.x, player_position.y)

        # generer une pomme
        apple_position = tmx_data.get_object_by_name("apple")
        self.apple = Item("apple", apple_position.x, apple_position.y)
        apple2_position = tmx_data.get_object_by_name("apple2")
        self.apple2 = Item("apple", apple2_position.x, apple2_position.y)

        # the e to pick things up
        self.e_image = pygame.image.load("images/e.png")

        # the lists of interactable objects
        self.walls = []
        self.items = []

        for obj in tmx_data.objects:
            if obj.type == "obj":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

            if obj.type == "item":
                self.items.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

        # dessiner le groupe de calque
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=5)
        self.group.add(self.apple)
        self.group.add(self.apple2)
        self.group.add(self.player)

        # counter for items collected
        self.items_collected = 0
        
    def handle_input(self):
        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        # reset walking state
        self.player.walking = False

        # vertical movement
        if keys[pygame.K_UP]:
            dy -= 1
            self.player.direction = "up"
            self.player.walking = True

        elif keys[pygame.K_DOWN]:
            dy += 1
            self.player.direction = "down"
            self.player.walking = True

        # horizontal movement
        if keys[pygame.K_LEFT]:
            dx -= 1
            self.player.direction = "left"
            self.player.walking = True

        elif keys[pygame.K_RIGHT]:
            dx += 1
            self.player.direction = "right"
            self.player.walking = True

        # normalize diagonal movement
        direction = pygame.math.Vector2(dx, dy)
        if direction.length() > 0:
            direction = direction.normalize()

        # save old position (for collisions)
        self.player.save_location()

        # apply movement
        self.player.position[0] += direction.x * self.player.speed
        self.player.position[1] += direction.y * self.player.speed

        # update animation
        self.player.animate()

        # pick up items with the e key
        if keys[pygame.K_e] and self.check_collision_with_list(self.items):
            if self.check_collision_with_item(self.apple):
                self.remove_item(self.apple)
                self.items_collected += 1
            
            if self.check_collision_with_item(self.apple2):
                self.remove_item(self.apple2)
                self.items_collected += 1
    
    def remove_item(self, item):
        self.group.remove(item)
        self.items.remove(item.rect)
    
    def check_collision_with_item(self, item):
        return self.player.feet.colliderect(item.rect)

    def check_collision_with_list(self, obj):
        # verification collision
        return self.player.feet.collidelist(obj) > -1
    
    def get_dynamic_font(self):
        font_size = int(self.screen.get_height() // 20)
        font_size = max(12, min(font_size, 72))  # Limite la taille de la police entre 12 et 72
        return pygame.font.SysFont("Arial", font_size)
    
    def draw_counter(self):
        font = self.get_dynamic_font()
        text = font.render(f"{self.items_collected}/10", True, (255, 255, 255))
        self.screen.blit(text, (self.screen.get_width()*92/100, 0))

    def run(self):
        
        self.player.save_location()
        self.handle_input()

        self.group.update()
        self.group.center(self.player.rect)
        self.group.draw(self.screen)
        self.draw_counter()

        if self.check_collision_with_list(self.items):
            self.screen.blit(self.e_image, (20,20))
        
        pygame.display.flip()
        
        if self.items_collected == 2:
            return "world"

        

