import pygame
import pytmx
import pyscroll

from player import Player

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
        
        self.map = "world"

        self.walls = []

        for obj in tmx_data.objects:
            if obj.type == "obj":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))


        # dessiner le groupe de calque
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=4)
        self.group.add(self.player)

    def handle_input(self):
        pressed = pygame.key.get_pressed()

        dx = 0
        dy = 0

        if pressed[pygame.K_UP]:
            dy -= 1
            self.player.moving_up()
            self.player.image.set_colorkey([255, 255, 255])
            self.player.up = True
            self.player.down = False

        elif pressed[pygame.K_DOWN]:
            dy += 1
            self.player.moving_down()
            self.player.image.set_colorkey([255, 255, 255])
            self.player.up = False
            self.player.down = True

        else:
            self.player.up = False
            self.player.down = False
            self.player.walkCount1 = 0
            if self.player.image == self.player.walkUp[0] or self.player.image == self.player.walkUp[2]:
                self.player.image = self.player.walkUp[1]

        if pressed[pygame.K_LEFT]:
            dx -= 1
            self.player.moving_right_left()
            self.player.image.set_colorkey([255, 255, 255])
            self.player.left = True
            self.player.right = False

        elif pressed[pygame.K_RIGHT]:
            dx += 1
            self.player.moving_right_left()
            self.player.image.set_colorkey([255, 255, 255])
            self.player.left = False
            self.player.right = True

        else:
            self.player.right = False
            self.player.left = False
            self.player.walkCount = 0
            if self.player.image == self.player.walkLeft[0] or self.player.image == self.player.walkLeft[2]:
                self.player.image = self.player.walkLeft[1]
            elif self.player.image == self.player.walkRight[0] or self.player.image == self.player.walkRight[2]:
                self.player.image = self.player.walkRight[1]

        direction = pygame.math.Vector2(dx, dy)

        if direction.length() > 0:
            direction = direction.normalize()

        self.player.position[0] += direction.x * self.player.speed
        self.player.position[1] += direction.y * self.player.speed

    def check_collision(self):

        # verification collision
        for sprite in self.group.sprites():
            if self.player.feet.collidelist(self.walls) > -1:
                self.player.move_back()

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
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=4)
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

        running = True
        while running:

            self.player.save_location()
            self.handle_input()
            self.group.update()
            self.group.center(self.player.rect)
            self.group.draw(self.screen)
            self.check_collision()
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:    
                        running = False
                
            clock.tick(30)

        pygame.quit()
