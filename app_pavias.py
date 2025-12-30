import streamlit as st
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Rutas Pavías", page_icon="🌲", layout="centered")

st.title("🌲 Senderismo en Pavías")
st.write("Explora las rutas con trazado interactivo.")

# 2. MENÚ LATERAL
st.sidebar.header("Elige tu aventura")
opcion = st.sidebar.radio(
    "Rutas disponibles:",
    ["Inicio", "Ruta 1: La Cueva", "Ruta 2: El Pico"]
)

# 3. FUNCIÓN PARA DIBUJAR EL MAPA BASE
def crear_mapa_base(coordenadas_centro):
    # Creamos un mapa centrado en Pavías
    m = folium.Map(location=coordenadas_centro, zoom_start=15)
    return m

# 4. LÓGICA DE LAS PÁGINAS
if opcion == "Inicio":
    st.header("Bienvenido a Pavías")
    st.info("Selecciona una ruta en el menú de la izquierda para ver su trazado en el mapa.")
    
    # Mapa simple solo con el marcador del pueblo
    m = crear_mapa_base([39.9755, -0.5105]) # Coordenadas aprox de Pavías
    folium.Marker(
        [39.9755, -0.5105], 
        popup="Pavías", 
        tooltip="Inicio"
    ).add_to(m)
    
    st_folium(m, width=700, height=400)

elif opcion == "Ruta 1: La Cueva":
    st.header("📍 Ruta 1: La Cueva")
    st.write("Esta ruta es suave y perfecta para pasear.")

    # --- DATOS DE LA LÍNEA (Coordenadas Latitud, Longitud) ---
    # En el futuro, esto lo leeremos de un archivo GPX real.
    # Ahora simulamos una línea que sale del pueblo hacia el norte.
    ruta_cueva = [
        [39.9755, -0.5105], # Plaza del pueblo
        [39.9760, -0.5100],
        [39.9770, -0.5095],
        [39.9785, -0.5090], # Punto intermedio
        [39.9800, -0.5085],
        [39.9810, -0.5100], # Curva
        [39.9820, -0.5120], # Llegada a la cueva (ficticia)
    ]

    # Crear mapa
    m = crear_mapa_base([39.9755, -0.5105])
    
    # DIBUJAR LA LÍNEA (PolyLine)
    folium.PolyLine(
        locations=ruta_cueva, 
        color="blue",       # Color de la línea
        weight=5,           # Grosor
        opacity=0.8
    ).add_to(m)

    # Añadir marcadores de Inicio y Fin
    folium.Marker(ruta_cueva[0], popup="Salida", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(ruta_cueva[-1], popup="La Cueva", icon=folium.Icon(color="red")).add_to(m)

    # Mostrar mapa
    st_folium(m, width=700, height=500)

elif opcion == "Ruta 2: El Pico":
    st.header("📍 Ruta 2: El Pico")
    st.write("Ruta con más pendiente hacia la montaña.")

    # Simulamos otra línea hacia el oeste
    ruta_pico = [
        [39.9755, -0.5105],
        [39.9750, -0.5120],
        [39.9745, -0.5140],
        [39.9730, -0.5160],
        [39.9720, -0.5180], # Subiendo
        [39.9700, -0.5200], # Cima
    ]

    m = crear_mapa_base([39.9755, -0.5105])
    
    # Dibujar línea roja
    folium.PolyLine(locations=ruta_pico, color="red", weight=5).add_to(m)
    
    folium.Marker(ruta_pico[-1], popup="Cima", icon=folium.Icon(color="red", icon="flag")).add_to(m)

    st_folium(m, width=700, height=500)