from urllib.parse import quote_plus

#Listas de uso seguido
meses_espanol = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }

def construir_url_mysql(usuario_bd: str, contrasena_bd: str, host_bd: str, puerto_bd: str, nombre_bd: str) -> str:
    """
    Convierte los parámetros para una conexión a una base de datos MySQL en una cadena de conexión compatible con sqlalchemy.
    """
    contrasena_codificada = quote_plus(contrasena_bd)
    return f"mysql+mysqlconnector://{usuario_bd}:{contrasena_codificada}@{host_bd}:{puerto_bd}/{nombre_bd}"

