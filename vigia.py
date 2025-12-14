# PROYECTO: VIG.IA - SISTEMA DE INTELIGENCIA INDUSTRIAL
# ARCHIVO: vigia.py
# VERSIÓN: 2.2 (NO-SECRETS EDITION - LISTO PARA USAR)

import streamlit as st
import tempfile
import os
import time
from Nucleo_Vigia import InspectorIndustrial

# --- ⚠️ CONFIGURACIÓN ---
# Aquí está tu llave lista para usar:
CLAVE_MAESTRA = "AIzaSyCW7R-xFb9eupsLcHEeuuZUCvAp3-l3bn4" 
# ------------------------

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="VIG.IA | System", page_icon="🟠", layout="wide")

# 2. INYECCIÓN DE ESTILO
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    [data-testid="stSidebar"] { background-color: #f4f4f4; }
    h1, h2, h3 { color: #FF6F00 !important; font-weight: 700; }
    div.stButton > button:first-child {
        background-color: #FF6F00; color: white; border-radius: 4px; border: none; font-weight: bold;
    }
    div.stButton > button:first-child:hover { background-color: #E65100; border: 1px solid #333; }
    .stAlert { border-left-color: #FF6F00 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (SIMPLIFICADO) ---
def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True
    
    # Si ya pusiste la clave maestra en el código, permitimos el acceso, 
    # pero igual pedimos login por formalidad.
    
    col_spacer1, col_login, col_spacer2 = st.columns([1, 2, 1])
    with col_login:
        st.markdown("<h1 style='text-align: center; color: #333;'>🟠 VIG.IA</h1>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; color: #666;'>SISTEMA DE INTELIGENCIA INDUSTRIAL</h4>", unsafe_allow_html=True)
        st.markdown("---")
        pwd = st.text_input("Credencial de Acceso:", type="password")
        
        if st.button("INGRESAR AL SISTEMA", use_container_width=True):
            # --- CAMBIO: Contraseña fija "admin" para evitar errores ---
            if pwd == "admin": 
                st.session_state["password_correct"] = True
                st.rerun()
            else: 
                st.error("⛔ CREDENCIAL INVÁLIDA")
    return False

if not check_password(): st.stop()

# --- INICIO ---
if 'inspector' not in st.session_state: st.session_state.inspector = InspectorIndustrial()
inspector = st.session_state.inspector

# Usamos la clave maestra que pusimos arriba
api_key = CLAVE_MAESTRA 

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("# 🟠 VIG.IA")
    st.markdown("**Industrial Intelligence v2.2**")
    st.markdown("---")
    
    if api_key:
        st.success("🔓 Licencia: LOCAL (ACTIVA)")
    else:
        st.error("🔒 Falta API Key")
        
    st.markdown("---")
    st.markdown("### 👷‍♂️ Datos de Auditoría")
    
    # Mantenemos el usuario activo
    if 'usuario_actual' not in st.session_state: st.session_state.usuario_actual = "Invitado Remoto"
    usuario = st.text_input("Inspector:", st.session_state.usuario_actual)
    st.session_state.usuario_actual = usuario 
    
    proyecto = st.text_input("Activo / Tag:", "Inspección Móvil")

# --- TABS ---
tab1, tab2 = st.tabs(["🕵️ INSPECCIÓN EN CAMPO", "📜 MI MEMORIA TÉCNICA"])

# === PESTAÑA 1: INSPECCIÓN ===
with tab1:
    col_conf, col_form = st.columns([1, 2])
    
    with col_conf:
        st.subheader("1. Configuración")
        modulo = st.selectbox("Especialidad:", inspector.obtener_modulos())
        norma = st.selectbox("Norma Técnica:", inspector.obtener_normas(modulo))
        
        st.markdown("---")
        st.info("📷 **Captura de Evidencia (Múltiple)**")
        
        # A: Galería
        archivos_galeria = st.file_uploader("📁 Subir fotos (Máx 10)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        
        # B: Cámara
        st.markdown("**O agregar foto de Cámara:**")
        archivo_camara = st.camera_input("ACTIVAR CÁMARA", label_visibility="collapsed")

        # LOGICA DE UNIFICACIÓN
        lista_imagenes_final = []
        if archivos_galeria:
            lista_imagenes_final.extend(archivos_galeria)
        if archivo_camara:
            lista_imagenes_final.append(archivo_camara)

        if lista_imagenes_final:
            st.caption(f"✅ {len(lista_imagenes_final)} imágenes listas para analizar.")

    with col_form:
        st.subheader("2. Ficha Técnica (Entrevista)")
        datos_tecnicos = ""
        if "MECÁNICO" in modulo:
            c1, c2 = st.columns(2)
            diametro = c1.number_input("Diámetro (m):", 0.0, 100.0, 15.0)
            material = c2.text_input("Material:", "Acero ASTM A36")
            datos_tecnicos = f"Equipo Estático. Diámetro: {diametro}m. Material: {material}."
        elif "ELÉCTRICO" in modulo:
            c1, c2 = st.columns(2)
            voltaje = c1.selectbox("Voltaje:", ["110/220V", "440V", "13.8kV"])
            equipo = c2.text_input("Equipo:", "Transformador")
            datos_tecnicos = f"Equipo Eléctrico: {equipo}. Tensión: {voltaje}."
        else:
            datos_tecnicos = st.text_area("Condiciones:", height=100)

    st.markdown("---")
    
    # BOTÓN DE ACCIÓN
    if st.button("👁️ EJECUTAR ANÁLISIS VIG.IA (MULTI-FOTO)", use_container_width=True):
        if not api_key: st.error("⛔ Falta API Key en el código.")
        elif not lista_imagenes_final: st.error("⚠️ Debe cargar al menos una imagen.")
        else:
            with st.spinner(f"🔄 VIG.IA analizando {len(lista_imagenes_final)} imágenes..."):
                
                # Guardar imágenes temporalmente
                rutas_temporales = []
                for img_file in lista_imagenes_final:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                        tmp.write(img_file.getvalue())
                        rutas_temporales.append(tmp.name)
                
                info = {"usuario": usuario, "proyecto": proyecto, "modulo": modulo, "norma": norma}
                
                # Llamada al núcleo
                resultado = inspector.analizar_imagen_con_ia(api_key, rutas_temporales, info, datos_tecnicos)
                
                st.session_state['res_web'] = resultado
                st.session_state['imgs_web'] = rutas_temporales 
                st.session_state['info_web'] = info
            st.success("✅ DICTAMEN GENERADO")

    # RESULTADOS
    if 'res_web' in st.session_state:
        st.markdown("### 📋 Dictamen Técnico")
        st.write(st.session_state['res_web'])
        
        if st.button("📄 DESCARGAR PDF OFICIAL"):
            pdf = inspector.generar_pdf_ia(st.session_state['info_web'], st.session_state['res_web'], st.session_state['imgs_web'])
            st.download_button("Bajar Informe PDF", pdf, "Informe_VIGIA.pdf", "application/pdf", use_container_width=True)

# === PESTAÑA 2: HISTORIAL PRIVADO ===
with tab2:
    col_head, col_trash = st.columns([3, 1])
    with col_head: 
        st.header(f"Historial de: {usuario}") 
    with col_trash:
        # Borra solo lo de este usuario
        if st.button("🗑️ LIMPIAR MIS DATOS"): 
            inspector.borrar_memoria(usuario) 
            st.warning(f"Historial de {usuario} eliminado.")
            time.sleep(1)
            st.rerun()
            
    if st.button("🔄 Actualizar Tabla"): st.rerun()
    
    # Lee solo lo de este usuario (desde Google Sheets si ya actualizaste el Nucleo)
    historial = inspector.obtener_historial(usuario) 
    
    if historial:
        for fila in historial:
            with st.expander(f"📅 {fila[0]} | {fila[1]} ({fila[2]})"):
                st.markdown(f"**Norma Aplicada:** {fila[3]}")
                st.markdown("---")
                st.markdown(fila[4])
    else:
        st.info(f"No hay registros guardados para el inspector {usuario}.")
