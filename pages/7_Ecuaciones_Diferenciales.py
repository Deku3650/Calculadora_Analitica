def parse_seguro(entrada_str, transformaciones=None, local_dict=None):
    """
    Analizador matemático seguro.
    Utiliza expresiones regulares en lugar de AST para permitir sintaxis 
    matemática natural (ej. '2x') mientras bloquea intentos de inyección de código.
    """
    if not entrada_str.strip():
        return None
        
    # 1. Bloqueo de métodos y atributos (ej. os.system). Permite decimales (3.14)
    if re.search(r'\.[a-zA-Z_]', entrada_str):
        raise ValueError("El acceso a atributos (.) no está permitido por seguridad.")
        
    # 2. Bloqueo estricto de variables ocultas (dunders)
    if '__' in entrada_str:
        raise ValueError("El uso de dunders (__) no está permitido.")
        
    # 3. Bloqueo de funciones nativas peligrosas de Python
    palabras_prohibidas = r'\b(import|eval|exec|compile|open|globals|locals|getattr|setattr|delattr|os|sys|subprocess)\b'
    if re.search(palabras_prohibidas, entrada_str):
        raise ValueError("Uso de comandos de sistema no permitidos.")

    if local_dict is None:
        local_dict = {}
        
    # Si pasa los filtros de texto, es seguro enviarlo a SymPy
    return parse_expr(entrada_str, transformations=transformaciones, global_dict=None, local_dict=local_dict)
