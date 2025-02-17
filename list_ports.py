# Traz a ferramenta serial para apresentar quais portas estão disponíveis
from serial.tools import list_ports

import pydobot

# Listas as portas seriais disponíveis
available_ports = list_ports.comports()


# Imprime as portas disponíveis
print(f'available ports: {[x.device for x in available_ports]}')
