# main.py

import customtkinter
import logging
from ui.app_ui import ValidadorCSVApp

def main():
    """Punto de entrada principal de la aplicación."""

    # --- Configuración del Logging ---
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        filename='validator.log',
        filemode='w'
    )
    
    # --- Configuración de CustomTkinter ---
    customtkinter.set_appearance_mode("System")  # Modos: "System" (default), "Dark", "Light"
    customtkinter.set_default_color_theme("blue")  # Temas: "blue" (default), "green", "dark-blue"
    
    logging.info("Iniciando la aplicación Validador CSV con customtkinter...")

    try:
        root = customtkinter.CTk() # Usamos la ventana principal de customtkinter
        app = ValidadorCSVApp(root)
        root.mainloop()
    except Exception as e:
        logging.critical("Ha ocurrido un error fatal en la aplicación.", exc_info=True)
    finally:
        logging.info("La aplicación se ha cerrado.\n" + "="*50)

if __name__ == "__main__":
    main()