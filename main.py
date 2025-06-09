# main.py (Modificado)

import tkinter as tk
import logging  # <-- NUEVO
from ui.app_ui import ValidadorCSVApp

def main():
    """Punto de entrada principal de la aplicación."""

    # --- NUEVO: Configuración del Logging ---
    logging.basicConfig(
        level=logging.INFO,  # Nivel mínimo de mensajes a registrar (INFO, WARNING, ERROR, CRITICAL)
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', # Formato de cada línea de log
        filename='validator.log',  # Nombre del archivo de log
        filemode='w'  # 'w' para sobrescribir el log cada vez, 'a' para añadir (append)
    )
    # --- FIN de la Configuración ---

    logging.info("Iniciando la aplicación Validador CSV...")

    try:
        root = tk.Tk()
        app = ValidadorCSVApp(root)
        root.mainloop()
    except Exception as e:
        logging.critical("Ha ocurrido un error fatal en la aplicación.", exc_info=True)
    finally:
        logging.info("La aplicación se ha cerrado.\n" + "="*50)

if __name__ == "__main__":
    main()