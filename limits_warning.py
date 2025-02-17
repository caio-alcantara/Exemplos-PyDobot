from serial.tools import list_ports
import inquirer
import pydobot
from yaspin import yaspin  # Remove yaspin_palettes import
import threading
import time

def start_limit_monitor(device, margin=10):
    """
    Monitora os limites com interface interativa e feedback visual
    """
    limits = [
        {'name': 'direita pra cima', 'x': 210, 'z': 166.98},
        {'name': 'direita pra baixo', 'x': -119, 'y': 136.9, 'z': 6.57, 'r': 131},
        {'name': 'esquerda cima', 'x': -183, 'y': -156, 'z': 171, 'r': -139},
        {'name': 'esquerda baixo', 'x': -134, 'y': -126, 'z': 10, 'r': -136}
    ]

    def dynamic_spinner():
        """Gera texto dinâmico para o spinner com a posição atual"""
        with yaspin(text="Iniciando monitoramento...", color="green") as spinner:  # Customize color directly
            while True:
                try:
                    x, y, z, r, *_ = device.pose()
                    spinner.text = f"X:{x:6.1f} Y:{y:6.1f} Z:{z:6.1f} R:{r:6.1f}"
                    time.sleep(0.2)
                except:
                    spinner.fail("⚠️ Erro na leitura da posição!")
                    break

    def alert_system():
        """Sistema de alertas com interação do usuário"""
        nonlocal margin
        while True:
            try:
                x, y, z, r, *_ = device.pose()
                
                for limit in limits:
                    trigger = []
                    for coord in ['x', 'y', 'z', 'r']:
                        if coord in limit:
                            current = locals()[coord]
                            target = limit[coord]
                            trigger.append(abs(current - target) <= margin)

                    if all(trigger):
                        action = inquirer.prompt([
                            inquirer.List(
                                'action',
                                message=f"ALERTA: Aproximando do limite {limit['name']}",
                                choices=[
                                    ('Continuar movimento', 'continue'),
                                    ('Parar imediatamente', 'stop'),
                                    ('Ajustar margem de segurança', 'adjust')
                                ],
                                carousel=True
                            )
                        ])['action']

                        if action == 'stop':
                            device._set_queued_cmd_stop_exec()
                            return
                        elif action == 'adjust':
                            new_margin = inquirer.prompt([
                                inquirer.Text('margin', 
                                    message="Nova margem de segurança (mm)",
                                    validate=lambda _, x: x.isdigit() and 5 <= int(x) <= 50)
                            ])['margin']
                            margin = int(new_margin)

            except Exception as e:
                print(f"Erro no monitor: {str(e)}")
                break
            time.sleep(0.5)

    # Inicia os sistemas em threads separadas
    threading.Thread(target=dynamic_spinner, daemon=True).start()
    threading.Thread(target=alert_system, daemon=True).start()

def main():
    """Fluxo principal da aplicação com UI integrada"""
    with yaspin(text="Buscando portas seriais...", color="green") as spinner:  # Customize color directly
        ports = [p.device for p in list_ports.comports()]
        if not ports:
            spinner.fail("❌ Nenhuma porta serial encontrada!")
            return

    # Seleção de porta com menu interativo
    selected_port = inquirer.prompt([
        inquirer.List(
            'port',
            message="Selecione a porta do Dobot",
            choices=ports,
            carousel=True
        )
    ])['port']

    # Conexão com feedback visual
    with yaspin(text="Conectando ao Dobot...", color="green") as spinner:  # Customize color directly
        try:
            robo = pydobot.Dobot(port=selected_port, verbose=False)
            spinner.ok("✔ Conectado!")
        except Exception as e:
            spinner.fail(f"❌ Falha na conexão: {str(e)}")
            return

    # Configuração inicial
    with yaspin(text="Configurando parâmetros...", color="green") as spinner:  # Customize color directly
        robo.speed(100, 100)
        start_limit_monitor(robo, margin=15)
        spinner.ok("✔ Pronto para operar!")

    # Menu principal interativo
    while True:
        action = inquirer.prompt([
            inquirer.List(
                'action',
                message="Controle do Dobot",
                choices=[
                    ('Mostrar posição atual', 'pose'),
                    ('Mover para posição', 'move'),
                    ('Testar limites', 'test'),
                    ('Sair', 'exit')
                ],
                carousel=True
            )
        ])['action']

        if action == 'pose':
            x, y, z, r, *_ = robo.pose()
            print(f"\nPosição atual:\nX: {x:.1f} mm\nY: {y:.1f} mm\nZ: {z:.1f} mm\nR: {r:.1f}°\n")
        
        elif action == 'move':
            coords = inquirer.prompt([
                inquirer.Text('x', message="Posição X (mm)"),
                inquirer.Text('y', message="Posição Y (mm)"),
                inquirer.Text('z', message="Posição Z (mm)"),
                inquirer.Text('r', message="Rotação R (°)")
            ])
            with yaspin(text="Movendo robô...", color="green") as spinner:  # Customize color directly
                robo.move_to(
                    x=float(coords['x']),
                    y=float(coords['y']),
                    z=float(coords['z']),
                    r=float(coords['r']),
                    wait=True
                )
                spinner.ok("✔ Movimento concluído!")

        elif action == 'test':
            with yaspin(text="Testando limites...", color="green") as spinner:  # Customize color directly
                for limit in [-180, 0, 180]:
                    robo.move_to(limit, 0, 150, 0, wait=True)
                spinner.ok("✔ Teste completo!")

        elif action == 'exit':
            with yaspin(text="Encerrando operação...", color="green") as spinner:  # Customize color directly
                robo.close()
                spinner.ok("✔ Conexão encerrada!")
            break

if __name__ == "__main__":
    main()
