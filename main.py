import pygame

from game import Game


if __name__ == '__main__':
    pygame.init()
    """pygame.mixer_music.load("music/pottery level music.aif")
    pygame.mixer_music.play(-1)
    pygame.mixer_music.set_volume(0.5)"""
    game = Game()
    game.run()
