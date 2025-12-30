import streamlit as st
import pandas as pd
import gpxpy
import folium
from streamlit_folium import st_folium
import os

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(
    page_title="Pavías Senderismo", 
    page_icon="⛰️", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para que parezca más "App"
st.markdown("""
<style>
    .big-font { font-size:20px !important; }
    div.stButton > button:first-child {
        background-color: #4CAF50;
        color: white;
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
    }
    .reportview-container { background: #f0f2f6 }
</style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES (MOTOR) ---
def obtener_listado_rutas(carpeta="rutas"):
    if not os.path.exists(carpeta):
        return []
    archivos = os.listdir(carpeta)
    rutas_encontradas = []
    for archivo in archivos:
        if archivo.lower().endswith(".gpx"):
            nombre_bonito = archivo.replace(".gpx", "").replace("_", " ").title()
            rutas_encontradas.append({
                "nombre": nombre_bonito,
                "path": os.path.join(carpeta, archivo),
                "archivo_real": archivo
            })
    return rutas_encontradas

def cargar_datos_gpx(ruta_archivo):
    try:
        gpx_file = open(ruta_archivo, 'r')
        gpx = gpxpy.parse(gpx_file)
        
        distancia_km = gpx.length_2d() / 1000
        datos_altura = gpx.get_uphill_downhill()
        desnivel_positivo = datos_altura.uphill
        
        datos_grafica = []
        puntos_mapa = []
        distancia_acumulada = 0
        prev_point = None
        
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    puntos_mapa.append([point.latitude, point.longitude])
                    if prev_point:
                        distancia_acumulada += point.distance_2d(prev_point)
                    datos_grafica.append({
                        "Distancia (km)": distancia_acumulada / 1000,
                        "Altitud (m)": point.elevation
                    })
                    prev_point = point
                    
        df = pd.DataFrame(datos_grafica)
        return df, puntos_mapa, distancia_km, desnivel_positivo, gpx.to_xml()
        
    except Exception as e:
        return None, None, 0, 0, None

# --- 3. INTERFAZ PRINCIPAL ---

# Cabecera con imagen (puedes poner una URL de una foto de Pavías real aquí)
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/Pav%C3%ADas._Castell%C3%B3n.jpg/1024px-Pav%C3%ADas._Castell%C3%B3n.jpg", use_column_width=True)
st.title("⛰️ Rutas de Pavías")
st.markdown("**Descubre la Sierra de Espadán.** Selecciona una ruta, explora el mapa y descarga el track para tu GPS.")

# --- BARRA LATERAL ---
st.sidebar.header("🧭 Explorador")
mis_rutas = obtener_listado_rutas("rutas")

if not mis_rutas:
    st.error("No se encontraron rutas. Sube archivos .gpx a la carpeta 'rutas'.")
else:
    nombres_rutas = [r["nombre"] for r in mis_rutas]
    seleccion = st.sidebar.selectbox("Elige tu aventura:", nombres_rutas)
    ruta_elegida = next(r for r in mis_rutas if r["nombre"] == seleccion)
    
    # Procesar datos
    df, puntos, dist, desnivel, xml_data = cargar_datos_gpx(ruta_elegida["path"])
    
    if df is not None and not df.empty:
        st.header(f"📍 {ruta_elegida['nombre']}")
        
        # --- SISTEMA DE PESTAÑAS (Ideal para móviles) ---
        tab1, tab2, tab3 = st.tabs(["📊 Datos y Descarga", "🗺️ Mapa Interactivo", "ℹ️ Info y Seguridad"])
        
        with tab1:
            # 1. TARJETAS DE DATOS
            col1, col2, col3 = st.columns(3)
            col1.metric("📏 Distancia", f"{dist:.2f} km")
            col1.metric("📈 Desnivel +", f"{int(desnivel)} m")
            
            # Lógica de dificultad visual
            if desnivel > 600 or dist > 15:
                dif_texto = "Difícil"
                dif_color = "red"
            elif desnivel > 300:
                dif_texto = "Media"
                dif_color = "orange"
            else:
                dif_texto = "Fácil"
                dif_color = "green"
            
            col3.markdown(f"**Dificultad**<br><span style='color:{dif_color}; font-size:24px; font-weight:bold'>{dif_texto}</span>", unsafe_allow_html=True)
            
            st.divider()
            
            # 2. BOTÓN DE DESCARGA (LO MÁS IMPORTANTE)
            st.subheader("📲 Llevate la ruta")
            st.write("Descarga el archivo GPX para usarlo en tu reloj GPS, Wikiloc o móvil.")
            
            st.download_button(
                label=f"⬇️ DESCARGAR GPX ({ruta_elegida['nombre']})",
                data=xml_data,
                file_name=ruta_elegida['archivo_real'],
                mime="application/gpx+xml"
            )

            st.divider()
            st.subheader("📉 Perfil de Altimetría")
            st.area_chart(df, x="Distancia (km)", y="Altitud (m)", color=["#4CAF50"])

        with tab2:
            st.write("Usa el botón de capas (arriba derecha del mapa) para ver satélite.")
            if puntos:
                mid_point = puntos[len(puntos)//2]
                
                # Usamos OpenTopoMap por defecto que es mejor para montaña
                m = folium.Map(location=mid_point, zoom_start=13, tiles="OpenTopoMap")
                
                # Añadimos capa de satélite opcional
                folium.TileLayer(
                    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                    attr='Esri',
                    name='Satélite',
                    overlay=False,
                    control=True
                ).add_to(m)

                # Línea de ruta
                folium.PolyLine(puntos, color="red", weight=4, opacity=0.8, tooltip=ruta_elegida['nombre']).add_to(m)
                
                # Iconos chulos
                folium.Marker(puntos[0], popup="Inicio", icon=folium.Icon(color="green", icon="play", prefix='fa')).add_to(m)
                folium.Marker(puntos[-1], popup="Fin", icon=folium.Icon(color="black", icon="flag", prefix='fa')).add_to(m)
                
                # Control de capas
                folium.LayerControl().add_to(m)
                
                st_folium(m, width=700, height=500)

        with tab3:
            st.info("ℹ️ Recuerda que estás en el Parque Natural de la Sierra de Espadán.")
            st.markdown("""
            **Consejos de seguridad:**
            - 💧 **Agua:** No hay muchas fuentes potables en las cimas. Lleva al menos 1.5L.
            - 📱 **Cobertura:** Puede fallar en los barrancos. **Descarga el GPX antes de salir.**
            - 🐗 **Fauna:** Respeta a los animales y no salgas de las sendas marcadas.
            - 🔥 **Fuego:** Totalmente prohibido hacer fuego.
            
            **Teléfonos de interés:**
            - Emergencias: 112
            - Ayuntamiento Pavías: [Añadir teléfono]
            """)

    else:
        st.warning("Error al leer el archivo. Comprueba que el GPX es válido.")
