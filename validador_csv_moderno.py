# -*- coding: utf--8 -*-

import csv
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import tkinter.font as tkFont
import threading

# --- Constantes de configuración de la UI ---
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

        self.validation_thread = None
        self.resultados_validacion = None

        self._crear_widgets()

    def configurar_ventana(self):
        self.root.title("🧪 Validador CSV Profesional")
        self.root.geometry("900x850")
        self.root.configure(bg=COLOR_BG)
        self.root.minsize(700, 600)

    def _crear_widgets(self):
        tk.Label(self.root, text="🧪 Validador de CSV con revisión avanzada", font=self.font_titulo, bg=COLOR_BG, fg=COLOR_FG).pack(pady=(15, 0))
        tk.Label(self.root, text="Comprueba saltos de línea, columnas, duplicados y más", font=self.font_subtitulo, bg=COLOR_BG, fg="#555").pack(pady=(0, 10))

        boton_frame = tk.Frame(self.root, bg=COLOR_BG)
        boton_frame.pack(pady=5)
        self.select_button = tk.Button(boton_frame, text="📂 Seleccionar y Validar", command=self._seleccionar_archivo, bg="#e0e0e0", padx=10, pady=5)
        self.select_button.grid(row=0, column=0, padx=10)
        tk.Button(boton_frame, text="💾 Exportar informe", command=self._exportar_informe, bg="#e0e0e0", padx=10, pady=5).grid(row=0, column=1, padx=10)
        tk.Button(boton_frame, text="🔄 Limpiar todo", command=self._limpiar, bg="#e0e0e0", padx=10, pady=5).grid(row=0, column=2, padx=10)
        
        options_frame = tk.LabelFrame(self.root, text="Opciones de Validación Avanzada", padx=10, pady=10, bg=COLOR_BG, font=self.font_texto_bold)
        options_frame.pack(padx=20, pady=10, fill='x')

        self.var_check_vacias = tk.BooleanVar(value=True)
        self.var_check_duplicadas = tk.BooleanVar(value=True)
        self.var_check_header = tk.BooleanVar(value=False)
        self.var_ignore_case = tk.BooleanVar(value=False)

        ttk.Checkbutton(options_frame, text="Detectar filas vacías", variable=self.var_check_vacias).grid(row=0, column=0, sticky='w', padx=5)
        
        dup_frame = tk.Frame(options_frame, bg=COLOR_BG)
        dup_frame.grid(row=0, column=1, sticky='w')
        ttk.Checkbutton(dup_frame, text="Detectar filas duplicadas", variable=self.var_check_duplicadas).pack(side='left')
        ttk.Checkbutton(dup_frame, text="(Ignorar Mayús/Minús)", variable=self.var_ignore_case).pack(side='left', padx=5)
        
        header_check = ttk.Checkbutton(options_frame, text="Validar cabecera (separada por comas):", variable=self.var_check_header, command=self._toggle_header_entry)
        header_check.grid(row=1, column=0, sticky='w', padx=5, pady=5)
        
        self.entry_header = ttk.Entry(options_frame, width=60, state='disabled')
        self.entry_header.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        self.ruta_label = tk.Label(self.root, text="📂 Archivo: (ninguno seleccionado)", font=self.font_texto, wraplength=850, justify="center", bg=COLOR_BG, fg=COLOR_FG)
        self.ruta_label.pack(pady=(10, 5), padx=20)
        
        self.progressbar = ttk.Progressbar(self.root, mode='indeterminate')

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

    def _toggle_header_entry(self):
        self.entry_header.config(state='normal' if self.var_check_header.get() else 'disabled')

    def _seleccionar_archivo(self):
        ruta = filedialog.askopenfilename(title="Selecciona un archivo CSV", filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")])
        if not ruta: return
            
        expected_headers = [h.strip() for h in self.entry_header.get().split(',') if h]
        validation_options = {
            'check_vacias': self.var_check_vacias.get(),
            'check_duplicadas': self.var_check_duplicadas.get(),
            'check_header': self.var_check_header.get(),
            'ignore_case': self.var_ignore_case.get(),
            'expected_headers': expected_headers
        }

        self.select_button.config(state="disabled")
        self.ruta_label.config(text=f"📂 Procesando archivo:\n{ruta}")
        self._limpiar_resultados()
        self.progressbar.pack(fill='x', padx=20, pady=5)
        self.progressbar.start(10)

        self.validation_thread = threading.Thread(target=self._worker_validacion, args=(ruta, validation_options))
        self.validation_thread.start()
        self.root.after(100, self._verificar_hilo)

    def _worker_validacion(self, ruta_csv, options):
        self.resultados_validacion = self._realizar_validacion(ruta_csv, options)

    def _verificar_hilo(self):
        if self.validation_thread.is_alive():
            self.root.after(100, self._verificar_hilo)
        else:
            self.progressbar.stop()
            self.progressbar.pack_forget()
            self.select_button.config(state="normal")
            self.ruta_label.config(text=f"📂 Archivo analizado:\n{self.resultados_validacion['ruta_archivo']}")
            self._mostrar_resultados()
            
    def _limpiar_resultados(self):
        self.salida_texto.config(state='normal')
        self.salida_texto.delete(1.0, tk.END)
        self.salida_texto.config(state='disabled')
        self.estadisticas_label.config(text="📊 Calculando estadísticas...")

    def _realizar_validacion(self, ruta_csv, options):
        resultados = {
            'ruta_archivo': ruta_csv, 'total_filas': 0, 'num_columnas_esperadas': None,
            'filas_invalidas': [], 'celdas_con_saltos': [], 'error_lectura': None,
            'filas_vacias': [], 'filas_duplicadas': {}, 'error_header': None
        }
        seen_rows_and_lines = {}

        try:
            with open(ruta_csv, 'r', newline='', encoding='utf-8') as f:
                lector = csv.reader(f)
                
                try:
                    primera_fila = next(lector)
                    resultados['total_filas'] = 1
                    
                    header_to_validate = primera_fila
                    expected_headers = options['expected_headers']
                    if options['check_header'] and expected_headers:
                        if options['ignore_case']:
                            header_to_validate = [h.lower().strip() for h in header_to_validate]
                            expected_headers = [h.lower().strip() for h in expected_headers]
                        
                        if header_to_validate != expected_headers:
                            resultados['error_header'] = f"La cabecera no coincide.\nSe esperaba: {options['expected_headers']}\nSe encontró: {primera_fila}"
                    
                    resultados['num_columnas_esperadas'] = len(primera_fila)
                    self._validar_fila(primera_fila, 1, resultados, options, seen_rows_and_lines)

                except StopIteration:
                    return resultados

                for i, fila in enumerate(lector, start=2):
                    resultados['total_filas'] += 1
                    self._validar_fila(fila, i, resultados, options, seen_rows_and_lines)

        except Exception as e:
            resultados['error_lectura'] = f"Error inesperado al leer el archivo: {e}"
        
        if options['check_duplicadas']:
            for row, lines in seen_rows_and_lines.items():
                if len(lines) > 1:
                    resultados['filas_duplicadas'][row] = sorted(lines)
                
        return resultados

    def _validar_fila(self, fila, num_fila, resultados, options, seen_rows_and_lines):
        """Valida una única fila aplicando las reglas activas."""
        
        # --- CORRECCIÓN CLAVE: Salida anticipada si la estructura de la fila es incorrecta ---
        if len(fila) != resultados['num_columnas_esperadas']:
            resultados['filas_invalidas'].append((num_fila, len(fila), fila))
            return # Si el número de columnas es incorrecto, no se realizan más validaciones en esta fila.

        # Comprobar si la fila está vacía (ahora se hace después de la comprobación de columnas)
        if options['check_vacias'] and not any(field.strip() for field in fila):
            resultados['filas_vacias'].append(num_fila)
            return
        
        # Comprobar saltos de línea internos
        for j, campo in enumerate(fila, start=1):
            if '\n' in campo or '\r' in campo:
                resultados['celdas_con_saltos'].append((num_fila, j, campo))
        
        # Lógica de duplicados (ahora solo se ejecuta en filas estructuralmente válidas)
        if options['check_duplicadas']:
            normalized_fila = [field.strip() for field in fila]
            if options['ignore_case']:
                normalized_fila = [field.lower() for field in normalized_fila]
            
            row_tuple = tuple(normalized_fila)
            
            if row_tuple not in seen_rows_and_lines:
                seen_rows_and_lines[row_tuple] = []
            seen_rows_and_lines[row_tuple].append(num_fila)

    def _mostrar_resultados(self):
        # (Sin cambios respecto a la versión anterior, ya era correcta)
        self.salida_texto.config(state='normal')
        self.salida_texto.delete(1.0, tk.END)
        res = self.resultados_validacion
        if res.get('error_lectura'):
            self.estadisticas_label.config(text="📊 Error al procesar el archivo")
            self.salida_texto.insert(tk.END, f"Error Crítico:\n{res['error_lectura']}", "error")
            self.salida_texto.config(state='disabled')
            return
        stats_text = (f"📊 Total filas: {res.get('total_filas', 0)} | "
                      f"❌ Columnas: {len(res.get('filas_invalidas', []))} | "
                      f"❌ Saltos: {len(res.get('celdas_con_saltos', []))} | "
                      f"❌ Vacías: {len(res.get('filas_vacias', []))} | "
                      f"❌ Duplicadas: {len(res.get('filas_duplicadas', {}))}")
        self.estadisticas_label.config(text=stats_text)
        if res.get('error_header'):
            self.salida_texto.insert(tk.END, "Validación de Cabecera\n\n", "info")
            self.salida_texto.insert(tk.END, f"⛔ {res['error_header']}\n\n", "error")
        self.salida_texto.insert(tk.END, "Validación de Número de Columnas\n\n", "info")
        if not res.get('filas_invalidas'):
            msg = f"✅ Todas las filas tienen el número esperado de columnas ({res.get('num_columnas_esperadas', 'N/A')}).\n\n"
            self.salida_texto.insert(tk.END, msg, "ok")
        else:
            msg = f"⚠️ Se esperaba {res.get('num_columnas_esperadas', 'N/A')} columnas, pero se encontraron filas con un número diferente:\n\n"
            self.salida_texto.insert(tk.END, msg, "error")
            for fila_num, num_cols, contenido in res['filas_invalidas']:
                self.salida_texto.insert(tk.END, f"Fila {fila_num}: tiene {num_cols} columnas\n   Contenido: {contenido}\n\n")
        self.salida_texto.insert(tk.END, "Validación de Saltos de Línea Internos\n\n", "info")
        if not res.get('celdas_con_saltos'):
             self.salida_texto.insert(tk.END, "✅ Ninguna celda contiene saltos de línea internos.\n\n", "ok")
        else:
            self.salida_texto.insert(tk.END, "⚠️ Se encontraron celdas con saltos de línea internos:\n\n", "error")
            for fila_num, col_num, contenido in res['celdas_con_saltos']:
                resumen = contenido.replace('\n', r'{\n}').replace('\r', r'{\r}')
                self.salida_texto.insert(tk.END, f"- Fila {fila_num}, Columna {col_num}:\n   Contenido: {resumen}\n\n")
        if res.get('filas_vacias'):
            self.salida_texto.insert(tk.END, "Detección de Filas Vacías\n\n", "info")
            self.salida_texto.insert(tk.END, f"⚠️ Se encontraron filas vacías en las líneas: {', '.join(map(str, res['filas_vacias']))}\n\n", "error")
        if res.get('filas_duplicadas'):
            self.salida_texto.insert(tk.END, "Detección de Filas Duplicadas\n\n", "info")
            self.salida_texto.insert(tk.END, "⚠️ Se encontraron los siguientes grupos de filas duplicadas:\n\n", "error")
            for row_tuple, line_numbers in res['filas_duplicadas'].items():
                self.salida_texto.insert(tk.END, f"Contenido duplicado encontrado en las filas {', '.join(map(str, line_numbers))}:\n")
                self.salida_texto.insert(tk.END, f"   {list(row_tuple)}\n\n")
        self.salida_texto.config(state='disabled')

    def _exportar_informe(self):
        # (Sin cambios)
        if not self.resultados_validacion: messagebox.showinfo("Información", "Primero debes seleccionar y validar un archivo."); return
        has_errors = any([self.resultados_validacion.get(key) for key in ['filas_invalidas', 'celdas_con_saltos', 'error_lectura', 'filas_vacias', 'filas_duplicadas', 'error_header']])
        if not has_errors: messagebox.showinfo("¡Todo correcto!", "El archivo está perfectamente validado. No hay errores que exportar."); return
        ruta_guardado = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Archivos de texto", "*.txt")], title="Guardar informe de errores")
        if not ruta_guardado: return
        try:
            with open(ruta_guardado, "w", encoding="utf-8") as f:
                f.write("="*50 + "\nINFORME DE VALIDACIÓN DE ARCHIVO CSV\n" + "="*50 + "\n")
                f.write(f"Archivo: {self.resultados_validacion['ruta_archivo']}\n\n")
                f.write(f"RESUMEN ESTADÍSTICO:\n{self.estadisticas_label.cget('text')}\n\n")
                f.write(self.salida_texto.get("1.0", tk.END))
            messagebox.showinfo("Exportado", f"Informe de errores guardado en:\n{ruta_guardado}")
        except Exception as e: messagebox.showerror("Error al exportar", f"No se pudo guardar el archivo:\n{e}")

    def _limpiar(self):
        # (Sin cambios)
        self._limpiar_resultados()
        self.ruta_label.config(text="📂 Archivo: (ninguno seleccionado)")
        self.estadisticas_label.config(text="📊 Selecciona un archivo para ver las estadísticas")
        self.resultados_validacion = None
        self.var_check_header.set(False)
        self.var_check_vacias.set(True)
        self.var_check_duplicadas.set(True)
        self.var_ignore_case.set(False)
        self._toggle_header_entry()

if __name__ == "__main__":
    root = tk.Tk()
    app = ValidadorCSVApp(root)
    root.mainloop()