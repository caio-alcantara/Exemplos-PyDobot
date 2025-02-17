################################

## Este exemplo não é autoral. Foi desenvolvido com o apoio de LLM's e tem 
## função de atuar como uma base, um exemplo, de como uma CLI pode ser feita
## para realizar o controle do Dobot via terminal. Esse exemplo pode e deve 
## ser seguido para a elaboração do artefato da sprint 2. Entretanto, será
## necessário melhorar não apenas a qualidade do código (tá daquele jeito que só o GPT faz)
## mas também a sua organização e modularidade, além de remover comentários desnecessários 
## e aprimorar algumas funções para melhor movimentação do Dobot

################################

# Importa os módulos necessários:
from serial.tools import list_ports        # Para listar as portas seriais disponíveis
import inquirer                            # Para criação de menus interativos na CLI
import pydobot                             # Biblioteca para controle do robô Dobot
from yaspin import yaspin                  # Para exibir spinners (animações) no terminal durante operações
import time                                # Para manipulação de tempo e delays
import keyboard                            #Para monitorar entradas do teclado

# Lista de posições pré-definidas para o Dobot
POSICOES_PREDEFINIDAS = [
    {'nome': 'Posição 1 - Base', 'x': 200.0, 'y': 0.0,   'z': 150.0, 'r': 0.0},
    {'nome': 'Posição 2 - Esquerda', 'x': 150.0, 'y': -100.0, 'z': 100.0, 'r': -45.0},
    {'nome': 'Posição 3 - Direita', 'x': 150.0, 'y': 100.0,  'z': 100.0, 'r': 45.0},
    {'nome': 'Posição 4 - Coleta', 'x': 180.0, 'y': 0.0,   'z': 50.0,  'r': 0.0},
    {'nome': 'Posição 5 - Alto', 'x': 200.0, 'y': 0.0,     'z': 200.0, 'r': 0.0},
]

def mover_para_home(robo):
    """
    Move o robô para a posição 'home' (posição padrão definida).
    """
    with yaspin(text="Movendo para home...", color="green") as spinner:
        # Comando para mover o robô para as coordenadas especificadas (posição home)
        robo.move_to(
            x=242.2293, 
            y=0.0, 
            z=151.3549, 
            r=0.0, 
            wait=True  # Aguarda a conclusão do movimento
        )
        spinner.ok("✔ Home alcançado!")  # Atualiza o spinner com mensagem de sucesso

def controle_manual(robo, delta=20, interval=0.005):
    """
    Permite mover o robô manualmente usando várias teclas:
      - Setas ←/→: movimento no eixo X
      - Setas ↑/↓: movimento no eixo Y
      - W/S: movimento no eixo Z (para cima/baixo)
      - A/D: ajuste de rotação (eixo R)
      - Q: sair do modo manual
      
    O movimento é contínuo enquanto a tecla estiver pressionada.
    O parâmetro 'delta' define o incremento base e 'interval' define o tempo de delay entre atualizações.
    """
    print("Modo de controle manual ativado.")
    print("Use as teclas:")
    print("  ←/→: mover em X")
    print("  ↑/↓: mover em Y")
    print("  W/S: mover em Z")
    print("  A/D: ajustar rotação")
    print("Pressione 'q' para sair.")
    
    # Loop principal do modo manual
    while True:
        # Se a tecla 'q' for pressionada, sai do modo manual
        if keyboard.is_pressed('q'):
            print("Saindo do modo de controle manual.")
            break

        # Obtém a posição atual do robô (x, y, z, r) usando o método pose()
        x, y, z, r, *_ = robo.pose()

        # Variáveis que armazenam os incrementos para cada eixo (inicialmente zero)
        dx, dy, dz, dr = 0, 0, 0, 0

        # Verifica se as teclas direcionais ou de ajuste estão pressionadas e define os incrementos:
        if keyboard.is_pressed('left'):
            dx = -delta
        if keyboard.is_pressed('right'):
            dx = delta
        if keyboard.is_pressed('up'):
            dy = delta
        if keyboard.is_pressed('down'):
            dy = -delta
        if keyboard.is_pressed('w'):
            dz = delta
        if keyboard.is_pressed('s'):
            dz = -delta
        if keyboard.is_pressed('a'):
            dr = -delta
        if keyboard.is_pressed('d'):
            dr = delta

        # Se houver alteração (ou seja, alguma tecla está pressionada), atualiza a posição:
        if dx or dy or dz or dr:
            new_x = x + dx
            new_y = y + dy
            new_z = z + dz
            new_r = r + dr
            # Envia o comando para mover o robô para a nova posição sem esperar a conclusão
            robo.move_to(new_x, new_y, new_z, new_r, wait=False)
            # Aguarda um pequeno intervalo para suavizar o movimento e permitir atualização contínua
            time.sleep(interval)

def main():
    """Fluxo principal da aplicação."""
    # Busca as portas seriais disponíveis e exibe uma animação enquanto busca
    with yaspin(text="Buscando portas seriais...", color="green") as spinner:
        ports = [p.device for p in list_ports.comports()]
        if not ports:
            spinner.fail("❌ Nenhuma porta serial encontrada!")
            return

    # Menu para seleção da porta serial do Dobot
    selected_port = inquirer.prompt([
        inquirer.List(
            'port',
            message="Selecione a porta do Dobot",
            choices=ports,
            carousel=True
        )
    ])['port']

    # Tenta conectar ao Dobot e exibe uma animação de progresso
    with yaspin(text="Conectando ao Dobot...", color="green") as spinner:
        try:
            robo = pydobot.Dobot(port=selected_port, verbose=False)
            spinner.ok("✔ Conectado!")
        except Exception as e:
            spinner.fail(f"❌ Falha na conexão: {str(e)}")
            return

    # Loop principal do menu de controle
    while True:
        action = inquirer.prompt([
            inquirer.List(
                'action',
                message="Controle do Dobot",
                choices=[
                    ('Mostrar posição atual', 'pose'),
                    ('Mover para posição pré-definida', 'move'),
                    ('Ir para posição home', 'home'),
                    ('Controle manual (teclas para eixos)', 'manual'),
                    ('Sair', 'exit')
                ],
                carousel=True
            )
        ])['action']

        # Se opção "Mostrar posição atual" foi escolhida:
        if action == 'pose':
            x, y, z, r, *_ = robo.pose()
            print(f"\nPosição atual:\nX: {x:.1f} mm\nY: {y:.1f} mm\nZ: {z:.1f} mm\nR: {r:.1f}°\n")
        
        # Se opção "Mover para posição pré-definida" foi escolhida:
        elif action == 'move':
            posicao = inquirer.prompt([
                inquirer.List(
                    'pos',
                    message="Selecione a posição",
                    choices=[(p['nome'], p) for p in POSICOES_PREDEFINIDAS],
                    carousel=True
                )
            ])['pos']
            
            with yaspin(text=f"Movendo para {posicao['nome']}...", color="green") as spinner:
                robo.move_to(
                    x=posicao['x'],
                    y=posicao['y'],
                    z=posicao['z'],
                    r=posicao['r'],
                    wait=True
                )
                spinner.ok("✔ Movimento concluído!")

        # Se opção "Ir para posição home" foi escolhida:
        elif action == 'home':
            mover_para_home(robo)

        # Se opção "Controle manual" foi escolhida:
        elif action == 'manual':
            controle_manual(robo)

        # Se opção "Sair" foi escolhida:
        elif action == 'exit':
            with yaspin(text="Encerrando operação...", color="green") as spinner:
                robo.close()
                spinner.ok("✔ Conexão encerrada!")
            break

# Ponto de entrada do programa
if __name__ == "__main__":
    main()
