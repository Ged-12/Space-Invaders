import sys
import pygame
from random import choice

# Initialize Pygame
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()
pygame.init()

# Define global constants
FPS = 60
SCREEN_WIDTH = 1125
SCREEN_HEIGHT = 800
AREA_LEFT_LIMIT = SCREEN_WIDTH * 0.12  # Play area left limit
AREA_RIGHT_LIMIT = SCREEN_WIDTH * 0.30  # Play area right limit 
MAX_POINTS_FEED = 11    # Max points viewable in the feed section
EXPLOSION_SPEED = 3     # Explosion animation speed

# Define aliens global constants 
ALIEN_BULLETS_MIN_COOLDOWN = 500# Minimum alien bullet cooldown in milliseconds
ALIEN_BULLETS_SPEED = 5 # Alien bullets movement speed aka number of pixel per movement
ALIENS_COLS = 5         # Number of Alien columns
ALIENS_MAX_BULLETS = 4  # Aliens max bullets presence in a instant
ALIENS_MAX_SPEED = 6    # Maximum aliens movement speed aka number of pixel per movement
ALIENS_MAX_ROWS = 6     # Aliens max rows 
ALIENS_STANDARD_ROWS = 4# Aliens initial rows, needs to be on par with number of enemy types 
ALIENS_STANDARD_SPEED = 3# Aliens initial speed
ALIEN_BULLETS_STANDARD_COOLDOWN = 800   #Aliens initial bullet cooldown

# Define player global constants 
PLAYER_MAXIMUM_LIVES = 6   # Maximum amount of lives obtainable
PLAYER_MAX_SPEED = 10       # Maximum player movement speed aka number of pixel per movement 
PLAYER_MIN_SHOOT_COOLDOWN = 500# Minimum amount of cooldown
PLAYER_BULLETS_SPEED = 5    # Player bullets movement speed aka number of pixel per movement
PLAYER_STANDARD_LIVES = 3   # Player initial lives
PLAYER_STANDARD_COOLDOWN = 800  # Player initial bullet cooldown
PLAYER_STANDARD_SPEED = 4       # Player initial speed

# Initialize game variables
clock = pygame.time.Clock()                 # Pygame clock
feed_points = [0, ""]                       # Feed tuple with counter and text message for the feed section 
alien_speed = ALIENS_STANDARD_SPEED         # Alien movement speed aka number of pixel per movement
alien_bullets_cooldown = ALIEN_BULLETS_STANDARD_COOLDOWN # Alien bullet shot cooldown
alien_last_shot = pygame.time.get_ticks()   # Last alien shot time
rows = ALIENS_STANDARD_ROWS                 # Number of enemy rows
player_score = 0                            # Player score
player_waves = 0                            # Player waves
player_lives = PLAYER_STANDARD_LIVES        # Player amount of lives
player_max_lives = PLAYER_STANDARD_LIVES    # Player max lives
player_bullets_cooldown = PLAYER_STANDARD_COOLDOWN  # Player bullet cooldown in milliseconds
player_speed = PLAYER_STANDARD_SPEED        # Player movement speed aka number of pixel per movement

# Define upgrades type and price by using a dict{string:int}
upgrades = {"lives": 10000,
            "bullet speed": 8000,
            "speed": 6000
}

# Define scores for each enemy type by using a dict{int:int}
enemy_scores = {
    5: 10,  # FirstEnemy
    4: 20,  # SecondEnemy
    3: 75,  # ThirdEnemy
    2: 150, # FourthEnemy
    1: 200, # FifthEnemy
    0: 300  # SixthEnemy
}

# Screen Setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders")

# Define fonts
font30 = pygame.font.SysFont('Constantia', 30)
font40 = pygame.font.SysFont('Constantia', 40)

# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Load sounds
explosion_fx = pygame.mixer.Sound("sounds/explosion.wav")
explosion_fx.set_volume(0.25)
explosion2_fx = pygame.mixer.Sound("sounds/explosion2.wav")
explosion2_fx.set_volume(0.25)
laser_fx = pygame.mixer.Sound("sounds/laser.wav")
laser_fx.set_volume(0.25)

# Create sprite groups
spaceship_group = pygame.sprite.GroupSingle()
bullet_group = pygame.sprite.Group()
alien_group = pygame.sprite.Group()
alien_bullet_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
button_group = pygame.sprite.Group()

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
        self.rect.y -= PLAYER_BULLETS_SPEED    # Modifies bullet posion to go up  
        if self.rect.bottom < 45:    # If bullet arrives at the top of the screen 
            self.kill() # Kill object
        hit_aliens = pygame.sprite.spritecollide(self, alien_group, True)   # Check for collision with aliens
        hit_aliensbullets = pygame.sprite.spritecollide(self, alien_bullet_group, True)   # Check for collision with aliens bullets
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
        if hit_aliensbullets:
            self.kill()
        

# Create spaceship class
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("img/spaceship.png") # Loads spaceship image
        self.rect = self.image.get_rect(center=(x, y))      # Creates a rectangular area with center in x,y
        self.last_shot = pygame.time.get_ticks()

    def update(self):

        key = pygame.key.get_pressed() # Retrieves the current state of all keyboard keys

        # Movement logic
        if key[pygame.K_LEFT] and self.rect.left > AREA_LEFT_LIMIT: # Check if the player presses left limit at 180
            self.rect.x -= player_speed    # Moves left by speed
        if key[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:  # Check if the player presses right limit at SCREEN_WIDTH
            self.rect.x += player_speed    # Moves right by speed

        # Shooting logic
        time_now = pygame.time.get_ticks()  # Retrieves current time
        if key[pygame.K_SPACE] and time_now - self.last_shot > player_bullets_cooldown: # Check if the player presses space to shoot and verify if the cooldown is fulfilled
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
        self.rect.x += self.move_direction * alien_speed
        self.move_counter += alien_speed

        # Change direction if the limit is reached
        if self.move_counter <= -AREA_LEFT_LIMIT or self.move_counter >= AREA_RIGHT_LIMIT:
            self.move_direction *= -1  # Reverse direction
            self.move_counter = 0  # Reset counter

# Create Alien Bullets class
class Alien_Bullets(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("img/alien_bullet.png")  # Loads alien bullet image
        self.rect = self.image.get_rect(center=(x, y))  # Creates a rectangular area with center in x,y

    def update(self):
        self.rect.y += ALIEN_BULLETS_SPEED    # Modifies bullet posion to go up 
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

class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, type, image):
        super().__init__()
        self.type = type
        self.image = image  # Sets button image
        self.rect = self.image.get_rect(center=(x, y))  # Creates a rectangular area with center in x,y
        self.clicked = False

    def update(self):
        action = False
        pos = pygame.mouse.get_pos()  # Get mouse position

        # Check if mouse hovers on the button and if clicked
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True
        if (
            pygame.mouse.get_pressed()[0] == 0
):  # If button isn't pressed
            self.clicked = False
        return action

# Function to create text
def draw_text(text, font, text_col, x, y):
    render = font.render(text, True, text_col)
    screen.blit(render, (x, y))


# Function to create aliens
def create_aliens():
    for row in range(rows):
        for col in range(ALIENS_COLS):
            alien = Aliens(250 + col * 125, 90 + row * 100, row)   # Creates Alien(distance from x screen border + col * distance x from each element, distance from y screen border + row * distance y from each element, type of enemy based on the row)
            alien_group.add(alien)  # Adds alien to sprite group 

# Function to create player
def create_player():
    spaceship = Player(SCREEN_WIDTH/2, SCREEN_HEIGHT-75) # Create player
    spaceship_group.add(spaceship)  # Adds player to sprite group

# Function to reset game variables and sprites group
def reset():
    global feed_points, alien_last_shot, alien_speed, alien_bullets_cooldown, rows, player_score, player_lives, player_max_lives, player_bullets_cooldown, player_speed, player_waves   # Declare global variables

    if(player_lives == 0):
        feed_points = [0, ""]
        alien_last_shot = pygame.time.get_ticks()
        alien_speed = ALIENS_STANDARD_SPEED
        alien_bullets_cooldown = ALIEN_BULLETS_STANDARD_COOLDOWN
        rows = ALIENS_STANDARD_ROWS
        player_score = 0
        player_waves = 0
        player_lives = PLAYER_STANDARD_LIVES
        player_max_lives = PLAYER_STANDARD_LIVES
        player_bullets_cooldown = PLAYER_STANDARD_COOLDOWN
        player_speed = PLAYER_STANDARD_SPEED
    
    player_lives = player_max_lives
    alien_group.empty()
    alien_bullet_group.empty()
    bullet_group.empty()
    explosion_group.empty()
    button_group.empty()


# Function to display Start Screen
def start_screen():
    # Load images
    IMAGE_SIZE = (75, 75)
    images = [pygame.transform.scale(pygame.image.load(f"img/Enemy{num}.png"), IMAGE_SIZE) for num in range(1, 7)]    # Loads enemy images 

    # Main loop
    while True:
        # Fill the background
        screen.fill(WHITE)

        # Draw title
        draw_text("""  Space
Invaders""", font40, BLACK, SCREEN_WIDTH/2.5, 0)

        # Draw text and images
        Y = 150
        for i in range(len(images)):
            # Draw image
            screen.blit(images[i], (SCREEN_WIDTH/3, Y - 25))
            # Draw label
            draw_text(f"{enemy_scores[i]}pts", font30, BLACK, SCREEN_WIDTH/2.4, Y)
            Y += 75

        # Draw bottom text
        draw_text("Press any key to start", font30, BLACK, SCREEN_WIDTH/2.8, SCREEN_HEIGHT/1.35)

        # Update the display
        pygame.display.flip()

        # Event handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN:  # Check for key down event
                play_screen()  # Start the game when any key is pressed

# Function to display Game Over Screen
def gameover_screen():

    while True:

        # Fill the background
        screen.fill(BLACK)

        # Draw text
        draw_text("GAME OVER!", font40, (255, 0, 0), SCREEN_WIDTH/2.75, SCREEN_HEIGHT/3)
        draw_text(f"WAVES: {player_waves}", font30, WHITE, SCREEN_WIDTH/2.45, SCREEN_HEIGHT/2.55)
        draw_text(f"SCORE: {player_score}", font30, WHITE, SCREEN_WIDTH/2.42, SCREEN_HEIGHT/2.25)
        draw_text(f"Press ESC key to restart!", font30, WHITE, SCREEN_WIDTH/2.75, SCREEN_HEIGHT/2)

        # Event handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    reset()
                    play_screen()

        # Update the display
        pygame.display.flip()

def shop_screen():
    global player_score, player_max_lives, player_bullets_cooldown, player_lives, player_speed, upgrades

    clock.tick(60)

    IMAGE_SIZE = (275,275)
    images = [pygame.transform.scale(pygame.image.load("img/lives_upgrade.png"),IMAGE_SIZE),
              pygame.transform.scale(pygame.image.load("img/speed_upgrade.png"),IMAGE_SIZE),
              pygame.transform.scale(pygame.image.load("img/bullet_upgrade.png"),IMAGE_SIZE),
              pygame.transform.scale(pygame.image.load("img/exit.png"), (150,150))
    ]

    # Create Buttons

    button_group.add(Button(SCREEN_WIDTH/5.5, SCREEN_HEIGHT/2.55, "lives", images[0]))
    button_group.add(Button(SCREEN_WIDTH/1.95, SCREEN_HEIGHT/2.55, "speed", images[1]))
    button_group.add(Button(SCREEN_WIDTH/1.2, SCREEN_HEIGHT/2.55, "bullet speed", images[2]))
    button_group.add(Button(SCREEN_WIDTH/1.08, SCREEN_HEIGHT/20.5, "exit", images[3]))

    while True:

        # Fill the background
        screen.fill(WHITE)

        # Draw title
        draw_text("Upgrade Shop", font40, BLACK, SCREEN_WIDTH/2.5, 0)
        
        # Draw score
        draw_text(f"Score: {player_score}", font30, BLACK, 0, 0)

        # Draw Subtext
        draw_text(f"""Increase max lives count
            {upgrades["lives"]}pts""", font30, BLACK, SCREEN_WIDTH/20, SCREEN_HEIGHT/1.75)
        draw_text(f"""Increase movement speed
            {upgrades["speed"]}pts""", font30, BLACK, SCREEN_WIDTH/2.85, SCREEN_HEIGHT/1.75)
        draw_text(f"""Decrease bullet cooldown
            {upgrades["bullet speed"]}pts""", font30, BLACK, SCREEN_WIDTH/1.5, SCREEN_HEIGHT/1.75)
        
        # Draw upgrade indicator
        draw_text(f"{player_max_lives}/{PLAYER_MAXIMUM_LIVES}", font30, BLACK, SCREEN_WIDTH/6.5, SCREEN_HEIGHT/1.5)
        draw_text(f"{player_speed - PLAYER_STANDARD_SPEED}/{PLAYER_MAX_SPEED - PLAYER_STANDARD_SPEED}", font30, BLACK, SCREEN_WIDTH/2.15, SCREEN_HEIGHT/1.5)
        draw_text(f"{int((PLAYER_STANDARD_COOLDOWN - player_bullets_cooldown)/100)}/{int((PLAYER_STANDARD_COOLDOWN - PLAYER_MIN_SHOOT_COOLDOWN)/100)}", font30, BLACK, SCREEN_WIDTH/1.28, SCREEN_HEIGHT/1.5)

        # Draw buttons
        button_group.draw(screen)

        # Buttons logic
        for button in button_group:
            if button.update(): 
                if button.type == "lives" and button.clicked:   # Verify if lives upgrade button as been clicked
                    if player_score - upgrades["lives"] >= 0 and player_max_lives != PLAYER_MAXIMUM_LIVES:  # Check credit and if maximum upgrade reached
                        player_score -= upgrades["lives"]   # Decrease credit
                        player_max_lives +=1    # Increase max lives
                elif button.type == "speed" and button.clicked: # Verify if speed upgrade button as been clicked
                    if player_score - upgrades["speed"] >= 0 and player_speed != PLAYER_MAX_SPEED:# Check credit and if maximum upgrade reached
                        player_score -= upgrades["speed"]   # Decrease credit
                        player_speed +=1    # Increase speed
                elif button.type == "bullet speed" and button.clicked:  # Verify if bullet cooldown upgrade button as been clicked
                    if player_score - upgrades["bullet speed"] >= 0 and player_bullets_cooldown != PLAYER_MIN_SHOOT_COOLDOWN:# Check credit and if maximum upgrade reached
                        player_score -= upgrades["bullet speed"]    # Decrease credit
                        player_bullets_cooldown -=100   # Decrease bullet cooldown
                elif button.type == "exit" and button.clicked:  # Verify if exit button as been clicked
                    return

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        # Update the display
        pygame.display.flip()


# Function to start to play
def play_screen():
    global alien_last_shot, alien_speed, alien_bullets_cooldown, player_score, player_lives, player_waves, feed_points, rows  # Declare global variables

    # Load background image
    bg = pygame.transform.scale(pygame.image.load("img/bg.png"), (SCREEN_WIDTH, SCREEN_HEIGHT))

    create_aliens() # Create Aliens
    create_player() # Create Player

    while True:

        #Sets Background
        screen.fill(BLACK)  # Fill background with black
        screen.blit(bg, (0, 0)) # Place background

        # Writes Indicator
        draw_text("Wave", font30, WHITE, SCREEN_WIDTH/20, SCREEN_HEIGHT/18)  
        draw_text("Lives", font30, WHITE, SCREEN_WIDTH/20, SCREEN_HEIGHT/4.45)
        draw_text("Feed", font30, WHITE, SCREEN_WIDTH/20, SCREEN_HEIGHT/2.35)

        clock.tick(FPS) # Sets clock speed
        time_now = pygame.time.get_ticks()  # Retrives current time
        
        # Aliens timing shooting logic
        if time_now - alien_last_shot > alien_bullets_cooldown and len(alien_bullet_group) < ALIENS_MAX_BULLETS and len(alien_group) > 0:    # Verify if alien cooldown fulfilled if there are enough aliens to shoot and verify if there there are more than max alien bullets 
            attacking_alien = choice(alien_group.sprites())  # Random chose between which alien to shoot
            alien_bullet = Alien_Bullets(attacking_alien.rect.centerx, attacking_alien.rect.bottom) # Create Alien Bullet from the choosen alien position
            alien_bullet_group.add(alien_bullet)    # Adds Alien Bullet to sprite group
            alien_last_shot = time_now  # Register last alien shot

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
        draw_text(f'Score: {player_score}', font30, WHITE, SCREEN_WIDTH/1.5, -1)
        draw_text(f"{player_waves}", font30, WHITE, SCREEN_WIDTH/13.75, SCREEN_HEIGHT/9.5)
        draw_text(f"{player_lives}", font30, WHITE, SCREEN_WIDTH/15, SCREEN_HEIGHT/3.75)
        draw_text(f"{feed_points[1]}", font30, WHITE, SCREEN_WIDTH/20, SCREEN_HEIGHT/2.15)

        # Check game advancement
        if player_lives <= 0:   # If player has no more lives
            gameover_screen()   # Start Game Over Screen
        if len(alien_group) == 0:   # If all alien have been killed
            draw_text(f'Wave {player_waves} Defeated!', font40, (255, 0, 0), SCREEN_WIDTH/2.25, SCREEN_HEIGHT/2.45)  # Warn player
            pygame.display.flip()   # Update the display
            pygame.time.delay(3000)  # Wait for 3 seconds before next wave
            player_waves += 1   # Increase player wave
            if player_waves % 2 == 0:
                ch = choice(("rows","speed", "bullet speed"))
                if ch == "rows":
                    if rows != ALIENS_MAX_ROWS:
                        rows += 1
                elif ch == "speed":
                    if alien_speed != ALIENS_MAX_SPEED:
                        alien_speed += 1
                elif ch == "bullet speed":
                    if alien_bullets_cooldown != ALIEN_BULLETS_MIN_COOLDOWN:
                        alien_bullets_cooldown -= 100
                shop_screen()
            reset() # Reset Sprites
            create_aliens() # Recreate Aliens

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        # Update the display
        pygame.display.flip()

start_screen()
pygame.quit() # Quit Pygame