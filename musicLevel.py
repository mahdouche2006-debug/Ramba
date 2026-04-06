import pygame
import pytmx
import pyscroll

from player import Player

class MusicLevel:
    def __init__(self, screen, game_instance):
        self.screen = screen
        self.game = game_instance

        tmx_data = pytmx.util_pygame.load_pygame("tilsets/rayenTileset/best-version-so-far.tmx")
        map_data = pyscroll.data.TiledMapData(tmx_data) 
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 2

        
        # generer un joueur
        player_position = tmx_data.get_object_by_name("player")
        self.player = Player(player_position.x, player_position.y)
        self.player.animations = {
            "left": [
                self.player.load_image("player/Player64/playerleft2.png"),
                self.player.load_image("player/Player64/player_stop_left.png"),
                self.player.load_image("player/Player64/playerleft1.png"),
                self.player.load_image("player/Player64/player_stop_left.png")
            ],
            "right": [
                self.player.load_image("player/Player64/playerright2.png"),
                self.player.load_image("player/Player64/player_stop_right.png"),
                self.player.load_image("player/Player64/playerright1.png"),
                self.player.load_image("player/Player64/player_stop_right.png")
            ],
            "up": [
                self.player.load_image("player/Player64/playerup1.png"),
                self.player.load_image("player/Player64/player_stop_up.png"),
                self.player.load_image("player/Player64/playerup2.png"),
                self.player.load_image("player/Player64/player_stop_up.png")
            ],
            "down": [
                self.player.load_image("player/Player64/playerdown1.png"),
                self.player.load_image("player/Player64/player_stop_down.png"),
                self.player.load_image("player/Player64/playerdown2.png"),
                self.player.load_image("player/Player64/player_stop_down.png")
            ]
        }

        # dessiner le groupe de calque
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=0)
        self.group.add(self.player) 

        self.walls = []
        for obj in tmx_data.objects:

            if obj.type == "obj":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

    def handle_input(self):
        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0
        
        if not self.player.canMove:
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
    
    def check_collision_with_list(self, obj):
        # verification collision
        return self.player.feet.collidelist(obj) > -1

    def update(self, events): 
        self.player.save_location()

        self.handle_input()

        self.group.update()
        self.group.center(self.player.rect)
        self.group.draw(self.screen)

        if self.check_collision_with_list(self.walls):
            self.player.move_back()

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()

        