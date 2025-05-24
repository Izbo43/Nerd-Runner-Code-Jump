# 🎮 Nerd Runner: Code & Jump

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Pygame 2.6](https://img.shields.io/badge/Pygame-2.6-green)](https://pygame.org)
[![OpenCV 4.11](https://img.shields.io/badge/OpenCV-4.11-red)](https://opencv.org)

Um jogo de corrida infinita controlado por movimentos corporais! Desenvolvido para a **Fatec de Portas Abertas** usando visão computacional.

## 🚀 Sobre o Projeto
Inspirado no clássico T-Rex Game do Google, com:
- 👨💻 Controle por detecção de poses corporais
- 🏫 Cenário personalizado da Fatec Campinas
- 🔊 Efeitos sonoros imersivos
- 🚀 Dificuldade progressiva

## ✨ Funcionalidades Principais
- 🕹️ Controle por pulo físico via webcam
- 🚧 4 tipos de obstáculos dinâmicos
- 🎮 Sistema de colisão preciso
- 📈 Pontuação progressiva com aumento de dificuldade
- 🔄 Sistema de reinício instantâneo (tecla R)
- 🎨 Sprites e cenário personalizados


## 🕹️ Como Jogar  
- Posicione-se em frente à webcam  
- Pule fisicamente para fazer o personagem saltar  
- Desvie dos obstáculos  
- Acompanhe sua pontuação  
- Pressione **R** para reiniciar após *Game Over*  
- Use **ESC** para sair do jogo  

## 💡 Dica  
**Mantenha boa iluminação e fique a ~1.5m da webcam para melhor detecção!**

## ⚙️ Instalação

### Pré-requisitos
- Python 3.12 ou superior
- Webcam funcional
- Acesso à internet para baixar dependências

```bash
# Clone o repositório
git clone https://github.com/Izbo43/Nerd-Runner-Code-Jump.git
cd Nerd-Runner-Code-Jump

# Crie e ative o ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/MacOS
.\venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r requirements.txt
