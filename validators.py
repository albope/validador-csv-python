# validators.py

import csv
import re

def realizar_validacion_completa(ruta_csv, options):
    """
    Lógica de validación pura. No interactúa con la UI.
    Usa el diccionario de opciones para realizar comprobaciones selectivas.
    """
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
                _validar_fila_interna(primera_fila, 1, resultados, options, seen_rows_and_lines)

            except StopIteration:
                return resultados

            for i, fila in enumerate(lector, start=2):
                resultados['total_filas'] += 1
                _validar_fila_interna(fila, i, resultados, options, seen_rows_and_lines)

    except Exception as e:
        resultados['error_lectura'] = f"Error inesperado al leer el archivo: {e}"
    
    if options['check_duplicadas']:
        for row, lines in seen_rows_and_lines.items():
            if len(lines) > 1:
                resultados['filas_duplicadas'][row] = sorted(lines)
            
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