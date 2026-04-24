import pygame
import pytmx
import pyscroll
import game
import math

from player import Player, PlayerShadow
from item import Item
from dialogue import Dialogue
from inventory import Inventory
from board import Board
from enigmaUI import EnigmaUI


class Level1:
    def __init__(self, timer, screen, game_instance):
        # cree la fenetre du jeu
        self.screen = screen
        self.game = game_instance
        # charger la carte (tmx)
        tmx_data = pytmx.util_pygame.load_pygame('newPotteryLvl.tmx')
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 3
        map_layer.bgcolor = (30, 20, 15)   # dark fill so map edges don't flash black

        # generer un joueur
        try:
            player_position = tmx_data.get_object_by_name("player")
            self.player = Player(player_position.x, player_position.y)
        except KeyError:
            self.player = Player(200, 200)  # fallback spawn if no player object in map

        # dessiner le groupe de calque
        # onTop is tile layer index 1 — player must be at pyscroll layer 0 to render beneath it
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=0)
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
        self.sculptures = []
        self.side_stairs = []
        self.board = None

        for obj in tmx_data.objects:

            if obj.type == "obj":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

            elif obj.type == "sculpture":
                sculpture = Item(obj.name, obj.x, obj.y, False)
                self.sculptures.append(sculpture)
                self.group.add(sculpture)

            elif obj.type == "side_stairs":
                self.side_stairs.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

            if obj.name == "board":
                self.board = Board(obj.x, obj.y, obj.width, obj.height)

        # onTop layer is tile index 1 — player/shadow must be at layer 0
        self.group.change_layer(self.player, 0)
        self.group.change_layer(self.e_sprite, 0)

        # Shadow below the player (same layer 0, inserted before player so it draws first)
        self.player_shadow = PlayerShadow(self.player)
        self.group.add(self.player_shadow)
        self.group.change_layer(self.player_shadow, 0)

        # counter for items collected
        self.items_collected = 0

        # timer creation
        self.timer = timer

        # font
        self.font = pygame.font.Font("fonts/Pixel Emulator.otf", 36)

        # inventory creation
        self.inventory = Inventory()

        # change the soud of the footsteps
        self.player.walk_sounds = [
            pygame.mixer.Sound("music/woodWalk1.wav"),
            pygame.mixer.Sound("music/woodWalk2.wav"),
            pygame.mixer.Sound("music/woodWalk3.wav")
        ]

        for sound in self.player.walk_sounds:
            sound.set_volume(0.4)

        # dictionary for the enigma UI
        self.enigma_data = {
            "TheThinker": {
                "options": ["Auguste Rodin", "Michelangelo", "Banksy"],
                "correct": 0,
                "image": pygame.transform.scale(pygame.image.load("images/TheThinker.png").convert_alpha(), (400, 300))
            },
            "David": {
                "options": ["Donatello", "Bernini", "Michelangelo"],
                "correct": 2,
                "image": pygame.transform.scale(pygame.image.load("images/David.png").convert_alpha(), (400, 300))
            },
            "Pieta": {
                "options": ["Michelangelo", "R. Smithson", "A. Savage"],
                "correct": 0,
                "image": pygame.transform.scale(pygame.image.load("images/Pieta.png").convert_alpha(), (400, 300))
            },
            "ChristTheRedeemer": {
                "options": ["Lee Bontecou", "P. Landowski", "Ruth Asawa"],
                "correct": 1,
                "image": pygame.transform.scale(pygame.image.load("images/ChristTheRedeemer.png").convert_alpha(), (400, 300))
            },
            "Medusa": {
                "options": ["Bernini", "D. Judd", "Eva Hesse"],
                "correct": 0,
                "image": pygame.transform.scale(pygame.image.load("images/Medusa.png").convert_alpha(), (400, 300))
            },
            "VenusDeMilo": {
                "options": ["Sol LeWitt", "Alexandros", "T. Eakins"],
                "correct": 1,
                "image": pygame.transform.scale(pygame.image.load("images/VenusDeMilo.png").convert_alpha(), (400, 300))
            },
        }

        #initialize the cooldown dictionary for sculptures
        self.sculpture_cooldowns = {}

        self.is_viewing_enigma = False
        
    def handle_input(self):
        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0
        stairs_deviation = 0.33

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

        direction = pygame.math.Vector2(dx, dy)

        if direction.length() > 0:
            direction = direction.normalize()

        self.player.save_location()

        self.player.position[0] += direction.x * self.player.speed
        self.player.position[1] += direction.y * self.player.speed

        self.player.animate()
    
    def remove_sculpture_from_list(self, item):
        self.group.remove(item)
        self.sculptures.remove(item)

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
                    if event.key == pygame.K_SPACE:
                        self.screen.fill((0, 0, 0))

                dialogue.handle_event(event)
            dialogue.update()
            dialogue.draw(self.screen)
            pygame.display.flip()

    def add_sculpture_to_inventory(self, item):
        if item:
            self.items_collected += 1
            self.remove_sculpture_from_list(item)
            self.inventory.add_item(item)

    def generate_new_item(self, item, item_name):
        new_item = Item(item_name, item.rect.x, item.rect.y)
        self.items.append(new_item)
        self.group.add(new_item)

    def check_collision_between_mouse_and_buttons(self, mouse_pos):
        for i, rect in enumerate(self.current_ui.button_rects):
            if rect.collidepoint(mouse_pos):
                return i
        return None
    
    def check_enigma_answer(self, mouse_pos):
        clicked_index = self.check_collision_between_mouse_and_buttons(mouse_pos)
        
        if clicked_index is not None:
            if clicked_index == self.current_ui.correct_index:
                # CORRECT: Trigger green shake
                self.current_ui.trigger_shake_anim(clicked_index, correct=True)
                self.add_sculpture_to_inventory(self.get_colliding_item(self.sculptures))
                self.timer.duration += 5
                # You could add your "Clay Collected" logic here!
            else:
                # WRONG: Trigger red shake and set lock
                self.current_ui.trigger_shake_anim(clicked_index, correct=False)
                self.timer.duration -= 10
                
                sculpture = self.get_colliding_item(self.sculptures)
                if sculpture:
                    self.sculpture_cooldowns[sculpture.name] = pygame.time.get_ticks() + 5000

    def open_board(self):
        self.board.open_sound.play()
        self.board.open = not self.board.open
        self.player.canMove = not self.player.canMove

    def drawing_e(self):
        # 1. Get a shifting offset based on time
        # pygame.time.get_ticks() gives us the time in milliseconds
        # We divide by 200 to control the speed of the bobbing
        bobbing_offset = math.sin(pygame.time.get_ticks() / 200) * 8

        near_sculpture = self.get_colliding_item(self.sculptures)
        near_board = self.board and self.player.feet.colliderect(self.board.rect)
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

    def open_inventory(self):
        self.inventory.open_sound.play()
        self.inventory.open = not self.inventory.open
        self.player.canMove = not self.player.canMove

    def create_current_enigma(self, sculpture):
        # Get the specific data for this sculpture from your dictionary
        if sculpture.name in self.enigma_data:
            data = self.enigma_data[sculpture.name]
            self.current_ui = EnigmaUI(data["image"], data["options"], data["correct"])
            self.is_viewing_enigma = True

    def update(self, events):

        self.player.save_location()
    
        # Only allow movement if NOT in a menu
        if not self.is_viewing_enigma:
            self.handle_input()

        self.group.update()
        self.group.center(self.player.rect)
        self.group.draw(self.screen)

        self.timer.update()
        self.timer.draw(self.screen)

        self.inventory.draw(self.screen)

        if self.board:
            self.board.draw(self.screen)

        if self.is_viewing_enigma:
            # 1. Draw the UI and check if it has finished its "Wrong" animation
            # (This assumes you added 'return is_done_shaking' to your EnigmaUI.draw)
            animation_finished = self.current_ui.draw(self.screen)

            # 3. If the UI says it's done shaking (or a correct answer was picked), close it
            if animation_finished:
                self.is_viewing_enigma = False
                self.player.canMove = True

        if self.check_collision_with_list(self.walls):
            self.player.move_back()

        self.drawing_e()

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()

                if event.key == pygame.K_i:
                    self.open_inventory()

                if event.key == pygame.K_e and not self.inventory.open:
                    if self.is_viewing_enigma:
                        self.is_viewing_enigma = False
                        self.player.canMove = True
                    else:
                        sculpture = self.get_colliding_item(self.sculptures)
                        if sculpture:
                            # --- COOLDOWN CHECK ---
                            current_time = pygame.time.get_ticks()
                            lock_end_time = self.sculpture_cooldowns.get(sculpture.name, 0)

                            if current_time < lock_end_time:
                                # Still locked! Calculate seconds remaining
                                timeLeft = int((lock_end_time - current_time) / 1000)
                                print(f"Locked! Try again in {timeLeft}s")
                                print(f"DEBUG: Sculpture {sculpture.name} is locked until {lock_end_time}. Current: {current_time}")
                            else:
                                # Not locked! Open normally
                                self.create_current_enigma(sculpture)
                                self.player.canMove = False 
                            # -----------------------

                    if self.board and self.player.feet.colliderect(self.board.rect):
                        self.open_board()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.is_viewing_enigma:
                    self.check_enigma_answer(event.pos)
        
        # items counter — semi-transparent box (matches timer style)
        label      = self.font.render(f"Items  {self.items_collected}/6", False, (255, 255, 255))
        pad        = 8
        box_w      = label.get_width()  + pad * 2
        box_h      = label.get_height() + pad * 2
        box_x      = self.screen.get_width() - box_w - 12
        box_y      = 12
        bg         = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        self.screen.blit(bg,    (box_x, box_y))
        self.screen.blit(label, (box_x + pad, box_y + pad))
        # return to world when all items are collected
        if self.items_collected == 6:
            self.ending_the_level(["You found all the items!", "Press c to return to world map..."])
            self.game.map = "world"
            self.game.level1_completed = True

        if self.timer.remaining_time <= 0:
            self.ending_the_level(["Time's up! Returning to world map..."])
            self.game.map = "world"

        
        if self.is_viewing_enigma:
            pygame.mouse.set_visible(True)
