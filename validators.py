# validators.py

import csv
import re
import logging

logger = logging.getLogger(__name__)

def leer_primeras_lineas(ruta_csv, num_lineas, encoding):
    """
    Lee las primeras N líneas de un archivo CSV para previsualización.
    Devuelve la cabecera y una lista de filas.
    """
    logger.info(f"Leyendo primeras {num_lineas} líneas de {ruta_csv} con codificación {encoding}")
    header = []
    preview_rows = []
    try:
        with open(ruta_csv, 'r', newline='', encoding=encoding) as f:
            lector = csv.reader(f)
            header = next(lector, [])
            for i, row in enumerate(lector):
                if i >= num_lineas - 1:
                    break
                preview_rows.append(row)
        return {'exito': True, 'header': header, 'rows': preview_rows}
    except Exception as e:
        logger.error(f"Error al previsualizar el archivo {ruta_csv}: {e}")
        return {'exito': False, 'error': str(e)}

def realizar_validacion_completa(ruta_csv, options):
    """
    Lógica de validación pura que ahora incluye la comprobación de unicidad de columna.
    """
    logger.info(f"Iniciando validación para el fichero: {ruta_csv}")
    
    resultados = {
        'ruta_archivo': ruta_csv, 'total_filas': 0, 'num_columnas_esperadas': None,
        'cabecera': [], 'filas_invalidas': [], 'celdas_con_saltos': [], 
        'error_lectura': None, 'filas_vacias': [], 'filas_duplicadas': {}, 
        'error_header': None, 'errores_de_unicidad': {}
    }
    seen_rows_and_lines = {}
    
    unique_column_values = {}
    unique_col_index = -1

    encoding = options.get('encoding', 'utf-8')
    logger.info(f"Intentando leer el fichero con la codificación: {encoding}")

    try:
        with open(ruta_csv, 'r', newline='', encoding=encoding) as f:
            lector = csv.reader(f)
            
            try:
                primera_fila = next(lector)
                resultados['total_filas'] = 1
                resultados['cabecera'] = primera_fila
                
                header_to_validate = primera_fila
                expected_headers = options.get('expected_headers', [])
                if options.get('check_header') and expected_headers:
                    if options.get('ignore_case'):
                        header_to_validate = [h.lower().strip() for h in header_to_validate]
                        expected_headers = [h.lower().strip() for h in expected_headers]
                    
                    if header_to_validate != expected_headers:
                        resultados['error_header'] = f"La cabecera no coincide.\nSe esperaba: {options['expected_headers']}\nSe encontró: {primera_fila}"
                
                if options.get('check_uniqueness') and options.get('unique_column_name'):
                    try:
                        unique_col_index = primera_fila.index(options['unique_column_name'])
                        logger.info(f"Se comprobará la unicidad de la columna '{options['unique_column_name']}' en el índice {unique_col_index}.")
                    except ValueError:
                        logger.warning(f"La columna de unicidad '{options['unique_column_name']}' no se encontró en la cabecera.")
                
                resultados['num_columnas_esperadas'] = len(primera_fila)
                _validar_fila_interna(primera_fila, 1, resultados, options, seen_rows_and_lines, unique_col_index, unique_column_values)

            except StopIteration:
                logger.warning(f"El fichero {ruta_csv} está vacío o no tiene contenido.")
                return resultados

            for i, fila in enumerate(lector, start=2):
                resultados['total_filas'] += 1
                _validar_fila_interna(fila, i, resultados, options, seen_rows_and_lines, unique_col_index, unique_column_values)

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
    
    if options.get('check_duplicadas'):
        for row, lines in seen_rows_and_lines.items():
            if len(lines) > 1:
                resultados['filas_duplicadas'][row] = sorted(lines)
    
    if unique_col_index != -1:
        for value, lines in unique_column_values.items():
            if len(lines) > 1:
                resultados['errores_de_unicidad'][value] = sorted(lines)
            
    logger.info("Validación finalizada. Devolviendo resultados.")
    return resultados

def _validar_fila_interna(fila, num_fila, resultados, options, seen_rows_and_lines, unique_col_index, unique_column_values):
    """Valida una única fila aplicando las reglas activas."""
    
    if len(fila) != resultados['num_columnas_esperadas']:
        resultados['filas_invalidas'].append((num_fila, len(fila), fila))
        return

    if options.get('check_vacias') and not any(field.strip() for field in fila):
        resultados['filas_vacias'].append(num_fila)
        return
    
    for j, campo in enumerate(fila, start=1):
        if '\n' in campo or '\r' in campo:
            resultados['celdas_con_saltos'].append((num_fila, j, campo))
    
    if num_fila > 1 and unique_col_index != -1 and unique_col_index < len(fila):
        valor_celda = fila[unique_col_index].strip()
        if options.get('ignore_case'):
            valor_celda = valor_celda.lower()
        
        if valor_celda:
            if valor_celda not in unique_column_values:
                unique_column_values[valor_celda] = []
            unique_column_values[valor_celda].append(num_fila)

    if options.get('check_duplicadas'):
        normalized_fila = [field.strip() for field in fila]
        if options.get('ignore_case'):
            normalized_fila = [field.lower() for field in normalized_fila]
        
        row_tuple = tuple(normalized_fila)
        
        if row_tuple not in seen_rows_and_lines:
            seen_rows_and_lines[row_tuple] = []
        seen_rows_and_lines[row_tuple].append(num_fila)

def crear_csv_limpio(ruta_original, ruta_destino, resultados_validacion, options):
    """
    Crea un nuevo archivo CSV limpio.
    """
    logger.info(f"Iniciando proceso de limpieza. Origen: {ruta_original}, Destino: {ruta_destino}")
    
    lineas_a_omitir = set()
    
    filas_vacias = resultados_validacion.get('filas_vacias', [])
    lineas_a_omitir.update(filas_vacias)
    
    filas_invalidas = resultados_validacion.get('filas_invalidas', [])
    for linea_invalida, _, _ in filas_invalidas:
        lineas_a_omitir.add(linea_invalida)
    
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
                    fila_limpia = [celda.strip() for celda in fila]
                    escritor.writerow(fila_limpia)
                    filas_escritas += 1
        
        resumen_limpieza = {
            'exito': True,
            'vacias_eliminadas': len(filas_vacias),
            'duplicados_eliminados': duplicados_eliminados,
            'formato_incorrecto_eliminadas': len(filas_invalidas),
            'filas_escritas': filas_escritas
        }
        logger.info(f"Proceso de limpieza finalizado con éxito: {resumen_limpieza}")
        return resumen_limpieza

    except Exception as e:
        logger.error("Error durante el proceso de creación del CSV limpio.", exc_info=True)
        return {'exito': False, 'error': str(e)}