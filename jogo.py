import pygame  # Biblioteca principal para criar jogos
from pygame.locals import *  # Constantes do Pygame (como QUIT, KEYDOWN, etc.)
from sys import exit  # Função para encerrar o programa
import os  # Interação com o sistema de arquivos
from random import randrange, choice  # Para posição de nuvens e escolha de obstáculo
import cv2  # OpenCV, usada para captura e processamento de vídeo
import mediapipe as mp  # Biblioteca para detecção de pose
import threading  # Para execução paralela da webcam
import sys  # Para verificar se está em ambiente "frozen" (PyInstaller)

# Inicialização do Pygame e do mixer de áudio
pygame.init()
pygame.mixer.init()

# Configuração do MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Evento de salto compartilhado entre thread e loop principal
jump_event = threading.Event()
JUMP_THRESHOLD = -0.03  # Limite de variação de posição para detectar salto

# Resolução base do jogo
BASE_WIDTH, BASE_HEIGHT = 640, 480
# Pegando resolução real da tela para ajustar escala
desktop_info = pygame.display.Info()
SCREEN_WIDTH = desktop_info.current_w
SCREEN_HEIGHT = desktop_info.current_h
scale = min(SCREEN_WIDTH / BASE_WIDTH, SCREEN_HEIGHT / BASE_HEIGHT)
scaled_width = int(BASE_WIDTH * scale)
scaled_height = int(BASE_HEIGHT * scale)

# Variáveis globais para captura de webcam (frame compartilhado)
global_frame = None
frame_lock = threading.Lock()

# Configuração da janela do jogo (modo fullscreen)
tela = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
base_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
pygame.display.set_caption('Player')

# Diretórios de imagens e sons
diretorio_imagens = os.path.join(diretorio_principal, 'imagens')
diretorio_sons = os.path.join(diretorio_principal, 'sons')

# Carregando sprite sheet
sprite_sheet = pygame.image.load(os.path.join(diretorio_imagens, 'spritesheet.png')).convert_alpha()

# Função: thread que captura webcam e detecta salto via MediaPipe
def webcam_jump_detection():
    global global_frame
    cap = cv2.VideoCapture(0)  # Acessa a webcam padrão
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    prev_y = None
    smoothed_y = None
    alpha = 0.7  # Fator de suavização exponencial

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                continue  # Se falhar, tenta ler o próximo frame

            # Converte BGR (OpenCV) para RGB (MediaPipe)
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)  # Detecta pose
            image.flags.writeable = True

            # Se detectar landmarks, verifica posição do nariz
            if results.pose_landmarks:
                nose = results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE]
                current_y = nose.y

                # Inicializa suavização
                if smoothed_y is None:
                    smoothed_y = current_y
                else:
                    smoothed_y = alpha * current_y + (1 - alpha) * smoothed_y

                # Calcula variação vertical para detectar salto
                if prev_y is not None:
                    delta_y = smoothed_y - prev_y
                    if delta_y < JUMP_THRESHOLD:
                        jump_event.set()  # Indica salto
                prev_y = smoothed_y

                # Desenha landmarks na imagem para debugging
                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
                )

            # Espelha e redimensiona imagem para exibir no jogo
            image = cv2.flip(image, 1)
            resized_image = cv2.resize(image, (200, 150))

            with frame_lock:
                global_frame = resized_image.copy()

    cap.release()

# Inicia thread de detecção de salto (daemon para encerrar junto ao principal)
thread = threading.Thread(target=webcam_jump_detection, daemon=True)
thread.start()

# Carrega sons de colisão e pontuação
som_colisao = pygame.mixer.Sound(os.path.join(diretorio_sons, 'death_sound.wav'))
som_colisao.set_volume(1)
som_pontuacao = pygame.mixer.Sound(os.path.join(diretorio_sons, 'score_sound.wav'))
som_pontuacao.set_volume(1)

# Estado inicial do jogo
colidiu = False
escolha_obstaculo = choice([0, 1])
pontos = 0
velocidade_jogo = 10

# Função para exibir texto
def exibe_mensagem(msg, tamanho, cor):
    fonte = pygame.font.SysFont('comicsansms', tamanho, True, False)
    return fonte.render(msg, True, cor)

# Função para reiniciar variáveis ao pressionar 'R'
def reiniciar_jogo():
    global pontos, velocidade_jogo, colidiu, escolha_obstaculo
    pontos = 0
    velocidade_jogo = 10
    colidiu = False
    player.rect.y = BASE_HEIGHT - 64 - 96//2
    player.pulo = False
    obstaculo_voador.rect.x = BASE_WIDTH
    obstaculo_chao.rect.x = BASE_WIDTH
    escolha_obstaculo = choice([0, 1])

# Classe: jogador principal
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Carrega som de pulo
        self.som_pulo = pygame.mixer.Sound(os.path.join(diretorio_sons, 'jump_sound.wav'))
        self.som_pulo.set_volume(1)
        # Carrega frames de animação do sprite
        self.imagens_player = []
        for i in range(2):
            frame = sprite_sheet.subsurface((i*32, 0), (32, 32))
            frame = pygame.transform.scale(frame, (32*3, 32*3))
            self.imagens_player.append(frame)
        self.index_lista = 0
        self.image = self.imagens_player[0]
        # Posição inicial na tela
        self.pos_y_inicial = BASE_HEIGHT - 75 - 96//2
        self.rect = self.image.get_rect(center=(175, BASE_HEIGHT - 64))
        self.mask = pygame.mask.from_surface(self.image)  # Para colisões precisas
        self.pulo = False

    # Método: inicia pulo
    def pular(self):
        self.pulo = True
        self.som_pulo.play()

    # Atualiza posição e animação
    def update(self):
        if self.pulo:
            # Sobe até limite e depois volta
            if self.rect.y <= 160:
                self.pulo = False
            self.rect.y -= 30
        else:
            # Cai de volta até posição inicial
            if self.rect.y < self.pos_y_inicial:
                self.rect.y += 20
            else:
                self.rect.y = self.pos_y_inicial
        # Ciclo de animação dos frames
        self.index_lista += 0.25
        if self.index_lista >= len(self.imagens_player):
            self.index_lista = 0
        self.image = self.imagens_player[int(self.index_lista)]

# Classe: nuvens decorativas
class Nuvens(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = sprite_sheet.subsurface((11*32, 0), (32, 32))
        self.image = pygame.transform.scale(self.image, (32*3, 32*3))
        self.rect = self.image.get_rect()
        self.rect.y = randrange(50, 200, 50)
        self.rect.x = BASE_WIDTH - randrange(30, 300, 90)

    def update(self):
        # Move para a esquerda e reposiciona ao sair da tela
        if self.rect.topright[0] < 0:
            self.rect.x = BASE_WIDTH
            self.rect.y = randrange(50, 200, 50)
        self.rect.x -= velocidade_jogo

# Classe: chão que se repete
class Chao(pygame.sprite.Sprite):
    def __init__(self, pos_x):
        pygame.sprite.Sprite.__init__(self)
        self.image = sprite_sheet.subsurface((10 * 32, 0), (32, 32))
        self.image = pygame.transform.scale(self.image, (32 * 2, 32 * 2))
        self.rect = self.image.get_rect()
        self.rect.y = BASE_HEIGHT - 64
        self.rect.x = pos_x * 64

    def update(self):
        self.rect.x -= velocidade_jogo

# Classe: obstáculos no chão
class ObstaculosChao(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.escolha = escolha_obstaculo
        self.escolher_frame()
        self.mask = pygame.mask.from_surface(self.image)

    def escolher_frame(self):
        # Escolhe frame com base em pontos (dificuldade)
        frames_disponiveis = [5, 6]
        if pontos >= 500:
            frames_disponiveis += [7, 8, 9]
        frame = choice(frames_disponiveis)
        self.image = sprite_sheet.subsurface((frame * 32, 0), (32, 32))
        self.image = pygame.transform.scale(self.image, (32 * 3, 32 * 3))
        self.rect = self.image.get_rect()
        # Ajusta altura dependendo do frame
        if frame in [6, 7, 8, 9]:
            self.rect.centery = BASE_HEIGHT - 50 - 10
        else:
            self.rect.centery = BASE_HEIGHT - 50
        self.rect.x = BASE_WIDTH

    def update(self):
        # Move apenas se for obstáculo escolhido
        if self.escolha == 0:
            if self.rect.topright[0] < 0:
                self.rect.x = BASE_WIDTH
            self.rect.x -= velocidade_jogo

# Classe: obstáculos voadores
class ObstaculoVoador(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.imagens_obstaculo = []
        for i in range(3, 5):
            img = sprite_sheet.subsurface((i*32, 0), (32, 32))
            img = pygame.transform.scale(img, (32*4, 32*4))
            self.imagens_obstaculo.append(img)
        self.index_lista = 0
        self.image = self.imagens_obstaculo[self.index_lista]
        self.mask = pygame.mask.from_surface(self.image)
        self.escolha = escolha_obstaculo
        self.rect = self.image.get_rect()
        self.rect.center = (BASE_WIDTH, 300)
        self.rect.x = BASE_WIDTH

    def update(self):
        # Move apenas se for obstáculo escolhido e anima
        if self.escolha == 1:
            if self.rect.topright[0] < 0:
                self.rect.x = BASE_WIDTH
            self.rect.x -= velocidade_jogo
            self.index_lista += 0.10
            if self.index_lista >= len(self.imagens_obstaculo):
                self.index_lista = 0
            self.image = self.imagens_obstaculo[int(self.index_lista)]

# Agrupamentos de sprites
todas_as_sprites = pygame.sprite.Group()
player = Player()
todas_as_sprites.add(player)

# Adiciona nuvens
for _ in range(4):
    todas_as_sprites.add(Nuvens())

# Adiciona blocos de chão suficientes para preencher a largura
quantidade_de_chaos = (BASE_WIDTH // 64) + 2
for i in range(quantidade_de_chaos):
    todas_as_sprites.add(Chao(i))

# Cria obstáculos e agrupa
obstaculo_chao = ObstaculosChao()
obstaculo_voador = ObstaculoVoador()
grupo_obstaculos = pygame.sprite.Group(obstaculo_chao, obstaculo_voador)
todas_as_sprites.add(obstaculo_chao, obstaculo_voador)

# Carrega e escala imagem de fundo
imagem_fundo = pygame.image.load('imagens/bg_chickenRun.png').convert()
imagem_fundo = pygame.transform.scale(imagem_fundo, (BASE_WIDTH, BASE_HEIGHT))

# Clock para fps
relogio = pygame.time.Clock()

# Loop principal do jogo
while True:
    relogio.tick(30)  # Limita a 30 frames por segundo
    base_surface.blit(imagem_fundo, (0, 0))  # Desenha fundo

    # Desenha frame da webcam, se disponível
    frame_surface = None
    with frame_lock:
        if global_frame is not None:
            frame_surface = pygame.image.frombuffer(
                global_frame.tobytes(),
                (global_frame.shape[1], global_frame.shape[0]),
                'RGB'
            )
    if frame_surface:
        base_surface.blit(frame_surface, (10, 10))

    # Eventos do Pygame (teclado e fechar)
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                exit()
            if event.key == K_r and colidiu:
                reiniciar_jogo()

    # Processa salto detectado pela webcam
    if not colidiu and jump_event.is_set():
        if player.rect.y == player.pos_y_inicial:
            player.pular()
        jump_event.clear()

    # Colisões
    colisoes = pygame.sprite.spritecollide(player, grupo_obstaculos, False, pygame.sprite.collide_mask)

    if not colidiu:
        todas_as_sprites.update()  # Atualiza posição e anima todos

        # Reposiciona blocos de chão que saíram da tela
        chao_sprites = [s for s in todas_as_sprites if isinstance(s, Chao)]
        for chao in chao_sprites:
            if chao.rect.right < 0:
                max_x = max((s.rect.x for s in chao_sprites), default=-64)
                chao.rect.x = max_x + 64
    else:
        # Se colidiu, para movimento dos obstáculos
        obstaculo_chao.rect.x += 0
        obstaculo_voador.rect.x += 0

    todas_as_sprites.draw(base_surface)  # Desenha sprites na surface

    # Escolha de novo obstáculo quando algum sair da tela
    if obstaculo_chao.rect.topright[0] <= 0 or obstaculo_voador.rect.topright[0] <= 0:
        escolha_obstaculo = choice([0, 1])
        obstaculo_chao.rect.x = obstaculo_voador.rect.x = BASE_WIDTH
        obstaculo_chao.escolha = obstaculo_voador.escolha = escolha_obstaculo
        if escolha_obstaculo == 0:
            obstaculo_chao.escolher_frame()

    # Quando colidir, toca som e exibe "GAME OVER"
    if colisoes and not colidiu:
        som_colisao.play()
        colidiu = True

    if colidiu:
        game_over = exibe_mensagem('GAME OVER', 40, (0, 0, 0))
        restart = exibe_mensagem('Pressione R para reiniciar', 20, (0, 0, 0))
        base_surface.blit(game_over, (BASE_WIDTH//2 - game_over.get_width()//2, BASE_HEIGHT//2 - 50))
        base_surface.blit(restart, (BASE_WIDTH//2 - restart.get_width()//2, BASE_HEIGHT//2))
    else:
        # Atualiza pontuação e dificulta o jogo a cada 100 pontos
        pontos += 1
        texto_pontos = exibe_mensagem(str(pontos), 40, (0, 0, 0))
        base_surface.blit(texto_pontos, (520, 30))
        if pontos % 100 == 0:
            som_pontuacao.play()
            velocidade_jogo = min(velocidade_jogo + 1, 23)

    # Ajusta escala e desenha na tela principal
    scaled_surface = pygame.transform.smoothscale(base_surface, (scaled_width, scaled_height))
    tela.blit(scaled_surface, ((SCREEN_WIDTH - scaled_width)//2, (SCREEN_HEIGHT - scaled_height)//2))

    pygame.display.flip()  # Atualiza display
