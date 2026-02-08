import pygame
import pytmx
import pyscroll

from player import Player
from item import Item
from level1 import Level1

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

        # the e to pick things up
        self.e_image = pygame.image.load("images/e.png")

        # tunnel creation
        self.tunnel1 = tmx_data.get_object_by_name("tunnel1")
        self.tunnel2 = tmx_data.get_object_by_name("tunnel2")

        # by default world
        self.map = "world"

        self.walls = []
        self.side_stairs = []
        self.front_stairs = []
        self.doors = []
        self.tunnels = []

        for obj in tmx_data.objects:
            if obj.type == "obj":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
            
            if obj.type == "side_stairs":
                self.side_stairs.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height)) 

            if obj.type == "front_stairs":
                self.front_stairs.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))  
            
            if obj.type == "door":
                self.doors.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

            if obj.type == "tunnel":
                self.tunnels.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

        # dessiner le groupe de calque
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=5)
        self.group.add(self.player)

    def handle_input(self):
        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0
        stairs_deviation = 0.33

        # reset walking state
        self.player.walking = False

        # vertical movement
        if keys[pygame.K_UP]:
            dy -= 1
            self.player.direction = "up"
            self.player.walking = True
            
            if self.check_collision_with_list(self.front_stairs):
                dy += stairs_deviation

        elif keys[pygame.K_DOWN]:
            dy += 1
            self.player.direction = "down"
            self.player.walking = True

            if self.check_collision_with_list(self.front_stairs):
                dy -= stairs_deviation

        # horizontal movement
        if keys[pygame.K_LEFT]:
            dx -= 1
            self.player.direction = "left"
            self.player.walking = True

            if self.check_collision_with_list(self.side_stairs):
                dy += stairs_deviation
                dx += stairs_deviation
                
        elif keys[pygame.K_RIGHT]:
            dx += 1
            self.player.direction = "right"
            self.player.walking = True

            if self.check_collision_with_list(self.side_stairs):
                dy -= stairs_deviation
                dx -= stairs_deviation

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
    
    def check_collision_with_door(self, item):
        return self.player.feet.colliderect(item)

    def check_collision_with_tunnel(self, item):
        return self.player.feet.colliderect(item)

    def check_collision_with_list(self, obj):
        # verification collision
        return self.player.feet.collidelist(obj) > -1
    
    def fade_in_to_black(self):
        fade = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        fade.fill((0, 0, 0))
        for alpha in range(0, 200):
            fade.set_alpha(alpha)
            self.screen.blit(fade, (0, 0))
            pygame.display.update()
            pygame.time.delay(5)

    def fade_out_from_black(self):
        fade = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        fade.fill((0, 0, 0))
        for alpha in range(200, -1, -1):
            fade.set_alpha(alpha)
            self.screen.blit(fade, (0, 0))
            pygame.display.update()
            pygame.time.delay(5)

    def enter_the_tunnel(self):
        paused = True
        font = pygame.font.SysFont(None, 48)
        text = font.render("Entering the tunnel...", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))

        self.fade_in_to_black()

        while paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    paused = False
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        paused = False
                        pygame.quit()
                        exit()

            self.screen.fill((0, 0, 0))
            self.screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.delay(2000)  # Pause for 2 seconds
            paused = False
        
        self.fade_out_from_black()

    def enter_level1(self):
        paused = True 
        font = pygame.font.SysFont(None, 48)
        text = font.render("Entering the level1...", True, (255, 0, 0))
        text_rect = text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
        
        self.fade_in_to_black()
        
        while paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    paused = False
                elif event.type == pygame.KEYDOWN:
                    paused = False

            self.screen.fill((0, 0, 0))
            self.screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.delay(2000)  # Affiche le message pendant 2 secondes
            paused = False

    def run(self):
        clock = pygame.time.Clock()
        fps = 60

        running = True
        level1 = Level1()
        while running:
            
            if self.map == "world":

                self.player.save_location()
                self.handle_input()
                self.group.update()
                self.group.center(self.player.rect)
                self.group.draw(self.screen)
                
                if self.check_collision_with_list(self.walls):
                    self.player.move_back()

                if self.check_collision_with_door(self.doors[0]):
                    self.map = "level1"
                    self.enter_level1()  # Affiche le message d'entrée avant de commencer le jeu

                if self.check_collision_with_tunnel(self.tunnels[0]):
                    self.enter_the_tunnel()
                    self.player.position[0] = self.tunnel2.x
                    self.player.position[1] = self.tunnel2.y - 54
                
                if self.check_collision_with_tunnel(self.tunnels[1]):
                    self.enter_the_tunnel()
                    self.player.position[0] = self.tunnel1.x
                    self.player.position[1] = self.tunnel1.y + 32
                
            elif self.map == "level1":
                
                level1.run()
            
            pygame.display.flip()

            # event handeling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:    
                        running = False
            

            clock.tick(fps)

        pygame.quit()
