# main.py

import tkinter as tk
from ui.app_ui import ValidadorCSVApp

def main():
    """Punto de entrada principal de la aplicación."""
    root = tk.Tk()
    app = ValidadorCSVApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()