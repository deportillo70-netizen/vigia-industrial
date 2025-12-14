# PROYECTO: VIG.IA - CEREBRO (BRANDED PDF VERSION)
# ARCHIVO: Nucleo_Vigia.py
# DESCRIPCIÓN: Backend con IA, Base de Datos y Reportes PDF con Logo Corporativo.

import google.generativeai as genai
from fpdf import FPDF
import PIL.Image
import datetime
import os
import sqlite3
import time

# --- 1. GESTOR DE BASE DE DATOS (MEMORIA) ---
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

    def leer_historial(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT fecha, proyecto, modulo, norma, dictamen FROM inspecciones ORDER BY fecha DESC")
        datos = c.fetchall()
        conn.close()
        return datos

    def borrar_historial(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
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
    def obtener_historial(self): return self.db.leer_historial()
    def borrar_memoria(self): self.db.borrar_historial()

    def _encontrar_modelo_disponible(self):
        try:
            lista = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            for m in lista:
                if 'flash' in m and '1.5' in m: return m
            for m in lista:
                if 'pro' in m and 'vision' in m: return m
            return lista[0] if lista else None
        except: return None

    def analizar_imagen_con_ia(self, api_key, ruta_imagen, datos_ins, datos_tec):
        genai.configure(api_key=api_key)
        modelo = self._encontrar_modelo_disponible()
        if not modelo: return "ERROR: No hay modelos IA disponibles."

        try:
            img = PIL.Image.open(ruta_imagen)
        except: return "Error al abrir imagen."

        prompt = f"""
        Rol: Inspector Senior {datos_ins['modulo']}. Norma: {datos_ins['norma']}.
        Contexto Técnico: {datos_tec}
        Tarea: Auditoría visual. Genera REPORTE TÉCNICO ESTRUCTURADO:
        1. HALLAZGOS VISUALES (Detallado).
        2. ANÁLISIS NORMATIVO {datos_ins['norma']} (Cumple/No Cumple y Criterio).
        3. CAUSA RAÍZ PROBABLE.
        4. RECOMENDACIÓN EJECUTIVA (Acción concreta).
        Tono: Autoritario, técnico, sin saludos.
        """
        try:
            model = genai.GenerativeModel(modelo)
            response = model.generate_content([prompt, img])
            text = response.text
            self.db.guardar_inspeccion(datos_ins['proyecto'], datos_ins['usuario'], datos_ins['modulo'], datos_ins['norma'], text)
            return text
        except Exception as e: return f"Error IA: {str(e)}"

    def generar_pdf_ia(self, datos, texto_ia, ruta_imagen):
        pdf = PDFReport()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Datos del reporte
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'DICTAMEN TÉCNICO DE INSPECCIÓN', 0, 1, 'C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f"Proyecto: {datos['proyecto']} | Norma: {datos['norma']}", 0, 1, 'C')
        pdf.cell(0, 6, f"Inspector: {datos['usuario']} | Fecha: {datetime.datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'C')
        pdf.ln(10)
        
        # Imagen de Evidencia
        if os.path.exists(ruta_imagen):
            pdf.set_fill_color(255, 230, 200) # Fondo naranja claro
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, " EVIDENCIA VISUAL ANALIZADA", 1, 1, 'L', 1)
            pdf.ln(2)
            try:
                x_pos = (210 - 100) / 2 # Centrar imagen
                pdf.image(ruta_imagen, x=x_pos, w=100)
                pdf.ln(5)
            except: pass

        # Texto del Dictamen
        pdf.set_fill_color(50, 50, 50) # Fondo oscuro para título
        pdf.set_text_color(255, 255, 255) # Texto blanco
        pdf.cell(0, 8, " RESULTADOS DEL ANÁLISIS VIG.IA", 1, 1, 'L', 1)
        pdf.set_text_color(0, 0, 0) # Volver a negro
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 11)
        texto_limpio = texto_ia.replace('**', '').replace('##', '').replace('•', '-')
        texto_limpio = texto_limpio.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, texto_limpio)
        
        return pdf.output(dest='S').encode('latin-1')

# --- 3. CLASE DE DISEÑO PDF (CON LOGO) ---
class PDFReport(FPDF):
    def header(self):
        # 1. INSERTAR LOGO (Debe llamarse "logo.png" en GitHub)
        # Coordenadas: x=10, y=8. Ancho: 25mm
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 25)
            
        # 2. TEXTO DEL ENCABEZADO (Movido a la derecha)
        self.set_font('Arial', 'B', 12)
        self.cell(30) # Espacio en blanco para el logo
        self.cell(0, 10, 'VIG.IA - INDUSTRIAL INTELLIGENCE', 0, 0, 'L')
        
        # 3. LÍNEA SEPARADORA NARANJA (BRANDING)
        self.set_draw_color(255, 111, 0) # Color Safety Orange
        self.set_line_width(1)
        self.line(10, 28, 200, 28) # Línea debajo del logo
        self.ln(25) # Salto de línea grande para no tapar

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128) # Gris
        self.cell(0, 10, f'Reporte generado por Sistema VIG.IA | Página {self.page_no()}', 0, 0, 'C')
