import streamlit as st
import pandas as pd
import gpxpy
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import os
import streamlit.components.v1 as components # NUEVO: Para el widget del tiempo

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Pavías Senderismo", 
    page_icon="⛰️", 
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    div.stButton > button:first-child {
        background-color: #2E8B57;
        color: white;
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 10px;
    }
    /* Estilo para el botón de Google Maps (Azul) */
    .google-btn {
        background-color: #4285F4 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES ---

@st.cache_data # NUEVO: ESTO HACE QUE LA APP VUELE (CACHÉ)
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

@st.cache_data # NUEVO: MEMORIA DE DATOS
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
        
        # Guardamos el primer punto para Google Maps
        inicio_lat = None
        inicio_lon = None
        
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if inicio_lat is None: # Guardamos el primero
                        inicio_lat = point.latitude
                        inicio_lon = point.longitude
                        
                    puntos_mapa.append([point.latitude, point.longitude])
                    if prev_point:
                        distancia_acumulada += point.distance_2d(prev_point)
                    datos_grafica.append({
                        "Distancia (km)": distancia_acumulada / 1000,
                        "Altitud (m)": point.elevation
                    })
                    prev_point = point
                    
        df = pd.DataFrame(datos_grafica)
        # Devolvemos también las coordenadas de inicio
        return df, puntos_mapa, distancia_km, desnivel_positivo, gpx.to_xml(), inicio_lat, inicio_lon
        
    except Exception as e:
        return None, None, 0, 0, None, None, None

def crear_grafica_perfil(df):
    if df is None or df.empty: return None
    punto_max = df.loc[df['Altitud (m)'].idxmax()]
    
    fig = px.area(df, x="Distancia (km)", y="Altitud (m)", color_discrete_sequence=["#2E8B57"],
        labels={"Distancia (km)": "Km", "Altitud (m)": "Metros"})
    
    fig.add_trace(go.Scatter(x=[punto_max['Distancia (km)']], y=[punto_max['Altitud (m)']],
        mode='markers+text', name='Cima', text=[f"🏁 Cima: {int(punto_max['Altitud (m)'])}m"],
        textposition="top center", marker=dict(color='#FF4B4B', size=12, symbol='circle', line=dict(color='white', width=2))))
    
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0), height=300, showlegend=False,
        xaxis=dict(showgrid=False, showspikes=True), yaxis=dict(showgrid=True, gridcolor="#eee"))
    fig.update_traces(fillcolor="rgba(46, 139, 87, 0.4)", line=dict(width=2))
    return fig

# --- 3. INTERFAZ ---

st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/Pav%C3%ADas._Castell%C3%B3n.jpg/1024px-Pav%C3%ADas._Castell%C3%B3n.jpg", use_column_width=True)
st.title("⛰️ Rutas de Pavías")

# --- NUEVO: WIDGET DEL TIEMPO (Meteoblue para Pavías) ---
with st.expander("🌦️ Ver Previsión del Tiempo en Pavías"):
    # Insertamos un iframe de Meteoblue gratuito
    components.iframe("https://www.meteoblue.com/en/weather/widget/three/pav%c3%adas_spain_2512450?geoloc=fixed&nocurrent=0&noforecast=0&days=4&tempunit=CELSIUS&windunit=KILOMETER_PER_HOUR&layout=bright", height=230)

# --- MENÚ ---
st.sidebar.header("🧭 Explorador")
mis_rutas = obtener_listado_rutas("rutas")

if not mis_rutas:
    st.sidebar.error("⚠️ No hay rutas en la carpeta.")
else:
    nombres_rutas = [r["nombre"] for r in mis_rutas]
    seleccion = st.sidebar.selectbox("Elige tu aventura:", nombres_rutas)
    ruta_elegida = next(r for r in mis_rutas if r["nombre"] == seleccion)
    
    # Cargamos (Ahora con Coordenadas de inicio)
    df, puntos, dist, desnivel, xml_data, lat_inicio, lon_inicio = cargar_datos_gpx(ruta_elegida["path"])
    
    if df is not None:
        st.header(f"📍 {ruta_elegida['nombre']}")
        
        tab1, tab2, tab3 = st.tabs(["📊 Datos y GPS", "🗺️ Mapa", "ℹ️ Info"])
        
        with tab1:
            col1, col2, col3 = st.columns(3)
            col1.metric("📏 Distancia", f"{dist:.2f} km")
            col1.metric("⛰️ Desnivel +", f"{int(desnivel)} m")
            
            if desnivel > 600 or dist > 15: dif_txt, dif_color = "Difícil", "red"
            elif desnivel > 300: dif_txt, dif_color = "Media", "orange"
            else: dif_txt, dif_color = "Fácil", "green"
            col3.markdown(f"**Dificultad**<br><span style='color:{dif_color}; font-size:24px; font-weight:bold'>{dif_txt}</span>", unsafe_allow_html=True)
            
            st.divider()
            
            # --- NUEVO: BOTÓN GOOGLE MAPS ---
            if lat_inicio and lon_inicio:
                url_maps = f"https://www.google.com/maps/dir/?api=1&destination={lat_inicio},{lon_inicio}"
                st.link_button("🚗 CÓMO LLEGAR AL INICIO (Google Maps)", url_maps, type="secondary")
            
            st.write("---") # Separador
            
            st.subheader("📲 Descargar Track")
            st.download_button(label=f"⬇️ DESCARGAR GPX", data=xml_data, file_name=ruta_elegida['archivo_real'], mime="application/gpx+xml")

            st.subheader("📉 Perfil")
            st.plotly_chart(crear_grafica_perfil(df), use_container_width=True)

        with tab2:
            st.info("💡 Usa el icono de capas para Satélite.")
            if puntos:
                mid = puntos[len(puntos)//2]
                m = folium.Map(location=mid, zoom_start=13, tiles="OpenTopoMap")
                folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satélite').add_to(m)
                
                folium.PolyLine(puntos, color="#FF4B4B", weight=4, opacity=0.8).add_to(m)
                folium.Marker(puntos[0], popup="Inicio", icon=folium.Icon(color="green", icon="play", prefix='fa')).add_to(m)
                folium.Marker(puntos[-1], popup="Fin", icon=folium.Icon(color="black", icon="flag", prefix='fa')).add_to(m)
                
                folium.LayerControl().add_to(m)
                st_folium(m, width=700, height=500)

        with tab3:
            st.markdown("""
            ### 🌲 Sierra de Espadán
            * **Agua:** Lleva al menos 1.5L.
            * **Cobertura:** Limitada. Descarga el track antes.
            * **Emergencias:** 112.
            """)
