# PROYECTO: VIGÍA INDUSTRIAL - WEB APP (SECURE)
# ARCHIVO: vigia.py

import streamlit as st
import tempfile
import os
import time
from Nucleo_Vigia import InspectorIndustrial

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="VIGÍA PRO", page_icon="🛡️", layout="wide")

# --- 🔒 SISTEMA DE SEGURIDAD (LOGIN SIMPLE) ---
def check_password():
    """Retorna True si el usuario ingresó la clave correcta."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # Input de contraseña
    st.markdown("## 🔐 Acceso Restringido - SUNBELT SURPLUS")
    pwd = st.text_input("Ingrese la clave de acceso:", type="password")
    
    # Verificamos contra los secretos de la nube
    if st.button("Entrar"):
        if pwd == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("⛔ Clave incorrecta")
    return False

if not check_password():
    st.stop() # Si no hay clave, aquí se detiene todo.

# --- 🚀 INICIO DE LA APLICACIÓN ---
if 'inspector' not in st.session_state:
    st.session_state.inspector = InspectorIndustrial()

inspector = st.session_state.inspector

# Intentamos tomar la API Key de los secretos de la nube
try:
    API_KEY_NUBE = st.secrets["GOOGLE_API_KEY"]
except:
    API_KEY_NUBE = ""

# --- SIDEBAR ---
with st.sidebar:
    st.title("VIGÍA PRO")
    
    # Gestión de API Key
    if API_KEY_NUBE:
        api_key = API_KEY_NUBE
        st.success("☁️ Conectado a Servidor AI")
    else:
        api_key = st.text_input("🔑 API Key (Manual):", type="password")

    st.markdown("---")
    usuario = st.text_input("Inspector:", "Invitado Remoto")
    proyecto = st.text_input("Proyecto:", "Inspección Móvil")

# --- TABS ---
tab1, tab2 = st.tabs(["🕵️ INSPECCIÓN", "📜 HISTORIAL"])

# === PESTAÑA 1 ===
with tab1:
    col_conf, col_form = st.columns([1, 2])
    with col_conf:
        st.subheader("Configuración")
        modulo = st.selectbox("Especialidad:", inspector.obtener_modulos())
        norma = st.selectbox("Norma:", inspector.obtener_normas(modulo))
        st.info("Subir Evidencia:")
        imagen_archivo = st.file_uploader("Foto", type=["jpg", "png", "jpeg"])

    with col_form:
        st.subheader("Ficha Técnica")
        datos_tecnicos = st.text_area("Describa el equipo y condiciones:", height=100)

    st.markdown("---")
    if st.button("👁️ ANALIZAR AHORA", use_container_width=True):
        if not api_key or not imagen_archivo:
            st.error("Faltan datos.")
        else:
            with st.spinner("VIGÍA Analizando..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    tmp.write(imagen_archivo.getvalue())
                    ruta_temp = tmp.name
                
                info = {"usuario": usuario, "proyecto": proyecto, "modulo": modulo, "norma": norma}
                resultado = inspector.analizar_imagen_con_ia(api_key, ruta_temp, info, datos_tecnicos)
                
                st.session_state['res_web'] = resultado
                st.session_state['img_web'] = ruta_temp
                st.session_state['info_web'] = info
            st.success("¡Listo!")

    if 'res_web' in st.session_state:
        st.markdown("### Dictamen:")
        st.write(st.session_state['res_web'])
        if st.button("📄 PDF"):
            pdf = inspector.generar_pdf_ia(st.session_state['info_web'], st.session_state['res_web'], st.session_state['img_web'])
            st.download_button("Bajar Reporte", pdf, "Reporte_Vigia.pdf", "application/pdf")

# === PESTAÑA 2 ===
with tab2:
    st.header("Historial de Sesión")
    if st.button("Borrar"): inspector.borrar_memoria(); st.rerun()
    historial = inspector.obtener_historial()
    if historial:
        for fila in historial:
            with st.expander(f"{fila[0]} - {fila[2]}"): st.write(fila[4])