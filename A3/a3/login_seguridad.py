import hmac
import hashlib

# Simulamos una base de datos. NUNCA texto plano.
DB_USUARIOS = {
    "admin": {
        "salt": b'sal_aleatoria_segura_123',
        "hash": hashlib.pbkdf2_hmac('sha256', b'1234', b'sal_aleatoria_segura_123', 200000)
    }
}

def login_seguridad(user, password):
    """Versión blindada: mitiga enumeración y ataques de tiempo."""
    record = DB_USUARIOS.get(user)
    
    # 1. Mitigación de enumeración: Mismo error siempre
    mensaje_error = "Credenciales incorrectas"
    
    if not record:
        # 2. Mitigación de Timing Attacks: Simulamos el cómputo de hash aunque el usuario no exista
        hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), b'sal_falsa_321', 200000)
        return mensaje_error
        
    # Calculamos el hash de la contraseña ingresada
    hash_calculado = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), record["salt"], 200000)
    
    # 3. Comparación en tiempo constante (evita fugas de información)
    if hmac.compare_digest(hash_calculado, record["hash"]):
        return "access granted"
    
    return mensaje_error