import pygame


class AnimateSprite(pygame.sprite.Sprite):
    def __init__(self, sprite_name):
        super().__init__()

        # animation speed (bigger = slower)
        self.animation_speed = 5

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
            ]
        }


        # default state
        self.direction = "down"
        self.walking = False
        self.frame_index = 0

        self.image = self.animations[self.direction][0]
        self.rect = self.image.get_rect()


    def animate(self):
        if self.walking:
            self.frame_index += 1

            frames = self.animations[self.direction]
            max_frames = len(frames) * self.animation_speed

            if self.frame_index >= max_frames:
                self.frame_index = 0

            self.image = frames[self.frame_index // self.animation_speed]

        else:
            # standing still → first frame of direction
            self.frame_index = 0
            self.image = self.animations[self.direction][1]

    def load_image(self, path):
        image = pygame.image.load(path).convert()
        image.set_colorkey((255, 255, 255))
        return image
