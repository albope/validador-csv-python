# 🧪 Validador CSV Profesional

![Interfaz de la Aplicación](https://i.imgur.com/kY7qW8r.png)

Una aplicación de escritorio moderna y potente desarrollada en Python para validar la integridad y estructura de archivos CSV. Diseñada para ser intuitiva, rápida y funcional, esta herramienta ayuda a limpiar y preparar datos antes de su procesamiento o importación.

Desarrollado por **albope**.

---

## ✨ Funcionalidades Principales

Esta herramienta va más allá de una simple comprobación, ofreciendo un conjunto completo de validaciones y una experiencia de usuario de primer nivel.

### ✅ Validaciones Estructurales
- **Consistencia de Columnas:** Verifica que todas las filas en el archivo CSV tengan exactamente el mismo número de columnas que la cabecera.
- **Saltos de Línea Internos:** Detecta y reporta la presencia de saltos de línea (`\n`) o retornos de carro (`\r`) dentro de una celda, un problema común que puede corromper la importación de datos.

### 🚀 Validaciones Avanzadas (Opcionales)
El usuario puede activar o desactivar estas reglas según sus necesidades:
- **Detección de Filas Vacías:** Identifica filas que no contienen ningún dato.
- **Detección de Filas Duplicadas:**
    - Encuentra y agrupa filas que son idénticas.
    - **Normalización Inteligente:** Elimina espacios en blanco al inicio y final de cada celda antes de comparar.
    - **Opción de Ignorar Mayúsculas/Minúsculas:** Puede tratar `Juan` y `juan` como idénticos para una detección más flexible.
- **Validación de Cabecera:** Permite al usuario especificar la cabecera exacta que espera, y la aplicación la verificará contra la primera fila del archivo.

### 🖥️ Interfaz y Experiencia de Usuario
- **Interfaz Moderna:** Construida con **CustomTkinter**, ofreciendo un aspecto limpio y actual.
- **Temas Personalizables:** Incluye un selector para cambiar entre temas **Claro**, **Oscuro** y el **del Sistema** en tiempo real.
- **Resultados en Tabla Interactiva:** Los errores no se muestran en un texto plano, sino en una tabla (`ttk.Treeview`) que permite **ordenar los resultados** por número de línea, tipo de error o descripción con un solo clic.
- **Rendimiento sin Congelaciones:** Gracias al uso de **multithreading**, la interfaz permanece completamente responsiva y muestra una barra de progreso animada mientras se procesan archivos grandes.

### 🛠️ Para Desarrolladores
- **Logging Detallado:** Todas las acciones importantes y cualquier error inesperado se registran en un archivo `validator.log` con su `traceback` completo, facilitando enormemente la depuración.
- **Código Modular:** El proyecto está estructurado profesionalmente, separando la lógica de la interfaz (`ui/app_ui.py`) de la lógica de validación (`validators.py`), lo que facilita su mantenimiento y expansión.
- **Empaquetado para Distribución:** Preparado para ser empaquetado como un ejecutable `.exe` independiente para Windows usando **PyInstaller**.

---

## 🚀 Cómo Usar

### Opción 1: Ejecutar desde el Código Fuente
Ideal para desarrolladores y para contribuir al proyecto.

1.  Clona el repositorio:
    ```bash
    git clone [https://github.com/albope/validador-csv-python.git](https://github.com/albope/validador-csv-python.git)
    cd validador-csv-python
    ```
2.  Crea un entorno virtual (recomendado):
    ```bash
    python -m venv venv
    venv\Scripts\activate  # En Windows
    ```
3.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
    *(Nota: deberás crear un archivo `requirements.txt` con `pip freeze > requirements.txt` que contenga `customtkinter` y `watchdog`)*.

4.  Ejecuta la aplicación:
    ```bash
    python main.py
    ```

### Opción 2: Usar el Ejecutable (Windows)
La forma más fácil para usuarios finales.

1.  Ve a la sección de **"Releases"** en la página de GitHub del proyecto.
2.  Descarga el archivo `ValidadorCSV.exe` de la última versión.
3.  ¡Haz doble clic y úsalo! No requiere instalación ni Python.

---

## 🤝 Cómo Contribuir

Las contribuciones son siempre bienvenidas. Si quieres mejorar la herramienta:

1.  Haz un "Fork" del repositorio.
2.  Crea una nueva rama para tu funcionalidad (`git checkout -b anadir-mi-mejora`).
3.  Haz tus cambios y haz "commit" de ellos.
4.  Haz "Push" a tu rama (`git push origin anadir-mi-mejora`).
5.  Abre un "Pull Request".