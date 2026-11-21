# Bitácora de Inteligencia Artificial y Postmortem (Laboratorios A3 y A4)

**Proyecto:** FinNorte IA  
**Variante:** `v5-triage` (Equipo 5)  
**Responsable de Documentación, Evidencia y Postmortem:** Axel  

---

## 1. Resumen de Implementación
Durante este avance, se implementó la capa de seguridad y autenticación de la API, así como el flujo de autorización en dos pasos (Human-in-the-loop) para las acciones del agente. El objetivo principal fue asegurar que ninguna herramienta crítica se ejecute sin validación humana y blindar el sistema contra vulnerabilidades comunes de acceso.

## 2. Mitigaciones de Seguridad (A3)
Se integraron las siguientes defensas en el módulo `api/auth.py`:

* **Almacenamiento Seguro:** Se implementó `PBKDF2-HMAC-SHA256` con 200,000 iteraciones y una sal criptográfica aleatoria de 16 bytes generada con `os.urandom()`. Ninguna contraseña se almacena en texto plano.
* **Ataques de Enumeración:** El sistema devuelve un error genérico (HTTP 401) con exactamente el mismo mensaje (`"Correo o contraseña incorrectos"`) tanto si el usuario no existe como si la contraseña es errónea.
* **Ataques de Tiempo (Timing Attacks):** 
  * Se forzó un cálculo de hash simulado cuando el usuario no existe en la base de datos para igualar los tiempos de respuesta.
  * Se reemplazó la comparación estándar de cadenas por `hmac.compare_digest()` para evitar fugas de información por tiempo de cómputo en la validación de contraseñas y firmas de tokens.
* **Protección contra Fuerza Bruta:** Se limitaron los intentos de acceso a 5 por usuario dentro de una ventana de 15 minutos, almacenando la bitácora en la tabla `intentos` de SQLite. Al superar el límite, la cuenta se bloquea temporalmente devolviendo un HTTP 429.
* **Gestión de Tokens (JWT-like):** Se emitieron tokens cifrados en base64url con un *payload* firmado mediante HMAC-SHA256 y una vigencia estricta de 15 minutos.

## 3. Control y Validación del Agente (A4)
Se configuró el entorno para garantizar que el modelo de lenguaje (Gemini) no interactúe directamente con sistemas de producción sin supervisión.

* **Flujo de Dos Pasos:** Cuando el agente decide utilizar una herramienta (ej. crear un ticket de despliegue), la petición queda pausada en un estado pendiente y devuelve un `id` único. El usuario debe consumir el endpoint `/v1/agente/confirmar/{id}` con el payload `{"aprobar": true}` para ejecutar la acción.
* **Validación de Reglas de Negocio:** El Validador intercepta peticiones que violan las políticas internas (ej. programar despliegues de alto riesgo en viernes) y las bloquea antes de generar una tarea pendiente, impidiendo su ejecución en la interfaz.

---

## 4. Postmortem y Resolución de Problemas

Durante el desarrollo e integración, nos enfrentamos a los siguientes retos técnicos, los cuales fueron documentados y resueltos:

1. **Adaptación del Esquema SQLite:** Inicialmente, intentamos guardar el contador de bloqueos directamente en la tabla `usuarios` o en memoria temporal. Al analizar la arquitectura base, descubrimos que el diseño óptimo requería utilizar la tabla `intentos` para contar los registros con `ok=0` en los últimos 15 minutos (`VENTANA_FALLOS_S`), manteniendo la base de datos normalizada.
2. **Error 503 (Service Unavailable) en la conexión con el LLM:** Tras superar el checkpoint de seguridad de la API, las peticiones al agente devolvieron un error 503. Mediante diagnóstico, se determinó que la API Key de Gemini había alcanzado su límite de cuota. La incidencia se mitigó rápidamente generando y configurando una nueva llave de entorno, restaurando la conectividad del agente.
3. **Manejo de Sesiones Expiradas:** Durante las pruebas del flujo de confirmación del agente, obtuvimos un error 401 en el paso de aprobación. Esto validó exitosamente que nuestra vigencia de tokens (15 minutos) estaba activa y funcionando.

---

## 5. Evidencia Gráfica



### 5.1 Pruebas Automatizadas (pytest)
Prueba superada con el 100% de cobertura en los tests de seguridad y lógica del agente (12 passed).


### 5.2 Bloqueo por Fuerza Bruta (HTTP 429)
Respuesta del servidor tras 6 intentos fallidos de inicio de sesión.



### 5.3 Rechazo de Token Alterado (HTTP 401)
El servidor rechaza peticiones protegidas al modificar o expirar el token de autorización.


### 5.4 Flujo de Autorización del Agente (Interfaz)
Demostración de la acción retenida por el agente esperando aprobación humana (botón Autorizar).


### 5.5 Reglas de Negocio (Bloqueo en Viernes)
El Validador rechazando un cambio de alto riesgo programado para un viernes (27 de noviembre de 2026), evitando que aparezcan los botones de confirmación.


### 5.6 Resiliencia de la Interfaz
Manejo amigable de errores en el frontend al perder conexión con la API (simulación de caída de servidor).

