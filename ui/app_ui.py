# ui/app_ui.py

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import tkinter.font as tkFont
import threading
import logging

# Importaciones de nuestros propios módulos
from .constants import *
from validators import realizar_validacion_completa

logger = logging.getLogger(__name__)

class ValidadorCSVApp:
    def __init__(self, root):
        self.root = root
        logger.info("Inicializando la clase ValidadorCSVApp.")
        self.configurar_ventana()

        try:
            self.font_titulo = tkFont.Font(family=FONT_FAM, size=16, weight="bold")
            self.font_subtitulo = tkFont.Font(family=FONT_FAM, size=11)
            self.font_stats = tkFont.Font(family=FONT_FAM, size=10, slant="italic")
            self.font_texto = tkFont.Font(family=FONT_FAM, size=10)
            self.font_texto_bold = tkFont.Font(family=FONT_FAM, size=10, weight="bold")
        except tk.TclError:
            logger.warning(f"La fuente '{FONT_FAM}' no se encontró. Usando 'Arial' como alternativa.")
            self.font_titulo = tkFont.Font(family="Arial", size=16, weight="bold")
            self.font_subtitulo = tkFont.Font(family="Arial", size=11)
            self.font_stats = tkFont.Font(family="Arial", size=10, slant="italic")
            self.font_texto = tkFont.Font(family="Arial", size=10)
            self.font_texto_bold = tkFont.Font(family="Arial", size=10, weight="bold")

        self.validation_thread = None
        self.resultados_validacion = None
        self.treeview_sort_column = None
        self.treeview_sort_reverse = False

        self._crear_widgets()

    def configurar_ventana(self):
        self.root.title("🧪 Validador CSV Profesional")
        self.root.geometry("950x900")
        self.root.configure(bg=COLOR_BG)
        self.root.minsize(800, 600)

    def _crear_widgets(self):
        # --- Contenedor principal ---
        main_frame = tk.Frame(self.root, bg=COLOR_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Frame superior para controles ---
        top_frame = tk.Frame(main_frame, bg=COLOR_BG)
        top_frame.pack(fill=tk.X, pady=5)

        tk.Label(top_frame, text="🧪 Validador de CSV con revisión avanzada", font=self.font_titulo, bg=COLOR_BG, fg=COLOR_FG).pack(pady=(5, 0))
        tk.Label(top_frame, text="Comprueba saltos de línea, columnas, duplicados y más", font=self.font_subtitulo, bg=COLOR_BG, fg="#555").pack(pady=(0, 10))

        boton_frame = tk.Frame(top_frame, bg=COLOR_BG)
        boton_frame.pack(pady=5)
        self.select_button = tk.Button(boton_frame, text="📂 Seleccionar y Validar", command=self._seleccionar_archivo, bg="#e0e0e0", padx=10, pady=5)
        self.select_button.grid(row=0, column=0, padx=10)
        tk.Button(boton_frame, text="💾 Exportar informe", command=self._exportar_informe, bg="#e0e0e0", padx=10, pady=5).grid(row=0, column=1, padx=10)
        tk.Button(boton_frame, text="🔄 Limpiar todo", command=self._limpiar, bg="#e0e0e0", padx=10, pady=5).grid(row=0, column=2, padx=10)
        
        options_frame = tk.LabelFrame(top_frame, text="Opciones de Validación Avanzada", padx=10, pady=10, bg=COLOR_BG, font=self.font_texto_bold)
        options_frame.pack(padx=10, pady=10, fill='x')

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

        self.ruta_label = tk.Label(top_frame, text="📂 Archivo: (ninguno seleccionado)", font=self.font_texto, wraplength=850, justify="center", bg=COLOR_BG, fg=COLOR_FG)
        self.ruta_label.pack(pady=5, padx=20)
        
        self.progressbar = ttk.Progressbar(top_frame, mode='indeterminate')
        self.progressbar.pack(fill='x', padx=20, pady=5)
        self.progressbar.pack_forget() # Ocultarla al inicio

        self.estadisticas_label = tk.Label(top_frame, text="📊 Selecciona un archivo para ver las estadísticas", font=self.font_stats, bg=COLOR_BG, fg="#555")
        self.estadisticas_label.pack(pady=5)

        # --- NUEVO: Frame para el Treeview ---
        tree_frame = tk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ('linea', 'tipo_error', 'descripcion', 'contenido')
        self.results_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

        # Definir cabeceras y funcionalidad de ordenación
        self.results_tree.heading('linea', text='Línea', command=lambda: self._sort_treeview_column('linea', False))
        self.results_tree.heading('tipo_error', text='Tipo de Error', command=lambda: self._sort_treeview_column('tipo_error', False))
        self.results_tree.heading('descripcion', text='Descripción', command=lambda: self._sort_treeview_column('descripcion', False))
        self.results_tree.heading('contenido', text='Contenido de la Fila', command=lambda: self._sort_treeview_column('contenido', False))

        # Definir anchos de columna
        self.results_tree.column('linea', width=80, stretch=tk.NO, anchor='center')
        self.results_tree.column('tipo_error', width=150, stretch=tk.NO)
        self.results_tree.column('descripcion', width=300)
        self.results_tree.column('contenido', width=500)

        # Añadir Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.results_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.results_tree.pack(side='left', fill='both', expand=True)

    def _sort_treeview_column(self, col, reverse):
        """Función para ordenar las columnas del Treeview al hacer clic."""
        try:
            # Obtener los datos de la columna como una lista de tuplas (valor, item_id)
            data_list = [(self.results_tree.set(k, col), k) for k in self.results_tree.get_children('')]
            
            # Determinar la clave de ordenación (numérica para línea, texto para el resto)
            key_func = lambda t: t[0]
            if col == 'linea':
                # Intentar convertir a entero para ordenación numérica correcta
                try:
                    key_func = lambda t: int(t[0])
                except (ValueError, TypeError):
                    pass # Si falla, se ordena como texto

            data_list.sort(key=key_func, reverse=reverse)

            # Reorganizar los items en el treeview
            for index, (val, k) in enumerate(data_list):
                self.results_tree.move(k, '', index)

            # Invertir el orden para el próximo clic en la misma columna
            self.results_tree.heading(col, command=lambda: self._sort_treeview_column(col, not reverse))
        except Exception as e:
            logger.error(f"Error al ordenar la columna {col}: {e}")


    def _toggle_header_entry(self):
        self.entry_header.config(state='normal' if self.var_check_header.get() else 'disabled')

    def _seleccionar_archivo(self):
        ruta = filedialog.askopenfilename(title="Selecciona un archivo CSV", filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")])
        if not ruta:
            logger.warning("El usuario canceló la selección de archivo.")
            return
        
        logger.info(f"Archivo seleccionado por el usuario: {ruta}")
        
        expected_headers = [h.strip() for h in self.entry_header.get().split(',') if h]
        
        validation_options = {
            'check_vacias': self.var_check_vacias.get(),
            'check_duplicadas': self.var_check_duplicadas.get(),
            'check_header': self.var_check_header.get(),
            'ignore_case': self.var_ignore_case.get(),
            'expected_headers': expected_headers
        }
        
        logger.info(f"Opciones de validación seleccionadas: {validation_options}")

        self.select_button.config(state="disabled")
        self.ruta_label.config(text=f"📂 Procesando archivo:\n{ruta}")
        self._limpiar_resultados()
        self.progressbar.pack(fill='x', padx=20, pady=5)
        self.progressbar.start(10)

        logger.info("Iniciando hilo de validación...")
        self.validation_thread = threading.Thread(target=self._worker_validacion, args=(ruta, validation_options))
        self.validation_thread.start()
        self.root.after(100, self._verificar_hilo)

    def _worker_validacion(self, ruta_csv, options):
        logger.info(f"El hilo de trabajo ha comenzado la validación para: {ruta_csv}")
        self.resultados_validacion = realizar_validacion_completa(ruta_csv, options)
        logger.info(f"El hilo de trabajo ha finalizado la validación.")

    def _verificar_hilo(self):
        if self.validation_thread.is_alive():
            self.root.after(100, self._verificar_hilo)
        else:
            logger.info("El hilo de trabajo ha sido verificado como finalizado. Mostrando resultados.")
            self.progressbar.pack_forget()
            self.select_button.config(state="normal")
            if self.resultados_validacion:
                self.ruta_label.config(text=f"📂 Archivo analizado:\n{self.resultados_validacion['ruta_archivo']}")
                self._mostrar_resultados()
            else:
                logger.error("El hilo de validación terminó pero no se encontraron resultados.")
                messagebox.showerror("Error", "La validación terminó inesperadamente sin resultados.")
            
    def _limpiar_resultados(self):
        """Limpia la tabla de resultados y las estadísticas."""
        self.results_tree.delete(*self.results_tree.get_children())
        self.estadisticas_label.config(text="📊 Calculando estadísticas...")
    
    def _mostrar_resultados(self):
        self._limpiar_resultados() # Limpiamos antes de mostrar
        res = self.resultados_validacion
        if not res:
            logger.error("Se intentó mostrar resultados, pero el diccionario de resultados está vacío.")
            return

        if res.get('error_lectura'):
            self.estadisticas_label.config(text="📊 Error al procesar el archivo")
            messagebox.showerror("Error de Lectura", res['error_lectura'])
            return

        stats_text = (f"📊 Total filas: {res.get('total_filas', 0)} | "
                      f"❌ Columnas: {len(res.get('filas_invalidas', []))} | "
                      f"❌ Saltos: {len(res.get('celdas_con_saltos', []))} | "
                      f"❌ Vacías: {len(res.get('filas_vacias', []))} | "
                      f"❌ Duplicadas: {len(res.get('filas_duplicadas', {}))}")
        self.estadisticas_label.config(text=stats_text)
        
        # Insertar errores en el Treeview
        if res.get('error_header'):
            self.results_tree.insert('', 'end', values=('-', 'Cabecera', res['error_header'], ''))

        for fila_num, num_cols, contenido in res.get('filas_invalidas', []):
            desc = f"Se esperaban {res.get('num_columnas_esperadas')} columnas, pero tiene {num_cols}"
            self.results_tree.insert('', 'end', values=(fila_num, 'Nº de Columnas', desc, str(contenido)))

        for fila_num, col_num, contenido in res.get('celdas_con_saltos', []):
            desc = f"Salto de línea encontrado en la columna {col_num}"
            self.results_tree.insert('', 'end', values=(fila_num, 'Salto de Línea', desc, contenido.replace('\n', r'{\n}')))

        for fila_num in res.get('filas_vacias', []):
            self.results_tree.insert('', 'end', values=(fila_num, 'Fila Vacía', 'La fila no contiene datos', ''))

        for row_tuple, line_numbers in res.get('filas_duplicadas', {}).items():
            desc = f"Aparece en las líneas: {', '.join(map(str, line_numbers))}"
            self.results_tree.insert('', 'end', values=(line_numbers[0], 'Fila Duplicada', desc, str(list(row_tuple))))

    def _exportar_informe(self):
        if not self.resultados_validacion:
            messagebox.showinfo("Información", "Primero debes seleccionar y validar un archivo.")
            return

        has_errors = any([self.resultados_validacion.get(key) for key in ['filas_invalidas', 'celdas_con_saltos', 'error_lectura', 'filas_vacias', 'filas_duplicadas', 'error_header']])
        if not has_errors:
            messagebox.showinfo("¡Todo correcto!", "El archivo está perfectamente validado. No hay errores que exportar.")
            return
            
        ruta_guardado = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Archivos de texto", "*.txt")], title="Guardar informe de errores")
        if not ruta_guardado:
            logger.warning("El usuario canceló la exportación del informe.")
            return
        
        logger.info(f"Exportando informe a: {ruta_guardado}")
        try:
            with open(ruta_guardado, "w", encoding="utf-8") as f:
                res = self.resultados_validacion
                f.write("="*80 + "\nINFORME DE VALIDACIÓN DE ARCHIVO CSV\n" + "="*80 + "\n")
                f.write(f"Archivo: {res['ruta_archivo']}\n\n")
                f.write(f"RESUMEN ESTADÍSTICO:\n{self.estadisticas_label.cget('text')}\n\n")
                
                f.write("-" * 80 + "\nDETALLE DE ERRORES\n" + "-"*80 + "\n\n")

                if res.get('error_header'):
                    f.write("--- ERROR DE CABECERA ---\n")
                    f.write(f"{res['error_header']}\n\n")

                if res.get('filas_invalidas'):
                    f.write("--- ERRORES DE NÚMERO DE COLUMNAS ---\n")
                    for fila_num, num_cols, contenido in res['filas_invalidas']:
                        f.write(f"Línea {fila_num}: Se esperaban {res.get('num_columnas_esperadas')} columnas, pero tiene {num_cols}. Contenido: {contenido}\n")
                    f.write("\n")
                
                if res.get('celdas_con_saltos'):
                    f.write("--- ERRORES DE SALTOS DE LÍNEA ---\n")
                    for fila_num, col_num, contenido in res['celdas_con_saltos']:
                        f.write(f"Línea {fila_num}, Columna {col_num}: Contenido con salto de línea: {contenido.replace(chr(10), '{LF}')}\n")
                    f.write("\n")

                if res.get('filas_vacias'):
                    f.write("--- FILAS VACÍAS ENCONTRADAS ---\n")
                    f.write(f"Líneas: {', '.join(map(str, res['filas_vacias']))}\n\n")

                if res.get('filas_duplicadas'):
                    f.write("--- GRUPOS DE FILAS DUPLICADAS ---\n")
                    for row_tuple, line_numbers in res['filas_duplicadas'].items():
                        f.write(f"Contenido duplicado en líneas {', '.join(map(str, line_numbers))}:\n")
                        f.write(f"   {list(row_tuple)}\n")
                    f.write("\n")

            messagebox.showinfo("Exportado", f"Informe de errores guardado en:\n{ruta_guardado}")
            logger.info("Informe exportado con éxito.")
        except Exception:
            logger.error("Error durante la exportación del informe.", exc_info=True)
            messagebox.showerror("Error al exportar", f"No se pudo guardar el archivo. Revise 'validator.log' para detalles.")

    def _limpiar(self):
        logger.info("Limpiando la interfaz de usuario.")
        self._limpiar_resultados()
        self.ruta_label.config(text="📂 Archivo: (ninguno seleccionado)")
        self.estadisticas_label.config(text="📊 Selecciona un archivo para ver las estadísticas")
        self.resultados_validacion = None
        self.var_check_header.set(False)
        self.var_check_vacias.set(True)
        self.var_check_duplicadas.set(True)
        self.var_ignore_case.set(False)
        self._toggle_header_entry()