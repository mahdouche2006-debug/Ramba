import pygame
import pytmx
import pyscroll
import math

from board import Board
from dialogue import Dialogue
from inventory import Inventory
from paintingUI import PaintingUI
from paintingClue import PaintingClue
from player import PlayerShadow


class _FoundPainting:
    """Lightweight inventory entry for a correctly identified painting."""
    def __init__(self, name, image):
        self.name          = name
        self.display_image = image  # used by Inventory.draw via getattr

class PaintingLevel:
    def __init__(self, screen, game_instance):
        self.screen = screen
        self.game = game_instance
        # charger la carte (tmx)
        tmx_data = pytmx.util_pygame.load_pygame('paintingLevel.tmx')
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 3
        map_layer.bgcolor = (30, 20, 15)   # dark fill so map edges don't flash black

        # reuse the player from the game instance
        self.player = game_instance.player

        # dessiner le groupe de calque
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=1)
        self.group.add(self.player)

        self.music = pygame.mixer.music
        self.music.load("music/ClairLune.mp3")
        self.music.set_volume(0.3)
        self.music.play(-1, fade_ms=3000)

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

        # inventory creation
        self.inventory = Inventory()

        # Add it to the group so it moves with the camera
        self.group.add(self.e_sprite)

        self.walls = []
        self.paintings = {}
        self.board = None

        for obj in tmx_data.objects:

            if obj.type == "obj":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

            if obj.type == "painting":
                # Store the rect using the name as the key
                # Example: self.paintings["Monalisa"] = pygame.Rect(...)
                self.paintings[obj.name] = pygame.Rect(obj.x, obj.y, obj.width, obj.height)

            if obj.name == "board":
                self.board = Board(obj.x, obj.y, obj.width, obj.height)

        # "onTop" is tile layer index 2 — player must be at layer 1 to render beneath it
        self.group.change_layer(self.player, 1)
        self.group.change_layer(self.e_sprite, 1)

        # Shadow below the player (layer 0)
        self.player_shadow = PlayerShadow(self.player)
        self.group.add(self.player_shadow)
        self.group.change_layer(self.player_shadow, 0)

        # counter for items collected
        self.paintings_collected = 0
        self.is_viewing_painting = False
        self.current_painting_rect = None # Tracks which painting the player is looking at

        self.current_target_index = 0
        self.paintings_found = 0
        self.lives = 3

        # The "Clue" logic
        self.clue_active = False

        # ── All paintings: image_path + art-historical clue ─────────────────
        # Keys must match the object names used in paintingLevel.tmx.
        # image_path points to images/paintings/<Filename>.<ext>
        self.paintings_data = {
            "MonaLisa": {
                "clue": "Find the lady with the mysterious smile, painted by the master of the Renaissance.",
                "image_path": "images/paintings/MonaLisa.jpg",
            },
            "TheScream": {
                "clue": "Seek the figure clutching its face against a swirling blood-red sky.",
                "image_path": "images/paintings/TheScream.jpg",
            },
            "TheStarryNight": {
                "clue": "Look for the swirling night sky blazing over a sleeping village and church spire.",
                "image_path": "images/paintings/TheStarryNight.jpg",
            },
            "GirlWithAPearlEarring": {
                "clue": "Seek the girl gazing over her shoulder, wearing a single luminous pearl.",
                "image_path": "images/paintings/GirlWithAPearlEarring.jpg",
            },
            "TheSchoolOfAthens": {
                "clue": "Find Raphael's grand fresco of ancient Greek philosophers gathered beneath sweeping arches.",
                "image_path": "images/paintings/TheSchoolOfAthens.jpg",
            },
            "TheLambAmongWolves": {
                "clue": "Look for the innocent lamb surrounded by predators in this allegorical scene.",
                "image_path": "images/paintings/TheLambAmongWolves.jpg",
            },
            "LesSaltimbanques": {
                "clue": "Find Picasso's melancholy group of circus performers drifting through an empty landscape.",
                "image_path": "images/paintings/LesSaltimbanques.jpg",
            },
            "Ophelia": {
                "clue": "Seek the tragic Shakespearean figure floating serenely among flowers on a river's surface.",
                "image_path": "images/paintings/Ophelia.jpg",
            },
            "TheFallenAngel": {
                "clue": "Look for the expelled angel, wings spread wide, falling from heavenly grace.",
                "image_path": "images/paintings/TheFallenAngel.jpg",
            },
            "SelfPortraitWithDeathPlayingTheFiddle": {
                "clue": "Find the artist face-to-face with Death, who plays a fiddle over his shoulder.",
                "image_path": "images/paintings/SelfPortraitWithDeathPlayingTheFiddle.jpg",
            },
            "Anguish": {
                "clue": "Seek the raw expression of unbearable grief captured in dark, tortured strokes.",
                "image_path": "images/paintings/Anguish.jpg",
            },
            "TheHesitantFiance": {
                "clue": "Find the reluctant suitor caught between desire and doubt on his wedding day.",
                "image_path": "images/paintings/TheHesitantFiance.jpg",
            },
            "TheDefender": {
                "clue": "Look for the lone figure standing guard, shielding something precious.",
                "image_path": "images/paintings/TheDefender.jpg",
            },
            "TheBlueboy": {
                "clue": "Seek the elegantly dressed young man in shimmering blue satin.",
                "image_path": "images/paintings/TheBlueboy.jpg",
            },
            "AFriendInNeed": {
                "clue": "Find the dogs gathered around a card table — one secretly dealing from beneath.",
                "image_path": "images/paintings/AFriendInNeed.webp",
            },
            "TheLastSupper": {
                "clue": "Look for Christ and his twelve apostles at the long table on the eve of his betrayal.",
                "image_path": "images/paintings/TheLastSupper.webp",
            },
            "SaturnDevouringHisSon": {
                "clue": "Find the terrifying god consuming his own child in a fit of fear and madness.",
                "image_path": "images/paintings/SaturnDevouringHisSon.jpg",
            },
            "IvanTheTerribileAndHisSon": {
                "clue": "Seek the tsar cradling his dying son, horror and regret written across his face.",
                "image_path": "images/paintings/IvanTheTerribileAndHisSon.jpg",
            },
            "NapoleonCrossingTheAlps": {
                "clue": "Find the general atop a rearing horse, commanding the mountain pass.",
                "image_path": "images/paintings/NapoleonCrossingTheAlps.jpg",
            },
            "Stanczyk": {
                "clue": "Look for the court jester sitting alone in grim thought while festivities rage behind him.",
                "image_path": "images/paintings/Stanczyk.jpg",
            },
            "LOrphelin": {
                "clue": "Seek the solitary orphan child, wandering and grieving in a desolate setting.",
                "image_path": "images/paintings/LOrphelin.jpg",
            },
            "LibertyLeadingThePeople": {
                "clue": "Find the allegorical figure of Liberty holding the tricolour flag amid revolutionary chaos.",
                "image_path": "images/paintings/LibertyLeadingThePeople.jpg",
            },
            "TheCreationOfAdam": {
                "clue": "Seek the divine spark — God reaching toward Adam's outstretched finger on the Sistine ceiling.",
                "image_path": "images/paintings/TheCreationOfAdam.jpg",
            },
            "TheBirthOfVenus": {
                "clue": "Find the goddess rising from the sea on a shell, carried by the breath of the wind.",
                "image_path": "images/paintings/TheBirthOfVenus.jpg",
            },
            "TheKiss": {
                "clue": "Look for the golden couple locked in an embrace, wrapped in a jewelled tapestry.",
                "image_path": "images/paintings/TheKiss.jpg",
            },
            "TheSwing": {
                "clue": "Find the lady on the swing, her shoe flying off into the lush garden air.",
                "image_path": "images/paintings/TheSwing.jpg",
            },
            "TheGreatWaveOffKanagawa": {
                "clue": "Seek the towering wave about to crash, with Mount Fuji small and calm in the distance.",
                "image_path": "images/paintings/TheGreatWaveOffKanagawa.jpg",
            },
            "SelfPortraitVanGogh": {
                "clue": "Find the artist's own face, painted with swirling brushstrokes and piercing eyes.",
                "image_path": "images/paintings/SelfPortraitVanGogh.jpg",
            },
            "ThePersistenceOfMemory": {
                "clue": "Look for the melting clocks draped like cloth over a barren dreamscape.",
                "image_path": "images/paintings/ThePersistenceOfMemory.jpg",
            },
            "WaterLilies": {
                "clue": "Find Monet's tranquil pond, its shimmering surface alive with soft dabs of colour.",
                "image_path": "images/paintings/WaterLilies.jpg",
            },
            # Legacy entries kept for TMX backwards compatibility
            "Guernica": {
                "clue": "Identify the chaotic monochrome scene depicting the horrors of war.",
                "image_path": "images/Guernica.png",
            },
            "LasMeninas": {
                "clue": "Find the painting showing the Infanta Margarita with her attendants and Velázquez himself.",
                "image_path": "images/LasMeninas.png",
            },
        }
        # ────────────────────────────────────────────────────────────────────

        # Paintings the player MUST find (first 5 from the dictionary)
        self.masterpieces = list(self.paintings_data.keys())[:5]

        # Build clue list in masterpieces order (index matches current_target_index)
        self.painting_clue_dialogues = [
            self.paintings_data[name]["clue"] for name in self.masterpieces
        ]

        # painting clue creation
        self.painting_clue = PaintingClue(self.screen, self.game, self.painting_clue_dialogues)
        self.painting_clue.dialogues.append("Congratulations! You've found all the masterpieces!")

        # font
        self.font = pygame.font.Font("fonts/Pixel Emulator.otf", 70)
        self.hud_font = pygame.font.Font("fonts/Pixel Emulator.otf", 36)

        # change the soud of the footsteps
        self.player.walk_sounds = [
            pygame.mixer.Sound("music/woodWalk1.wav"),
            pygame.mixer.Sound("music/woodWalk2.wav"),
            pygame.mixer.Sound("music/woodWalk3.wav")
        ]

        for sound in self.player.walk_sounds:
            sound.set_volume(0.45)
    
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
    
    def get_colliding_painting_name(self):
        for name, rect in self.paintings.items():
            if self.player.feet.colliderect(rect):
                return name
        return None

    def check_painting_choice(self, mouse_pos):
        # Find which button in the UI was clicked
        clicked_button_index = -1
        for i, rect in enumerate(self.current_ui.button_rects):
            if rect.collidepoint(mouse_pos):
                clicked_button_index = i

        if clicked_button_index == 1: # They clicked "Go Back"
            self.is_viewing_painting = False
            self.player.canMove = True

        elif clicked_button_index == 0: # They clicked "This is it"
            actual_name = self.get_colliding_painting_name()
            target_name = self.masterpieces[self.current_target_index]

            if actual_name == target_name:
                # CORRECT: Success animation (Green)
                self.current_ui.trigger_feedback(0, correct=True)
                self.paintings_found += 1
                self.current_target_index += 1
                self.painting_clue.current_dialogue_idx += 1 # Move to the next clue for the next painting

                # Add the found painting to the inventory
                img_path = self.paintings_data[actual_name]["image_path"]
                try:
                    img = pygame.image.load(img_path).convert()
                except Exception:
                    img = pygame.Surface((1, 1))
                self.inventory.add_item(_FoundPainting(actual_name, img))
                print("Correct!")
            else:
                # WRONG: Error animation (Red)
                self.current_ui.trigger_feedback(0, correct=False)
                self.lives -= 1
                print(f"Wrong! You have {self.lives} lives left.")
    
    def drawing_e(self):
        # 1. Bobbing Math
        bobbing_offset = math.sin(pygame.time.get_ticks() / 200) * 8

        # 2. Updated collision check for Dictionary
        # We check if the player's feet touch ANY of the rects in our dictionary
        near_painting = False
        for rect in self.paintings.values():
            if self.player.feet.colliderect(rect):
                near_painting = True
                break # Stop looking once we find one

        near_board = self.board and self.player.feet.colliderect(self.board.rect)

        # 3. Display Logic
        if near_board or near_painting:
            self.e_sprite.rect.midbottom = (
                self.player.rect.centerx, 
                self.player.rect.top - 10 + bobbing_offset # Applied to Y for vertical bobbing
            )
        else:
            self.e_sprite.rect.topleft = (-500, -500)
    
    def _draw_hud_box(self, text, color, x, y):
        """Draw a semi-transparent HUD box (same style as the timer)."""
        pad   = 8
        label = self.hud_font.render(text, False, color)
        box_w = label.get_width()  + pad * 2
        box_h = label.get_height() + pad * 2
        bg    = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        self.screen.blit(bg,    (x, y))
        self.screen.blit(label, (x + pad, y + pad))

    def draw_stats(self):
        margin = 12

        # top-left: lives (red)
        self._draw_hud_box(
            f"Lives  {self.lives}",
            (220, 60, 60),
            margin, margin
        )

        # top-right: found counter (gold)
        total = len(self.masterpieces)
        found_label = self.hud_font.render(f"Found  {self.paintings_found}/{total}", False, (255, 215, 0))
        pad   = 8
        box_w = found_label.get_width() + pad * 2
        self._draw_hud_box(
            f"Found  {self.paintings_found}/{total}",
            (255, 215, 0),
            self.screen.get_width() - box_w - margin, margin
        )
    
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

    def open_board(self):
        if not self.board:
            return
        self.board.open_sound.play()
        self.board.open = not self.board.open
        self.player.canMove = not self.board.open

    def open_inventory(self):
        self.inventory.open_sound.play()
        self.inventory.open = not self.inventory.open
        self.player.canMove = not self.inventory.open
    
    def create_painting_ui(self, p_name):
        # Only open if board is NOT open
        if not self.board or not self.board.open:
            if p_name not in self.paintings_data:
                print(f"No data for painting: {p_name}")
                return
            img_path = self.paintings_data[p_name]["image_path"]
            try:
                # Use convert() — safe for jpg/webp/png (no alpha channel required)
                self.current_ui = PaintingUI(pygame.image.load(img_path).convert())
                self.is_viewing_painting = True
                self.player.canMove = False
                self.current_painting_name = p_name
            except (pygame.error, FileNotFoundError) as e:
                print(f"Error loading painting '{p_name}': {e}")
            
    def update(self, events):
        self.player.save_location()
        self.handle_input()

        # 1. Draw the World (Bottom Layer)
        self.group.update()
        self.group.center(self.player.rect)
        self.group.draw(self.screen)

        self.draw_stats() # Draw stats on top of the world but below the UI

        # 2. Draw World Objects (Middle Layer)
        if self.board:
            self.board.draw(self.screen)
        self.drawing_e()

        self.painting_clue.update()

        # 3. Draw the UI (Top Layer)
        # Inventory drawn before painting UI so painting UI sits on top if both open
        self.inventory.draw(self.screen)

        # We draw this LAST so it covers the player and the map
        if self.is_viewing_painting:
            pygame.mouse.set_visible(True)
            finished = self.current_ui.draw(self.screen)
            
            if finished:
                self.is_viewing_painting = False
                self.player.canMove = True
                pygame.mouse.set_visible(False) # Hide mouse when going back to walking
                
        else:
            # If not viewing a painting, make sure the mouse stays hidden
            pygame.mouse.set_visible(False)

        if self.check_collision_with_list(self.walls):
            self.player.move_back()

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()

            if event.type == pygame.KEYDOWN:   
                if event.key == pygame.K_e and not self.inventory.open:
                    # --- CASE 1: Close Painting UI ---
                    if self.is_viewing_painting:
                        self.is_viewing_painting = False
                        self.player.canMove = True
                        
                    # --- CASE 2: Board Interaction ---
                    elif self.board and self.player.feet.colliderect(self.board.rect):
                        self.open_board()

                    # --- CASE 3: Painting Interaction ---
                    else:
                        p_name = self.get_colliding_painting_name()
                        if p_name:
                            self.create_painting_ui(p_name)

                if event.key == pygame.K_q:
                    pygame.quit()
                
                if event.key == pygame.K_i:
                    self.open_inventory()

            if event.type == pygame.MOUSEBUTTONDOWN and self.is_viewing_painting:
                # This checks if they clicked the "This is it" button
                self.check_painting_choice(event.pos)

        if self.paintings_found == len(self.masterpieces):
            self.ending_the_level(["Congratulations! You've found all the masterpieces!", "Press c to return to world map..."])
            self.game.map = "world" # Return to world map after ending
            self.game.painting_level_completed = True

        if self.lives <= 0:
            self.ending_the_level(["You've lost all your lives!", "Game Over.", ";)", ":)", "                  :)"])
            self.game.map = "world" # Return to world map after ending

