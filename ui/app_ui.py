# ui/app_ui.py

import customtkinter
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import logging

from .constants import *
from validators import realizar_validacion_completa, crear_csv_limpio, leer_primeras_lineas

logger = logging.getLogger(__name__)

class ValidadorCSVApp:
    def __init__(self, root):
        self.root = root
        logger.info("Inicializando la clase ValidadorCSVApp con customtkinter.")
        self.configurar_ventana()

        self.validation_thread = None
        self.resultados_validacion = None
        self.ruta_archivo_actual = None
        
        self._configure_treeview_style()
        self._crear_widgets()
        self._update_treeview_theme(customtkinter.get_appearance_mode())

    def configurar_ventana(self):
        self.root.title("🧪 Validador CSV Profesional")
        self.root.geometry("1100x900")
        self.root.minsize(800, 700)

    def _configure_treeview_style(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
    def _update_treeview_theme(self, mode):
        logger.info(f"Actualizando el tema del Treeview a: {mode}")
        mode = mode.capitalize()
        if mode == "Dark":
            self.style.configure('Treeview', background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
            self.style.configure('Treeview.Heading', background="#3a3d40", foreground="white", relief="flat")
            self.style.map('Treeview.Heading', background=[('active', '#4a4d50')])
        else:
            self.style.configure('Treeview', background="#ffffff", foreground="black", fieldbackground="#ffffff", borderwidth=0)
            self.style.configure('Treeview.Heading', background="#f0f0f0", foreground="black", relief="flat")
            self.style.map('Treeview.Heading', background=[('active', '#e0e0e0')])

    def _crear_widgets(self):
        main_frame = customtkinter.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill=customtkinter.BOTH, expand=True, padx=10, pady=10)

        top_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        top_frame.pack(fill=customtkinter.X, pady=5)
        
        title_theme_frame = customtkinter.CTkFrame(top_frame, fg_color="transparent")
        title_theme_frame.pack(fill=customtkinter.X, pady=(0, 5))
        customtkinter.CTkLabel(title_theme_frame, text="🧪 Validador de CSV con revisión avanzada", font=("Segoe UI", 20, "bold")).pack(side="left", pady=(5, 0))
        theme_menu = customtkinter.CTkOptionMenu(title_theme_frame, values=["Light", "Dark", "System"], command=self.change_appearance_mode_event, width=100)
        theme_menu.pack(side="right", pady=(5,0), padx=5)
        customtkinter.CTkLabel(title_theme_frame, text="Tema:", font=("Segoe UI", 12)).pack(side="right", pady=(5,0))

        customtkinter.CTkLabel(top_frame, text="Comprueba saltos de línea, columnas, duplicados y más", font=("Segoe UI", 12)).pack(anchor="w", pady=(0, 10))

        boton_frame = customtkinter.CTkFrame(top_frame, fg_color="transparent")
        boton_frame.pack(fill=customtkinter.X, pady=5)
        
        # --- CORRECCIÓN: Asignar el botón a self.select_button ---
        self.select_button = customtkinter.CTkButton(boton_frame, text="📂 Seleccionar Archivo", command=self._seleccionar_archivo)
        self.select_button.pack(side="left", padx=(0, 5))
        
        self.validate_button = customtkinter.CTkButton(boton_frame, text="🚀 Iniciar Validación", command=self._iniciar_validacion, state="disabled")
        self.validate_button.pack(side="left", padx=5)
        self.clean_export_button = customtkinter.CTkButton(boton_frame, text="✨ Exportar CSV Limpio", command=self._exportar_csv_limpio, state="disabled")
        self.clean_export_button.pack(side="left", padx=5)
        self.export_informe_button = customtkinter.CTkButton(boton_frame, text="💾 Exportar Informe", command=self._exportar_informe, state="disabled")
        self.export_informe_button.pack(side="left", padx=5)
        customtkinter.CTkButton(boton_frame, text="🔄 Limpiar Todo", command=self._limpiar).pack(side="left", padx=5)
        
        options_frame = customtkinter.CTkFrame(top_frame)
        options_frame.pack(padx=0, pady=10, fill='x')

        self.var_check_vacias = customtkinter.BooleanVar(value=True)
        self.var_check_duplicadas = customtkinter.BooleanVar(value=True)
        self.var_check_header = customtkinter.BooleanVar(value=False)
        self.var_ignore_case = customtkinter.BooleanVar(value=False)
        self.var_check_uniqueness = customtkinter.BooleanVar(value=False)

        customtkinter.CTkCheckBox(options_frame, text="Detectar filas vacías", variable=self.var_check_vacias).grid(row=0, column=0, sticky='w', padx=10, pady=5)
        dup_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        dup_frame.grid(row=0, column=1, sticky='w', padx=10, pady=5)
        customtkinter.CTkCheckBox(dup_frame, text="Detectar filas duplicadas", variable=self.var_check_duplicadas).pack(side='left')
        customtkinter.CTkCheckBox(dup_frame, text="(Ignorar Mayús/Minús)", variable=self.var_ignore_case).pack(side='left', padx=5)
        header_check_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        header_check_frame.grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        customtkinter.CTkCheckBox(header_check_frame, text="Validar cabecera (separada por comas):", variable=self.var_check_header, command=self._toggle_header_entry).pack(side='left')
        self.entry_header = customtkinter.CTkEntry(header_check_frame, width=400, state='disabled')
        self.entry_header.pack(side='left', padx=5, fill='x', expand=True)
        encoding_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        encoding_frame.grid(row=2, column=0, sticky='w', padx=5, pady=5)
        customtkinter.CTkLabel(encoding_frame, text="Codificación del archivo:").pack(side='left', padx=(5,0))
        self.encoding_var = customtkinter.StringVar(value='utf-8')
        self.encoding_menu = customtkinter.CTkOptionMenu(encoding_frame, variable=self.encoding_var, values=['utf-8', 'latin-1', 'cp1252', 'iso-8859-1'])
        self.encoding_menu.pack(side='left', padx=5)
        
        uniqueness_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        uniqueness_frame.grid(row=2, column=1, sticky='w', padx=10, pady=5)
        customtkinter.CTkCheckBox(uniqueness_frame, text="Verificar unicidad en columna:", variable=self.var_check_uniqueness).pack(side='left')
        self.unique_column_var = customtkinter.StringVar(value="(Seleccione archivo)")
        self.unique_column_menu = customtkinter.CTkOptionMenu(uniqueness_frame, variable=self.unique_column_var, values=["(Seleccione archivo)"], state="disabled")
        self.unique_column_menu.pack(side='left', padx=5)

        self.ruta_label = customtkinter.CTkLabel(top_frame, text="📂 Archivo: (ninguno seleccionado)", font=("Segoe UI", 12), wraplength=850)
        self.ruta_label.pack(fill=customtkinter.X, pady=5, padx=10)
        
        self.progressbar = customtkinter.CTkProgressBar(top_frame)
        self.progressbar.set(0)

        self.estadisticas_label = customtkinter.CTkLabel(top_frame, text="📊 Selecciona un archivo para ver las estadísticas", font=("Segoe UI", 12, "italic"))
        self.estadisticas_label.pack(fill=customtkinter.X, pady=5)

        self.tab_view = customtkinter.CTkTabview(main_frame, fg_color="transparent")
        self.tab_view.pack(fill='both', expand=True, padx=0, pady=(5,0))
        self.tab_preview = self.tab_view.add("📄 Previsualización del Archivo")
        self.tab_results = self.tab_view.add("📊 Resultados de Validación")
        self.tab_view.set("📄 Previsualización del Archivo")

        self.preview_tree = ttk.Treeview(self.tab_preview, style='Treeview', show='headings')
        self.preview_tree.pack(fill='both', expand=True, padx=2, pady=2)

        results_tree_frame = customtkinter.CTkFrame(self.tab_results, fg_color="transparent")
        results_tree_frame.pack(fill='both', expand=True, padx=2, pady=2)
        columns = ('linea', 'tipo_error', 'descripcion', 'contenido')
        self.results_tree = ttk.Treeview(results_tree_frame, columns=columns, show='headings', style='Treeview')
        self.results_tree.heading('linea', text='Línea', command=lambda: self._sort_treeview_column('linea', False))
        self.results_tree.heading('tipo_error', text='Tipo de Error', command=lambda: self._sort_treeview_column('tipo_error', False))
        self.results_tree.heading('descripcion', text='Descripción', command=lambda: self._sort_treeview_column('descripcion', False))
        self.results_tree.heading('contenido', text='Contenido de la Fila', command=lambda: self._sort_treeview_column('contenido', False))
        self.results_tree.column('linea', width=80, stretch=tk.NO, anchor='center')
        self.results_tree.column('tipo_error', width=180, stretch=tk.NO)
        self.results_tree.column('descripcion', width=350)
        self.results_tree.column('contenido', width=500)
        vsb = customtkinter.CTkScrollbar(results_tree_frame, command=self.results_tree.yview)
        hsb = customtkinter.CTkScrollbar(results_tree_frame, command=self.results_tree.xview, orientation="horizontal")
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.results_tree.pack(side='left', fill='both', expand=True)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)
        self._update_treeview_theme(new_appearance_mode)
        
    def _sort_treeview_column(self, col, reverse):
        try:
            data_list = [(self.results_tree.set(k, col), k) for k in self.results_tree.get_children('')]
            key_func = lambda t: t[0]
            if col == 'linea':
                try:
                    key_func = lambda t: int(t[0].split(',')[0]) if t[0] != '-' else float('inf')
                except (ValueError, TypeError, IndexError): pass
            data_list.sort(key=key_func, reverse=reverse)
            for index, (val, k) in enumerate(data_list):
                self.results_tree.move(k, '', index)
            self.results_tree.heading(col, command=lambda: self._sort_treeview_column(col, not reverse))
        except Exception as e:
            logger.error(f"Error al ordenar la columna {col}: {e}")

    def _toggle_header_entry(self):
        self.entry_header.configure(state='normal' if self.var_check_header.get() else 'disabled')

    def _seleccionar_archivo(self):
        ruta = filedialog.askopenfilename(title="Selecciona un archivo CSV", filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")])
        if not ruta: logger.warning("El usuario canceló la selección de archivo."); return
        
        self._limpiar()
        self.ruta_archivo_actual = ruta
        self.ruta_label.configure(text=f"📂 Archivo seleccionado:\n{self.ruta_archivo_actual}")
        
        preview_data = self._mostrar_previsualizacion(self.ruta_archivo_actual)

        if preview_data.get('exito') and preview_data.get('header'):
            self.unique_column_menu.configure(state="normal", values=preview_data['header'])
            self.unique_column_var.set(preview_data['header'][0])
            self.validate_button.configure(state="normal")

    def _iniciar_validacion(self):
        if not self.ruta_archivo_actual:
            messagebox.showwarning("Sin Archivo", "Por favor, selecciona primero un archivo.")
            return

        expected_headers = [h.strip() for h in self.entry_header.get().split(',') if h]
        self.validation_options = {
            'encoding': self.encoding_var.get(),
            'check_vacias': self.var_check_vacias.get(),
            'check_duplicadas': self.var_check_duplicadas.get(),
            'check_header': self.var_check_header.get(),
            'ignore_case': self.var_ignore_case.get(),
            'check_uniqueness': self.var_check_uniqueness.get(),
            'unique_column_name': self.unique_column_var.get(),
            'expected_headers': expected_headers
        }
        
        logger.info(f"Opciones de validación seleccionadas: {self.validation_options}")
        self.select_button.configure(state="disabled")
        self.validate_button.configure(state="disabled")
        self.ruta_label.configure(text=f"📂 Validando archivo... (Previsualización disponible)")
        
        self.progressbar.pack(fill='x', padx=20, pady=(10,5))
        self.progressbar.start()

        logger.info("Iniciando hilo de validación...")
        self.validation_thread = threading.Thread(target=self._worker_validacion, args=(self.ruta_archivo_actual, self.validation_options))
        self.validation_thread.start()
        self.root.after(100, self._verificar_hilo)

    def _mostrar_previsualizacion(self, ruta):
        logger.info("Generando previsualización del archivo.")
        self.tab_view.set("📄 Previsualización del Archivo")
        
        self.preview_tree.delete(*self.preview_tree.get_children())
        self.preview_tree['columns'] = ()

        preview_data = leer_primeras_lineas(ruta, 50, self.encoding_var.get())

        if not preview_data.get('exito'):
            messagebox.showerror("Error de Previsualización", f"No se pudo leer el archivo para previsualizar:\n{preview_data.get('error')}")
            return preview_data

        header = preview_data.get('header', [])
        if not header:
            logger.warning("El archivo seleccionado para previsualizar no tiene cabecera o está vacío.")
            return preview_data

        self.preview_tree['columns'] = header
        for col in header:
            self.preview_tree.heading(col, text=col, anchor='w')
            self.preview_tree.column(col, width=150, anchor='w')
        
        for i, row in enumerate(preview_data.get('rows', [])):
            if len(row) < len(header): row.extend([''] * (len(header) - len(row)))
            elif len(row) > len(header): row = row[:len(header)]
            self.preview_tree.insert('', 'end', values=row, iid=f"preview_row_{i}")
        
        return preview_data

    def _worker_validacion(self, ruta_csv, options):
        logger.info(f"El hilo de trabajo ha comenzado la validación para: {ruta_csv}")
        self.resultados_validacion = realizar_validacion_completa(ruta_csv, options)
        logger.info(f"El hilo de trabajo ha finalizado la validación.")

    def _verificar_hilo(self):
        if self.validation_thread.is_alive():
            self.root.after(100, self._verificar_hilo)
        else:
            logger.info("El hilo de trabajo ha sido verificado como finalizado. Mostrando resultados.")
            self.progressbar.stop()
            self.progressbar.pack_forget()
            self.select_button.configure(state="normal")
            self.validate_button.configure(state="normal")
            if self.resultados_validacion:
                self.ruta_label.configure(text=f"📂 Archivo analizado:\n{self.resultados_validacion['ruta_archivo']}")
                self.clean_export_button.configure(state="normal")
                self.export_informe_button.configure(state="normal")
                self._mostrar_resultados()
                self.tab_view.set("📊 Resultados de Validación")
            else:
                logger.error("El hilo de validación terminó pero no se encontraron resultados.")
                messagebox.showerror("Error", "La validación terminó inesperadamente sin resultados.")
            
    def _limpiar_resultados(self):
        self.results_tree.delete(*self.results_tree.get_children())
        self.estadisticas_label.configure(text="📊 Selecciona un archivo para ver las estadísticas")
    
    def _mostrar_resultados(self):
        self._limpiar_resultados()
        res = self.resultados_validacion
        if not res: logger.error("Se intentó mostrar resultados, pero el diccionario de resultados está vacío."); return

        if res.get('error_lectura'):
            self.estadisticas_label.configure(text="📊 Error al procesar el archivo")
            messagebox.showerror("Error de Lectura", res['error_lectura'])
            self.clean_export_button.configure(state="disabled")
            self.export_informe_button.configure(state="disabled")
            return

        stats_text = (f"📊 Total filas: {res.get('total_filas', 0)} | "
                      f"❌ Columnas: {len(res.get('filas_invalidas', []))} | "
                      f"❌ Unicidad: {len(res.get('errores_de_unicidad', {}))} | "
                      f"❌ Duplicadas: {len(res.get('filas_duplicadas', {}))}")
        self.estadisticas_label.configure(text=stats_text)
        
        if res.get('error_header'):
            self.results_tree.insert('', 'end', values=('-', 'Cabecera', res['error_header'], ''))
        
        for fila_num, num_cols, contenido in res.get('filas_invalidas', []):
            desc = f"Se esperaban {res.get('num_columnas_esperadas')} columnas, pero tiene {num_cols}"
            self.results_tree.insert('', 'end', values=(fila_num, 'Nº de Columnas', desc, str(contenido)))
        
        for valor_repetido, lineas in res.get('errores_de_unicidad', {}).items():
            desc = f"El valor '{valor_repetido}' está repetido en {len(lineas)} filas."
            line_str = ', '.join(map(str, lineas))
            col_name = self.validation_options.get('unique_column_name', '')
            self.results_tree.insert('', 'end', values=(line_str, 'Error de Unicidad', desc, f"Columna: '{col_name}'"))
        
        for row_tuple, line_numbers in res.get('filas_duplicadas', {}).items():
            line_str = ', '.join(map(str, line_numbers))
            desc = f"Aparece en las líneas: {line_str}"
            self.results_tree.insert('', 'end', values=(line_numbers[0], 'Fila Duplicada', desc, str(list(row_tuple))))
    
    def _exportar_informe(self):
        if not self.resultados_validacion: messagebox.showinfo("Información", "Primero debes seleccionar y validar un archivo."); return
        has_errors = any([self.resultados_validacion.get(key) for key in ['filas_invalidas', 'celdas_con_saltos', 'error_lectura', 'filas_vacias', 'filas_duplicadas', 'error_header', 'errores_de_unicidad']])
        if not has_errors: messagebox.showinfo("¡Todo correcto!", "El archivo está perfectamente validado. No hay errores que exportar."); return
        
        ruta_guardado = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Archivos de texto", "*.txt")], title="Guardar informe de errores")
        if not ruta_guardado: logger.warning("El usuario canceló la exportación del informe."); return
        
        logger.info(f"Exportando informe a: {ruta_guardado}")
        try:
            with open(ruta_guardado, "w", encoding="utf-8") as f:
                res = self.resultados_validacion
                f.write("="*80 + "\nINFORME DE VALIDACIÓN DE ARCHIVO CSV\n" + "="*80 + "\n")
                f.write(f"Archivo: {res['ruta_archivo']}\n\n")
                f.write(f"RESUMEN ESTADÍSTICO:\n{self.estadisticas_label.cget('text')}\n\n")
                f.write("-" * 80 + "\nDETALLE DE ERRORES\n" + "-"*80 + "\n\n")

                if res.get('error_header'):
                    f.write(f"--- ERROR DE CABECERA ---\n{res['error_header']}\n\n")
                if res.get('filas_invalidas'):
                    f.write("--- ERRORES DE NÚMERO DE COLUMNAS ---\n")
                    for fn, nc, co in res['filas_invalidas']:
                        f.write(f"Línea {fn}: Esperadas {res.get('num_columnas_esperadas')} cols, encontradas {nc}. Contenido: {co}\n")
                    f.write("\n")
                if res.get('errores_de_unicidad'):
                    f.write("--- ERRORES DE UNICIDAD DE COLUMNA ---\n")
                    col_name = self.validation_options.get('unique_column_name', '')
                    f.write(f"Comprobación en la columna: '{col_name}'\n")
                    for valor, lineas in res['errores_de_unicidad'].items():
                        f.write(f"  - El valor '{valor}' se repite en las líneas: {', '.join(map(str, lineas))}\n")
                    f.write("\n")
                if res.get('filas_duplicadas'):
                    f.write("--- GRUPOS DE FILAS DUPLICADAS ---\n")
                    for rt, lns in res['filas_duplicadas'].items():
                        f.write(f"Contenido duplicado en líneas {', '.join(map(str, lns))}:\n   {list(rt)}\n")
                    f.write("\n")
                if res.get('celdas_con_saltos'):
                    f.write("--- ERRORES DE SALTOS DE LÍNEA ---\n")
                    for fn, cn, co in res['celdas_con_saltos']:
                        f.write(f"Línea {fn}, Columna {cn}: Contenido con salto: {co.replace(chr(10), '{LF}')}\n")
                    f.write("\n")
                if res.get('filas_vacias'):
                    f.write(f"--- FILAS VACÍAS ENCONTRADAS ---\nLíneas: {', '.join(map(str, res['filas_vacias']))}\n\n")
            
            messagebox.showinfo("Exportado", f"Informe de errores guardado en:\n{ruta_guardado}")
            logger.info("Informe exportado con éxito.")
        except Exception as e:
            logger.error("Error durante la exportación del informe.", exc_info=True)
            messagebox.showerror("Error al exportar", f"No se pudo guardar el archivo. Revise 'validator.log' para detalles.")

    def _exportar_csv_limpio(self):
        if not self.resultados_validacion: messagebox.showwarning("Sin resultados", "Primero debes realizar una validación."); return
        ruta_original = self.resultados_validacion.get('ruta_archivo')
        if not ruta_original: messagebox.showerror("Error", "No se encontró la ruta del archivo original."); return
        
        import os
        base, ext = os.path.splitext(os.path.basename(ruta_original))
        default_filename = f"{base}_limpio.csv"
        ruta_destino = filedialog.asksaveasfilename(title="Guardar CSV Limpio", initialfile=default_filename, defaultextension=".csv", filetypes=[("Archivos CSV", "*.csv")])
        if not ruta_destino: logger.warning("El usuario canceló la exportación del CSV limpio."); return

        thread = threading.Thread(target=self._worker_limpieza, args=(ruta_original, ruta_destino, self.resultados_validacion, self.validation_options))
        thread.start()

    def _worker_limpieza(self, ruta_original, ruta_destino, resultados_validacion, options):
        logger.info("Iniciando el hilo de trabajo para la limpieza del CSV.")
        resumen = crear_csv_limpio(ruta_original, ruta_destino, resultados_validacion, options)
        
        if resumen.get('exito'):
            info_msg = (
                f"¡Archivo CSV limpiado con éxito!\n\n"
                f"Ruta: {ruta_destino}\n"
                f"-------------------------------------\n"
                f"Filas con formato incorrecto eliminadas: {resumen.get('formato_incorrecto_eliminadas', 0)}\n"
                f"Filas vacías eliminadas: {resumen.get('vacias_eliminadas', 0)}\n"
                f"Filas duplicadas eliminadas: {resumen.get('duplicados_eliminados', 0)}\n"
                f"Total de filas escritas en el nuevo archivo: {resumen.get('filas_escritas', 0)}"
            )
            messagebox.showinfo("Limpieza Completada", info_msg)
            logger.info("El CSV limpio se ha exportado correctamente.")
        else:
            messagebox.showerror("Error en la Limpieza", f"No se pudo crear el archivo limpio:\n{resumen.get('error')}")
            logger.error(f"Falló la creación del CSV limpio: {resumen.get('error')}")

    def _limpiar(self):
        logger.info("Limpiando la interfaz de usuario.")
        self.preview_tree.delete(*self.preview_tree.get_children())
        self.preview_tree['columns'] = ()
        self.results_tree.delete(*self.results_tree.get_children())
        self.tab_view.set("📄 Previsualización del Archivo")
        self.ruta_label.configure(text="📂 Archivo: (ninguno seleccionado)")
        self.estadisticas_label.configure(text="📊 Selecciona un archivo para ver las estadísticas")
        self.resultados_validacion = None
        self.ruta_archivo_actual = None
        self.validate_button.configure(state="disabled")
        self.clean_export_button.configure(state="disabled")
        self.export_informe_button.configure(state="disabled")
        self.unique_column_menu.configure(state="disabled", values=["(Seleccione archivo)"])
        self.unique_column_var.set("(Seleccione archivo)")
        self.var_check_uniqueness.set(False)
        self.var_check_header.set(False)
        self.var_check_vacias.set(True)
        self.var_check_duplicadas.set(True)
        self.var_ignore_case.set(False)
        self._toggle_header_entry()