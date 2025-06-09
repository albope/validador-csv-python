import csv
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk # <-- MODIFICADO: importamos ttk
import tkinter.font as tkFont
import threading # <-- NUEVO: importamos la librería para hilos

# ... (Las constantes no cambian) ...
COLOR_BG = "#f2f2f2"
COLOR_FG = "#333333"
COLOR_ERROR = "red"
COLOR_SUCCESS = "#008000"
FONT_FAM = "Segoe UI" 

class ValidadorCSVApp:
    def __init__(self, root):
        self.root = root
        self.configurar_ventana()
        
        try:
            self.font_titulo = tkFont.Font(family=FONT_FAM, size=16, weight="bold")
            self.font_subtitulo = tkFont.Font(family=FONT_FAM, size=11)
            self.font_stats = tkFont.Font(family=FONT_FAM, size=10, slant="italic")
            self.font_texto = tkFont.Font(family=FONT_FAM, size=10)
            self.font_texto_bold = tkFont.Font(family=FONT_FAM, size=10, weight="bold")
        except tk.TclError:
            self.font_titulo = tkFont.Font(family="Arial", size=16, weight="bold")
            self.font_subtitulo = tkFont.Font(family="Arial", size=11)
            self.font_stats = tkFont.Font(family="Arial", size=10, slant="italic")
            self.font_texto = tkFont.Font(family="Arial", size=10)
            self.font_texto_bold = tkFont.Font(family="Arial", size=10, weight="bold")

        # --- Variables de estado para el hilo ---
        self.validation_thread = None # <-- NUEVO: Para mantener una referencia al hilo
        self.resultados_validacion = None

        self._crear_widgets()

    def configurar_ventana(self):
        self.root.title("🧪 Validador CSV Profesional")
        self.root.geometry("900x750")
        self.root.configure(bg=COLOR_BG)
        self.root.minsize(700, 500)

    def _crear_widgets(self):
        tk.Label(self.root, text="🧪 Validador de CSV con revisión avanzada", font=self.font_titulo, bg=COLOR_BG, fg=COLOR_FG).pack(pady=(15, 0))
        tk.Label(self.root, text="Comprueba saltos de línea ocultos y errores de columnas", font=self.font_subtitulo, bg=COLOR_BG, fg="#555").pack(pady=(0, 20))

        boton_frame = tk.Frame(self.root, bg=COLOR_BG)
        boton_frame.pack(pady=5)
        
        # --- Guardamos una referencia al botón para poder deshabilitarlo ---
        self.select_button = tk.Button(boton_frame, text="📂 Seleccionar archivo CSV", command=self._seleccionar_archivo, bg="#e0e0e0", padx=10, pady=5) # <-- MODIFICADO
        self.select_button.grid(row=0, column=0, padx=10)
        
        tk.Button(boton_frame, text="💾 Exportar informe", command=self._exportar_informe, bg="#e0e0e0", padx=10, pady=5).grid(row=0, column=1, padx=10)
        tk.Button(boton_frame, text="🔄 Limpiar todo", command=self._limpiar, bg="#e0e0e0", padx=10, pady=5).grid(row=0, column=2, padx=10)

        self.ruta_label = tk.Label(self.root, text="📂 Archivo: (ninguno seleccionado)", font=self.font_texto, wraplength=850, justify="center", bg=COLOR_BG, fg=COLOR_FG)
        self.ruta_label.pack(pady=(10, 5), padx=20)
        
        # --- Creamos la barra de progreso ---
        self.progressbar = ttk.Progressbar(self.root, mode='indeterminate') # <-- NUEVO
        # No la mostramos todavía, lo haremos con .pack() cuando la necesitemos

        self.estadisticas_label = tk.Label(self.root, text="📊 Selecciona un archivo para ver las estadísticas", font=self.font_stats, bg=COLOR_BG, fg="#555")
        self.estadisticas_label.pack(pady=5)

        output_frame = tk.Frame(self.root, bd=1, relief="sunken")
        output_frame.pack(padx=20, pady=10, expand=True, fill="both")
        
        self.salida_texto = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, font=self.font_texto, relief="flat")
        self.salida_texto.pack(expand=True, fill="both")
        
        self.salida_texto.tag_config("error", foreground=COLOR_ERROR, font=self.font_texto_bold)
        self.salida_texto.tag_config("ok", foreground=COLOR_SUCCESS, font=self.font_texto_bold)
        self.salida_texto.tag_config("info", foreground="#444", font=self.font_texto_bold)
        self.salida_texto.config(state='disabled')

    def _seleccionar_archivo(self): # <-- MODIFICADO: Ahora orquesta el proceso
        """Abre el diálogo de archivo e inicia el proceso de validación en un hilo."""
        ruta = filedialog.askopenfilename(
            title="Selecciona un archivo CSV",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        if not ruta:
            return

        # Preparamos la UI para la validación
        self.select_button.config(state="disabled") # Deshabilitamos el botón
        self.ruta_label.config(text=f"📂 Procesando archivo:\n{ruta}")
        self._limpiar_resultados() # Limpiamos la pantalla anterior
        self.progressbar.pack(fill='x', padx=20, pady=5) # Mostramos la barra de progreso
        self.progressbar.start(10) # Iniciamos la animación

        # Creamos y arrancamos el hilo que hará el trabajo pesado
        self.validation_thread = threading.Thread(
            target=self._worker_validacion,
            args=(ruta,)
        )
        self.validation_thread.start()

        # Le pedimos a Tkinter que verifique el estado del hilo periódicamente
        self.root.after(100, self._verificar_hilo)

    def _worker_validacion(self, ruta_csv): # <-- NUEVO: El trabajo que se ejecuta en segundo plano
        """
        Esta función se ejecuta en un hilo separado.
        Llama a la función de validación original y almacena el resultado.
        """
        resultados = self._realizar_validacion(ruta_csv)
        self.resultados_validacion = resultados # Guardamos el resultado

    def _verificar_hilo(self): # <-- NUEVO: El verificador que se ejecuta en el hilo principal
        """
        Verifica si el hilo de trabajo ha terminado. Si es así, procesa los resultados.
        Si no, se vuelve a llamar a sí misma después de 100ms.
        """
        if self.validation_thread.is_alive():
            # El hilo sigue trabajando, volvemos a comprobar en 100ms
            self.root.after(100, self._verificar_hilo)
        else:
            # El hilo ha terminado, procesamos los resultados
            self.progressbar.stop() # Detenemos la animación
            self.progressbar.pack_forget() # Ocultamos la barra de progreso
            self.select_button.config(state="normal") # Rehabilitamos el botón
            self.ruta_label.config(text=f"📂 Archivo analizado:\n{self.resultados_validacion['ruta_archivo']}")

            self._mostrar_resultados()
            
    def _limpiar_resultados(self): # <-- NUEVO: Pequeña función de ayuda
        """Limpia el área de texto y las estadísticas."""
        self.salida_texto.config(state='normal')
        self.salida_texto.delete(1.0, tk.END)
        self.salida_texto.config(state='disabled')
        self.estadisticas_label.config(text="📊 Calculando estadísticas...")


    def _realizar_validacion(self, ruta_csv): # <-- MODIFICADO: Ahora solo hace el cálculo
        """
        Lógica de validación pura. No interactúa con la UI.
        Devuelve un diccionario con los resultados.
        """
        resultados = {
            'ruta_archivo': ruta_csv, # Guardamos la ruta para mostrarla después
            'total_filas': 0,
            'num_columnas_esperadas': None,
            'filas_invalidas': [],
            'celdas_con_saltos': [],
            'error_lectura': None
        }
        
        try:
            with open(ruta_csv, 'r', newline='', encoding='utf-8') as f:
                lector = csv.reader(f)
                
                try:
                    primera_fila = next(lector)
                    resultados['num_columnas_esperadas'] = len(primera_fila)
                    resultados['total_filas'] = 1
                    self._validar_fila(primera_fila, 1, resultados)
                except StopIteration:
                    return resultados

                for i, fila in enumerate(lector, start=2):
                    resultados['total_filas'] += 1
                    self._validar_fila(fila, i, resultados)

        except FileNotFoundError:
            resultados['error_lectura'] = "El archivo no se ha encontrado."
        except UnicodeDecodeError:
            resultados['error_lectura'] = "Error de codificación. Asegúrate de que el archivo está en formato UTF-8."
        except Exception as e:
            resultados['error_lectura'] = f"Error inesperado al leer el archivo:\n{e}"
            
        return resultados

    # El resto de funciones (_validar_fila, _mostrar_resultados, _exportar_informe, _limpiar)
    # permanecen prácticamente iguales, aunque _limpiar es ahora más simple.
    
    def _validar_fila(self, fila, num_fila, resultados):
        # ... (sin cambios)
        if len(fila) != resultados['num_columnas_esperadas']:
            resultados['filas_invalidas'].append((num_fila, len(fila), fila))
        for j, campo in enumerate(fila, start=1):
            if '\n' in campo or '\r' in campo:
                resultados['celdas_con_saltos'].append((num_fila, j, campo))

    def _mostrar_resultados(self):
        # ... (sin cambios)
        self.salida_texto.config(state='normal')
        self.salida_texto.delete(1.0, tk.END)
        res = self.resultados_validacion
        if res['error_lectura']:
            self.estadisticas_label.config(text="📊 Error al procesar el archivo")
            self.salida_texto.insert(tk.END, f"Error Crítico:\n{res['error_lectura']}", "error")
            self.salida_texto.config(state='disabled')
            return
        stats_text = (f"📊 Total filas: {res['total_filas']}  |  "
                      f"❌ Errores columnas: {len(res['filas_invalidas'])}  |  "
                      f"❌ Saltos internos: {len(res['celdas_con_saltos'])}")
        self.estadisticas_label.config(text=stats_text)
        self.salida_texto.insert(tk.END, "1. Validación de Número de Columnas\n\n", "info")
        if not res['filas_invalidas']:
            msg = f"✅ Todas las filas tienen el número esperado de columnas ({res['num_columnas_esperadas']}).\n\n"
            self.salida_texto.insert(tk.END, msg, "ok")
        else:
            msg = f"⚠️ Se esperaba {res['num_columnas_esperadas']} columnas, pero se encontraron filas con un número diferente:\n\n"
            self.salida_texto.insert(tk.END, msg)
            for fila_num, num_cols, contenido in res['filas_invalidas']:
                self.salida_texto.insert(tk.END, f"Fila {fila_num}: tiene {num_cols} columnas\n", "error")
                self.salida_texto.insert(tk.END, f"   Contenido: {contenido}\n\n")
        self.salida_texto.insert(tk.END, "2. Validación de Saltos de Línea Internos\n\n", "info")
        if not res['celdas_con_saltos']:
            self.salida_texto.insert(tk.END, "✅ Ninguna celda contiene saltos de línea internos.\n", "ok")
        else:
            self.salida_texto.insert(tk.END, "⚠️ Se encontraron celdas con saltos de línea internos:\n\n")
            for fila_num, col_num, contenido in res['celdas_con_saltos']:
                resumen = contenido.replace('\n', r'{\n}').replace('\r', r'{\r}')
                self.salida_texto.insert(tk.END, f"- Fila {fila_num}, Columna {col_num}:\n", "error")
                self.salida_texto.insert(tk.END, f"   Contenido: {resumen}\n\n")
        self.salida_texto.config(state='disabled')

    def _exportar_informe(self):
        # ... (sin cambios)
        if not self.resultados_validacion:
            messagebox.showinfo("Información", "Primero debes seleccionar y validar un archivo.")
            return
        if not self.resultados_validacion['filas_invalidas'] and not self.resultados_validacion['celdas_con_saltos'] and not self.resultados_validacion['error_lectura']:
            messagebox.showinfo("¡Todo correcto!", "El archivo está perfectamente validado. No hay errores que exportar.")
            return
        ruta_guardado = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt")],
            title="Guardar informe de errores"
        )
        if not ruta_guardado:
            return
        try:
            with open(ruta_guardado, "w", encoding="utf-8") as f:
                f.write("="*50 + "\n")
                f.write("INFORME DE VALIDACIÓN DE ARCHIVO CSV\n")
                f.write("="*50 + "\n")
                f.write(f"Archivo: {self.resultados_validacion['ruta_archivo']}\n\n")
                f.write(f"RESUMEN ESTADÍSTICO:\n{self.estadisticas_label.cget('text')}\n\n")
                contenido_informe = self.salida_texto.get("1.0", tk.END)
                f.write(contenido_informe)
            messagebox.showinfo("Exportado", f"Informe de errores guardado en:\n{ruta_guardado}")
        except Exception as e:
            messagebox.showerror("Error al exportar", f"No se pudo guardar el archivo:\n{e}")

    def _limpiar(self):
        # ... (ligeramente modificado para usar la nueva función de ayuda)
        self._limpiar_resultados()
        self.ruta_label.config(text="📂 Archivo: (ninguno seleccionado)")
        self.estadisticas_label.config(text="📊 Selecciona un archivo para ver las estadísticas")
        self.resultados_validacion = None

if __name__ == "__main__":
    root = tk.Tk()
    app = ValidadorCSVApp(root)
    root.mainloop()