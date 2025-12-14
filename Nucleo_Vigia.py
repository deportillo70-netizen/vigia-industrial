# PROYECTO: VIGÍA INDUSTRIAL - CEREBRO CON GESTIÓN DE MEMORIA
# ARCHIVO: Nucleo_Vigia.py
# DESCRIPCIÓN: Backend con funciones de IA, PDF y limpieza de Base de Datos.

import google.generativeai as genai
from fpdf import FPDF
import PIL.Image
import datetime
import os
import sqlite3
import time

# --- 1. GESTOR DE BASE DE DATOS (LA MEMORIA) ---
class GestorDatos:
    def __init__(self, db_name="historial_vigia.db"):
        self.db_name = db_name
        self._inicializar_db()

    def _inicializar_db(self):
        """Crea la tabla si no existe."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS inspecciones
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      fecha TEXT,
                      proyecto TEXT,
                      inspector TEXT,
                      modulo TEXT,
                      norma TEXT,
                      dictamen TEXT)''')
        conn.commit()
        conn.close()

    def guardar_inspeccion(self, proyecto, inspector, modulo, norma, dictamen):
        """Guarda el resultado de la IA en la base de datos."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO inspecciones (fecha, proyecto, inspector, modulo, norma, dictamen) VALUES (?, ?, ?, ?, ?, ?)",
                  (fecha, proyecto, inspector, modulo, norma, dictamen))
        conn.commit()
        conn.close()

    def leer_historial(self):
        """Devuelve todas las inspecciones guardadas."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT fecha, proyecto, modulo, norma, dictamen FROM inspecciones ORDER BY fecha DESC")
        datos = c.fetchall()
        conn.close()
        return datos

    def borrar_historial(self):
        """ELIMINA TODOS LOS REGISTROS DE LA BASE DE DATOS."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("DELETE FROM inspecciones")
        conn.commit()
        conn.close()

# --- 2. CEREBRO PRINCIPAL ---
class InspectorIndustrial:
    def __init__(self):
        self.db = GestorDatos()
        # Base de conocimiento
        self.estructura_conocimiento = {
            "MECÁNICO (Tanques/Recipientes)": ["API 653 (Tanques)", "API 510 (Presión)", "API 570 (Tuberías)"],
            "SOLDADURA Y ESTRUCTURA": ["ASME IX (WPS/PQR)", "AWS D1.1 (Acero)", "API 1104 (Lineas)"],
            "CORROSIÓN Y PINTURA": ["NACE SP0188", "SSPC-PA2 (Espesores)", "ISO 8501 (Limpieza)"],
            "ELÉCTRICO Y POTENCIA": ["NFPA 70B (Mantenimiento)", "NETA MTS", "IEEE 43 (Aislamiento)"],
            "SEGURIDAD (HSE)": ["OSHA 1910", "ISO 45001"]
        }

    def obtener_modulos(self):
        return list(self.estructura_conocimiento.keys())

    def obtener_normas(self, modulo):
        return self.estructura_conocimiento.get(modulo, [])
    
    def obtener_historial(self):
        return self.db.leer_historial()

    def borrar_memoria(self):
        """Llama al gestor de datos para limpiar la tabla."""
        self.db.borrar_historial()

    def _encontrar_modelo_disponible(self):
        """Busca el mejor modelo disponible en la cuenta de Google."""
        try:
            lista_modelos = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    lista_modelos.append(m.name)
            
            # Prioridades
            for m in lista_modelos:
                if 'flash' in m and '1.5' in m: return m
            for m in lista_modelos:
                if 'pro' in m and 'vision' in m: return m
            
            if lista_modelos: return lista_modelos[0]
            return None
        except:
            return None

    def analizar_imagen_con_ia(self, api_key, ruta_imagen, datos_inspeccion, ficha_tecnica_str):
        """
        Analiza la imagen usando datos técnicos específicos y guarda en DB.
        """
        # 1. Configurar
        genai.configure(api_key=api_key)
        modelo_nombre = self._encontrar_modelo_disponible()
        
        if not modelo_nombre:
            return "ERROR CRÍTICO: No se encontraron modelos de IA disponibles. Revise conexión/VPN."

        # 2. Cargar imagen
        try:
            img = PIL.Image.open(ruta_imagen)
        except Exception as e:
            return f"Error imagen: {e}"

        # 3. Prompt Avanzado (Con Datos Técnicos)
        prompt = f"""
        Rol: Inspector Senior en {datos_inspeccion['modulo']}.
        Tarea: Auditoría según {datos_inspeccion['norma']}.
        
        DATOS TÉCNICOS DEL EQUIPO (FICHA TÉCNICA):
        {ficha_tecnica_str}
        
        Instrucciones: Analiza la imagen buscando fallas que contradigan la norma o los datos técnicos provistos.
        
        Genera REPORTE TÉCNICO:
        1. HALLAZGOS VISUALES: (Sé específico).
        2. ANÁLISIS NORMATIVO: (Cita la norma {datos_inspeccion['norma']}).
        3. CAUSA RAÍZ: (Basada en la física del fallo).
        4. RECOMENDACIÓN: (Acción correctiva).
        """

        try:
            model = genai.GenerativeModel(modelo_nombre)
            response = model.generate_content([prompt, img])
            texto_resultado = response.text
            
            # 4. GUARDAR EN MEMORIA (DB)
            self.db.guardar_inspeccion(
                datos_inspeccion['proyecto'],
                datos_inspeccion['usuario'],
                datos_inspeccion['modulo'],
                datos_inspeccion['norma'],
                texto_resultado
            )
            
            return f"[Fuente: {modelo_nombre}]\n\n" + texto_resultado
            
        except Exception as e:
            return f"Error IA: {str(e)}"

    def generar_pdf_ia(self, datos, texto_ia, ruta_imagen):
        pdf = PDFReport()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Título
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'REPORTE TÉCNICO DE INSPECCIÓN', 0, 1, 'C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f"Norma: {datos['norma']} | Fecha: {datetime.datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'C')
        pdf.cell(0, 6, f"Proyecto: {datos['proyecto']}", 0, 1, 'C')
        pdf.ln(5)
        
        # Imagen
        if os.path.exists(ruta_imagen):
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 8, " EVIDENCIA FOTOGRÁFICA", 1, 1, 'L', 1)
            pdf.ln(2)
            try:
                x_pos = (210 - 100) / 2
                pdf.image(ruta_imagen, x=x_pos, w=100)
                pdf.ln(5)
            except: pass

        # Texto
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, " DICTAMEN DEL INSPECTOR", 1, 1, 'L', 1)
        pdf.ln(2)
        
        pdf.set_font('Arial', '', 11)
        texto_limpio = texto_ia.replace('**', '').replace('##', '').replace('•', '-')
        texto_limpio = texto_limpio.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, texto_limpio)
        
        return pdf.output(dest='S').encode('latin-1')

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'VIGÍA INDUSTRIAL - SISTEMA INTELIGENTE', 0, 0, 'L')
        self.line(10, 18, 200, 18)
        self.ln(12)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pág {self.page_no()}', 0, 0, 'C')