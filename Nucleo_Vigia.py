# PROYECTO: VIG.IA - CEREBRO (CLOUD EDITION)
# ARCHIVO: Nucleo_Vigia.py
# DESCRIPCIÓN: Backend conectado a Google Sheets + Google Gemini

import google.generativeai as genai
from fpdf import FPDF
import PIL.Image
import datetime
import os
import time

# LIBRERÍAS DE GOOGLE SHEETS
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. GESTOR DE DATOS (GOOGLE SHEETS) ---
class GestorDatos:
    def __init__(self, json_key="credentials.json", sheet_name="BD_VIGIA"):
        self.json_key = json_key
        self.sheet_name = sheet_name
        self.client = None
        self.sheet = None
        self._conectar_drive()

    def _conectar_drive(self):
        """Conecta con Google Drive y Sheets usando el robot"""
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.json_key, scope)
            self.client = gspread.authorize(creds)
            # Abrimos la hoja. Si da error, asegúrate de haberla compartido con el robot.
            self.sheet = self.client.open(self.sheet_name).sheet1 
        except Exception as e:
            print(f"⚠️ ERROR DE CONEXIÓN A SHEETS: {e}")
            self.sheet = None

    def guardar_inspeccion(self, proyecto, inspector, modulo, norma, dictamen):
        """Escribe una nueva fila en Google Sheets"""
        if not self.sheet: self._conectar_drive()
        
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Columnas: Fecha | Proyecto | Inspector | Modulo | Norma | Dictamen
        fila = [fecha, proyecto, inspector, modulo, norma, dictamen]
        
        try:
            self.sheet.append_row(fila)
            return True
        except:
            return False

    def leer_historial(self, usuario_filtro=None):
        """Lee todas las filas y filtra por usuario"""
        if not self.sheet: self._conectar_drive()
        
        try:
            # Obtenemos todos los registros (lista de listas)
            datos_raw = self.sheet.get_all_values()
            
            # Saltamos la fila 1 si son encabezados (Fecha, Proyecto...)
            if datos_raw and "Fecha" in datos_raw[0][0]:
                datos_raw = datos_raw[1:]
                
            resultados = []
            # Estructura en Sheet: [0]Fecha, [1]Proyecto, [2]Inspector, [3]Modulo, [4]Norma, [5]Dictamen
            
            for fila in datos_raw:
                if len(fila) < 6: continue # Saltar filas incompletas
                
                inspector_row = fila[2] # Columna C es Inspector
                
                # Si hay filtro, solo guardamos si coincide el usuario
                if usuario_filtro:
                    if inspector_row.strip().lower() == usuario_filtro.strip().lower():
                        # Devolvemos formato para vigia.py: (fecha, proyecto, modulo, norma, dictamen)
                        resultados.append((fila[0], fila[1], fila[3], fila[4], fila[5]))
                else:
                    # Si no hay filtro, devuelve todo
                    resultados.append((fila[0], fila[1], fila[3], fila[4], fila[5]))
            
            # Ordenar por fecha descendente (la más reciente primero)
            return sorted(resultados, key=lambda x: x[0], reverse=True)
            
        except Exception as e:
            print(f"Error leyendo sheet: {e}")
            return []

    def borrar_historial(self, usuario_filtro=None):
        """
        Borrar en Sheets es delicado.
        Estrategia: Leer todo, filtrar lo que NO se borra, y reescribir.
        """
        if not self.sheet: self._conectar_drive()
        
        try:
            todos_datos = self.sheet.get_all_values()
            cabecera = todos_datos[0] # Guardamos encabezados
            datos = todos_datos[1:]   # Datos reales
            
            # Lista de filas que SOBREVIVEN (Las que NO son de este usuario)
            filas_nuevas = [cabecera]
            
            if usuario_filtro:
                for fila in datos:
                    if len(fila) > 2:
                        inspector_row = fila[2]
                        # Si NO es el usuario, se queda. Si ES el usuario, no se añade (se borra).
                        if inspector_row.strip().lower() != usuario_filtro.strip().lower():
                            filas_nuevas.append(fila)
            else:
                # Si no hay usuario filtro, borramos todo (solo dejamos cabecera)
                pass 
            
            # Limpiamos la hoja y escribimos de nuevo
            self.sheet.clear()
            self.sheet.update(filas_nuevas) # Escribe todo de golpe
            
        except Exception as e:
            print(f"Error borrando sheet: {e}")

# --- 2. CEREBRO PRINCIPAL (IA) ---
class InspectorIndustrial:
    def __init__(self):
        # AQUÍ ESTÁ EL CAMBIO CLAVE: Usamos el nuevo GestorDatos de Sheets
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
    
    def obtener_historial(self, usuario=None): 
        return self.db.leer_historial(usuario)
    
    def borrar_memoria(self, usuario=None): 
        self.db.borrar_historial(usuario)

    def _encontrar_modelo_disponible(self):
        try:
            lista = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # Prioridad 1: Flash (Rápido y barato)
            for m in lista:
                if 'flash' in m and '1.5' in m: return m
            # Prioridad 2: Pro Vision
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
        
        Tarea: Auditoría visual basada en las {len(imagenes_pil)} imágenes proporcionadas.
        Genera REPORTE TÉCNICO ESTRUCTURADO:
        1. HALLAZGOS VISUALES (Descripción técnica de lo observado).
        2. ANÁLISIS NORMATIVO {datos_ins['norma']} (Cumplimiento/Incumplimiento detallado).
        3. CAUSA RAÍZ PROBABLE (Diagnóstico experto).
        4. RECOMENDACIÓN EJECUTIVA (Acciones correctivas inmediatas).
        Tono: Profesional, directo, sin introducciones genéricas.
        """
        try:
            model = genai.GenerativeModel(modelo)
            contenido = [prompt] + imagenes_pil
            response = model.generate_content(contenido)
            text = response.text
            
            # Guardamos en la NUBE
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
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # PORTADA / ENCABEZADO
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'DICTAMEN TÉCNICO DE INSPECCIÓN', 0, 1, 'C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f"Proyecto: {datos['proyecto']} | Norma: {datos['norma']}", 0, 1, 'C')
        pdf.cell(0, 6, f"Inspector: {datos['usuario']} | Fecha: {datetime.datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'C')
        pdf.ln(10)
        
        # CUERPO DEL INFORME
        pdf.set_fill_color(50, 50, 50) 
        pdf.set_text_color(255, 255, 255) 
        pdf.cell(0, 8, " RESULTADOS DEL ANÁLISIS VIG.IA", 1, 1, 'L', 1)
        pdf.set_text_color(0, 0, 0) 
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 11)
        # Limpieza de caracteres Markdown básicos para PDF
        texto_limpio = texto_ia.replace('**', '').replace('##', '').replace('•', '-')
        texto_limpio = texto_limpio.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, texto_limpio)
        
        # ANEXO FOTOGRÁFICO
        if lista_rutas_imagenes:
            pdf.add_page()
            pdf.set_fill_color(255, 111, 0) # Naranja Industrial
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
                    pdf.cell(0, 10, f"Figura {i+1}: Evidencia de inspección.", 0, 1, 'L')
                    try:
                        # Ajustamos tamaño de imagen para que quepa bien
                        pdf.image(ruta, x=35, y=y_pos+8, w=140, h=105)
                    except: pass
                    y_pos += 120

        return pdf.output(dest='S').encode('latin-1')

class PDFReport(FPDF):
    def header(self):
        # Si tienes logo.png, lo usa. Si no, no pasa nada.
        if os.path.exists("logo.png"): self.image("logo.png", 10, 8, 25)
        self.set_font('Arial', 'B', 12)
        self.cell(30)
        self.cell(0, 10, 'VIG.IA - SISTEMA DE INTELIGENCIA INDUSTRIAL', 0, 0, 'L')
        self.set_draw_color(255, 111, 0)
        self.set_line_width(1)
        self.line(10, 28, 200, 28)
        self.ln(25)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Reporte Generado por VIG.IA Cloud | Página {self.page_no()}', 0, 0, 'C')
