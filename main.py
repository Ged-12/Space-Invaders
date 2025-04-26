import sys
import pygame
from random import choice

# Initialize Pygame
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()
pygame.init()

# Define constants
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
FPS = 60
ALIEN_COOLDOWN = 1000   # Alien bullet cooldown in milliseconds
ALIEN_SPEED = 1         # Alien movement speed aka number of pixel per movement
ALIENS_MAXBULLETS = 4   # Aliens max bullets presence in a instant
PLAYER_COOLDOWN = 500   # Player bullet cooldown in milliseconds
PLAYER_SPEED = 6        # Spaceship movement speed aka number of pixel per movement
AREA_LIMIT = 160        # Play area left limit
EXPLOSION_SPEED = 3     # Explosion animation speed
MAX_POINTS_FEED = 8     # Max points viewable in the feed section

# Initialize game variables
clock = pygame.time.Clock()
last_alien_shot = pygame.time.get_ticks()
player_score = 0
player_lives = 3
player_waves = 1
rows = 5                # Number of enemy rows
cols = 5                # Number of enemy cols
feed_points = [0, ""]   # Feed tuple with counter and text message for the feed section 

# Define scores for each enemy type by using a dict[int,int]
enemy_scores = {
    4: 10,   # FirstEnemy
    3: 20,   # SecondEnemy
    2: 75,   # ThirdEnemy
    1: 150,  # FourthEnemy
    0: 250   # FifthEnemy
}

# Set up the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders")

# Define fonts
font30 = pygame.font.SysFont('Constantia', 30)
font40 = pygame.font.SysFont('Constantia', 40)

# Load sounds
explosion_fx = pygame.mixer.Sound("sounds/explosion.wav")
explosion_fx.set_volume(0.25)
explosion2_fx = pygame.mixer.Sound("sounds/explosion2.wav")
explosion2_fx.set_volume(0.25)
laser_fx = pygame.mixer.Sound("sounds/laser.wav")
laser_fx.set_volume(0.25)

# Load background image
bg = pygame.transform.scale(pygame.image.load("img/bg.png"), (SCREEN_WIDTH, SCREEN_HEIGHT))

# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Create sprite groups
spaceship_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
alien_group = pygame.sprite.Group()
alien_bullet_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()

# Create Explosion class
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, size):
        super().__init__()
        self.images = [pygame.transform.scale(pygame.image.load(f"img/exp{num}.png"), (20 * size, 20 * size)) for num in range(1, 6)]   # Loads explosion animation image
        self.counter = 0
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect(center=(x, y))  # Creates a rectangular area with center in x,y

    # Animation update
    def update(self):
        self.counter += 1
        if self.counter >= EXPLOSION_SPEED and self.index < len(self.images) - 1:
            self.counter = 0
            self.index += 1
            self.image = self.images[self.index]    # Changes the image
        if self.index >= len(self.images) - 1 and self.counter >= EXPLOSION_SPEED:
            self.kill() # After executing the animation kill object

# Create Bullets class
class Bullets(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("img/bullet.png")    # Loads bullet image
        self.rect = self.image.get_rect(center=(x, y))      # Creates a rectangular area with center in x,y

    # Bullet movement and collision
    def update(self):
        self.rect.y -= 5    # Modifies bullet posion to go up  
        if self.rect.bottom < 0:    # If bullet arrives at the top of the screen 
            self.kill() # Kill object
        hit_aliens = pygame.sprite.spritecollide(self, alien_group, True)   # Check for collision with aliens
        if hit_aliens:
            self.kill() # Kill object
            explosion_fx.play() # Plays explosion sound
            explosion = Explosion(self.rect.centerx, self.rect.centery, 2)  # Creates explosion
            explosion_group.add(explosion)  # Adds explosion in sprite group 
            for alien in hit_aliens:    # Check which alien was hit
                global player_score, feed_points # Declares as global score and feed message
                player_score += enemy_scores[alien.type]  # Update score based on enemy type
                if MAX_POINTS_FEED == feed_points[0]:   # If feed message reaches max, resets and add last score
                    feed_points[0] = 1
                    feed_points[1] = f"+{enemy_scores[alien.type]}\n"
                else:
                    feed_points[0] += 1
                    feed_points[1] += f"+{enemy_scores[alien.type]}\n"

# Create spaceship class
class Spaceship(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("img/spaceship.png") # Loads spaceship image
        self.rect = self.image.get_rect(center=(x, y))      # Creates a rectangular area with center in x,y
        self.last_shot = pygame.time.get_ticks()

    def update(self):

        key = pygame.key.get_pressed() # Retrieves the current state of all keyboard keys

        # Movement logic
        if key[pygame.K_LEFT] and self.rect.left > AREA_LIMIT: # Check if the player presses left limit at 180
            self.rect.x -= PLAYER_SPEED    # Moves left by speed
        if key[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:  # Check if the player presses right limit at SCREEN_WIDTH
            self.rect.x += PLAYER_SPEED    # Moves right by speed

        # Shooting logic
        time_now = pygame.time.get_ticks()  # Retrieves current time
        if key[pygame.K_SPACE] and time_now - self.last_shot > PLAYER_COOLDOWN: # Check if the player presses space to shoot and verify if the cooldown is fulfilled
            laser_fx.play()                 # Plays laser sound
            bullet = Bullets(self.rect.centerx, self.rect.top)  # Creates bullet from the top of the rectangular object
            bullet_group.add(bullet)    # Adds bullet to sprite group
            self.last_shot = time_now   # Saves last shot time


# Create Aliens class
class Aliens(pygame.sprite.Sprite):
    def __init__(self, x, y, type):
        super().__init__()
        self.type = type  # Acquire type of enemy
        self.image = pygame.transform.scale(pygame.image.load(f'img/Enemy{type + 1}.png'), (50, 50))  # Load alien image
        self.rect = self.image.get_rect(center=(x, y))  # Creates a rectangular area with center in x,y
        self.move_direction = 1  # 1 for right, -1 for left
        self.move_counter = 0  # Track movement distance

    def update(self):
        self.rect.x += self.move_direction * ALIEN_SPEED
        self.move_counter += ALIEN_SPEED

        # Change direction if the limit is reached
        if self.move_counter <= -AREA_LIMIT or self.move_counter >= AREA_LIMIT:
            self.move_direction *= -1  # Reverse direction
            self.move_counter = 0  # Reset counter

# Create Alien Bullets class
class Alien_Bullets(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("img/alien_bullet.png")  # Loads alien bullet image
        self.rect = self.image.get_rect(center=(x, y))  # Creates a rectangular area with center in x,y

    def update(self):
        self.rect.y += 2    # Modifies bullet posion to go up 
        if self.rect.top > SCREEN_HEIGHT:   # If bullet arrives at the bottom of the screen 
            self.kill() # Kill object
        if pygame.sprite.spritecollide(self, spaceship_group, False):   # Check for collision with player 
            self.kill() # Kill object
            explosion2_fx.play()    # Plays explosion sound
            explosion = Explosion(self.rect.centerx, self.rect.centery, 1)  # Creates explosion
            explosion_group.add(explosion)  # Adds explosion in sprite group 
            global player_lives # Declare global player lives
            player_lives -= 1   # Decreases player lives
            if player_lives <= 0:   # If player lives reach 0
                spaceship_group.empty()  # Kill spaceship object

# Function to create text
def draw_text(text, font, text_col, x, y):
    render = font.render(text, True, text_col)
    screen.blit(render, (x, y))

# Function to draw background
def draw_bg():
    screen.fill(BLACK)  # Fill background with black
    screen.blit(bg, (0, 0)) # Place background

    # Writes Indicator
    draw_text("Wave", font30, WHITE, 40, 35)  
    draw_text("Lives", font30, WHITE, 40, 135)
    draw_text("Feed", font30, WHITE, 40, 255)

# Function to create aliens
def create_aliens():
    for row in range(rows):
        for col in range(cols):
            alien = Aliens(200 + col * 125, 50 + row * 100, row)   # Creates Alien(distance from x screen border + col * distance x from each element, distance from y screen border + row * distance y from each element, type of enemy based on the row)
            alien_group.add(alien)  # Adds alien to sprite group 

# Function to create player
def create_player():
    spaceship = Spaceship(450, 550) # Create player
    spaceship_group.add(spaceship)  # Adds player to sprite group

# Function to reset game variables and sprites group
def reset():
    global last_alien_shot, player_score, player_lives, player_waves, feed_points  # Declare global variables

    if(player_lives == 0):
        last_alien_shot = pygame.time.get_ticks()
        player_score = 0
        player_lives = 3
        player_waves = 1
        feed_points = [0, ""]

    alien_group.empty()
    alien_bullet_group.empty()
    bullet_group.empty()
    explosion_group.empty()


# Function to display Start Screen
def Start_Screen():
    # Load images
    IMAGE_SIZE = (75, 75)
    images = [pygame.transform.scale(pygame.image.load(f"img/Enemy{num}.png"), IMAGE_SIZE) for num in range(1, 6)]    # Loads enemy images 

    # Main loop
    while True:
        # Fill the background
        screen.fill(WHITE)

        # Draw title
        draw_text("""  Space
Invaders""", font40, BLACK, 330, 0)

        # Draw text and images
        Y = 150
        for i in range(5):
            # Draw image
            screen.blit(images[i], (300, Y - 25))
            # Draw label
            draw_text(f"{enemy_scores[i]}pts", font30, BLACK, 375, Y)
            Y += 75

        # Draw bottom text
        draw_text("Press any key to start", font30, BLACK, 280, 525)

        # Update the display
        pygame.display.flip()

        # Event handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN:  # Check for key down event
                Play()  # Start the game when any key is pressed

# Function to display Game Over Screen
def GameOver_Screen():

    while True:

        # Fill the background
        screen.fill(BLACK)

        # Draw text
        draw_text("GAME OVER!", font40, (255, 0, 0), 300, 220)
        draw_text(f"WAVES: {player_waves}", font30, WHITE, 310, 270)
        draw_text(f"SCORE: {player_score}", font30, WHITE, 310, 300)
        draw_text(f"Press ESC key to restart!", font30, WHITE, 300, 350)

        # Update the display
        pygame.display.flip()

        # Event handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    reset()
                    Play()

# Function to start to play
def Play():
    global last_alien_shot, player_score, player_lives, player_waves, feed_points  # Declare global variables

    create_aliens() # Create Aliens
    create_player() # Create Player

    while True:
        clock.tick(FPS) # Sets clock speed
        draw_bg()       # Draw background
        time_now = pygame.time.get_ticks()  # Retrives current time

        # Aliens timing shooting logic
        if time_now - last_alien_shot > ALIEN_COOLDOWN and len(alien_bullet_group) < ALIENS_MAXBULLETS and len(alien_group) > 0:    # Verify if alien cooldown fulfilled if there are enough aliens to shoot and verify if there there are more than max alien bullets 
            attacking_alien = choice(alien_group.sprites())  # Random chose between which alien to shoot
            alien_bullet = Alien_Bullets(attacking_alien.rect.centerx, attacking_alien.rect.bottom) # Create Alien Bullet from the choosen alien position
            alien_bullet_group.add(alien_bullet)    # Adds Alien Bullet to sprite group
            last_alien_shot = time_now  # Register last alien shot

        # Update game objects
        spaceship_group.update()
        bullet_group.update()
        alien_group.update()
        alien_bullet_group.update()
        explosion_group.update()

        # Draw everything
        spaceship_group.draw(screen)
        bullet_group.draw(screen)
        alien_group.draw(screen)
        alien_bullet_group.draw(screen)
        explosion_group.draw(screen)

        # Display score and lives
        draw_text(f'Score: {player_score}', font30, WHITE, 650, -1)
        draw_text(f"{player_waves}", font30, WHITE, 70, 65)
        draw_text(f"{player_lives}", font30, WHITE, 70, 165)
        draw_text(f"{feed_points[1]}", font30, WHITE, 50, 290)

        # Check game advancement
        if player_lives <= 0:   # If player has no more lives
            GameOver_Screen()   # Start Game Over Screen
        if len(alien_group) == 0:   # If all alien have been killed
            draw_text(f'Wave {player_waves} Defeated!', font40, (255, 0, 0), 380, 290)  # Warn player
            pygame.display.flip()   # Update the display
            pygame.time.delay(3000)  # Wait for 3 seconds before next wave
            player_waves += 1   # Increase player wave
            reset() # Reset Sprites
            create_aliens() # Recreate Aliens

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        # Update the display
        pygame.display.flip()



Start_Screen()
pygame.quit() # Quit Pygame