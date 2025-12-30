import streamlit as st
import pandas as pd
import gpxpy
import folium
from streamlit_folium import st_folium
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Senderismo Pavías", page_icon="🌲", layout="centered")

# --- 1. FUNCIÓN PARA ESCANEAR LA CARPETA ---
def obtener_listado_rutas(carpeta="rutas"):
    """Busca archivos .gpx en la carpeta y devuelve una lista limpia."""
    rutas_encontradas = []
    
    # Verificamos si la carpeta existe
    if not os.path.exists(carpeta):
        os.makedirs(carpeta) # La crea si no existe para evitar errores
        return []

    # Leemos los archivos
    archivos = os.listdir(carpeta)
    
    for archivo in archivos:
        if archivo.endswith(".gpx"):
            # Limpiamos el nombre para que se vea bonito en el menú
            # Ejemplo: "ruta_cueva.gpx" -> "Ruta Cueva"
            nombre_bonito = archivo.replace(".gpx", "").replace("_", " ").title()
            
            rutas_encontradas.append({
                "nombre": nombre_bonito,
                "path": os.path.join(carpeta, archivo)
            })
            
    return rutas_encontradas

# --- 2. FUNCIÓN DE PROCESAMIENTO (Igual que antes) ---
def cargar_datos_gpx(ruta_archivo):
    try:
        gpx_file = open(ruta_archivo, 'r')
        gpx = gpxpy.parse(gpx_file)
        
        distancia = gpx.length_2d() / 1000
        subida = gpx.get_uphill_downhill().uphill
        
        puntos_mapa = []
        datos_grafica = []
        dist_acumulada = 0
        prev_point = None
        
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    puntos_mapa.append([point.latitude, point.longitude])
                    
                    if prev_point:
                        dist_acumulada += point.distance_2d(prev_point)
                    
                    datos_grafica.append({
                        "Distancia": dist_acumulada / 1000, # En km
                        "Altitud": point.elevation
                    })
                    prev_point = point
                    
        df = pd.DataFrame(datos_grafica)
        return df, puntos_mapa, distancia, subida
    except Exception as e:
        st.error(f"Error leyendo el archivo: {e}")
        return None, None, 0, 0

# --- 3. INTERFAZ VISUAL ---
st.title("🌲 Senderismo en Pavías")
st.write("Explora las rutas de la Sierra de Espadán.")

# --- MENÚ AUTOMÁTICO ---
st.sidebar.header("Rutas Disponibles")

mis_rutas = obtener_listado_rutas()

if not mis_rutas:
    st.warning("⚠️ No he encontrado rutas. Sube archivos .gpx a la carpeta 'rutas'.")
else:
    # Creamos un selector con los nombres bonitos
    nombres_rutas = [r["nombre"] for r in mis_rutas]
    seleccion = st.sidebar.selectbox("Selecciona una ruta:", nombres_rutas)
    
    # Buscamos el archivo correspondiente a la selección
    ruta_elegida = next(r for r in mis_rutas if r["nombre"] == seleccion)
    
    # --- MOSTRAR LA RUTA ---
    st.header(f"📍 {ruta_elegida['nombre']}")
    
    # Cargamos datos
    df, puntos, dist, desnivel = cargar_datos_gpx(ruta_elegida["path"])
    
    if df is not None:
        # Métricas
        c1, c2, c3 = st.columns(3)
        c1.metric("Distancia", f"{dist:.2f} km")
        c1.metric("Desnivel +", f"{int(desnivel)} m")
        
        # Cálculo automático de dificultad (Simple)
        # Si tiene más de 600m de desnivel o más de 15km, la marcamos difícil
        if desnivel > 600 or dist > 15:
            dificultad = "Alta 🔴"
        elif desnivel > 300 or dist > 8:
            dificultad = "Media 🟡"
        else:
            dificultad = "Baja 🟢"
        c3.metric("Dificultad Est.", dificultad)

        # Mapa
        if puntos:
            m = folium.Map(location=puntos[0], zoom_start=13)
            folium.PolyLine(puntos, color="#FF4B4B", weight=4).add_to(m)
            folium.Marker(puntos[0], popup="Inicio", icon=folium.Icon(color="green", icon="play")).add_to(m)
            folium.Marker(puntos[-1], popup="Fin", icon=folium.Icon(color="black", icon="stop")).add_to(m)
            st_folium(m, width=700, height=500)
            
        # Gráfica
        st.subheader("Perifl de Elevación")
        st.area_chart(df, x="Distancia", y="Altitud")
