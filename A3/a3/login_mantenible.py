from typing import Dict

class AutenticacionError(Exception):
    """Excepción personalizada para el dominio de autenticación."""
    pass

_db: Dict[str, str] = {"admin": "1234"}

def _credenciales_son_validas(user: str, password: str) -> bool:
    """Función helper con responsabilidad única."""
    return _db.get(user) == password

def login_mantenible(user: str, password: str) -> str:
    """
    Autentica a un usuario en el sistema de forma clara y escalable.
    
    Args:
        user (str): El identificador del usuario.
        password (str): La credencial secreta.
        
    Returns:
        str: Mensaje de éxito si las credenciales son válidas.
        
    Raises:
        ValueError: Si los argumentos están vacíos.
        AutenticacionError: Si el usuario o la contraseña no coinciden.
    """
    if not user or not password:
        raise ValueError("Usuario y contraseña no pueden estar vacíos")
        
    if _credenciales_son_validas(user, password):
        return "access granted"
        
    raise AutenticacionError("Credenciales inválidas")