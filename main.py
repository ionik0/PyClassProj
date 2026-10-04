"""Pixel Rider - a tiny retro traffic-dodging game.

Run:  python main.py
"""
import pygame

from game import Game


def main():
    Game().run()
    pygame.quit()


if __name__ == "__main__":
    main()
