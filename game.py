import pygame
import pytmx
import pyscroll

from musicLevel import MusicLevel
from paintingLevel import PaintingLevel
from player import Player
from dialogue import Dialogue
from level1 import Level1
from timer import CountdownTimer

class Game:
    def __init__(self):
        # cree la fenetre du jeu
        self.screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN | pygame.SCALED)
        pygame.display.set_caption("RAMBA")

        # charger la carte (tmx)
        tmx_data = pytmx.util_pygame.load_pygame('main map demo.tmx')
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 3

        # Keep self.music as a convenience alias used by sub-levels
        self.music = pygame.mixer.music

        # ── World-map background music ────────────────────────────────────
        self._world_music_active = False   # managed by helpers below
        self._music_start_world()          # fade in on first load

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

        self.current_level = None

        # create boolean for each level to know if the payer won the level or not
        self.level1_completed = False
        self.painting_level_completed = False
        self.music_level_completed = False

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

    # ------------------------------------------------------------------ #
    #  Music helpers
    # ------------------------------------------------------------------ #
    def _music_start_world(self):
        """Load the world-map track and fade it in over 3 s."""
        if self._world_music_active:
            return
        pygame.mixer.music.load("music/main map music.aif")
        pygame.mixer.music.set_volume(0.15)
        pygame.mixer.music.play(-1, fade_ms=3000)
        self._world_music_active = True

    def _music_stop_world(self):
        """Fade the world music out over 1 s (non-blocking).

        The 1 s fadeout is intentionally matched to the 1 s screen-blackout
        in fade_in_to_black() so both finish at the same time.
        """
        if not self._world_music_active:
            return
        pygame.mixer.music.fadeout(1000)
        self._world_music_active = False

    # ------------------------------------------------------------------ #
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
        # Start audio fade-out BEFORE the visual one so both finish together
        # (200 steps × 5 ms = 1 000 ms — same duration as fadeout below)
        self._music_stop_world()

        fade = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        fade.fill((0, 0, 0))
        for alpha in range(0, 200):
            fade.set_alpha(alpha)
            self.screen.blit(fade, (0, 0))
            pygame.display.update()
            pygame.time.delay(5)

    def display_entering_message(self, message):
        self.fade_in_to_black()
        dialogue = Dialogue(message)
        dialogue.start()

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

    def try_enter_level(self, level_name, level_class, completed_flag, msg, timer_val=None):
        if not completed_flag:
            self.display_entering_message(msg)
            self.map = level_name
            
            # Move player so they aren't on the door when they return
            if level_name == "level1":
                self.player.position[0] -= 30
            else:
                self.player.position[1] += 30 
            
            # Initialize the level
            if timer_val:
                timer = CountdownTimer(timer_val)
                self.current_level = level_class(timer, self.screen, self)
            else:
                self.current_level = level_class(self.screen, self)
        else:
            self.display_entering_message(["You already completed this!", "Go explore!"])
            if level_name == "level1":
                self.player.position[0] -= 30
            else:
                self.player.position[1] += 30
    
    def update_world(self):

        self.player.save_location()
        self.handle_input()
        self.group.update()
        self.group.center(self.player.rect)
        self.group.draw(self.screen)
        
        if self.check_collision_with_list(self.walls):
            self.player.move_back()

        # --- DOOR COLLISIONS (Cleaned up using the helper) ---
        
        if self.check_collision_with_door(self.doors[0]):
            self.music.stop()
            self.try_enter_level("level1", Level1, self.level1_completed, ["Welcome!", "stuck!"], 40)

        if self.check_collision_with_door(self.doors[1]):
            self.music.stop()
            self.try_enter_level("paintingLevel", PaintingLevel, self.painting_level_completed, ["Art Gallery!", "Look Closely, and find all 5 paintings!"])

        if self.check_collision_with_door(self.doors[2]):
            self.music.stop()
            self.try_enter_level("musicLevel", MusicLevel, self.music_level_completed, ["Music Hall!", "Listen closely."])

        # --- TUNNEL COLLISIONS ---
        if self.check_collision_with_tunnel(self.tunnels[0]):
            self.display_entering_message(["Entering the tunnel...", "Be careful!"])
            self.player.position[0] = self.tunnel2.x
            self.player.position[1] = self.tunnel2.y - 54
        
        if self.check_collision_with_tunnel(self.tunnels[1]):
            self.display_entering_message(["Leaving the tunnel...", "You were lucky!"])
            self.player.position[0] = self.tunnel1.x
            self.player.position[1] = self.tunnel1.y + 32

    def run(self):
        clock = pygame.time.Clock()
        fps = 60

        running = True
        
        while running:
            events = pygame.event.get()
            
            pygame.mouse.set_visible(False)
            
            if self.map == "world":
                # Fade world music back in whenever we return from a level
                # (or after a tunnel transition faded it out)
                if not self._world_music_active:
                    self._music_start_world()
                self.update_world()

            else:
                if self.current_level:
                    self.current_level.update(events)
            
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False

            pygame.display.update()

            clock.tick(fps)

        pygame.quit()
