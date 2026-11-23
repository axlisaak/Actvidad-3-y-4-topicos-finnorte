import streamlit as st
import requests
import json
import time

# Configuración básica de Streamlit
st.set_page_config(page_title="Triage AI (A4) - FinNorte", layout="wide")
st.title("Triage de Incidentes y Logs (Variante v5-triage)")

# --- CONFIGURACIÓN Y TOKEN ---
# URL base de tu backend local de la Actividad 3
BASE_URL = "http://127.0.0.1:8000/v1"

st.sidebar.header("Autenticación")
token = st.sidebar.text_input("Token de Acceso (JWT)", type="password", help="Pega aquí el token devuelto por el login de la A3")

if not token:
    st.warning(" Debes proporcionar un token de acceso en la barra lateral para utilizar el servicio.")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# --- SECCIÓN DEL AGENTE ---
st.markdown("### Orquestador de Tareas (Agente)")

tarea = st.text_area("Ingresa la instrucción para el agente de Triage:", placeholder="Ej: Analiza los logs de las últimas 1 horas para el patrón 'Exception'")

# Estado de la sesión para manejar pausas humanas
if "esperando_confirmacion" not in st.session_state:
    st.session_state.esperando_confirmacion = False
    st.session_state.ultima_tarea = ""

if st.button("Ejecutar Tarea") or st.session_state.esperando_confirmacion:
    # Bloque de "cargando"
    with st.spinner(" El agente está procesando tu solicitud..."):
        # Llamada a la API de tu Actividad 3 (/v1/agente)
        try:
            # Aquí asumimos que el endpoint recibe un json con {"tarea": <texto>}
            payload = {"tarea": tarea}
            if st.session_state.esperando_confirmacion:
                 # Si estábamos pausados, re-enviamos para simular el reintento/confirmación en esta demo básica
                 pass 

            start_time = time.time()
            response = requests.post(f"{BASE_URL}/agente", headers=headers, json=payload)
            response.raise_for_status()
            
            datos = response.json()
            terminado = datos.get("terminado", False)
            respuesta = datos.get("respuesta", "")
            pasos = datos.get("pasos", [])
            validador = datos.get("validador_hallazgos", []) # Asumiendo que tu API devuelve los hallazgos del validador

            # Mostrar errores del validador de lógica tradicional (Rúbrica A4)
            if validador:
                st.error(" **Alertas del Validador Tradicional:**")
                for alerta in validador:
                    st.write(f"- {alerta}")

            # Mostrar el resultado final
            if terminado:
                st.success(" **Respuesta del Agente:**")
                st.write(respuesta)
                st.session_state.esperando_confirmacion = False
                
                # Mostrar fuentes
                fuentes = datos.get("fuentes", [])
                if fuentes:
                    with st.expander("Ver Fuentes Utilizadas"):
                        st.json(fuentes)
            else:
                st.warning("⏸️ **El Agente se ha pausado.** Requiere confirmación humana.")
                st.session_state.esperando_confirmacion = True

            # Mostrar la traza de pasos de la herramienta (bitácora del agente)
            st.markdown("### Bitácora de Ejecución")
            for p in pasos:
                estado = p.get("estado", "")
                with st.expander(f"Paso {p['n']}: {estado.upper()}", expanded=(estado == "sin_confirmar")):
                    st.json(p.get("propuesta", {}))
                    if estado == "sin_confirmar":
                        st.error("Esta acción es SENSIBLE y requiere tu autorización.")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Aprobar", key=f"aprobar_{p['n']}"):
                                st.info("Simulando aprobación...")
                                # Lógica para enviar aprobación al backend
                        with col2:
                            if st.button("Rechazar", key=f"rechazar_{p['n']}"):
                                st.error("Simulando rechazo...")
                                # Lógica para rechazar
                    else:
                        st.write("**Resultado:**", p.get("resultado"))

        except requests.exceptions.HTTPError as errh:
            st.error(f"Error HTTP: {errh}")
            try:
                st.json(response.json()) # Mostrar el problem+json
            except:
                pass
        except Exception as e:
            st.error(f"Error de conexión: {e}")