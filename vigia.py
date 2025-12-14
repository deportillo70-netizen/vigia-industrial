# PROYECTO: VIG.IA - SISTEMA DE INTELIGENCIA INDUSTRIAL
# ARCHIVO: vigia.py
# VERSIÓN: 1.0 (BRANDED DEPOT/INDUSTRIAL STYLE)

import streamlit as st
import tempfile
import os
import time
from Nucleo_Vigia import InspectorIndustrial

# --- ⚠️ ZONA DE CONFIGURACIÓN ---
# Si quieres dejar la clave fija para tus amigos, ponla aquí:
CLAVE_MAESTRA = "" 
# --------------------------------

# 1. CONFIGURACIÓN DE PÁGINA (BRANDING)
st.set_page_config(page_title="VIG.IA | System", page_icon="🟠", layout="wide")

# 2. INYECCIÓN DE ESTILO (CSS INDUSTRIAL/FUTURISTA)
st.markdown("""
    <style>
    /* Importamos fuente robótica/técnica */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }

    /* Color de fondo de la barra lateral */
    [data-testid="stSidebar"] {
        background-color: #f4f4f4;
    }

    /* Títulos Principales en NARANJA SEGURIDAD (SAFETY ORANGE) */
    h1, h2, h3 {
        color: #FF6F00 !important; 
        font-weight: 700;
    }

    /* Botones Principales (Primary) */
    div.stButton > button:first-child {
        background-color: #FF6F00;
        color: white;
        border-radius: 4px;
        border: none;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Efecto Hover en Botones */
    div.stButton > button:first-child:hover {
        background-color: #E65100; /* Naranja más oscuro */
        border: 1px solid #333;
    }

    /* Alertas y Mensajes */
    .stAlert {
        border-left-color: #FF6F00 !important;
    }
    
    /* Input de Cámara */
    button[kind="secondary"] {
        border-color: #FF6F00;
        color: #FF6F00;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (CON NUEVA IMAGEN) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    
    # Si hay CLAVE_MAESTRA configurada, saltamos el login de la nube
    if CLAVE_MAESTRA:
        st.session_state["password_correct"] = True
        return True

    # PANTALLA DE ACCESO BRANDED
    col_spacer1, col_login, col_spacer2 = st.columns([1, 2, 1])
    with col_login:
        st.markdown("<h1 style='text-align: center; color: #333;'>🟠 VIG.IA</h1>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; color: #666;'>SISTEMA DE INTELIGENCIA INDUSTRIAL</h4>", unsafe_allow_html=True)
        st.markdown("---")
        pwd = st.text_input("Credencial de Acceso:", type="password")
        
        if st.button("INGRESAR AL SISTEMA", use_container_width=True):
            if pwd == st.secrets["APP_PASSWORD"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("⛔ CREDENCIAL INVÁLIDA")
    return False

if not check_password():
    st.stop()

# --- INICIO DEL PROGRAMA ---
if 'inspector' not in st.session_state:
    st.session_state.inspector = InspectorIndustrial()

inspector = st.session_state.inspector

# Gestión de API Key (Prioridad: Maestra > Nube > Manual)
try:
    API_KEY_NUBE = st.secrets["GOOGLE_API_KEY"]
except:
    API_KEY_NUBE = ""

# --- SIDEBAR (PANEL DE CONTROL) ---
with st.sidebar:
    st.markdown("# 🟠 VIG.IA")
    st.markdown("**Industrial Intelligence v1.0**")
    st.markdown("---")
    
    # Estado de la Licencia
    if CLAVE_MAESTRA:
        api_key = CLAVE_MAESTRA
        st.success("🔓 Licencia: LOCAL (DEV)")
    elif API_KEY_NUBE:
        api_key = API_KEY_NUBE
        st.info("☁️ Licencia: CLOUD (PRO)")
    else:
        api_key = st.text_input("🔑 API Key (Manual):", type="password")

    st.markdown("---")
    st.markdown("### 👷‍♂️ Datos de Auditoría")
    usuario = st.text_input("Inspector:", "Invitado Remoto")
    proyecto = st.text_input("Activo / Tag:", "Inspección Móvil")

# --- TABS PRINCIPALES ---
tab1, tab2 = st.tabs(["🕵️ INSPECCIÓN EN CAMPO", "📜 MEMORIA TÉCNICA"])

# === PESTAÑA 1: INSPECCIÓN ===
with tab1:
    col_conf, col_form = st.columns([1, 2])
    
    with col_conf:
        st.subheader("1. Configuración")
        modulo = st.selectbox("Especialidad:", inspector.obtener_modulos())
        norma = st.selectbox("Norma Técnica:", inspector.obtener_normas(modulo))
        
        st.markdown("---")
        st.info("📷 **Captura de Evidencia**")
        
        # --- SISTEMA DUAL DE IMAGEN ---
        # Opción A: Galería
        archivo_galeria = st.file_uploader("📁 Subir desde Galería", type=["jpg", "png", "jpeg"])
        
        # Opción B: Cámara Directa
        st.markdown("**O usar Cámara Directa:**")
        archivo_camara = st.camera_input("ACTIVAR CÁMARA", label_visibility="collapsed")

        # Prioridad: Cámara mata Galería
        imagen_archivo = archivo_camara if archivo_camara else archivo_galeria

    with col_form:
        st.subheader("2. Ficha Técnica (Entrevista)")
        
        # --- FORMULARIOS DINÁMICOS ---
        datos_tecnicos = ""
        
        if "MECÁNICO" in modulo:
            c1, c2 = st.columns(2)
            diametro = c1.number_input("Diámetro (m):", 0.0, 100.0, 15.0)
            altura = c2.number_input("Altura (m):", 0.0, 50.0, 8.0)
            material = c1.text_input("Material Base:", "Acero ASTM A36")
            fluido = c2.text_input("Fluido:", "Crudo")
            datos_tecnicos = f"Equipo Estático. Dimensiones: {diametro}x{altura}m. Material: {material}. Fluido: {fluido}."
            
        elif "ELÉCTRICO" in modulo:
            c1, c2 = st.columns(2)
            voltaje = c1.selectbox("Voltaje:", ["110/220V", "440V", "13.8kV", "115kV"])
            equipo = c2.text_input("Equipo:", "Transformador")
            carga = c1.number_input("Amperaje (A):", 0.0, 5000.0, 100.0)
            falla = c2.selectbox("Condición:", ["Punto Caliente", "Ruido", "Arco"])
            datos_tecnicos = f"Equipo Eléctrico: {equipo}. Tensión: {voltaje}. Carga: {carga}A. Condición: {falla}."
            
        elif "SOLDADURA" in modulo:
            proceso = st.selectbox("Proceso:", ["SMAW", "GTAW", "GMAW", "FCAW"])
            posicion = st.selectbox("Posición:", ["1G", "2G", "3G", "4G", "6G"])
            datos_tecnicos = f"Inspección de Soldadura. Proceso: {proceso}. Posición: {posicion}."
            
        else:
            datos_tecnicos = st.text_area("Describa las condiciones técnicas:", height=100, placeholder="Ej: Corrosión severa en ambiente marino...")

        st.caption(f"Contexto técnico para IA: {datos_tecnicos}")

    st.markdown("---")
    
    # BOTÓN DE ACCIÓN (NARANJA POR CSS)
    if st.button("👁️ EJECUTAR ANÁLISIS VIG.IA", use_container_width=True):
        if not api_key:
             st.error("⛔ ERROR: Falta API Key de Google.")
        elif not imagen_archivo:
            st.error("⚠️ ALERTA: Debe cargar evidencia visual.")
        else:
            with st.spinner("🔄 VIG.IA procesando normas y evidencia..."):
                # Crear temporal
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    tmp.write(imagen_archivo.getvalue())
                    ruta_temp = tmp.name
                
                info = {"usuario": usuario, "proyecto": proyecto, "modulo": modulo, "norma": norma}
                resultado = inspector.analizar_imagen_con_ia(api_key, ruta_temp, info, datos_tecnicos)
                
                st.session_state['res_web'] = resultado
                st.session_state['img_web'] = ruta_temp
                st.session_state['info_web'] = info
            st.success("✅ DICTAMEN GENERADO")

    # RESULTADOS
    if 'res_web' in st.session_state:
        st.markdown("### 📋 Dictamen Técnico")
        st.write(st.session_state['res_web'])
        
        if st.button("📄 DESCARGAR PDF OFICIAL"):
            pdf = inspector.generar_pdf_ia(st.session_state['info_web'], st.session_state['res_web'], st.session_state['img_web'])
            st.download_button("Bajar Informe PDF", pdf, "Informe_VIGIA.pdf", "application/pdf", use_container_width=True)

# === PESTAÑA 2: MEMORIA ===
with tab2:
    col_head, col_trash = st.columns([3, 1])
    with col_head:
        st.header("Historial de Inspecciones")
    with col_trash:
        if st.button("🗑️ FORMATEAR"):
            inspector.borrar_memoria()
            st.toast("Memoria borrada", icon="🗑️")
            time.sleep(1)
            st.rerun()

    if st.button("🔄 Actualizar Lista"): st.rerun()
    
    historial = inspector.obtener_historial()
    if historial:
        for fila in historial:
            # fila: fecha, proyecto, modulo, norma, dictamen
            with st.expander(f"📅 {fila[0]} | {fila[1]} ({fila[2]})"):
                st.markdown(f"**Norma:** {fila[3]}")
                st.divider()
                st.markdown(fila[4])
    else:
        st.info("La base de datos está limpia.")
