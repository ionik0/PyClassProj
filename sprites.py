"""All game art, drawn from text pixel maps - no image files needed.

Each map is a list of rows; every character is one pixel and '.' is transparent.
"""
import random

import pygame

from ui import (BLACK, PURPLE, RED, ORANGE, YELLOW, LIME, GREEN, TEAL, NAVY,
                BLUE, SKY, WHITE, SILVER, GREY, DARK)

BIKE = [
    "...k...",
    "..kgk..",
    "..kgk..",
    "..kwk..",
    ".kkrkk.",
    "kgrrrgk",
    "kbhhhbk",
    "kbhHhbk",
    "kbbhbbk",
    ".kbbbk.",
    ".krrrk.",
    "..krk..",
    "..ktk..",
    "..kgk..",
    "...k...",
]
BIKE_COLORS = {"k": BLACK, "g": DARK, "w": WHITE, "r": RED, "h": YELLOW,
               "H": RED, "b": BLUE, "t": ORANGE}

CAR = [
    "..kkkkkkkk..",
    ".kwccccccwk.",
    "kcccccccccck",
    "kcccccccccck",
    "kdccccccccdk",
    "gkbbbbbbbbkg",
    "gkbllbbbbbkg",
    "gkbblbbbbbkg",
    "kdccccccccdk",
    "kdccccccccdk",
    "kdccccccccdk",
    "kdccccccccdk",
    "gkbbbbbbbbkg",
    "gkbbbbbbbbkg",
    "kdccccccccdk",
    "kcccccccccck",
    "kcccccccccck",
    "krccccccccrk",
    ".kcccccccck.",
    "..kkkkkkkk..",
]

TRUCK = [
    "..kkkkkkkk..",
    ".kwccccccwk.",
    "kcccccccccck",
    "kdccccccccdk",
    "gkbbbbbbbbkg",
    "gkbllbbbbbkg",
    "kdccccccccdk",
    "kkkkkkkkkkkk",
] + [("kXXXXXXXXXXk" if i % 5 == 4 else "kXxxxxxxxxXk") for i in range(18)] + [
    "krXXXXXXXXrk",
    ".kkkkkkkkkk.",
]

PAINTS = [(RED, PURPLE), (BLUE, NAVY), (GREEN, TEAL), (ORANGE, RED),
          (SKY, BLUE), (SILVER, GREY), (YELLOW, ORANGE)]

TREE = [
    "...kkkk...",
    ".kkllGGkk.",
    "klllGGGGGk",
    "klGGGGGGGk",
    "kGGGGGGGdk",
    "kGGGGGGddk",
    ".kGGGdddk.",
    "..kkdddk..",
    "....kk....",
]
BUSH = [
    ".kkkkk.",
    "kllGGGk",
    "kGGGGdk",
    "kGGdddk",
    ".kkkkk.",
]
ROCK = [".kkk.", "kwsgk", "ksggk", ".kkk."]
FLOWER = [".y.", "yry", ".y."]
NATURE_COLORS = {"k": BLACK, "l": LIME, "G": GREEN, "d": TEAL, "w": WHITE,
                 "s": SILVER, "g": GREY, "y": YELLOW, "r": RED}


def make_sprite(rows, colors):
    img = pygame.Surface((len(rows[0]), len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                img.set_at((x, y), colors[ch])
    return img


def shadow_of(img):
    return pygame.mask.from_surface(img).to_surface(
        setcolor=(0, 0, 0, 90), unsetcolor=(0, 0, 0, 0))


def with_shadow(img):
    return img, shadow_of(img)


def make_ground(width, road_l, road_r, height=32):
    """A vertically tileable strip: grass on both sides, asphalt in the middle."""
    rng = random.Random(7)
    s = pygame.Surface((width, height))
    s.fill(GREEN)
    pygame.draw.rect(s, DARK, (road_l, 0, road_r - road_l, height))
    for _ in range(70):  # grass tufts
        x, y = rng.randrange(1, width - 1), rng.randrange(height)
        if road_l - 4 <= x <= road_r + 3:
            continue
        if rng.random() < 0.6:
            s.set_at((x, y), LIME)
            s.set_at((x - 1, (y - 1) % height), LIME)
            s.set_at((x + 1, (y - 1) % height), LIME)
        else:
            s.set_at((x, y), TEAL)
    for _ in range(45):  # asphalt specks
        x, y = rng.randrange(road_l, road_r), rng.randrange(height)
        s.set_at((x, y), rng.choice((GREY, NAVY, BLACK)))
    return s


def load(width, road_l, road_r):
    bike = make_sprite(BIKE, BIKE_COLORS)
    art = {
        "bike": with_shadow(bike),
        "bike_lean": {
            -1: with_shadow(pygame.transform.rotate(bike, 12)),
            0: with_shadow(bike),
            1: with_shadow(pygame.transform.rotate(bike, -12)),
        },
        "bike_fallen": with_shadow(pygame.transform.rotate(bike, 75)),
        "cars": [],
        "trucks": [],
        "ground": make_ground(width, road_l, road_r),
    }
    for main, shade in PAINTS:
        colors = {"k": BLACK, "w": YELLOW, "c": main, "d": shade, "b": NAVY,
                  "l": SKY, "g": DARK, "r": RED, "x": WHITE, "X": SILVER}
        art["cars"].append(with_shadow(make_sprite(CAR, colors)))
        art["trucks"].append(with_shadow(make_sprite(TRUCK, colors)))
    for name, rows in (("tree", TREE), ("bush", BUSH), ("rock", ROCK),
                       ("flower", FLOWER)):
        art[name] = with_shadow(make_sprite(rows, NATURE_COLORS))
    white = dict(NATURE_COLORS, y=WHITE, r=YELLOW)
    art["flower2"] = with_shadow(make_sprite(FLOWER, white))

    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
    icon.blit(pygame.transform.scale(bike, (14, 30)), (9, 1))
    art["icon"] = icon
    return art
