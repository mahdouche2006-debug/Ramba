import pygame
import pytmx
import pyscroll

from player import Player
from item import Item

class Game:
    def __init__(self):
        # cree la fenetre du jeu
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("RAMBA")

        # charger la carte (tmx)
        tmx_data = pytmx.util_pygame.load_pygame('main map demo.tmx')
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 3

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

        self.map = "world"

        self.walls = []
        self.stairs = []
        self.items = []

        for obj in tmx_data.objects:
            if obj.type == "obj":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
            
            if obj.name == "stairs_above" or obj.name == "stairs_below":
                self.stairs.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))   

            if obj.type == "item":
                self.items.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))


        # dessiner le groupe de calque
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=5)
        self.group.add(self.apple)
        self.group.add(self.apple2)
        self.group.add(self.player)

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
            
            if self.check_collision_with_item(self.apple2):
                self.remove_item(self.apple2)
    
    def remove_item(self, item):
        self.group.remove(item)
        self.items.remove(item.rect)
    
    def check_collision_with_item(self, item):
        return self.player.feet.colliderect(item.rect)

    def check_collision_with_list(self, obj):
        # verification collision
        return self.player.feet.collidelist(obj) > -1
            

    """def switch_house(self, level):
        tmx_data = pytmx.util_pygame.load_pygame(f'{level}.tmx')
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 3

        # definir une liste qui va stocker les rectangles de collision
        self.walls = []
        for obj in tmx_data.objects:
            if obj.type == "collision":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

        # dessiner le groupe de calque
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=5)
        self.group.add(self.player)

        # definir le rectengle de colision pour sortir dans la maison
        exit_level = tmx_data.get_object_by_name(f'exit_{level}')
        self.enter_level_rect = pygame.Rect(exit_level.x, exit_level.y, exit_level.width, exit_level.height)

        spawn_level_point = tmx_data.get_object_by_name(f'spawn_{level}')
        self.player.position[0] = spawn_level_point.x
        self.player.position[1] = spawn_level_point.y - 20

    def update(self):
        self.group.update()

        # verifier l'entrer dans la maison
        if self.map == 'world' and self.player.feet.colliderect(self.enter_level_rect):
            self.switch_house("cave")
            self.map = 'cave'

        # verifier l'entrer dans la maison
        if self.map == 'cave' and self.player.feet.colliderect(self.enter_level_rect):
            self.switch_house("main map demo")
            self.map = 'world'

        # verification collision
        for sprite in self.group.sprites():
            if self.player.feet.collidelist(self.walls) > -1:
                self.player.move_back()"""

    def run(self):
        clock = pygame.time.Clock()
        fps = 60

        running = True
        while running:
            

            self.player.save_location()
            self.handle_input()
            self.group.update()
            self.group.center(self.player.rect)
            self.group.draw(self.screen)
            if self.check_collision_with_list(self.walls):
                self.player.move_back()
            
            if self.check_collision_with_list(self.items):
                self.screen.blit(self.e_image, (20,20))
                
            
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:    
                        running = False
            
            

            clock.tick(fps)

        pygame.quit()
