## Actividad 4: Orquestador, Pruebas e Interfaz (a4-axel)

**Prompt principal utilizado:**
> "aqui esta el herramientas.py. El modelo PROPONE una acción en JSON; tu código decide y la ejecuta... Necesito inyectar la herramienta buscar_logs, el validador de reiniciar todo y pasar las pruebas de test_a4_agente.py."

**Propuesta de la IA:**
La IA sugirió reemplazar la función `ejecutar_agente` implementando un bucle para manejar hasta 5 pasos, deteniendo el flujo si la herramienta tiene `sensible=True` para pedir confirmación humana. También generó la herramienta `buscar_logs` con el control estricto de 2 horas y enmascaramiento de correos/IPs mediante expresiones regulares.

**Modificaciones y Decisiones (Lo que se aceptó/rechazó):**
- **Rechazo/Modificación técnica:** El código inicial de la IA falló los tests automatizados por dos razones: un `KeyError` debido al uso de `.format()` con llaves de JSON, y un `TypeError` por incompatibilidad con la firma oculta de la función `llm.generar` simulada por el profesor.
- **Solución implementada:** Modifiqué el código junto con la IA para usar `.replace()` en lugar de `.format()`, y añadí un bloque `try/except` doble para tolerar las distintas formas de pasar el argumento `sistema`.
- **Resultado:** El código final superó exitosamente el 100% de las pruebas automatizadas (`test_a4_agente.py`) y se integró sin problemas a la interfaz interactiva en Streamlit.