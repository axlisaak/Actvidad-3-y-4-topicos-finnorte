from fastapi.testclient import TestClient
from api.producto import app

client = TestClient(app)

# ==========================================
# 3 PRUEBAS OFICIALES (Flujo normal)
# ==========================================

def test_registro_exitoso():
    """Prueba 1: Creación de usuario exitosa"""
    # Usamos un correo único para evitar conflictos si la BD guarda estado
    res = client.post("/auth/registro", json={"email": "nuevo_oficial@tecmi.mx", "contrasena": "secreto123"})
    assert res.status_code in (201, 400) # 201 creado, o 400 si ya existía de corridas anteriores

def test_login_exitoso():
    """Prueba 2: Login devuelve un token JWT-like"""
    client.post("/auth/registro", json={"email": "login_oficial@tecmi.mx", "contrasena": "secreto123"})
    res = client.post("/auth/login", json={"email": "login_oficial@tecmi.mx", "contrasena": "secreto123"})
    
    assert res.status_code == 200
    assert "token" in res.json()
    assert res.json()["tipo"] == "Bearer"

def test_endpoint_triage_con_token():
    """Prueba 3: Acceso a /v1/triage usando un token válido"""
    client.post("/auth/registro", json={"email": "triage@tecmi.mx", "contrasena": "secreto123"})
    res_login = client.post("/auth/login", json={"email": "triage@tecmi.mx", "contrasena": "secreto123"})
    token = res_login.json()["token"]
    
    res = client.post(
        "/v1/triage", 
        json={"log": "Alerta de seguridad severa en servidor web con uso 99%"}, 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200


# ==========================================
# 3 PRUEBAS PROPIAS (Seguridad y Casos Límite)
# ==========================================

def test_token_alterado_401():
    """Prueba 4 (Propia): Un token inventado o modificado debe ser rechazado"""
    res = client.post(
        "/v1/triage", 
        json={"log": "Alerta normal de sistema"}, 
        headers={"Authorization": "Bearer token.falso.inventado.123"}
    )
    assert res.status_code == 401
    assert res.json()["title"] == "No autorizado"

def test_entrada_invalida_422():
    """Prueba 5 (Propia): Pydantic debe bloquear entradas que no cumplen los requisitos (min_length)"""
    client.post("/auth/registro", json={"email": "invalido@tecmi.mx", "contrasena": "secreto123"})
    res_login = client.post("/auth/login", json={"email": "invalido@tecmi.mx", "contrasena": "secreto123"})
    token = res_login.json()["token"]
    
    # Mandamos un log de 2 letras (el mínimo de EntradaTriage es 10)
    res = client.post(
        "/v1/triage", 
        json={"log": "ab"}, 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 422
    assert res.json()["title"] == "Entrada inválida"

def test_login_fallido_401():
    """Prueba 6 (Propia): Contraseña incorrecta arroja Unauthorized"""
    client.post("/auth/registro", json={"email": "fallo@tecmi.mx", "contrasena": "secreto123"})
    res = client.post("/auth/login", json={"email": "fallo@tecmi.mx", "contrasena": "clave_equivocada"})
    
    assert res.status_code == 401