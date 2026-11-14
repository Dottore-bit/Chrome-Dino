import math
import os
import random
import sys
import pygame

pygame.init()

# Global Constants
SCREEN_HEIGHT = 600
SCREEN_WIDTH = 1100
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
NIGHT_INTERVAL = 700
NIGHT_DURATION = 200
NIGHT_FADE_DURATION = 24
NIGHT_MAX_DARKNESS = 128
MOON_SPEED = 0.5
STAR_SPEED = 1.5
STAR_LIFETIME = 6.0
HIGH_SCORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "high_score.txt")


def load_high_score():
  try:
    with open(HIGH_SCORE_PATH, encoding="utf-8") as high_score_file:
      return int(high_score_file.read().strip())
  except FileNotFoundError:
    return 0


def save_high_score():
  global high_score_needs_save
  temporary_path = HIGH_SCORE_PATH + ".tmp"
  with open(temporary_path, "w", encoding="utf-8") as high_score_file:
    high_score_file.write(f"{global_high_score}\n")
    high_score_file.flush()
    os.fsync(high_score_file.fileno())
  os.replace(temporary_path, HIGH_SCORE_PATH)
  high_score_needs_save = False


def record_high_score(score):
  global global_high_score, high_score_needs_save
  if score > global_high_score:
    global_high_score = score
    high_score_needs_save = True


global_high_score = load_high_score()
high_score_needs_save = False
RUNNING = [pygame.image.load(os.path.join("Assets/Dino", "DinoRun1.png")),
    pygame.image.load(os.path.join("Assets/Dino", "DinoRun2.png")),]
JUMPING = pygame.image.load(os.path.join("Assets/Dino", "DinoJump.png"))
DUCKING = [pygame.image.load(os.path.join("Assets/Dino", "DinoDuck1.png")),
    pygame.image.load(os.path.join("Assets/Dino", "DinoDuck2.png")),]
DEAD_DINO = pygame.image.load(os.path.join("Assets/Dino", "DinoDead.png"))

SMALL_CACTUS = [pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus1.png")),
    pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus2.png")),
    pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus3.png")),]
LARGE_CACTUS = [pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus1.png")),
    pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus2.png")),
    pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus3.png")),]

BIRD = [ pygame.image.load(os.path.join("Assets/Bird", "Bird1.png")),
    pygame.image.load(os.path.join("Assets/Bird", "Bird2.png")),]

CLOUD = pygame.image.load(os.path.join("Assets/Other", "Cloud.png"))
STARS = [
    pygame.image.load(os.path.join("Assets/Other", "Star1.png")),
    pygame.image.load(os.path.join("Assets/Other", "Star2.png")),
]
MOON = pygame.transform.scale(
    pygame.image.load(os.path.join("Assets/Other", "Moon.png")), (81, 101)
)
BG = pygame.image.load(os.path.join("Assets/Other", "Track.png"))
BG_DOUBLE = pygame.transform.scale(BG, (BG.get_width() * 2, BG.get_height() * 2))
RESET = pygame.image.load(os.path.join("Assets/Other", "Reset.png"))

JUMP_SOUND = pygame.mixer.Sound(os.path.join("Assets/Other", "jump.wav"))
DIE_SOUND = pygame.mixer.Sound(os.path.join("Assets/Other", "die.wav"))
POINTS_SOUND = pygame.mixer.Sound(os.path.join("Assets/Other", "points.wav"))

FONT_PATH = os.path.join("Assets/Other", "PressStart2P-Regular.ttf")
game_font = pygame.font.Font(FONT_PATH, 20)
game_over_font = pygame.font.Font(FONT_PATH, 22)

_subpixel_buffers = {}


def smooth_blit(target, image, x, y):
  width, height = image.get_size()
  left = math.floor(x)
  fraction = x - left
  key = id(image)
  if key not in _subpixel_buffers:
    doubled = pygame.transform.scale(image, (width * 2, height * 2))
    high_res = pygame.Surface(
        ((width + 2) * 2, height * 2), pygame.SRCALPHA
    )
    smooth = pygame.Surface((width + 2, height), pygame.SRCALPHA)
    _subpixel_buffers[key] = doubled, high_res, smooth
  doubled, high_res, smooth = _subpixel_buffers[key]
  high_res.fill((0, 0, 0, 0))
  high_res.blit(doubled, (2 + round(fraction * 2), 0))
  pygame.transform.smoothscale(
      high_res.premul_alpha(), smooth.get_size(), smooth
  )
  target.blit(smooth, (left - 1, y), special_flags=pygame.BLEND_PREMULTIPLIED)


class Dinosaur:
  X_POS = 80
  Y_POS = 310
  Y_POS_DUCK = 340
  JUMP_VEL = 8.5

  def __init__(self):
    self.duck_img = DUCKING
    self.run_img = RUNNING
    self.jump_img = JUMPING
    self.dead_img = DEAD_DINO

    self.dino_duck = False
    self.dino_run = True
    self.dino_jump = False
    self.jump_vel = self.JUMP_VEL

    self.step_index = 0.0
    self.image = self.run_img[0]
    self.dino_rect = self.image.get_rect()
    self.dino_rect.x = self.X_POS
    self.dino_rect.y = self.Y_POS

  def update(self, userInput, frame_scale):
    if self.dino_duck:
      self.duck(frame_scale)
    if self.dino_run:
      self.run(frame_scale)
    if self.dino_jump:
      self.jump(frame_scale, userInput[pygame.K_DOWN])

    if self.step_index >= 10:
      self.step_index = 0

    if userInput[pygame.K_UP] and not self.dino_jump:
      self.dino_duck = False
      self.dino_run = False
      self.dino_jump = True
      JUMP_SOUND.play()
    elif userInput[pygame.K_DOWN] and not self.dino_jump:
      self.dino_duck = True
      self.dino_run = False
      self.dino_jump = False
    elif not (self.dino_jump or userInput[pygame.K_DOWN]):
      self.dino_duck = False
      self.dino_run = True
      self.dino_jump = False

  def duck(self, frame_scale):
    self.image = self.duck_img[int(self.step_index // 5)]
    self.dino_rect = self.image.get_rect()
    self.dino_rect.x = self.X_POS
    self.dino_rect.y = self.Y_POS_DUCK
    self.step_index += frame_scale

  def run(self, frame_scale):
    self.image = self.run_img[int(self.step_index // 5)]
    self.dino_rect = self.image.get_rect()
    self.dino_rect.x = self.X_POS
    self.dino_rect.y = self.Y_POS
    self.step_index += frame_scale

  def jump(self, frame_scale, fast_fall=False):
    self.image = self.jump_img
    if self.dino_jump:
      self.dino_rect.y -= self.jump_vel * 4 * frame_scale
      gravity = 1.5 if fast_fall and self.jump_vel < 0 else 0.8
      self.jump_vel -= gravity * frame_scale
      if self.dino_rect.y >= self.Y_POS:
        self.dino_rect.y = self.Y_POS
        self.dino_jump = False
        self.jump_vel = self.JUMP_VEL

  def die(self):
    self.image = self.dead_img
    if self.dino_duck:
      self.dino_rect.y = self.Y_POS

  def draw(self, SCREEN):
    SCREEN.blit(self.image, (self.dino_rect.x, self.dino_rect.y))


class Cloud:
  SPEED_FACTOR = 0.35

  def __init__(self, x):
    self.x = float(x)
    self.y = self._random_y()
    self.image = CLOUD
    self.width = self.image.get_width()

  @staticmethod
  def _random_y():
    if random.choice((True, False)):
      return random.randint(50, 100)
    return random.randint(150, 200)

  def update(self, clouds):
    self.x -= game_speed * self.SPEED_FACTOR * frame_scale
    if self.x < -self.image.get_width():
      farthest_cloud = max(cloud.x for cloud in clouds if cloud is not self)
      self.x = farthest_cloud + random.randint(600, 1100)
      self.y = self._random_y()

  def draw(self, SCREEN):
    SCREEN.blit(self.image, (self.x, self.y))


class Obstacle:

  def __init__(self, image, type):
    self.image = image
    self.type = type
    self.rect = self.image[self.type].get_rect()
    self.x = float(SCREEN_WIDTH)
    self.rect.x = round(self.x)

  def update(self):
    self.x -= game_speed * frame_scale
    self.rect.x = round(self.x)
    if self.x < -self.rect.width:
      obstacles.remove(self)

  def draw(self, SCREEN):
    smooth_blit(SCREEN, self.image[self.type], self.x, self.rect.y)


class SmallCactus(Obstacle):

  def __init__(self, image):
    self.type = random.randint(0, 2)
    super().__init__(image, self.type)
    self.rect.y = 325


class LargeCactus(Obstacle):

  def __init__(self, image):
    self.type = random.randint(0, 2)
    super().__init__(image, self.type)
    self.rect.y = 300


class Bird(Obstacle):

  def __init__(self, image):
    self.bird_type = random.randint(0, 2)
    super().__init__(image, 0)

    if self.bird_type == 0:
      self.rect.y = 200
    elif self.bird_type == 1:
      self.rect.y = 270
    else:
      self.rect.y = 310

    self.index = 0.0

  def draw(self, SCREEN, animate=True):
    if self.index >= 9:
      self.index = 0
    smooth_blit(
        SCREEN,
        self.image[int(self.index // 5)],
        self.x,
        self.rect.y,
    )
    if animate:
      self.index += frame_scale


def main():
  global game_speed, x_pos_bg, y_pos_bg, points, obstacles, frame_scale, global_high_score
  x_pos_bg = 0
  y_pos_bg = 380
  run = True
  clock = pygame.time.Clock()
  inverted_scene = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
  ground_high_res = pygame.Surface(
      (SCREEN_WIDTH * 2, BG.get_height() * 2), pygame.SRCALPHA
  )
  ground_layer = pygame.Surface(
      (SCREEN_WIDTH, BG.get_height()), pygame.SRCALPHA
  )
  moon_x = 900.0
  stars = []
  night_active = False
  player = Dinosaur()
  clouds = [
      Cloud(random.randint(-100, SCREEN_WIDTH)),
      Cloud(random.randint(SCREEN_WIDTH + 500, SCREEN_WIDTH * 2 + 500)),
  ]
  obstacles = []
  game_speed = 20
  frame_scale = 1.0
  points = 0
  game_over = False
  last_high_score_save = pygame.time.get_ticks()
  go_reset_rect = RESET.get_rect(
      center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 55)
  )

  start_ticks = pygame.time.get_ticks()

  def score():
    global points, game_speed
    nonlocal last_high_score_save
    if not game_over:
      elapsed_time = pygame.time.get_ticks() - start_ticks
      new_points = elapsed_time // 125

      if new_points > points:
        diff = new_points - points
        points = new_points
        record_high_score(points)

        if points // 60 > (points - diff) // 60:
          game_speed *= 1.08

        if points // 100 > (points - diff) // 100 and points > 0:
          POINTS_SOUND.play()

    if high_score_needs_save and pygame.time.get_ticks() - last_high_score_save >= 1000:
      save_high_score()
      last_high_score_save = pygame.time.get_ticks()

    formatted_current = str(points).zfill(5)
    formatted_high = str(global_high_score).zfill(5)

    high_score_text = game_font.render(
        f"HI {formatted_high}", True, (150, 150, 150)
    )
    current_score_text = game_font.render(formatted_current, True, (83, 83, 83))
    spacing = game_font.size("    ")[0]
    score_group = pygame.Rect(
        0,
        0,
        high_score_text.get_width() + spacing + current_score_text.get_width(),
        max(high_score_text.get_height(), current_score_text.get_height()),
    )
    score_group.center = (910, 40)
    text_y = score_group.centery - high_score_text.get_height() // 2
    SCREEN.blit(high_score_text, (score_group.left, text_y))
    SCREEN.blit(
        current_score_text,
        (score_group.left + high_score_text.get_width() + spacing, text_y),
    )

  def background():
    global x_pos_bg, y_pos_bg
    image_width = BG.get_width()
    ground_high_res.fill((0, 0, 0, 0))
    ground_high_res.blit(BG_DOUBLE, (round(x_pos_bg * 2), 0))
    ground_high_res.blit(BG_DOUBLE, (round((image_width + x_pos_bg) * 2), 0))
    pygame.transform.smoothscale(
        ground_high_res, ground_layer.get_size(), ground_layer
    )
    SCREEN.blit(ground_layer, (0, y_pos_bg))
    if x_pos_bg <= -image_width:
      x_pos_bg += image_width
    if not game_over:
      x_pos_bg -= game_speed * frame_scale

  def create_star():
    image = random.choice(STARS)
    return [
        image,
        float(random.randint(0, SCREEN_WIDTH - image.get_width())),
        random.randint(20, 380 - image.get_height()),
        0.0,
    ]

  while run:
    elapsed_ms = clock.tick_busy_loop(120)
    frame_scale = min(elapsed_ms / (1000 / 30), 2.0)
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        record_high_score(points)
        if high_score_needs_save:
          save_high_score()
        run = False
        pygame.quit()
        sys.exit()
      if game_over and (
          event.type == pygame.KEYDOWN
          or (
              event.type == pygame.MOUSEBUTTONDOWN
              and event.button == 1
              and go_reset_rect.collidepoint(event.pos)
          )
      ):
        main()

    SCREEN.fill((255, 255, 255))
    userInput = pygame.key.get_pressed()

    background()
    night_progress = points % NIGHT_INTERVAL
    is_night = points >= NIGHT_INTERVAL and night_progress < NIGHT_DURATION
    if is_night:
      if not night_active:
        stars = [create_star() for _ in range(random.randint(2, 3))]
      night_active = True
      fade = min(
          night_progress / NIGHT_FADE_DURATION,
          (NIGHT_DURATION - night_progress) / NIGHT_FADE_DURATION,
          1.0,
      )
      fade = fade * fade * (3 - 2 * fade)
      for index, star_state in enumerate(stars):
        star, x, y, age = star_state
        if not game_over:
          x -= STAR_SPEED * frame_scale
          age += elapsed_ms / 1000
        if age >= STAR_LIFETIME or x < -star.get_width():
          stars[index] = create_star()
          star, x, y, age = stars[index]
        else:
          stars[index] = [star, x, y, age]
        star.set_alpha(round(255 * fade))
        SCREEN.blit(star, (round(x), y))
    else:
      night_active = False
    for cloud in clouds:
      cloud.draw(SCREEN)
      if not game_over:
        cloud.update(clouds)

    player.draw(SCREEN)
    if not game_over:
      player.update(userInput, frame_scale)

    spawn_spacing = 410 if points >= 850 else 350
    if ( not game_over and (len(obstacles) == 0 or obstacles[-1].rect.x < SCREEN_WIDTH - int(spawn_spacing + (game_speed * 12)))):
      if random.random() < 1 - (18 / 19) ** frame_scale:
        if points < 500:
          if random.randint(0, 1) == 0:
            obs = SmallCactus(SMALL_CACTUS)
          else:
            obs = LargeCactus(LARGE_CACTUS)
        else:
          bird_chance = 0.20 if points >= 800 else 0.17
          if random.random() < bird_chance:
            obs = Bird(BIRD)
          elif random.randint(0, 1) == 0:
            obs = SmallCactus(SMALL_CACTUS)
          else:
            obs = LargeCactus(LARGE_CACTUS)
        obstacles.append(obs)

    for obstacle in obstacles.copy():
      if isinstance(obstacle, Bird):
        obstacle.draw(SCREEN, animate=not game_over)
      else:
        obstacle.draw(SCREEN)
      if not game_over:
        obstacle.update()

      dino_hitbox = pygame.Rect(player.dino_rect.x + 22, player.dino_rect.bottom - 50, 43, 50,)
      if not game_over and dino_hitbox.colliderect(obstacle.rect):
        DIE_SOUND.play()
        player.die()
        record_high_score(points)
        if high_score_needs_save:
          save_high_score()
        game_over = True

    score()

    # Game Over Overlay
    if game_over:
      go_text = game_over_font.render("G A M E   O V E R", True, (83, 83, 83))
      go_text_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 55))
      SCREEN.blit(go_text, go_text_rect)

      SCREEN.blit(RESET, go_reset_rect)

    if is_night:
      inverted_scene.fill((255, 255, 255))
      inverted_scene.blit(SCREEN, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
      inverted_scene.set_alpha(round(255 * fade))
      SCREEN.blit(inverted_scene, (0, 0))
      if not game_over:
        moon_x -= MOON_SPEED * frame_scale
        if moon_x < -MOON.get_width():
          moon_x = SCREEN_WIDTH
      MOON.set_alpha(round(255 * fade))
      SCREEN.blit(MOON, (round(moon_x), 70))

    pygame.display.update()


main()
