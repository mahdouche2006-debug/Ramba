import pygame
import pytmx
import pyscroll
import game

from player import Player
from item import Item
from timer import CountdownTimer


class Level1:
    def __init__(self):
        # cree la fenetre du jeu
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("RAMBA")

        # charger la carte (tmx)
        tmx_data = pytmx.util_pygame.load_pygame('one chamber.tmx')
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 3

        # generer un joueur
        player_position = tmx_data.get_object_by_name("player")
        self.player = Player(player_position.x, player_position.y)
        
        # dessiner le groupe de calque
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=3)
        self.group.add(self.player) 

        self.e_image = pygame.image.load("images/e.png").convert_alpha()
        
        # lists
        self.walls = []
        self.items = []

        for obj in tmx_data.objects:

            if obj.type == "obj":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

            elif obj.type == "item":
                has_item = (obj.name == "wood_chest")
                item = Item(obj.name, obj.x, obj.y, has_item)

                self.items.append(item)
                self.group.add(item)     
        
        self.group.change_layer(self.player, 4)  # Assure que le joueur est au-dessus des items et des murs

        # counter for items collected
        self.items_collected = 0

        # timer creation
        self.timer = CountdownTimer(10)

        # font
        self.font = pygame.font.SysFont(None, 70)
        
    def handle_input(self):
        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        # prevent movement while attacking
        if self.player.attacking:
            self.player.animate()
            return

        self.player.walking = False

        # attack key
        if keys[pygame.K_e]:
            self.player.attacking = True
            self.player.frame_index = 0
            self.player.animate()
            return

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
    
    def remove_item(self, item):
        self.group.remove(item)
        self.items.remove(item)

    def get_colliding_item(self, list):
        for item in list:
            if self.player.feet.colliderect(item.rect):
                return item
        return None
    
    def draw_counter(self):
        text = self.font.render(f"{self.items_collected}/10", True, (255, 255, 255))
        self.screen.blit(text, (self.screen.get_width()*92/100, 0))

    def ending_the_level(self, message):
        paused = True
        text = self.font.render(message, True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
        while paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    paused = False
                elif event.type == pygame.KEYDOWN:
                    paused = False

            self.screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.delay(2000)  # Affiche le message pendant 2 secondes
            paused = False

    def run(self):
        self.player.save_location()
        self.handle_input()

        self.group.update()
        self.group.center(self.player.rect)
        self.group.draw(self.screen)
        self.draw_counter()

        self.timer.update()
        self.timer.draw(self.screen)

        if self.get_colliding_item(self.items):
            self.screen.blit(self.e_image, (self.screen.get_width() - self.e_image.get_width(), self.screen.get_height() - self.e_image.get_height()))


        for event in pygame.event.get():

            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                pygame.quit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                item = self.get_colliding_item(self.items)

                if item:
                    if item.name == "apple":
                        self.items_collected += 1
                        self.remove_item(item)

                    elif item.name == "wood_chest":
                        if item.has_item:
                            new_apple = Item("apple", item.rect.x, item.rect.y)
                            self.items.append(new_apple)
                            self.group.add(new_apple)

                        self.remove_item(item)

        
        # return to world when all items are collected
        if self.items_collected == 4:
            self.ending_the_level("You found all the items! Returning to world map...")
            game.Game().map = "world"
            game.Game().run() # Return to world map (adjust as needed)

        if self.timer.remaining_time <= 0:
            self.ending_the_level("Time's up! Returning to world map...")
            game.Game().map = "world"
            game.Game().run() # Return to world map (adjust as needed)
