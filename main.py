import pygame

from game import Game


if __name__ == '__main__':
    pygame.init()
    pygame.mixer_music.load("music/main map music.aif")
    pygame.mixer_music.play(-1)
    game = Game()
    game.run()
