# validators.py

import csv
import re
import logging

# Obtenemos un logger específico para este módulo. Esto permite saber
# en el log qué parte del código está generando el mensaje.
logger = logging.getLogger(__name__)

def realizar_validacion_completa(ruta_csv, options):
    """
    Lógica de validación pura. No interactúa con la UI.
    Usa el diccionario de opciones para realizar comprobaciones selectivas.
    """
    logger.info(f"Iniciando validación para el fichero: {ruta_csv}")
    
    # Inicialización del diccionario de resultados
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
                
                # Validación de cabecera
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

            # Procesar el resto del fichero
            for i, fila in enumerate(lector, start=2):
                resultados['total_filas'] += 1
                _validar_fila_interna(fila, i, resultados, options, seen_rows_and_lines)

    except FileNotFoundError:
        logger.error(f"Error: Fichero no encontrado en la ruta {ruta_csv}")
        resultados['error_lectura'] = f"Fichero no encontrado: {ruta_csv}"
    except Exception:
        # Este es el cambio más importante: captura CUALQUIER otro error.
        # exc_info=True añade el traceback completo al log, crucial para depurar.
        logger.critical("Ha ocurrido una excepción no controlada durante la validación del CSV.", exc_info=True)
        resultados['error_lectura'] = (
            "Ha ocurrido un error crítico durante la validación. "
            "Por favor, revise el fichero 'validator.log' para más detalles técnicos."
        )
    
    # Post-procesamiento para encontrar los grupos de duplicados
    if options['check_duplicadas']:
        for row, lines in seen_rows_and_lines.items():
            if len(lines) > 1:
                resultados['filas_duplicadas'][row] = sorted(lines)
            
    logger.info("Validación finalizada. Devolviendo resultados.")
    return resultados

def _validar_fila_interna(fila, num_fila, resultados, options, seen_rows_and_lines):
    """Valida una única fila aplicando las reglas activas. (Helper interno)"""
    
    # Salida anticipada si la estructura de la fila es incorrecta
    if len(fila) != resultados['num_columnas_esperadas']:
        resultados['filas_invalidas'].append((num_fila, len(fila), fila))
        return

    # Comprobar si la fila está vacía
    if options['check_vacias'] and not any(field.strip() for field in fila):
        resultados['filas_vacias'].append(num_fila)
        return
    
    # Comprobar saltos de línea internos
    for j, campo in enumerate(fila, start=1):
        if '\n' in campo or '\r' in campo:
            resultados['celdas_con_saltos'].append((num_fila, j, campo))
    
    # Lógica de duplicados (solo se ejecuta en filas estructuralmente válidas)
    if options['check_duplicadas']:
        normalized_fila = [field.strip() for field in fila]
        if options['ignore_case']:
            normalized_fila = [field.lower() for field in normalized_fila]
        
        row_tuple = tuple(normalized_fila)
        
        if row_tuple not in seen_rows_and_lines:
            seen_rows_and_lines[row_tuple] = []
        seen_rows_and_lines[row_tuple].append(num_fila)