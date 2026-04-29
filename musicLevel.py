import math
import random

import pygame
import pytmx
import pyscroll

from item import Item
from player import PlayerShadow
from inventory import Inventory

class MusicLevel:
    def __init__(self, screen, game_instance):
        self.screen = screen
        self.game = game_instance
        
        self.game.music.stop()

        tmx_data = pytmx.util_pygame.load_pygame("musicLevel.tmx")
        map_data = pyscroll.data.TiledMapData(tmx_data) 
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 3
        map_layer.bgcolor = (36, 34, 39)   # match musicMap.png background colour

        
        # reuse the player from the game instance
        self.player = game_instance.player

        # dessiner le groupe de calque
        # Tile layer indices: 0 = ground, 1 = onTop
        # Sprites at layer N draw after tile layer N, so player must be at 0
        # to render between ground and onTop.
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=0)

        # Shadow added first at layer 0 → draws before player (beneath feet)
        self.player_shadow = PlayerShadow(self.player)
        self.group.add(self.player_shadow)
        self.group.change_layer(self.player_shadow, 0)

        # Player at layer 0 → draws after ground, before onTop tile layer
        self.group.add(self.player)
        self.group.change_layer(self.player, 0)

        self.music = pygame.mixer.music
        self.MUSIC_FINISHED_EVENT = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.MUSIC_FINISHED_EVENT)  # Custom event for music end

        # ── Music-themed pixel-art E badge (drawn directly to screen) ──────
        # Colours
        _BG      = (  8,   5,  20, 200)   # deep navy background
        _TEAL    = (  0, 210, 180, 255)   # bright teal — outer border + note
        _PURPLE  = (150,  60, 230, 255)   # bright purple — inner border + key border
        _KEY_BG  = ( 20,  10,  45, 250)   # dark purple key fill
        _TEXT    = (190, 255, 242, 255)   # near-white teal text

        _font      = pygame.font.Font("fonts/Pixel Emulator.otf", 18)
        _key_surf  = _font.render("E",        True, _TEXT)
        _hint_surf = _font.render("interact", True, _TEXT)

        _pad    = 7
        _key_sz = _key_surf.get_height() + _pad * 2   # square key box side

        # Hand-drawn pixel music note (10 × 11 px bitmap, 2 px per cell)
        _NOTE_BITMAP = [
            "...###",
            "....##",
            ".....#",
            ".....#",
            ".....#",
            ".....#",
            "..####",
            "..####",
            ".....#",
            ".####.",
            ".####.",
        ]
        _CELL = 2                                 # pixels per bitmap cell
        _note_w = len(_NOTE_BITMAP[0]) * _CELL
        _note_h = len(_NOTE_BITMAP)    * _CELL

        _badge_w = _pad + _note_w + _pad + _key_sz + _hint_surf.get_width() + _pad * 2
        _badge_h = _key_sz + _pad * 2

        self.e_badge = pygame.Surface((_badge_w, _badge_h), pygame.SRCALPHA)

        # Background (sharp pixel-art corners)
        pygame.draw.rect(self.e_badge, _BG,     (0, 0, _badge_w, _badge_h))
        # Outer teal border (2 px)
        pygame.draw.rect(self.e_badge, _TEAL,   (0, 0, _badge_w, _badge_h), 2)
        # Inner purple border (1 px, inset by 3)
        pygame.draw.rect(self.e_badge, _PURPLE, (3, 3, _badge_w - 6, _badge_h - 6), 1)

        # Pixel music note — centred vertically on the left side
        _nx = _pad
        _ny = (_badge_h - _note_h) // 2
        for _row_i, _row in enumerate(_NOTE_BITMAP):
            for _col_i, _px in enumerate(_row):
                if _px == "#":
                    pygame.draw.rect(self.e_badge, _TEAL,
                                     (_nx + _col_i * _CELL,
                                      _ny + _row_i * _CELL,
                                      _CELL, _CELL))

        # Key box
        _kx = _pad + _note_w + _pad
        _ky = _pad
        pygame.draw.rect(self.e_badge, _KEY_BG, (_kx, _ky, _key_sz, _key_sz))
        pygame.draw.rect(self.e_badge, _PURPLE, (_kx, _ky, _key_sz, _key_sz), 2)
        # Tiny highlight pixel (top-left of key)
        pygame.draw.rect(self.e_badge, _TEAL, (_kx + 2, _ky + 2, 3, 1))
        self.e_badge.blit(_key_surf,
                          (_kx + (_key_sz - _key_surf.get_width())  // 2,
                           _ky + (_key_sz - _key_surf.get_height()) // 2))

        # Hint text
        self.e_badge.blit(_hint_surf,
                          (_kx + _key_sz + _pad,
                           _ky + (_key_sz - _hint_surf.get_height()) // 2))
        # ─────────────────────────────────────────────────────────────────

        self.walls       = []
        self.instruments = []
        self.podium      = None   # set below if the map defines a Podium object
        self.guitar_zone = None   # interactive guitar object layer
        spawn_points     = []     # collects all "player" named objects

        self.instrument_sequence = ["Guitar", "Maracas", "Flute", "Banjo"]
        self.current_index = 0

        self.current_target = None  # The instrument the player needs to find
        self.shake_amount = 0       # For the shake animation
        self.womp_sound = pygame.mixer.Sound("music/womp-womp.mp3")

        for obj in tmx_data.objects:

            if obj.type == "obj":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

            if obj.type == "instrument":
                instrument = Item(f"instruments/{obj.name}", obj.x, obj.y)
                instrument.name = obj.name
                self.instruments.append(instrument)
                self.group.add(instrument)

            if obj.name == "Podium":
                self.podium = pygame.Rect(obj.x, obj.y, obj.width, obj.height)

            if obj.name and obj.name.lower() == "guitar":
                self.guitar_zone = pygame.Rect(obj.x, obj.y, obj.width, obj.height)

            if obj.name == "player":
                spawn_points.append((obj.x, obj.y))

        # Teleport player to a random spawn point defined in the map
        if spawn_points:
            spawn = random.choice(spawn_points)
            self.player.position[0] = spawn[0]
            self.player.position[1] = spawn[1]
            self.player.rect.topleft = self.player.position

        self.inventory = Inventory()

        self.instruments_collected = 0
        
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

    def get_colliding_item(self, list):
        for item in list:
            if self.player.feet.colliderect(item.rect):
                return item
        return None

    def check_collision_with_list(self, obj):
        # verification collision
        return self.player.feet.collidelist(obj) > -1

    def remove_instrument_from_list(self, item):
        self.group.remove(item)
        self.instruments.remove(item)

    def add_instrument_to_inventory(self, item):
        if item:
            self.remove_instrument_from_list(item)
            self.inventory.add_item(item)

    def drawing_e(self):
        """Draw the music-themed E badge directly on screen above the player.

        Drawn after group.draw() so it always sits above every tile layer.
        """
        near_instrument = self.get_colliding_item(self.instruments)
        near_podium     = self.podium      and self.player.feet.colliderect(self.podium)
        near_guitar     = self.guitar_zone and self.player.feet.colliderect(self.guitar_zone)
        if not (near_instrument or near_podium or near_guitar):
            return

        zoom   = 3
        sw, sh = self.screen.get_size()
        bob    = math.sin(pygame.time.get_ticks() / 200) * 5

        # Player is always at screen centre; convert world offset to screen offset
        badge_screen_x = sw // 2
        badge_screen_y = (sh // 2
                          + (self.player.rect.top - self.player.rect.centery) * zoom
                          - 12 + bob)

        badge = self.e_badge
        self.screen.blit(badge, (badge_screen_x - badge.get_width() // 2,
                                 badge_screen_y - badge.get_height()))

    def play_next_challenge(self):
        """Play the next instrument sound in the fixed sequence."""
        
        # Check if we have finished all instruments in the list
        if self.current_index < len(self.instrument_sequence):
            target_name = self.instrument_sequence[self.current_index]
            
            # Find the actual Item object in self.instruments that matches this name
            for inst in self.instruments:
                if inst.name == target_name:
                    self.current_target = inst
                    break
            
            # Play the sound
            sound_path = f"music/instSound/{target_name}/{target_name}.mp3"
            try:
                pygame.mixer.music.load(sound_path)
                pygame.mixer.music.play()
                print(f"Challenge started: Find the {target_name}")
            except Exception as e:
                print(f"Sound error: {e}")
        else:
            print("Level Complete! You've found all instruments.")

    def handle_interaction(self):
        """Logic for pressing E"""
        # 1. Check Podium Interaction
        if self.podium and self.player.feet.colliderect(self.podium):
            # Only play next challenge if we don't have one active
            if not self.current_target:
                self.play_next_challenge()
            return

        # 2. Check Instrument Interaction
        item = self.get_colliding_item(self.instruments)
        if item:
            if item == self.current_target:
                # SUCCESS
                self.add_instrument_to_inventory(item)
                pygame.mixer.music.set_endevent()
                self.music.stop()
                pygame.event.clear(self.MUSIC_FINISHED_EVENT) # Remove any "pending" fail signals
                pygame.mixer.music.set_endevent(self.MUSIC_FINISHED_EVENT)  # Re-enable for next round
                self.current_target = None 
                self.current_index += 1
                self.instruments_collected += 1
            else:
                # WRONG INSTRUMENT - Localized Shake
                item.shake_timer = 20 # Number of frames to shake
                self.womp_sound.play()

    def update(self, events): 
        self.player.save_location()

        self.handle_input()

        for inst in self.instruments:
            if hasattr(inst, 'shake_timer') and inst.shake_timer > 0:
                inst.shake_timer -= 1
                # Generate a random offset for the shake effect
                offset_x = random.randint(-4, 4)
                offset_y = random.randint(-4, 4)
                # Apply offset to the actual rect temporarily for the draw call
                inst.rect.x += offset_x
                inst.rect.y += offset_y
                
                # Note: We reset this after the draw or in the next frame 
                # to prevent the instrument from "walking" away.
                # A cleaner way is to store the original pos:
                if not hasattr(inst, 'original_pos'):
                    inst.original_pos = (inst.rect.x - offset_x, inst.rect.y - offset_y)

        self.group.update()
        self.group.center(self.player.rect)
        self.group.draw(self.screen)

        for inst in self.instruments:
            if hasattr(inst, 'original_pos'):
                inst.rect.topleft = inst.original_pos
                delattr(inst, 'original_pos')

        self.drawing_e()

        if self.check_collision_with_list(self.walls):
            self.player.move_back()

        for event in events:
            
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_i:
                    self.inventory.open = not self.inventory.open

                if event.key == pygame.K_e and not self.inventory.open:
                    self.handle_interaction()
            
            if event.type == self.MUSIC_FINISHED_EVENT:
                # This event is triggered when the music finishes playing
                self.game.display_entering_message(["Time's up! You failed to find the instrument in time.", "Try again later!"])
                
                self.game.music.load("music/pottery level music.aif")
                self.game.music.play(-1)
                self.game.music.set_volume(0.5)
                self.game.map = "world"  # Send player back to world map

        if self.inventory.open:
            self.inventory.draw(self.screen)

        if self.instruments_collected == len(self.instrument_sequence):
            self.game.display_entering_message(["Congratulations! You found all the instruments.", "You are a true musician!"])
            self.game.music.load("music/pottery level music.aif")
            self.game.music.play(-1)
            self.game.music.set_volume(0.5)
            self.game.map = "world"  # Send player back to world map