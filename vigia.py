# PROYECTO: VIGÍA INDUSTRIAL - WEB APP (DUAL CAMERA)
# ARCHIVO: vigia.py

import streamlit as st
import tempfile
import os
import time
from Nucleo_Vigia import InspectorIndustrial

# --- ⚠️ ZONA DE CONFIGURACIÓN ---
# Si quieres dejar la clave fija para tus amigos, ponla aquí:
CLAVE_MAESTRA = "" 
# --------------------------------

st.set_page_config(page_title="VIGÍA PRO", page_icon="🛡️", layout="wide")

# --- LOGIN ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    
    # Si hay CLAVE_MAESTRA configurada, saltamos el login de la nube
    # (Opcional, pero mantenemos la seguridad por defecto)
    
    st.markdown("## 🔐 Acceso Restringido - SUNBELT SURPLUS")
    pwd = st.text_input("Ingrese la clave de acceso:", type="password")
    if st.button("Entrar"):
        if pwd == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("⛔ Clave incorrecta")
    return False

if not check_password():
    st.stop()

# --- INICIO ---
if 'inspector' not in st.session_state:
    st.session_state.inspector = InspectorIndustrial()

inspector = st.session_state.inspector

# Gestión de API Key
try:
    API_KEY_NUBE = st.secrets["GOOGLE_API_KEY"]
except:
    API_KEY_NUBE = ""

# --- SIDEBAR ---
with st.sidebar:
    st.title("VIGÍA PRO")
    if CLAVE_MAESTRA:
        api_key = CLAVE_MAESTRA
        st.success("🔓 Licencia PRO (Local)")
    elif API_KEY_NUBE:
        api_key = API_KEY_NUBE
        st.success("☁️ Licencia PRO (Nube)")
    else:
        api_key = st.text_input("🔑 API Key:", type="password")

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
        
        st.markdown("---")
        st.info("📷 **Captura de Evidencia**")
        
        # --- SISTEMA DUAL DE IMAGEN ---
        # Opción A: Galería
        archivo_galeria = st.file_uploader("📁 Subir desde Galería", type=["jpg", "png", "jpeg"])
        
        # Opción B: Cámara Directa
        st.markdown("**O usar la Cámara Directa:**")
        archivo_camara = st.camera_input("Tomar Foto", label_visibility="collapsed")

        # Lógica de prioridad: Si hay foto de cámara, usa esa. Si no, usa galería.
        imagen_archivo = archivo_camara if archivo_camara else archivo_galeria

    with col_form:
        st.subheader("Ficha Técnica")
        datos_tecnicos = st.text_area("Describa el equipo y condiciones:", height=100, placeholder="Ej: Tubería oxidada, ambiente salino...")

    st.markdown("---")
    
    # Botón de acción
    if st.button("👁️ ANALIZAR AHORA", use_container_width=True):
        if not api_key:
             st.error("Falta API Key.")
        elif not imagen_archivo:
            st.error("⚠️ FALTAN DATOS: Debe subir una foto o tomar una con la cámara.")
        else:
            with st.spinner("Procesando imagen (esto puede tardar unos segundos)..."):
                # Crear temporal
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    tmp.write(imagen_archivo.getvalue())
                    ruta_temp = tmp.name
                
                info = {"usuario": usuario, "proyecto": proyecto, "modulo": modulo, "norma": norma}
                resultado = inspector.analizar_imagen_con_ia(api_key, ruta_temp, info, datos_tecnicos)
                
                st.session_state['res_web'] = resultado
                st.session_state['img_web'] = ruta_temp
                st.session_state['info_web'] = info
            st.success("¡Diagnóstico Completado!")

    # Resultados
    if 'res_web' in st.session_state:
        st.markdown("### Dictamen:")
        st.write(st.session_state['res_web'])
        if st.button("📄 Descargar PDF"):
            pdf = inspector.generar_pdf_ia(st.session_state['info_web'], st.session_state['res_web'], st.session_state['img_web'])
            st.download_button("Bajar Reporte", pdf, "Reporte_Vigia.pdf", "application/pdf")

# === PESTAÑA 2 ===
with tab2:
    st.header("Historial")
    if st.button("Borrar Todo"): inspector.borrar_memoria(); st.rerun()
    if st.button("Actualizar"): st.rerun()
    
    historial = inspector.obtener_historial()
    if historial:
        for fila in historial:
            with st.expander(f"{fila[0]} - {fila[2]}"): st.write(fila[4])
    else:
        st.info("Sin registros.")
