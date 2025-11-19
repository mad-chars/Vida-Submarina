import pygame
import random
import sys

# Arrancamos pygame
pygame.init()

# Cargamos los sonidos
bite_sound = pygame.mixer.Sound("Bite.mp3")
error_sound = pygame.mixer.Sound("Error.mp3")

# Definimos el tamaño de la ventana
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vida Submarina")

# Cargar y reproducir música de fondo
pygame.mixer.music.load("musicafondo.mp3")
pygame.mixer.music.play(-1)  # -1 para que se repita indefinidamente

# Fuente y reloj
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
clock = pygame.time.Clock()

# Cargar imágenes
fondo = pygame.image.load("Fondo.png")
pez_img = pygame.image.load("Pez.png")
pez_img = pygame.transform.scale(pez_img, (50, 50))

# Crear versiones del pez en diferentes direcciones
pez_right = pez_img  # Derecha (original)
pez_left = pygame.transform.flip(pez_img, True, False)  # Izquierda (espejo horizontal)
pez_up = pygame.transform.rotate(pez_img, 90)  # Arriba
pez_down = pygame.transform.rotate(pez_img, -90)  # Abajo

# Versiones diagonales
pez_up_right = pygame.transform.rotate(pez_img, 45)
pez_up_left = pygame.transform.rotate(pez_img, 135)
pez_down_right = pygame.transform.rotate(pez_img, -45)
pez_down_left = pygame.transform.rotate(pez_img, -135)

alga_img = pygame.image.load("Alga.png")
alga_img = pygame.transform.scale(alga_img, (40, 40))
lata_img = pygame.image.load("lata.png")
lata_img = pygame.transform.scale(lata_img, (30, 30))
llanta_img = pygame.image.load("llanta.png")
llanta_img = pygame.transform.scale(llanta_img, (30, 30))
papel_img = pygame.image.load("papel.png")
papel_img = pygame.transform.scale(papel_img, (30, 30))

# Variables del juego
points = 0
lives = 10
game_over = False

# pez
fish = pez_img.get_rect(topleft=(WIDTH // 2, HEIGHT - 60))
fish_speed = 5
fish_angle = 0
last_vertical_input = 0

# Dash del pez
dash_speed = 20
dash_duration = 10  # frames
dash_cooldown_max = 60  # frames
dash_active = False
dash_timer = 0
dash_cooldown = 0
dash_direction = [0, 0]
# Variables de energía del dash (definidas en la imagen)
max_dash_energy = 100
dash_energy = 100
dash_recovery_speed = 1  # energía recuperada por frame

# Partículas de polvo
particles = []

# Algas (objetos a recoger)
algas = []
for i in range(3):
    alga = alga_img.get_rect(topleft=(random.randint(0, WIDTH - 40), random.randint(0, HEIGHT - 40)))
    # velocidades razonables (pix/frame)
    algas.append({"img": alga_img, "rect": alga, "speed": random.randint(1, 3)})

# Enemigos (basura)
basura_imgs = [lata_img, llanta_img, papel_img]
enemigos = []
for _ in range(3):
    img = random.choice(basura_imgs)
    rect = img.get_rect(topleft=(random.randint(0, WIDTH - 30), random.randint(50, 500)))
    # velocidades razonables (antes había un 400 que provocaba movimiento instantáneo)
    enemigos.append({"img": img, "rect": rect, "speed": random.randint(2, 6)})

# Función para texto
def draw_text(text, x, y, color=(255, 255, 255)):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

# Función para crear partículas de polvo
def create_dust_particles(x, y, count=5):
    for _ in range(count):
        particle = {
            "x": x + random.randint(-10, 10),
            "y": y + random.randint(-10, 10),
            "vx": random.uniform(-2, 2),
            "vy": random.uniform(-2, 2),
            "lifetime": 30,
            "max_lifetime": 30
        }
        particles.append(particle)

# Función para actualizar y dibujar partículas
def update_particles():
    for particle in particles[:]:
        particle["x"] += particle["vx"]
        particle["y"] += particle["vy"]
        particle["lifetime"] -= 1
        particle["vy"] += 0.1  # gravedad
        
        if particle["lifetime"] <= 0:
            particles.remove(particle)
        else:
            # Dibujar partícula con transparencia
            alpha = int(255 * (particle["lifetime"] / particle["max_lifetime"]))
            surf = pygame.Surface((3, 3))
            surf.fill((180, 180, 180))
            surf.set_alpha(alpha)
            screen.blit(surf, (int(particle["x"]), int(particle["y"])))

# Función para dibujar la barra de dash
def draw_dash_bar(x, y, energy, max_energy):
    bar_width = 150
    bar_height = 15
    border_color = (255, 255, 255)
    
    # Borde
    pygame.draw.rect(screen, border_color, (x, y, bar_width, bar_height), 2)
    
    # Barra de energía
    bar_fill = (bar_width * energy) // max_energy
    if energy > 50:
        color = (0, 255, 0)
    elif energy > 25:
        color = (255, 255, 0)
    else:
        color = (255, 0, 0)
    
    pygame.draw.rect(screen, color, (x, y, bar_fill, bar_height))
    
    # Texto
    dash_text = pygame.font.Font(None, 20).render("Dash", True, (255, 255, 255))
    screen.blit(dash_text, (x - 40, y - 2))

# Función para manejar el dash
def handle_dash(keys):
    global dash_active, dash_timer, dash_cooldown, dash_direction, dash_energy
    
    # Verificar si se presiona la tecla de dash (SPACE)
    if keys[pygame.K_SPACE] and dash_cooldown <= 0 and dash_energy >= 20:
        dash_active = True
        dash_timer = dash_duration
        dash_cooldown = dash_cooldown_max
        dash_energy -= 20
        
        # Determinar dirección del dash
        dash_direction = [0, 0]
        if keys[pygame.K_LEFT]:
            dash_direction[0] = -1
        if keys[pygame.K_RIGHT]:
            dash_direction[0] = 1
        if keys[pygame.K_UP]:
            dash_direction[1] = -1
        if keys[pygame.K_DOWN]:
            dash_direction[1] = 1
        
        # Si no hay dirección, dash hacia adelante
        if dash_direction == [0, 0]:
            if fish_angle == 0:
                dash_direction[0] = 1
            elif fish_angle == 180:
                dash_direction[0] = -1
            elif fish_angle == 90:
                dash_direction[1] = -1
            elif fish_angle == 270:
                dash_direction[1] = 1
    
    # Ejecutar dash
    if dash_active:
        fish.x += dash_direction[0] * dash_speed
        fish.y += dash_direction[1] * dash_speed
        create_dust_particles(fish.centerx, fish.centery, count=3)
        dash_timer -= 1
        
        if dash_timer <= 0:
            dash_active = False
    
    # Reducir cooldown
    if dash_cooldown > 0:
        dash_cooldown -= 1

# Función para obtener la imagen correcta del pez según el ángulo
def get_fish_image(angle):
    if angle == 0:
        return pez_right
    elif angle == 180:
        return pez_left
    elif angle == 90:
        return pez_up
    elif angle == 270:
        return pez_down
    elif angle == 45:
        return pez_up_right
    elif angle == 135:
        return pez_up_left
    elif angle == -45 or angle == 315:
        return pez_down_right
    elif angle == -135 or angle == 225:
        return pez_down_left
    else:
        return pygame.transform.rotate(pez_img, angle)

# Función para dibujar la pantalla de pausa
def draw_pause_screen():
    pause_text = pygame.font.Font(None, 50).render("PAUSA", True, (255, 255, 255))
    resume_text = small_font.render("Presiona P para reanudar", True, (255, 255, 255))
    
    # Fondo semi-transparente
    s = pygame.Surface((WIDTH, HEIGHT))
    s.set_alpha(128)
    s.fill((0, 0, 0))
    screen.blit(s, (0, 0))
    
    screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - 50))
    screen.blit(resume_text, (WIDTH // 2 - resume_text.get_width() // 2, HEIGHT // 2 + 50))

# Variables de pausa
paused = False

# Bucle principal
while True:
    screen.blit(fondo, (0, 0))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                paused = not paused
    
    if paused:
        draw_pause_screen()
    elif not game_over:
        # Movimiento del pez
        Keys = pygame.key.get_pressed()
        moved = False
        
        # Control de movimiento con 8 direcciones
        if Keys[pygame.K_LEFT] and Keys[pygame.K_UP]:
            fish.x -= fish_speed
            fish.y -= fish_speed
            moved = True
            fish_angle = 135  # arriba-izquierda
        elif Keys[pygame.K_LEFT] and Keys[pygame.K_DOWN]:
            fish.x -= fish_speed
            fish.y += fish_speed
            moved = True
            fish_angle = 225  # abajo-izquierda
        elif Keys[pygame.K_RIGHT] and Keys[pygame.K_UP]:
            fish.x += fish_speed
            fish.y -= fish_speed
            moved = True
            fish_angle = 45   # arriba-derecha
        elif Keys[pygame.K_RIGHT] and Keys[pygame.K_DOWN]:
            fish.x += fish_speed
            fish.y += fish_speed
            moved = True
            fish_angle = 315  # abajo-derecha
        elif Keys[pygame.K_LEFT]:
            fish.x -= fish_speed
            moved = True
            fish_angle = 180  # izquierda
        elif Keys[pygame.K_RIGHT]:
            fish.x += fish_speed
            moved = True
            fish_angle = 0    # derecha
        elif Keys[pygame.K_UP]:
            fish.y -= fish_speed
            moved = True
            last_vertical_input = -1
            fish_angle = 90   # arriba
        elif Keys[pygame.K_DOWN]:
            fish.y += fish_speed
            moved = True
            last_vertical_input = 1
            fish_angle = 270  # abajo
        
        # Manejar el dash
        handle_dash(Keys)
        
        # Crear partículas si se está moviendo
        if moved:
            create_dust_particles(fish.centerx, fish.centery, count=2)
        
        # Limitar movimiento a los límites de la pantalla
        fish.clamp_ip(screen.get_rect())
        
        # Obtener y dibujar la imagen del pez correcta
        fish_img_to_draw = get_fish_image(fish_angle)
        fish_rect = fish_img_to_draw.get_rect(center=fish.center)
        screen.blit(fish_img_to_draw, fish_rect.topleft)
        
        # Recuperar energía de dash si no se está moviendo
        if dash_energy < max_dash_energy:
            dash_energy = min(dash_energy + dash_recovery_speed, max_dash_energy)

        # Algas: mover, dibujar y gestionar colisiones por cada alga
        for alga in algas:
            alga["rect"].y += alga["speed"]
            screen.blit(alga["img"], alga["rect"].topleft)

            # si sale por abajo, reubicarla arriba
            if alga["rect"].top > HEIGHT:
                alga["rect"].topleft = (random.randint(0, WIDTH - 40), random.randint(50, 300))

            # colisión con el pez
            if fish.colliderect(alga["rect"]):
                points += 1
                bite_sound.play()
                alga["rect"].topleft = (random.randint(0, WIDTH - 40), random.randint(50, 300))

        # Basura (enemigos): mover, dibujar y colisiones
        for enemigo in enemigos:
            enemigo["rect"].y += enemigo["speed"]
            screen.blit(enemigo["img"], enemigo["rect"].topleft)

            if enemigo["rect"].top > HEIGHT:
                enemigo["rect"].topleft = (random.randint(0, WIDTH - 30), random.randint(50, 400))

            if fish.colliderect(enemigo["rect"]):
                lives -= 1
                error_sound.play()
                enemigo["rect"].topleft = (random.randint(0, WIDTH - 30), random.randint(50, 400))

        # comprobar fin de juego
        if lives <= 0:
            game_over = True

    else:
        # pantalla de fin de juego
        draw_text("Perdiste, presiona ESC para salir", WIDTH // 2 - 170, HEIGHT // 2 - 20, (255, 0, 0))
        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            pygame.quit()
            sys.exit()
    
    # Actualizar partículas
    update_particles()
    
    # Marcadores           
    draw_text(f"Puntos: {points}", 10, 10)
    draw_text(f"Vidas: {lives}", 10, 50)
    
    # Dibujar barra de dash
    draw_dash_bar(10, 90, dash_energy, max_dash_energy)
    
    # Mostrar información de controles
    if not game_over and not paused:
        controls_text = small_font.render("Flechas: Mover | ESPACIO: Dash | P: Pausa", True, (200, 200, 200))
        screen.blit(controls_text, (10, HEIGHT - 30))
        
    pygame.display.flip()
    clock.tick(60)