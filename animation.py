import pygame
import random


class AnimateSprite(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        # animation speed (bigger = slower)
        self.animation_speed = 5

        # load sound effects
        self.walk_sounds = [
            pygame.mixer.Sound("music/grassWalk1.wav"),
            pygame.mixer.Sound("music/grassWalk2.wav"),
            pygame.mixer.Sound("music/grassWalk3.wav")
        ]
        
        # Set volume for all sounds in the list
        for sound in self.walk_sounds:
            sound.set_volume(0.3)

        """self.open_sfx = pygame.mixer.Sound("music/Chest_Open.wav")
        self.open_sfx.set_volume(0.3)"""

        # load animations
        self.animations = {
            "left": [
                self.load_image("player/playerleft2.png"),
                self.load_image("player/player_stop_left.png"),
                self.load_image("player/playerleft1.png"),
                self.load_image("player/player_stop_left.png")
            ],
            "right": [
                self.load_image("player/playerright2.png"),
                self.load_image("player/player_stop_right.png"),
                self.load_image("player/playerright1.png"),
                self.load_image("player/player_stop_right.png")
            ],
            "up": [
                self.load_image("player/playerup1.png"),
                self.load_image("player/player_stop_up.png"),
                self.load_image("player/playerup2.png"),
                self.load_image("player/player_stop_up.png")
            ],
            "down": [
                self.load_image("player/playerdown1.png"),
                self.load_image("player/player_stop_down.png"),
                self.load_image("player/playerdown2.png"),
                self.load_image("player/player_stop_down.png")
            ],
            "attack_right": [
                self.load_image("player/player_strike_side 1.png"),
                self.load_image("player/player_strike_side 2.png"),
                self.load_image("player/player_strike_side 3.png")
            ],
            "attack_left": [
                pygame.transform.flip(self.load_image("player/player_strike_side 1.png"), True, False),
                pygame.transform.flip(self.load_image("player/player_strike_side 2.png"), True, False),
                pygame.transform.flip(self.load_image("player/player_strike_side 3.png"), True, False),
            ],
            "attack_up": [
                self.load_image("player/player_strike_up 1.png"),
                self.load_image("player/player_strike_up 2.png"),
            ],
            "attack_down": [
                self.load_image("player/player_strike_down 1.png"),
                self.load_image("player/player_strike_down 2.png"),
            ]
        }


        # default state
        self.direction = "down"
        self.walking = False
        self.frame_index = 0
        self.attacking = False
        self.attack_finished = False

        self.image = self.animations[self.direction][0]
        self.rect = self.image.get_rect()


    def animate(self):

        # 🔴 ATTACK animation has priority
        if self.attacking:
            frames = self.animations[f"attack_{self.direction}"]

            self.frame_index += 1
            max_frames = len(frames) * self.animation_speed

            # self.open_sfx.play()

            if self.frame_index >= max_frames:
                self.frame_index = 0
                self.attacking = False   # stop attacking after animation
                return

            self.image = frames[self.frame_index // self.animation_speed]
            return


        # 🟢 WALK animation
        if self.walking:
            frames = self.animations[self.direction]

            self.frame_index += 1
            max_frames = len(frames) * self.animation_speed

            if self.frame_index % max_frames == 1:
                random_step = random.choice(self.walk_sounds)
                random_step.play()

            if self.frame_index >= max_frames:
                self.frame_index = 0

            self.image = frames[self.frame_index // self.animation_speed]

        # ⚪ IDLE
        else:
            self.frame_index = 0
            self.image = self.animations[self.direction][1]

    def load_image(self, path):
        image = pygame.image.load(path).convert()
        image.set_colorkey((255, 255, 255))
        return image
