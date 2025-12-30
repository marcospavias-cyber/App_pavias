import streamlit as st
import pandas as pd
import gpxpy
import folium
from streamlit_folium import st_folium
import os

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Rutas Pavías", page_icon="🌲", layout="centered")

# --- 2. FUNCIÓN PARA BUSCAR RUTAS (CON DIAGNÓSTICO) ---
def obtener_listado_rutas(carpeta="rutas"):
    """
    Busca archivos .gpx en la carpeta especificada.
    Si no encuentra la carpeta, avisa al usuario mostrando qué hay en el directorio.
    """
    rutas_encontradas = []
    
    # Verificamos si la carpeta existe
    if not os.path.exists(carpeta):
        st.error(f"❌ Error: No encuentro la carpeta llamada '{carpeta}'.")
        st.warning(f"📂 Lo que veo en el directorio principal es: {os.listdir('.')}")
        st.info("Pista: Asegúrate de que en GitHub la carpeta se llame exactamente 'rutas' (en minúsculas).")
        return []

    # Leemos los archivos dentro de la carpeta
    archivos = os.listdir(carpeta)
    
    # Filtramos solo los que terminan en .gpx
    for archivo in archivos:
        if archivo.lower().endswith(".gpx"):
            # Creamos un nombre bonito quitando .gpx y guiones bajos
            nombre_bonito = archivo.replace(".gpx", "").replace("_", " ").title()
            
            rutas_encontradas.append({
                "nombre": nombre_bonito,
                "path": os.path.join(carpeta, archivo),
                "archivo_real": archivo
            })
            
    return rutas_encontradas

# --- 3. FUNCIÓN PARA LEER EL GPX (MATEMÁTICAS) ---
def cargar_datos_gpx(ruta_archivo):
    """Lee el archivo GPX y extrae mapa y perfil de elevación."""
    try:
        gpx_file = open(ruta_archivo, 'r')
        gpx = gpxpy.parse(gpx_file)
        
        # Datos generales
        distancia_km = gpx.length_2d() / 1000
        datos_altura = gpx.get_uphill_downhill()
        desnivel_positivo = datos_altura.uphill
        
        # Extraer puntos para el mapa y la gráfica
        datos_grafica = []
        puntos_mapa = []
        distancia_acumulada = 0
        prev_point = None
        
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    # Guardamos coordenadas para el mapa (Latitud, Longitud)
                    puntos_mapa.append([point.latitude, point.longitude])
                    
                    # Calculamos distancia acumulada para la gráfica X
                    if prev_point:
                        distancia_acumulada += point.distance_2d(prev_point)
                    
                    # Guardamos datos para la gráfica
                    datos_grafica.append({
                        "Distancia (km)": distancia_acumulada / 1000,
                        "Altitud (m)": point.elevation
                    })
                    prev_point = point
                    
        df = pd.DataFrame(datos_grafica)
        return df, puntos_mapa, distancia_km, desnivel_positivo
        
    except Exception as e:
        st.error(f"Error leyendo el archivo {ruta_archivo}: {e}")
        return None, None, 0, 0

# --- 4. INTERFAZ DE USUARIO (LO QUE SE VE) ---
st.title("🌲 Senderismo en Pavías")
st.write("Descubre la Sierra de Espadán a través de sus sendas.")

# --- MENÚ LATERAL ---
st.sidebar.header("🎒 Tus Rutas")

# Llamamos a la función que busca los archivos
mis_rutas = obtener_listado_rutas("rutas")

if not mis_rutas:
    st.sidebar.warning("No hay rutas cargadas.")
    st.info("👆 Si ves el error de carpeta arriba, corrígelo en GitHub.")
else:
    # Selector de rutas
    nombres_rutas = [r["nombre"] for r in mis_rutas]
    seleccion = st.sidebar.selectbox("Elige una ruta:", nombres_rutas)
    
    # Encontramos la ruta seleccionada
    ruta_elegida = next(r for r in mis_rutas if r["nombre"] == seleccion)
    
    # --- MOSTRAR LA RUTA ---
    st.header(f"📍 {ruta_elegida['nombre']}")
    
    # Cargamos y procesamos el GPX
    df, puntos, dist, desnivel = cargar_datos_gpx(ruta_elegida["path"])
    
    if df is not None and not df.empty:
        # A. TARJETAS DE INFORMACIÓN
        c1, c2, c3 = st.columns(3)
        c1.metric("Distancia", f"{dist:.2f} km")
        c1.metric("Desnivel +", f"{int(desnivel)} m")
        
        # Cálculo automático de dificultad estimado
        if desnivel > 600 or dist > 15:
            dificultad = "Alta 🔴"
        elif desnivel > 300:
            dificultad = "Media 🟡"
        else:
            dificultad = "Baja 🟢"
        c3.metric("Dificultad", dificultad)
        
        # B. MAPA INTERACTIVO
        st.subheader("🗺️ Mapa del recorrido")
        if puntos:
            # Centramos el mapa en el punto medio de la ruta
            mid_point = puntos[len(puntos)//2]
            m = folium.Map(location=mid_point, zoom_start=13)
            
            # Dibujamos la línea roja
            folium.PolyLine(puntos, color="#FF4B4B", weight=4, opacity=0.8).add_to(m)
            
            # Marcadores Inicio (Verde) y Fin (Negro)
            folium.Marker(puntos[0], popup="Inicio", icon=folium.Icon(color="green", icon="play")).add_to(m)
            folium.Marker(puntos[-1], popup="Fin", icon=folium.Icon(color="black", icon="stop")).add_to(m)
            
            st_folium(m, width=700, height=500)
            
        # C. GRÁFICA DE ELEVACIÓN
        st.subheader("📈 Perfil de Altura")
        st.area_chart(df, x="Distancia (km)", y="Altitud (m)", color=["#FF4B4B"])
        
    else:
        st.warning("El archivo GPX parece estar vacío o dañado.")
