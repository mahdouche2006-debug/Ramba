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
        self.group.add(self.e_sprite)

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

            if obj.name.lower() == "guitar":
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
        # 1. Get a shifting offset based on time
        # pygame.time.get_ticks() gives us the time in milliseconds
        # We divide by 200 to control the speed of the bobbing
        bobbing_offset = math.sin(pygame.time.get_ticks() / 200) * 8

        near_instrument = self.get_colliding_item(self.instruments)
        near_podium     = self.podium      and self.player.feet.colliderect(self.podium)
        near_guitar     = self.guitar_zone and self.player.feet.colliderect(self.guitar_zone)
        if near_instrument or near_podium or near_guitar:
            # Position the E sprite relative to the player's WORLD coordinates
            # Pyscroll will automatically scale this by 3x and offset it for the camera
            self.e_sprite.rect.midbottom = (
                self.player.rect.centerx + bobbing_offset, 
                self.player.rect.top - 10
            )
        else:
            # Hide it when not near anything
            self.e_sprite.rect.topleft = (-500, -500)

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