# ui/tooltip.py

import customtkinter

class ToolTip:
    """
    Crea un tooltip (mensaje emergente) para un widget de customtkinter.
    """
    def __init__(self, widget, text, font=("Segoe UI", 10)):
        self.widget = widget
        self.text = text
        self.font = font
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        # Destruir cualquier tooltip anterior para evitar duplicados
        if self.tooltip_window:
            self.tooltip_window.destroy()

        # Posición del tooltip relativa al widget
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        # Crear una ventana Toplevel sin bordes
        self.tooltip_window = customtkinter.CTkToplevel(self.widget)
        self.tooltip_window.overrideredirect(True)
        self.tooltip_window.geometry(f"+{x}+{y}")
        self.tooltip_window.lift()

        label = customtkinter.CTkLabel(
            self.tooltip_window,
            text=self.text,
            font=self.font,
            fg_color=("#F0F0F0", "#2b2b2b"), # Colores para tema claro y oscuro
            text_color=("#121212", "#E0E0E0"),
            corner_radius=6,
            padx=8,
            pady=4,
            justify="left"
        )
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None