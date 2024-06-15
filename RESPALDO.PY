import pygame
import random
import sqlite3
from sqlite3 import Error

# Inicializar Pygame
pygame.init()
pygame.mixer.init()

# Cargar recursos
fondo = pygame.image.load('imagenes/fondo.png')
laser_sonido = pygame.mixer.Sound('laser.wav')
explosion_sonido = pygame.mixer.Sound('explosion.wav')
golpe_sonido = pygame.mixer.Sound('golpe.wav')

explosion_list = []
for i in range(1, 13):
    explosion = pygame.image.load(f'explosion/{i}.png')
    explosion_list.append(explosion)

# Colores
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
GRIS = (200, 200, 200)

# Tamaño de la pantalla
ANCHO = fondo.get_width()
ALTO = fondo.get_height()

# Crear pantalla
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Menú Principal")

# Fuente
fuente = pygame.font.Font(None, 36)

# Conexión a la base de datos SQLite
def crear_conexion():
    conn = None
    try:
        conn = sqlite3.connect('puntajes.db')
        print(sqlite3.version)
    except Error as e:
        print(e)
    return conn

def crear_tabla(conn):
    try:
        sql = '''CREATE TABLE IF NOT EXISTS puntajes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    puntaje INTEGER NOT NULL
                 );'''
        c = conn.cursor()
        c.execute(sql)
    except Error as e:
        print(e)

def obtener_mejores_puntajes(conn):
    sql = '''SELECT nombre, puntaje FROM puntajes ORDER BY puntaje DESC LIMIT 3'''
    cur = conn.cursor()
    cur.execute(sql)
    return cur.fetchall()

def insertar_puntaje(conn, nombre, puntaje):
    sql = '''INSERT INTO puntajes(nombre, puntaje) VALUES(?, ?)'''
    cur = conn.cursor()
    cur.execute(sql, (nombre, puntaje))
    conn.commit()

def reiniciar_historial(conn):
    sql = '''DELETE FROM puntajes'''
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()

# Menú principal
def menu_principal():
    conn = crear_conexion()
    crear_tabla(conn)

    ejecutar = True
    while ejecutar:
        pantalla.blit(fondo, (0, 0))
        mensaje("Menú Principal", 100, 50)

        boton_play = boton("Play", 350, 200, 100, 50, GRIS, NEGRO, iniciar_juego)
        boton_historial = boton("Historial", 350, 300, 130, 50, GRIS, NEGRO, lambda: mostrar_historial(conn))
        boton_reiniciar = boton("Reiniciar", 350, 400, 130, 50, GRIS, NEGRO, lambda: reiniciar_historial(conn))
        boton_quit = boton("Quit", 350, 500, 100, 50, GRIS, NEGRO, salir)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ejecutar = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if boton_play.collidepoint(event.pos):
                    iniciar_juego()
                if boton_historial.collidepoint(event.pos):
                    mostrar_historial(conn)
                if boton_reiniciar.collidepoint(event.pos):
                    reiniciar_historial(conn)
                if boton_quit.collidepoint(event.pos):
                    salir()

        pygame.display.flip()
    pygame.quit()

# Funciones auxiliares
def mensaje(texto, x, y):
    text_surface = fuente.render(texto, True, NEGRO)
    pantalla.blit(text_surface, (x, y))

def boton(texto, x, y, ancho, alto, color, color_texto, accion=None):
    rect = pygame.Rect(x, y, ancho, alto)
    pygame.draw.rect(pantalla, color, rect)
    text_surface = fuente.render(texto, True, color_texto)
    pantalla.blit(text_surface, (x + 10, y + 10))
    return rect

def iniciar_juego():
    run_game()

def mostrar_historial(conn):
    historial = obtener_mejores_puntajes(conn)
    pantalla.fill(BLANCO)
    mensaje("Historial de Puntajes", 100, 50)
    for i, (nombre, puntaje) in enumerate(historial):
        mensaje(f"{i + 1}. {nombre} - {puntaje}", 100, 100 + i * 40)
    pygame.display.flip()
    pygame.time.wait(3000)

def salir():
    pygame.quit()
    quit()

# Juego
def run_game():
    run = True
    fps = 60
    Clock = pygame.time.Clock()
    score = 0

    def texto_puntuacion(frame, text, size, x, y):
        font = pygame.font.SysFont('Small Fonts', size, bold=True)
        text_frame = font.render(text, True, BLANCO, NEGRO)
        text_rect = text_frame.get_rect()
        text_rect.midtop = (x, y)
        frame.blit(text_frame, text_rect)

    def barra_vida(frame, x, y, nivel):
        longitud = 100
        alto = 20
        fill = int((nivel / 100) * longitud)
        border = pygame.Rect(x, y, longitud, alto)
        fill = pygame.Rect(x, y, fill, alto)
        pygame.draw.rect(frame, (255, 0, 55), fill)
        pygame.draw.rect(frame, NEGRO, border, 4)

    class Jugador(pygame.sprite.Sprite):
        def __init__(self):
            super().__init__()
            self.image = pygame.image.load('imagenes/A1.png').convert_alpha()
            pygame.display.set_icon(self.image)
            self.rect = self.image.get_rect()
            self.rect.centerx = ANCHO // 2
            self.rect.centery = ALTO - 50
            self.velocidad_x = 0
            self.vida = 100

        def update(self):
            self.velocidad_x = 0
            keystate = pygame.key.get_pressed()
            if keystate[pygame.K_LEFT]:
                self.velocidad_x = -5
            elif keystate[pygame.K_RIGHT]:
                self.velocidad_x = 5

            self.rect.x += self.velocidad_x
            if self.rect.right > ANCHO:
                self.rect.right = ANCHO
            elif self.rect.left < 0:
                self.rect.left = 0

        def disparar(self):
            bala = Balas(self.rect.centerx, self.rect.top)
            grupo_balas_jugador.add(bala)
            laser_sonido.play()

    class Enemigos(pygame.sprite.Sprite):
        def __init__(self):
            super().__init__()
            self.image = pygame.image.load('imagenes/E1.png').convert_alpha()
            self.rect = self.image.get_rect()
            self.rect.x = random.randrange(ANCHO - self.rect.width)
            self.rect.y = random.randrange(50)
            self.velocidad_x = random.choice([-3, -2, -1, 1, 2, 3])
            self.shoot_delay = random.randint(1000, 3000)  # Retraso aleatorio entre disparos
            self.last_shot = pygame.time.get_ticks()

        def update(self):
            self.rect.x += self.velocidad_x
            if self.rect.right < 0 or self.rect.left > ANCHO:
                self.rect.y = random.randrange(50)
                self.rect.x = random.randrange(ANCHO - self.rect.width)
                self.velocidad_x = random.choice([-3, -2, -1, 1, 2, 3])

            now = pygame.time.get_ticks()
            if now - self.last_shot > self.shoot_delay:
                self.disparar_enemigos()
                self.last_shot = now
                self.shoot_delay = random.randint(1000, 3000)

        def disparar_enemigos(self):
            bala = Balas_enemigos(self.rect.centerx, self.rect.bottom)
            grupo_balas_enemigos.add(bala)
            laser_sonido.play()

    class Balas(pygame.sprite.Sprite):
        def __init__(self, x, y):
            super().__init__()
            self.image = pygame.image.load('imagenes/B2.png').convert_alpha()
            self.rect = self.image.get_rect()
            self.rect.centerx = x
            self.rect.y = y
            self.velocidad = -18

        def update(self):
            self.rect.y += self.velocidad
            if self.rect.bottom < 0:
                self.kill()

    class Balas_enemigos(pygame.sprite.Sprite):
        def __init__(self, x, y):
            super().__init__()
            self.image = pygame.image.load('imagenes/B1.png').convert_alpha()
            self.image = pygame.transform.rotate(self.image, 180)
            self.rect = self.image.get_rect()
            self.rect.centerx = x
            self.rect.y = y
            self.velocidad_y = 4

        def update(self):
            self.rect.y += self.velocidad_y
            if self.rect.top > ALTO:
                self.kill()

    class Explosion(pygame.sprite.Sprite):
        def __init__(self, position):
            super().__init__()
            self.image = pygame.transform.scale(explosion_list[0], (20, 20))
            self.rect = self.image.get_rect()
            self.rect.center = position
            self.time = pygame.time.get_ticks()
            self.velocidad_explo = 30
            self.frames = 0

        def update(self):
            tiempo = pygame.time.get_ticks()
            if tiempo - self.time > self.velocidad_explo:
                self.time = tiempo
                self.frames += 1
                if self.frames == len(explosion_list):
                    self.kill()
                else:
                    position = self.rect.center
                    self.image = explosion_list[self.frames]
                    self.rect = self.image.get_rect()
                    self.rect.center = position

    grupo_jugador = pygame.sprite.Group()
    grupo_enemigos = pygame.sprite.Group()
    grupo_balas_jugador = pygame.sprite.Group()
    grupo_balas_enemigos = pygame.sprite.Group()

    player = Jugador()
    grupo_jugador.add(player)

    for _ in range(10):
        enemigo = Enemigos()
        grupo_enemigos.add(enemigo)

    while run:
        Clock.tick(fps)
        pantalla.blit(fondo, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.disparar()

        grupo_jugador.update()
        grupo_enemigos.update()
        grupo_balas_jugador.update()
        grupo_balas_enemigos.update()

        grupo_jugador.draw(pantalla)
        grupo_enemigos.draw(pantalla)
        grupo_balas_jugador.draw(pantalla)
        grupo_balas_enemigos.draw(pantalla)

        # Colisiones balas_jugador - enemigo
        colision1 = pygame.sprite.groupcollide(grupo_enemigos, grupo_balas_jugador, True, True)
        for enemigo in colision1:
            score += 10
            nuevo_enemigo = Enemigos()
            grupo_enemigos.add(nuevo_enemigo)
            explo = Explosion(enemigo.rect.center)
            grupo_jugador.add(explo)
            explosion_sonido.play()

        # Colisiones jugador - balas_enemigo
        colision2 = pygame.sprite.spritecollide(player, grupo_balas_enemigos, True)
        for bala_enemiga in colision2:
            player.vida -= 10
            if player.vida <= 0:
                run = False
            explo1 = Explosion(bala_enemiga.rect.center)
            grupo_jugador.add(explo1)
            golpe_sonido.play()

        # Colisiones jugador - enemigo
        hits = pygame.sprite.spritecollide(player, grupo_enemigos, False)
        for hit in hits:
            player.vida -= 100
            if player.vida <= 0:
                run = False

        # Indicador y Score
        texto_puntuacion(pantalla, 'SCORE: ' + str(score), 30, ANCHO - 85, 2)
        barra_vida(pantalla, ANCHO - 285, 0, player.vida)

        pygame.display.flip()

    # Preguntar el nombre del jugador y guardar el puntaje si está entre los 3 mejores
    guardar_puntaje(score)
    menu_principal()

def guardar_puntaje(puntaje):
    conn = crear_conexion()
    mejores_puntajes = obtener_mejores_puntajes(conn)
    if len(mejores_puntajes) < 3 or puntaje > mejores_puntajes[-1][1]:
        nombre = input_nombre()
        insertar_puntaje(conn, nombre, puntaje)

def input_nombre():
    nombre = ""
    input_rect = pygame.Rect(100, 300, 200, 50)
    activo = True

    while activo:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    activo = False
                elif event.key == pygame.K_BACKSPACE:
                    nombre = nombre[:-1]
                else:
                    nombre += event.unicode

        pantalla.fill(BLANCO)
        mensaje("Ingrese su nombre: ", 100, 250)
        pygame.draw.rect(pantalla, GRIS, input_rect)
        text_surface = fuente.render(nombre, True, NEGRO)
        pantalla.blit(text_surface, (input_rect.x + 5, input_rect.y + 5))
        input_rect.w = max(200, text_surface.get_width() + 10)
        pygame.display.flip()

    return nombre

# Ejecutar el menú principal
if __name__ == "__main__":
    menu_principal()











