# ui/tooltip.py

import customtkinter

class ToolTip:
    """
    Crea un tooltip (mensaje emergente) robusto para un widget de customtkinter
    que se oculta automáticamente para no quedarse fijo en pantalla.
    """
    def __init__(self, widget, text, font=("Segoe UI", 10), delay=500, duration=7000):
        self.widget = widget
        self.text = text
        self.font = font
        self.delay = delay  # Tiempo en ms que tarda en aparecer
        self.duration = duration # Tiempo en ms que el tooltip permanece visible
        self.tooltip_window = None
        self.show_id = None
        self.hide_id = None

        self.widget.bind("<Enter>", self.schedule_show)
        self.widget.bind("<Leave>", self.schedule_hide)
        self.widget.bind("<Button-1>", self.hide_tooltip) # Ocultar si se hace clic

    def schedule_show(self, event=None):
        """Programa la aparición del tooltip después de un breve retraso."""
        self.cancel_scheduled_hide() # Cancelar cualquier ocultación programada
        if not self.tooltip_window:
            self.show_id = self.widget.after(self.delay, self.show_tooltip)

    def schedule_hide(self, event=None):
        """Programa la ocultación del tooltip."""
        self.cancel_scheduled_show()
        if self.tooltip_window:
            self.hide_id = self.widget.after(100, self.hide_tooltip)

    def show_tooltip(self, event=None):
        """Crea y muestra la ventana del tooltip."""
        if self.tooltip_window:
            return

        # Calcular posición
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tooltip_window = customtkinter.CTkToplevel(self.widget)
        self.tooltip_window.overrideredirect(True) # Ventana sin bordes
        self.tooltip_window.geometry(f"+{x}+{y}")
        self.tooltip_window.lift()
        self.tooltip_window.attributes("-topmost", True) # Mantener siempre visible

        label = customtkinter.CTkLabel(
            self.tooltip_window,
            text=self.text,
            font=self.font,
            fg_color=("#E5E5E5", "#222222"),
            text_color=("#121212", "#E0E0E0"),
            corner_radius=6,
            padx=10,
            pady=5,
            justify="left"
        )
        label.pack()

        # Programar la autodestrucción para evitar que se quede fijo
        self.hide_id = self.widget.after(self.duration, self.hide_tooltip)

    def hide_tooltip(self, event=None):
        """Destruye la ventana del tooltip."""
        self.cancel_scheduled_show()
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def cancel_scheduled_show(self):
        if self.show_id:
            self.widget.after_cancel(self.show_id)
            self.show_id = None
            
    def cancel_scheduled_hide(self):
        if self.hide_id:
            self.widget.after_cancel(self.hide_id)
            self.hide_id = None