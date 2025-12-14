# PROYECTO: VIG.IA - CEREBRO (CLOUD EDITION)
# ARCHIVO: Nucleo_Vigia.py

import google.generativeai as genai
from fpdf import FPDF
import PIL.Image
import datetime
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. GESTOR DE DATOS (GOOGLE SHEETS) ---
class GestorDatos:
    def __init__(self, json_key="credentials.json", sheet_name="BD_VIGIA"):
        self.json_key = json_key
        self.sheet_name = sheet_name
        self.sheet = None
        self._conectar_drive()

    def _conectar_drive(self):
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.json_key, scope)
            client = gspread.authorize(creds)
            self.sheet = client.open(self.sheet_name).sheet1
            print("✅ CONEXIÓN A SHEETS EXITOSA")
        except Exception as e:
            print(f"⚠️ ERROR FATAL CONECTANDO A SHEETS: {e}")
            self.sheet = None

    def guardar_inspeccion(self, proyecto, inspector, modulo, norma, dictamen):
        if not self.sheet: 
            print("❌ No hay conexión, intentando reconectar...")
            self._conectar_drive()
            if not self.sheet: return False
        
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fila = [fecha, proyecto, inspector, modulo, norma, dictamen]
        try:
            self.sheet.append_row(fila)
            print(f"📝 GUARDADO EN NUBE: {inspector} - {proyecto}")
            return True
        except Exception as e:
            print(f"❌ ERROR AL ESCRIBIR FILA: {e}")
            return False

    def leer_historial(self, usuario_filtro=None):
        if not self.sheet: self._conectar_drive()
        if not self.sheet: return []
        
        try:
            datos_raw = self.sheet.get_all_values()
            if not datos_raw: return []
            
            # Saltamos encabezados
            if "Fecha" in datos_raw[0][0]: datos_raw = datos_raw[1:]
            
            resultados = []
            for fila in datos_raw:
                if len(fila) < 6: continue
                
                # Fila Sheets: [0]Fecha, [1]Proy, [2]Insp, [3]Mod, [4]Norma, [5]Dict
                insp_actual = fila[2]
                
                if usuario_filtro:
                    if insp_actual.strip().lower() == usuario_filtro.strip().lower():
                        resultados.append((fila[0], fila[1], fila[2], fila[4], fila[5]))
                else:
                    resultados.append((fila[0], fila[1], fila[2], fila[4], fila[5]))
            
            return sorted(resultados, key=lambda x: x[0], reverse=True)
        except: return []

    def borrar_historial(self, usuario_filtro=None):
        # Por seguridad en la nube, evitamos borrar todo por error desde código simple
        # Solo borramos si es necesario. (Implementación simplificada para no borrar DB por error)
        pass 

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
    def obtener_historial(self, usuario=None): return self.db.leer_historial(usuario)
    def borrar_memoria(self, usuario=None): self.db.borrar_historial(usuario)

    def _encontrar_modelo_disponible(self):
        try:
            lista = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            for m in lista:
                if 'flash' in m and '1.5' in m: return m
            return lista[0] if lista else None
        except: return None

    def analizar_imagen_con_ia(self, api_key, lista_rutas_imagenes, datos_ins, datos_tec):
        genai.configure(api_key=api_key)
        modelo = self._encontrar_modelo_disponible()
        if not modelo: return "ERROR: No hay modelos IA disponibles."

        imagenes_pil = []
        try:
            if isinstance(lista_rutas_imagenes, str): lista_rutas_imagenes = [lista_rutas_imagenes]
            for ruta in lista_rutas_imagenes: imagenes_pil.append(PIL.Image.open(ruta))
        except: return "Error abriendo imagenes."

        prompt = f"""
        Rol: Inspector Senior {datos_ins['modulo']}. Norma: {datos_ins['norma']}.
        Contexto: {datos_tec}
        Genera REPORTE TÉCNICO: 1. Hallazgos, 2. Análisis {datos_ins['norma']}, 3. Recomendación.
        """
        try:
            model = genai.GenerativeModel(modelo)
            contenido = [prompt] + imagenes_pil
            response = model.generate_content(contenido)
            text = response.text
            
            # --- GUARDADO EN NUBE ---
            self.db.guardar_inspeccion(
                datos_ins['proyecto'], 
                datos_ins['usuario'], 
                datos_ins['modulo'], 
                datos_ins['norma'], 
                text
            )
            return text
        except Exception as e: return f"Error IA: {str(e)}"

    def generar_pdf_ia(self, datos, texto_ia, lista_rutas_imagenes):
        pdf = PDFReport()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'DICTAMEN TÉCNICO', 0, 1, 'C')
        pdf.set_font('Arial', '', 11)
        pdf.multi_cell(0, 6, texto_ia.encode('latin-1', 'replace').decode('latin-1'))
        return pdf.output(dest='S').encode('latin-1')

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'VIG.IA CLOUD SYSTEM', 0, 0, 'L')
        self.ln(20)
