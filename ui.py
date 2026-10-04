"""Pixel-art UI kit: palette, 5x7 bitmap font, panels, bars and menus.

Everything is drawn at low resolution and scaled up later, so every
rectangle here is a crisp, chunky pixel block.
"""
import pygame

# Sweetie-16 palette (a classic pixel-art palette)
BLACK = (26, 28, 44)
PURPLE = (93, 39, 93)
RED = (177, 62, 83)
ORANGE = (239, 125, 87)
YELLOW = (255, 205, 117)
LIME = (167, 240, 112)
GREEN = (56, 183, 100)
TEAL = (37, 113, 121)
NAVY = (41, 54, 111)
BLUE = (59, 93, 201)
SKY = (65, 166, 246)
CYAN = (115, 239, 247)
WHITE = (244, 244, 244)
SILVER = (148, 176, 194)
GREY = (86, 108, 134)
DARK = (51, 60, 87)

# 5x7 bitmap font, one string of 7 rows per glyph
_GLYPHS = {
    "0": "01110 10001 10011 10101 11001 10001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111",
    "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00010 01100",
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 10001 11001 10101 10011 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010",
    "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    " ": "00000 00000 00000 00000 00000 00000 00000",
    "!": "00100 00100 00100 00100 00100 00000 00100",
    "?": "01110 10001 00001 00010 00100 00000 00100",
    ".": "00000 00000 00000 00000 00000 01100 01100",
    ",": "00000 00000 00000 00000 01100 00100 01000",
    ":": "00000 01100 01100 00000 01100 01100 00000",
    "-": "00000 00000 00000 11111 00000 00000 00000",
    "+": "00000 00100 00100 11111 00100 00100 00000",
    "/": "00001 00010 00010 00100 01000 01000 10000",
    "(": "00010 00100 01000 01000 01000 00100 00010",
    ")": "01000 00100 00010 00010 00010 00100 01000",
    ">": "10000 11000 11100 11110 11100 11000 10000",  # menu cursor
}
GLYPHS = {ch: rows.split() for ch, rows in _GLYPHS.items()}
GLYPH_W, GLYPH_H = 5, 7

_cache = {}


def _render(text, color, scale):
    key = (text, color, scale)
    if key in _cache:
        return _cache[key]
    w = max(len(text) * (GLYPH_W + 1) - 1, 1)
    img = pygame.Surface((w, GLYPH_H), pygame.SRCALPHA)
    for i, ch in enumerate(text):
        for y, row in enumerate(GLYPHS.get(ch, GLYPHS["?"])):
            for x, bit in enumerate(row):
                if bit == "1":
                    img.set_at((i * (GLYPH_W + 1) + x, y), color)
    if scale > 1:
        img = pygame.transform.scale(img, (w * scale, GLYPH_H * scale))
    _cache[key] = img
    return img


def draw_text(surf, text, x, y, color=WHITE, scale=1, align="left",
              shadow=BLACK, outline=None):
    """Draw pixel text. Returns its width."""
    text = str(text).upper()
    img = _render(text, color, scale)
    w = img.get_width()
    if align == "center":
        x -= w // 2
    elif align == "right":
        x -= w
    if outline:
        edge = _render(text, outline, scale)
        surf.blit(edge, (x + scale, y + scale + 1))  # drop shadow under outline
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, -1), (1, 1), (-1, 1), (1, -1)):
            surf.blit(edge, (x + dx, y + dy))
    elif shadow:
        surf.blit(_render(text, shadow, scale), (x + scale, y + scale))
    surf.blit(img, (x, y))
    return w


def _chunky(surf, color, r):
    """Rectangle with the corner pixels cut off - the pixel-art 'rounded' rect."""
    pygame.draw.rect(surf, color, r.inflate(-2, 0))
    pygame.draw.rect(surf, color, r.inflate(0, -2))


def draw_panel(surf, rect, fill=WHITE, accent=BLUE, shadow=True):
    """Retro dialog box: hard drop shadow, dark outline, inner accent frame."""
    r = pygame.Rect(rect)
    if shadow:
        _chunky(surf, BLACK, r.move(2, 2))
    _chunky(surf, BLACK, r)
    _chunky(surf, fill, r.inflate(-2, -2))
    if accent:
        pygame.draw.rect(surf, accent, r.inflate(-6, -6), 1)
    return r


def _lighter(color, amount=60):
    return tuple(min(255, c + amount) for c in color)


def draw_bar(surf, rect, frac, color, back=DARK):
    """Segmented-look meter like an HP bar."""
    r = pygame.Rect(rect)
    _chunky(surf, BLACK, r)
    inner = r.inflate(-2, -2)
    pygame.draw.rect(surf, back, inner)
    w = int(inner.w * max(0.0, min(1.0, frac)))
    if w > 0:
        pygame.draw.rect(surf, color, (inner.x, inner.y, w, inner.h))
        pygame.draw.line(surf, _lighter(color), (inner.x, inner.y),
                         (inner.x + w - 1, inner.y))


def draw_menu(surf, items, selected, x, y, t, color=BLACK, spacing=11):
    """Pokemon-style list with a bobbing triangle cursor."""
    for i, item in enumerate(items):
        iy = y + i * spacing
        draw_text(surf, item, x + 9, iy, color, shadow=None)
        if i == selected:
            bob = int(t * 4) % 2
            draw_text(surf, ">", x + bob, iy, RED, shadow=None)


def draw_down_arrow(surf, x, y, color=RED):
    """Little 'more text' arrow for dialog boxes."""
    for i, w in enumerate((5, 3, 1)):
        pygame.draw.rect(surf, color, (x + i, y + i, w, 1))


def dim(surf, alpha=150):
    veil = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    veil.fill((*BLACK, alpha))
    surf.blit(veil, (0, 0))
