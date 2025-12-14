# PROYECTO: VIG.IA - CEREBRO (MULTI-USER & MULTI-IMAGE)
# ARCHIVO: Nucleo_Vigia.py
# DESCRIPCIÓN: Backend con soporte para múltiples imágenes y privacidad por usuario.

import google.generativeai as genai
from fpdf import FPDF
import PIL.Image
import datetime
import os
import sqlite3
import time

# --- 1. GESTOR DE BASE DE DATOS ---
class GestorDatos:
    def __init__(self, db_name="historial_vigia.db"):
        self.db_name = db_name
        self._inicializar_db()

    def _inicializar_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS inspecciones
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      fecha TEXT, proyecto TEXT, inspector TEXT,
                      modulo TEXT, norma TEXT, dictamen TEXT)''')
        conn.commit()
        conn.close()

    def guardar_inspeccion(self, proyecto, inspector, modulo, norma, dictamen):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO inspecciones (fecha, proyecto, inspector, modulo, norma, dictamen) VALUES (?, ?, ?, ?, ?, ?)",
                  (fecha, proyecto, inspector, modulo, norma, dictamen))
        conn.commit()
        conn.close()

    def leer_historial(self, usuario_filtro=None):
        """
        Devuelve el historial. Si se pasa un usuario, filtra solo sus inspecciones.
        """
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        if usuario_filtro:
            # Filtramos por el nombre exacto del inspector (evita que Henry vea lo de Miguel)
            c.execute("SELECT fecha, proyecto, modulo, norma, dictamen FROM inspecciones WHERE inspector = ? ORDER BY fecha DESC", (usuario_filtro,))
        else:
            # Si no hay filtro, mostramos todo (comportamiento legacy)
            c.execute("SELECT fecha, proyecto, modulo, norma, dictamen FROM inspecciones ORDER BY fecha DESC")
            
        datos = c.fetchall()
        conn.close()
        return datos

    def borrar_historial(self, usuario_filtro=None):
        """
        Borra el historial. Si se pasa usuario, borra SOLO lo de ese usuario.
        """
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        if usuario_filtro:
            c.execute("DELETE FROM inspecciones WHERE inspector = ?", (usuario_filtro,))
        else:
            c.execute("DELETE FROM inspecciones")
            
        conn.commit()
        conn.close()

# --- 2. CEREBRO PRINCIPAL (IA) ---
class InspectorIndustrial:
    def __init__(self):
        self.db = GestorDatos()
        self.estructura_conocimiento = {
            "MECÁNICO (Tanques/Recipientes)": ["API 653", "API 510", "API 570"],
            "SOLDADURA Y ESTRUCTURA": ["ASME IX", "AWS D1.1", "API 1104"],
            "CORROSIÓN Y PINTURA": ["NACE SP0188", "SSPC-PA2", "ISO 8501"],
            "ELÉCTRICO Y POTENCIA": ["NFPA 70B", "NETA MTS", "IEEE 43"],
            "SEGURIDAD (HSE)": ["OSHA 1910", "ISO 45001"]
        }

    def obtener_modulos(self): return list(self.estructura_conocimiento.keys())
    def obtener_normas(self, modulo): return self.estructura_conocimiento.get(modulo, [])
    
    # MODIFICADO: Pasamos el usuario a la base de datos
    def obtener_historial(self, usuario=None): 
        return self.db.leer_historial(usuario)
    
    # MODIFICADO: Borramos solo lo del usuario
    def borrar_memoria(self, usuario=None): 
        self.db.borrar_historial(usuario)

    def _encontrar_modelo_disponible(self):
        try:
            lista = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            for m in lista:
                if 'flash' in m and '1.5' in m: return m
            for m in lista:
                if 'pro' in m and 'vision' in m: return m
            return lista[0] if lista else None
        except: return None

    def analizar_imagen_con_ia(self, api_key, lista_rutas_imagenes, datos_ins, datos_tec):
        genai.configure(api_key=api_key)
        modelo = self._encontrar_modelo_disponible()
        if not modelo: return "ERROR: No hay modelos IA disponibles."

        imagenes_pil = []
        try:
            if isinstance(lista_rutas_imagenes, str):
                lista_rutas_imagenes = [lista_rutas_imagenes]
            for ruta in lista_rutas_imagenes:
                imagenes_pil.append(PIL.Image.open(ruta))
        except Exception as e:
            return f"Error abriendo archivos de imagen: {e}"

        prompt = f"""
        Rol: Inspector Senior {datos_ins['modulo']}. Norma: {datos_ins['norma']}.
        Contexto Técnico: {datos_tec}
        
        Tarea: Auditoría visual basada en las {len(imagenes_pil)} imágenes.
        Genera REPORTE TÉCNICO ESTRUCTURADO:
        1. HALLAZGOS VISUALES (Integra lo observado).
        2. ANÁLISIS NORMATIVO {datos_ins['norma']} (Cumple/No Cumple y Criterio).
        3. CAUSA RAÍZ PROBABLE.
        4. RECOMENDACIÓN EJECUTIVA (Acción concreta).
        Tono: Autoritario, técnico, sin saludos.
        """
        try:
            model = genai.GenerativeModel(modelo)
            contenido = [prompt] + imagenes_pil
            response = model.generate_content(contenido)
            text = response.text
            self.db.guardar_inspeccion(datos_ins['proyecto'], datos_ins['usuario'], datos_ins['modulo'], datos_ins['norma'], text)
            return text
        except Exception as e: return f"Error IA: {str(e)}"

    def generar_pdf_ia(self, datos, texto_ia, lista_rutas_imagenes):
        pdf = PDFReport()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # PÁGINA 1
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'DICTAMEN TÉCNICO DE INSPECCIÓN', 0, 1, 'C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f"Proyecto: {datos['proyecto']} | Norma: {datos['norma']}", 0, 1, 'C')
        pdf.cell(0, 6, f"Inspector: {datos['usuario']} | Fecha: {datetime.datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'C')
        pdf.ln(10)
        
        pdf.set_fill_color(50, 50, 50) 
        pdf.set_text_color(255, 255, 255) 
        pdf.cell(0, 8, " RESULTADOS DEL ANÁLISIS VIG.IA", 1, 1, 'L', 1)
        pdf.set_text_color(0, 0, 0) 
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 11)
        texto_limpio = texto_ia.replace('**', '').replace('##', '').replace('•', '-')
        texto_limpio = texto_limpio.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, texto_limpio)
        
        # PÁGINA 2+: ANEXO FOTOGRÁFICO
        if lista_rutas_imagenes:
            if isinstance(lista_rutas_imagenes, str):
                lista_rutas_imagenes = [lista_rutas_imagenes]
                
            pdf.add_page()
            pdf.set_fill_color(255, 111, 0)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, " ANEXO FOTOGRÁFICO", 0, 1, 'C', 1)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(10)
            
            y_pos = 40
            for i, ruta in enumerate(lista_rutas_imagenes):
                if os.path.exists(ruta):
                    if y_pos > 220:
                        pdf.add_page()
                        y_pos = 40
                    pdf.set_font('Arial', 'I', 10)
                    pdf.cell(0, 10, f"Figura {i+1}: Evidencia capturada.", 0, 1, 'L')
                    try:
                        pdf.image(ruta, x=35, y=y_pos+8, w=140, h=105)
                    except: pass
                    y_pos += 120

        return pdf.output(dest='S').encode('latin-1')

class PDFReport(FPDF):
    def header(self):
        if os.path.exists("logo.png"): self.image("logo.png", 10, 8, 25)
        self.set_font('Arial', 'B', 12)
        self.cell(30)
        self.cell(0, 10, 'VIG.IA - INDUSTRIAL INTELLIGENCE', 0, 0, 'L')
        self.set_draw_color(255, 111, 0)
        self.set_line_width(1)
        self.line(10, 28, 200, 28)
        self.ln(25)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Reporte VIG.IA | Página {self.page_no()}', 0, 0, 'C')
