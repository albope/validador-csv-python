# validators.py

import csv
import re
import logging

logger = logging.getLogger(__name__)

# --- Funciones de Validación de Tipos (si se implementan en el futuro) ---
# ...

def realizar_validacion_completa(ruta_csv, options):
    """Lógica de validación pura que ahora usa la codificación proporcionada."""
    logger.info(f"Iniciando validación para el fichero: {ruta_csv}")
    
    resultados = {
        'ruta_archivo': ruta_csv, 'total_filas': 0, 'num_columnas_esperadas': None,
        'filas_invalidas': [], 'celdas_con_saltos': [], 'error_lectura': None,
        'filas_vacias': [], 'filas_duplicadas': {}, 'error_header': None
    }
    seen_rows_and_lines = {}
    
    encoding = options.get('encoding', 'utf-8')
    logger.info(f"Intentando leer el fichero con la codificación: {encoding}")

    try:
        with open(ruta_csv, 'r', newline='', encoding=encoding) as f:
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
                _validar_fila_interna(primera_fila, 1, resultados, options, seen_rows_and_lines)

            except StopIteration:
                logger.warning(f"El fichero {ruta_csv} está vacío o no tiene contenido.")
                return resultados

            for i, fila in enumerate(lector, start=2):
                resultados['total_filas'] += 1
                _validar_fila_interna(fila, i, resultados, options, seen_rows_and_lines)

    except FileNotFoundError:
        logger.error(f"Error: Fichero no encontrado en la ruta {ruta_csv}")
        resultados['error_lectura'] = f"Fichero no encontrado: {ruta_csv}"
    except UnicodeDecodeError:
        error_msg = f"Error de codificación. No se pudo leer el archivo con el formato '{encoding}'.\n\nPrueba a seleccionar otra codificación como 'latin-1' o 'cp1252'."
        logger.error(f"UnicodeDecodeError para el fichero {ruta_csv} con la codificación {encoding}.")
        resultados['error_lectura'] = error_msg
    except Exception:
        logger.critical("Ha ocurrido una excepción no controlada durante la validación del CSV.", exc_info=True)
        resultados['error_lectura'] = "Ha ocurrido un error crítico. Revisa 'validator.log' para detalles."
    
    if options['check_duplicadas']:
        for row, lines in seen_rows_and_lines.items():
            if len(lines) > 1:
                resultados['filas_duplicadas'][row] = sorted(lines)
            
    logger.info("Validación finalizada. Devolviendo resultados.")
    return resultados

def _validar_fila_interna(fila, num_fila, resultados, options, seen_rows_and_lines):
    """Valida una única fila aplicando las reglas activas."""
    
    if len(fila) != resultados['num_columnas_esperadas']:
        resultados['filas_invalidas'].append((num_fila, len(fila), fila))
        return

    if options['check_vacias'] and not any(field.strip() for field in fila):
        resultados['filas_vacias'].append(num_fila)
        return
    
    for j, campo in enumerate(fila, start=1):
        if '\n' in campo or '\r' in campo:
            resultados['celdas_con_saltos'].append((num_fila, j, campo))
    
    if options['check_duplicadas']:
        normalized_fila = [field.strip() for field in fila]
        if options['ignore_case']:
            normalized_fila = [field.lower() for field in normalized_fila]
        
        row_tuple = tuple(normalized_fila)
        
        if row_tuple not in seen_rows_and_lines:
            seen_rows_and_lines[row_tuple] = []
        seen_rows_and_lines[row_tuple].append(num_fila)

# --- NUEVA FUNCIÓN ---
def crear_csv_limpio(ruta_original, ruta_destino, resultados_validacion, options):
    """
    Crea un nuevo archivo CSV limpio, omitiendo filas vacías/duplicadas y
    recortando espacios en blanco en todas las celdas.
    """
    logger.info(f"Iniciando proceso de limpieza. Origen: {ruta_original}, Destino: {ruta_destino}")
    
    lineas_a_omitir = set()
    
    # Añadir las líneas vacías al conjunto de omisión
    filas_vacias = resultados_validacion.get('filas_vacias', [])
    lineas_a_omitir.update(filas_vacias)
    
    # Añadir las líneas duplicadas (todas menos la primera aparición)
    filas_duplicadas = resultados_validacion.get('filas_duplicadas', {})
    duplicados_eliminados = 0
    for lines in filas_duplicadas.values():
        if len(lines) > 1:
            lineas_a_omitir.update(lines[1:])
            duplicados_eliminados += len(lines) - 1
            
    encoding = options.get('encoding', 'utf-8')
    filas_escritas = 0
    
    try:
        with open(ruta_original, 'r', newline='', encoding=encoding) as f_in, \
             open(ruta_destino, 'w', newline='', encoding=encoding) as f_out:
            
            lector = csv.reader(f_in)
            escritor = csv.writer(f_out)
            
            for i, fila in enumerate(lector, start=1):
                if i not in lineas_a_omitir:
                    # Limpiar espacios en blanco de cada celda
                    fila_limpia = [celda.strip() for celda in fila]
                    escritor.writerow(fila_limpia)
                    filas_escritas += 1
        
        resumen_limpieza = {
            'exito': True,
            'vacias_eliminadas': len(filas_vacias),
            'duplicados_eliminados': duplicados_eliminados,
            'filas_escritas': filas_escritas
        }
        logger.info(f"Proceso de limpieza finalizado con éxito: {resumen_limpieza}")
        return resumen_limpieza

    except Exception as e:
        logger.error("Error durante el proceso de creación del CSV limpio.", exc_info=True)
        return {'exito': False, 'error': str(e)}

