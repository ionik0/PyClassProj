"""Pixel Rider - scenes (menu, how-to, countdown, play, pause, game over)."""
import math
import os
import random

import pygame

import sprites
from ui import (BLACK, RED, ORANGE, YELLOW, LIME, NAVY, BLUE, WHITE, SILVER,
                GREY, draw_text, draw_panel, draw_bar, draw_menu,
                draw_down_arrow, dim)

# The game is drawn on a tiny 160x224 canvas, then scaled up 3x for crisp pixels
W, H = 160, 224
SCALE = 3
FPS = 60

ROAD_L, ROAD_R = 24, 136
LANES = 4
LANE_W = (ROAD_R - ROAD_L) // LANES

MIN_SPEED = 100      # all speeds in canvas pixels per second
CRUISE_SPEED = 150
START_MAX = 250      # top speed at the start...
TOP_MAX = 350        # ...rising to this as you travel further
KMH = 0.6            # pixels/s -> km/h shown on the speedometer
PX_PER_M = 6
X2_KMH = 120         # ride faster than this for double points

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.txt")

HOWTO_LINES = [
    "LEFT/RIGHT : STEER",
    "UP         : THROTTLE",
    "DOWN       : BRAKE",
    "P / ESC    : PAUSE",
    "(WASD WORKS TOO)",
    "",
    "WEAVE PAST TRAFFIC.",
    "PASS CLOSE FOR BONUS!",
    "120+ KM/H = X2 POINTS",
]


def lane_center(lane):
    return ROAD_L + LANE_W * lane + LANE_W // 2


def load_best():
    try:
        with open(SAVE_FILE) as f:
            return int(f.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def save_best(score):
    try:
        with open(SAVE_FILE, "w") as f:
            f.write(str(score))
    except OSError:
        pass


class Vehicle:
    def __init__(self, lane, art, speed):
        self.lane = lane
        self.img, self.shadow = art
        self.w, self.h = self.img.get_size()
        self.x = float(lane_center(lane) - self.w // 2)
        self.target_x = self.x
        self.y = float(-self.h - 2)
        self.speed = speed
        self.signal = 0.0      # indicator time left before a lane change
        self.turn = 0          # -1 left, 1 right, 0 straight
        self.min_gap = 99      # closest the player got while side by side
        self.passed = False

    @property
    def rect(self):
        return pygame.Rect(int(self.x) + 1, int(self.y) + 1, self.w - 2, self.h - 2)

    def steer(self, dt):
        if self.signal > 0:
            self.signal -= dt
            return
        d = self.target_x - self.x
        step = 22 * dt
        if abs(d) <= step:
            self.x = self.target_x
            self.turn = 0
        else:
            self.x += step if d > 0 else -step


class Player:
    def __init__(self, art):
        img = art[0]
        self.w, self.h = img.get_size()
        self.x = float((ROAD_L + ROAD_R) // 2 - self.w // 2)
        self.y = H - 44
        self.speed = 0.0
        self.lean = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x) + 1, self.y + 1, self.w - 2, self.h - 2)


class Game:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((W * SCALE, H * SCALE))
        pygame.display.set_caption("Pixel Rider")
        self.screen = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.art = sprites.load(W, ROAD_L, ROAD_R)
        pygame.display.set_icon(self.art["icon"])
        self.best = load_best()
        self.t = 0.0
        self.state = "menu"
        self.sel = 0
        self.howto_t = 0.0
        self.reset()

    # ------------------------------------------------------------ setup
    def reset(self):
        self.player = Player(self.art["bike"])
        self.vehicles = []
        self.decos = []
        self.particles = []
        self.popups = []
        self.scroll = 0.0
        self.distance = 0.0
        self.points = 0.0
        self.bonus = 0
        self.spawn_acc = 0.0
        self.next_gap = 80.0
        self.deco_acc = 0.0
        self.shake = 0.0
        self.timer = 0.0
        self.go_timer = 0.0
        self.new_best = False
        for y in range(-10, H, 14):
            self.spawn_deco(y)

    def start(self):
        self.reset()
        self.state = "countdown"
        self.timer = 3.0

    def to_menu(self):
        self.reset()
        self.state = "menu"
        self.sel = 0

    @property
    def progress(self):
        return min(1.0, self.distance / 4000)

    @property
    def max_speed(self):
        return START_MAX + (TOP_MAX - START_MAX) * self.progress

    @property
    def score(self):
        return int(self.points) + self.bonus

    # ------------------------------------------------------------ loop
    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000, 1 / 20)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and self.on_key(event.key) == "quit":
                    return
            self.update(dt)
            self.draw()

    def on_key(self, key):
        up = key in (pygame.K_UP, pygame.K_w)
        down = key in (pygame.K_DOWN, pygame.K_s)
        ok = key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)
        back = key == pygame.K_ESCAPE
        st = self.state

        if st == "menu":
            if up or down:
                self.sel = (self.sel + (1 if down else -1)) % 3
            elif ok:
                if self.sel == 0:
                    self.start()
                elif self.sel == 1:
                    self.state = "howto"
                    self.howto_t = 0.0
                else:
                    return "quit"
            elif back:
                return "quit"
        elif st == "howto":
            if ok or back:
                if self.howto_chars() < sum(len(l) for l in HOWTO_LINES):
                    self.howto_t = 99.0          # skip the typewriter
                else:
                    self.state = "menu"
        elif st == "play":
            if back or key == pygame.K_p:
                self.state = "pause"
                self.sel = 0
        elif st == "pause":
            if back or key == pygame.K_p:
                self.state = "play"
            elif up or down:
                self.sel ^= 1
            elif ok:
                if self.sel == 0:
                    self.state = "play"
                else:
                    self.to_menu()
        elif st == "over":
            if up or down:
                self.sel ^= 1
            elif ok:
                if self.sel == 0:
                    self.start()
                else:
                    self.to_menu()
            elif back:
                self.to_menu()
        return None

    # ------------------------------------------------------------ update
    def update(self, dt):
        self.t += dt
        self.shake = max(0.0, self.shake - dt)
        st = self.state
        if st in ("menu", "howto"):
            self.scroll_world(110 * dt)
            self.howto_t += dt
        elif st == "countdown":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "play"
                self.player.speed = CRUISE_SPEED
                self.go_timer = 0.8
        elif st == "play":
            self.update_play(dt)
        elif st == "crash":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "over"
                self.sel = 0
        if st != "pause":
            self.update_fx(dt)

    def scroll_world(self, move):
        self.scroll += move
        for d in self.decos:
            d[1] += move
        self.decos = [d for d in self.decos if d[1] < H + 4]
        self.deco_acc += move
        if self.deco_acc > 14:
            self.deco_acc = 0.0
            self.spawn_deco(-14)

    def spawn_deco(self, y):
        kind = random.choices(("tree", "bush", "rock", "flower", "flower2"),
                              weights=(4, 3, 1, 3, 2))[0]
        img, shadow = self.art[kind]
        if random.random() < 0.5:
            x = random.randint(0, ROAD_L - 4 - img.get_width())
        else:
            x = random.randint(ROAD_R + 4, W - img.get_width())
        self.decos.append([x, float(y), img, shadow])

    def spawn_traffic(self):
        lanes = list(range(LANES))
        random.shuffle(lanes)
        count = 2 if random.random() < 0.15 + 0.35 * self.progress else 1
        for lane in lanes:
            if count == 0:
                break
            if any(v.lane == lane and v.y < 10 for v in self.vehicles):
                continue  # lane entrance still busy
            pool = self.art["trucks"] if random.random() < 0.2 else self.art["cars"]
            self.vehicles.append(Vehicle(lane, random.choice(pool),
                                         random.uniform(40, 100)))
            count -= 1

    def update_play(self, dt):
        p = self.player
        keys = pygame.key.get_pressed()
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        gas = keys[pygame.K_UP] or keys[pygame.K_w]
        brake = keys[pygame.K_DOWN] or keys[pygame.K_s]

        if gas:
            p.speed += 90 * dt
        elif brake:
            p.speed -= 160 * dt
        else:  # let go of the throttle: drift back to cruising speed
            p.speed += (CRUISE_SPEED - p.speed) * min(1.0, 0.6 * dt)
        p.speed = max(MIN_SPEED, min(self.max_speed, p.speed))

        p.lean = int(right) - int(left)
        p.x += p.lean * (55 + p.speed * 0.2) * dt
        p.x = max(ROAD_L + 1, min(ROAD_R - p.w - 1, p.x))

        move = p.speed * dt
        self.scroll_world(move)
        metres = move / PX_PER_M
        kmh = p.speed * KMH
        self.distance += metres
        self.points += metres * (2 if kmh >= X2_KMH else 1)
        self.go_timer -= dt

        self.spawn_acc += move
        if self.spawn_acc >= self.next_gap:
            self.spawn_acc = 0.0
            self.spawn_traffic()
            self.next_gap = random.uniform(55, 110) * (1 - 0.45 * self.progress)

        pr = p.rect
        for v in self.vehicles:
            # don't rear-end the car in front: match its speed when close
            ahead = [o for o in self.vehicles if o.lane == v.lane and o.y > v.y]
            if ahead:
                nxt = min(ahead, key=lambda o: o.y)
                if nxt.y - (v.y + v.h) < 12:
                    v.speed = max(v.speed, nxt.speed)
            v.y += (p.speed - v.speed) * dt
            self.maybe_change_lane(v, dt)
            v.steer(dt)

            vr = v.rect
            if vr.colliderect(pr):
                self.crash()
                return
            if vr.bottom > pr.top and vr.top < pr.bottom:
                gap = max(vr.left - pr.right, pr.left - vr.right)
                v.min_gap = min(v.min_gap, gap)
            elif not v.passed and vr.top >= pr.bottom:
                v.passed = True
                if v.min_gap <= 5:
                    gain = 25 + int(kmh / 2)
                    self.bonus += gain
                    x = max(32, min(W - 32, p.x + p.w / 2))
                    self.popups.append(["CLOSE! +%d" % gain, x, p.y - 8, 1.0, YELLOW])
        self.vehicles = [v for v in self.vehicles if v.y < H + 4]

    def maybe_change_lane(self, v, dt):
        """Cars sometimes signal and switch lanes - no lane line is ever safe."""
        if v.turn or not 0 < v.y < H * 0.45:
            return
        if random.random() > (0.15 + 0.35 * self.progress) * dt:
            return
        new = v.lane + random.choice((-1, 1))
        if not 0 <= new < LANES:
            return
        if any(o is not v and o.lane == new and abs(o.y - v.y) < 40
               for o in self.vehicles):
            return
        v.turn = 1 if new > v.lane else -1
        v.lane = new
        v.target_x = float(lane_center(new) - v.w // 2)
        v.signal = 0.6

    def crash(self):
        p = self.player
        self.state = "crash"
        self.timer = 1.3
        self.shake = 0.5
        cx, cy = p.x + p.w / 2, p.y + p.h / 2
        for _ in range(40):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(20, 90)
            self.particles.append([cx, cy, math.cos(ang) * spd, math.sin(ang) * spd,
                                   random.uniform(0.5, 1.2),
                                   random.choice((YELLOW, ORANGE, RED, WHITE, GREY)),
                                   random.choice((1, 2, 2, 3))])
        if self.score > self.best:
            self.best = self.score
            self.new_best = True
            save_best(self.best)

    def update_fx(self, dt):
        drag = max(0.0, 1 - 3 * dt)
        for pt in self.particles:
            pt[0] += pt[2] * dt
            pt[1] += pt[3] * dt
            pt[2] *= drag
            pt[3] *= drag
            pt[4] -= dt
        self.particles = [pt for pt in self.particles if pt[4] > 0]
        for pop in self.popups:
            pop[2] -= 14 * dt
            pop[3] -= dt
        self.popups = [pop for pop in self.popups if pop[3] > 0]

    def howto_chars(self):
        return int(self.howto_t * 40)

    # ------------------------------------------------------------ draw
    def draw(self):
        s = self.screen
        self.draw_world(s)
        st = self.state
        if st == "menu":
            self.draw_menu(s)
        elif st == "howto":
            self.draw_howto(s)
        else:
            self.draw_hud(s)
            if st == "countdown":
                n = math.ceil(self.timer)
                draw_text(s, n, W // 2, H // 2 - 30, YELLOW, scale=4,
                          align="center", outline=BLACK)
                draw_text(s, "GET READY", W // 2, H // 2 + 4, WHITE, align="center")
            elif st == "play" and self.go_timer > 0:
                draw_text(s, "GO!", W // 2, H // 2 - 30, LIME, scale=4,
                          align="center", outline=BLACK)
            elif st == "pause":
                self.draw_pause(s)
            elif st == "over":
                self.draw_over(s)

        ox = oy = 0
        if self.shake > 0:
            ox, oy = random.randint(-2, 2), random.randint(-2, 2)
        self.window.fill(BLACK)
        self.window.blit(pygame.transform.scale(s, (W * SCALE, H * SCALE)),
                         (ox * SCALE, oy * SCALE))
        pygame.display.flip()

    def draw_world(self, s):
        ground = self.art["ground"]
        gh = ground.get_height()
        off = int(self.scroll) % gh
        for y in range(off - gh, H, gh):
            s.blit(ground, (0, y))

        off = int(self.scroll) % 16          # red/white kerbs
        for y in range(off - 16, H, 16):
            for x in (ROAD_L - 3, ROAD_R):
                pygame.draw.rect(s, RED, (x, y, 3, 8))
                pygame.draw.rect(s, WHITE, (x, y + 8, 3, 8))

        off = int(self.scroll) % 24          # lane dashes
        for lane in range(1, LANES):
            x = ROAD_L + lane * LANE_W - 1
            for y in range(off - 24, H, 24):
                pygame.draw.rect(s, SILVER, (x, y, 2, 12))

        for x, y, img, shadow in sorted(self.decos, key=lambda d: d[1]):
            s.blit(shadow, (x + 1, int(y) + 2))
            s.blit(img, (x, int(y)))

        for v in self.vehicles:
            s.blit(v.shadow, (v.x + 1, int(v.y) + 2))
            s.blit(v.img, (v.x, int(v.y)))
            if v.turn and int(self.t * 6) % 2 == 0:   # blinking indicators
                bx = int(v.x) - 1 if v.turn < 0 else int(v.x) + v.w - 1
                for by in (int(v.y) + 1, int(v.y) + v.h - 3):
                    pygame.draw.rect(s, ORANGE, (bx, by, 2, 2))

        p = self.player
        if self.state in ("crash", "over"):
            img, shadow = self.art["bike_fallen"]
        else:
            img, shadow = self.art["bike_lean"][p.lean]
        x = int(p.x) + p.w // 2 - img.get_width() // 2
        y = p.y + p.h // 2 - img.get_height() // 2
        s.blit(shadow, (x + 1, y + 2))
        s.blit(img, (x, y))

        for x, y, _, _, _, color, size in self.particles:
            pygame.draw.rect(s, color, (int(x), int(y), size, size))
        for text, x, y, _, color in self.popups:
            draw_text(s, text, int(x), int(y), color, align="center")

    def draw_hud(self, s):
        p = self.player
        draw_panel(s, (2, 2, W - 4, 15), fill=NAVY, accent=None)
        draw_text(s, "SCORE %06d" % self.score, 7, 6, WHITE)
        draw_text(s, "%.1fKM" % (self.distance / 1000), W - 7, 6, YELLOW, align="right")

        kmh = int(p.speed * KMH)
        draw_panel(s, (2, H - 22, 62, 20), fill=NAVY, accent=None)
        draw_text(s, "%3d KM/H" % kmh, 7, H - 18, WHITE)
        frac = (p.speed - MIN_SPEED) / (TOP_MAX - MIN_SPEED)
        color = LIME if kmh < X2_KMH else (YELLOW if kmh < 170 else RED)
        draw_bar(s, (6, H - 10, 54, 5), frac, color)
        if kmh >= X2_KMH and self.state == "play" and int(self.t * 4) % 2 == 0:
            draw_panel(s, (68, H - 20, 20, 15), fill=ORANGE, accent=None)
            draw_text(s, "X2", 78, H - 16, WHITE, align="center")

    def draw_menu(self, s):
        bob = int(math.sin(self.t * 3) * 2)
        draw_text(s, "PIXEL", W // 2, 20 + bob, YELLOW, scale=3, align="center", outline=BLACK)
        draw_text(s, "RIDER", W // 2, 44 + bob, ORANGE, scale=3, align="center", outline=BLACK)
        draw_text(s, "BEST %06d" % self.best, W // 2, 74, WHITE, align="center")

        draw_panel(s, (36, 90, 88, 44), fill=WHITE, accent=BLUE)
        draw_menu(s, ("START", "HOW TO", "QUIT"), self.sel, 46, 98, self.t)
        if int(self.t * 2) % 2 == 0:
            draw_text(s, "PRESS ENTER", W // 2, 144, WHITE, align="center")

    def draw_howto(self, s):
        dim(s, 90)
        draw_panel(s, (6, 30, 148, 150), fill=WHITE, accent=BLUE)
        draw_panel(s, (14, 20, 78, 16), fill=YELLOW, accent=None)
        draw_text(s, "HOW TO PLAY", 53, 25, BLACK, align="center", shadow=None)

        left = self.howto_chars()
        y = 44
        for line in HOWTO_LINES:
            shown = line[:max(0, left)]
            left -= len(line)
            if shown:
                draw_text(s, shown, 14, y, BLACK, shadow=None)
            y += 12
        if left >= 0 and int(self.t * 3) % 2 == 0:
            draw_down_arrow(s, 142, 168)

    def draw_pause(self, s):
        dim(s)
        draw_panel(s, (30, 76, 100, 62), fill=WHITE, accent=BLUE)
        draw_text(s, "PAUSED", W // 2, 86, NAVY, scale=2, align="center", shadow=None)
        draw_menu(s, ("RESUME", "MENU"), self.sel, 50, 108, self.t)

    def draw_over(self, s):
        dim(s)
        draw_panel(s, (14, 44, 132, 130), fill=WHITE, accent=BLUE)
        draw_text(s, "CRASHED!", W // 2, 54, RED, scale=2, align="center")
        rows = (("SCORE", "%d" % self.score),
                ("DIST", "%.2f KM" % (self.distance / 1000)),
                ("BEST", "%d" % self.best))
        for i, (label, value) in enumerate(rows):
            y = 78 + i * 12
            draw_text(s, label, 26, y, GREY, shadow=None)
            draw_text(s, value, W - 26, y, BLACK, align="right", shadow=None)
        if self.new_best and int(self.t * 3) % 2 == 0:
            draw_text(s, "NEW BEST!", W // 2, 116, ORANGE, align="center")
        draw_menu(s, ("RETRY", "MENU"), self.sel, 54, 134, self.t)
