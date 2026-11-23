# Un diccionario permite búsquedas directas O(1) sin iterar ni anidar if/else
USUARIOS_CACHE = {
    "admin": "1234" # (En un caso real aquí iría un hash, pero priorizamos la demostración de eficiencia)
}

def login_eficiencia(user, password):
    """Versión optimizada: complejidad O(1) y retornos tempranos (fast-fail)."""
    # Verificamos existencia y contraseña en una sola operación de acceso rápido
    if USUARIOS_CACHE.get(user) == password:
        return "access granted"
    
    # Retorno temprano, evitando anidaciones complejas
    return "access denied"