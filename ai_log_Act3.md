## Actividad 3 - Análisis y Refactorización del Login

**Prompt utilizado:**
"Analiza el siguiente código de login vulnerable en Python. Identifica sus vulnerabilidades (seguridad, eficiencia, mantenibilidad) y genera 3 versiones mejoradas: una enfocada estrictamente en seguridad mitigando timing attacks, otra en eficiencia algorítmica y otra en mantenibilidad con Clean Code."

**Evaluación de las propuestas de la IA (Comparación 5x4):**

| Criterio / Versión | Original | 1. Seguridad | 2. Eficiencia | 3. Mantenible |
| :--- | :--- | :--- | :--- | :--- |
| **Mitigación Timing Attack** | Falla (==) | Pasa (hmac.compare_digest) | Falla | Falla |
| **Fuga de Enumeración** | Falla | Pasa (Mensaje genérico) | Pasa | Falla |
| **Complejidad Algorítmica** | Regular O(n) | Regular O(n) | Excelente O(1) | Regular O(n) |
| **Tipado y Clean Code** | Falla | Regular | Regular | Excelente |
| **Almacenamiento Seguro** | Texto plano | PBKDF2 + Salt | Texto plano | Texto plano |

**Decisión Técnica:**
* **Versión Seguridad:** ACEPTADA Y MODIFICADA. Es la más robusta para producción, pero tuve que adaptarla para que encajara con el estándar del proyecto.
* **Versión Eficiencia:** RECHAZADA para auth. La búsqueda O(1) es rápida, pero sacrifica por completo la seguridad al comparar en texto plano.
* **Versión Mantenibilidad:** MODIFICADA. Se extrajo la idea de usar Type Hints y excepciones (raise ErrorAuth) para implementarlo en nuestro api/auth.py final.

**Reflexión (Paso 8):**
El uso de IA para refactorizar código demuestra que no existe una solución única. Si le pides eficiencia, la IA te da velocidad pero puede crear vulnerabilidades. Si le pides seguridad, el código se vuelve más pesado computacionalmente. El juicio humano es indispensable para orquestar estas piezas; en nuestro caso (api/auth.py), tomamos la seguridad criptográfica de la versión 1 y la estructura mantenible de la versión 3, alineando el resultado a la especificación problem+json requerida por el profesor.