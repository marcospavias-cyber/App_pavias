import streamlit as st
import pandas as pd
import gpxpy
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import os

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Pavías Senderismo", 
    page_icon="⛰️", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# Estilos CSS para mejorar la apariencia (Botones y contenedores)
st.markdown("""
<style>
    /* Botón de descarga verde y grande */
    div.stButton > button:first-child {
        background-color: #2E8B57;
        color: white;
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 10px;
    }
    div.stButton > button:hover {
        background-color: #1E5E3A;
        color: white;
    }
    /* Ajustes generales */
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES DE LÓGICA Y DATOS ---

def obtener_listado_rutas(carpeta="rutas"):
    """Escanea la carpeta en busca de archivos .gpx"""
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
    """Procesa el GPX: extrae dataframe, puntos para mapa y XML para descarga"""
    try:
        gpx_file = open(ruta_archivo, 'r')
        gpx = gpxpy.parse(gpx_file)
        
        # Datos generales
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
        # Devolvemos también gpx.to_xml() para permitir la descarga del archivo
        return df, puntos_mapa, distancia_km, desnivel_positivo, gpx.to_xml()
        
    except Exception as e:
        return None, None, 0, 0, None

def crear_grafica_perfil(df):
    """Crea la gráfica interactiva PRO con Plotly"""
    if df is None or df.empty:
        return None
        
    # Buscar punto más alto para marcarlo
    punto_max = df.loc[df['Altitud (m)'].idxmax()]
    
    # Gráfica base de área
    fig = px.area(
        df, 
        x="Distancia (km)", 
        y="Altitud (m)",
        color_discrete_sequence=["#2E8B57"], # Color verde bosque
        labels={"Distancia (km)": "Km", "Altitud (m)": "Metros"}
    )
    
    # Añadir marcador de Cima
    fig.add_trace(go.Scatter(
        x=[punto_max['Distancia (km)']],
        y=[punto_max['Altitud (m)']],
        mode='markers+text',
        name='Cima',
        text=[f"🏁 Cima: {int(punto_max['Altitud (m)'])}m"],
        textposition="top center",
        marker=dict(color='#FF4B4B', size=12, symbol='circle', line=dict(color='white', width=2))
    ))
    
    # Diseño limpio y minimalista
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=30, b=0),
        height=300,
        showlegend=False,
        xaxis=dict(showgrid=False, showspikes=True, spikecolor="gray", spikethickness=1),
        yaxis=dict(showgrid=True, gridcolor="#eee")
    )
    
    # Relleno con opacidad
    fig.update_traces(fillcolor="rgba(46, 139, 87, 0.4)", line=dict(width=2))
    
    return fig

# --- 3. INTERFAZ VISUAL PRINCIPAL ---

# Portada
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/Pav%C3%ADas._Castell%C3%B3n.jpg/1024px-Pav%C3%ADas._Castell%C3%B3n.jpg", use_column_width=True)
st.title("⛰️ Rutas de Pavías")
st.markdown("**Sierra de Espadán, Castellón.**")

# --- MENÚ LATERAL ---
st.sidebar.header("🧭 Explorador de Rutas")
mis_rutas = obtener_listado_rutas("rutas")

if not mis_rutas:
    st.sidebar.error("⚠️ No se encuentran rutas.")
    st.sidebar.info("Sube archivos .gpx a la carpeta 'rutas' en GitHub.")
else:
    # Selector
    nombres_rutas = [r["nombre"] for r in mis_rutas]
    seleccion = st.sidebar.selectbox("Elige tu aventura:", nombres_rutas)
    
    # Buscar archivo seleccionado
    ruta_elegida = next(r for r in mis_rutas if r["nombre"] == seleccion)
    
    # Cargar datos
    df, puntos, dist, desnivel, xml_data = cargar_datos_gpx(ruta_elegida["path"])
    
    if df is not None:
        st.header(f"📍 {ruta_elegida['nombre']}")
        
        # --- PESTAÑAS DE CONTENIDO ---
        tab1, tab2, tab3 = st.tabs(["📊 Perfil y Datos", "🗺️ Mapa Interactivo", "ℹ️ Info Práctica"])
        
        # --- PESTAÑA 1: DATOS ---
        with tab1:
            # Métricas principales
            col1, col2, col3 = st.columns(3)
            col1.metric("📏 Distancia", f"{dist:.2f} km")
            col1.metric("⛰️ Desnivel +", f"{int(desnivel)} m")
            
            # Lógica de dificultad (Estimación simple)
            if desnivel > 600 or dist > 15:
                dif_txt, dif_color = "Difícil", "red"
            elif desnivel > 300:
                dif_txt, dif_color = "Media", "orange"
            else:
                dif_txt, dif_color = "Fácil", "green"
            
            col3.markdown(f"**Dificultad**<br><span style='color:{dif_color}; font-size:24px; font-weight:bold'>{dif_txt}</span>", unsafe_allow_html=True)
            
            st.divider()
            
            # Gráfica Interactiva
            st.subheader("📉 Perfil de Altimetría")
            fig = crear_grafica_perfil(df)
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            # Botón de descarga
            st.subheader("📲 Descargar Track")
            st.write("Lleva la ruta en tu dispositivo (reloj, móvil o GPS).")
            st.download_button(
                label=f"⬇️ DESCARGAR GPX",
                data=xml_data,
                file_name=ruta_elegida['archivo_real'],
                mime="application/gpx+xml"
            )

        # --- PESTAÑA 2: MAPA ---
        with tab2:
            st.info("💡 Usa el icono de capas (arriba-derecha) para ver vista Satélite.")
            
            if puntos:
                mid_point = puntos[len(puntos)//2]
                
                # Mapa Base: OpenTopoMap (Mejor para montaña)
                m = folium.Map(location=mid_point, zoom_start=13, tiles="OpenTopoMap")
                
                # Capa Satélite (Esri World Imagery)
                folium.TileLayer(
                    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                    attr='Esri',
                    name='Satélite',
                    overlay=False,
                    control=True
                ).add_to(m)

                # Trazado de la ruta
                folium.PolyLine(
                    puntos, 
                    color="#FF4B4B", # Rojo visible
                    weight=4, 
                    opacity=0.8,
                    tooltip=ruta_elegida['nombre']
                ).add_to(m)
                
                # Marcadores Inicio y Fin
                folium.Marker(puntos[0], popup="Inicio", icon=folium.Icon(color="green", icon="play", prefix='fa')).add_to(m)
                folium.Marker(puntos[-1], popup="Fin", icon=folium.Icon(color="black", icon="flag", prefix='fa')).add_to(m)
                
                # Control de capas
                folium.LayerControl().add_to(m)
                
                st_folium(m, width=700, height=500)

        # --- PESTAÑA 3: INFO ---
        with tab3:
            st.image("https://upload.wikimedia.org/wikipedia/commons/2/23/Sierra_de_Espad%C3%A1n.jpg", caption="Parque Natural Sierra de Espadán")
            st.markdown("""
            ### 🌲 Consejos para esta zona
            Estás en el corazón de la **Sierra de Espadán**.
            
            * **Agua:** Las fuentes pueden estar secas en verano. Lleva siempre agua extra.
            * **Cobertura:** Es irregular en los barrancos. **Descarga el GPX** en la primera pestaña antes de salir.
            * **Época:** Evita las horas centrales del día en verano. El otoño y la primavera son espectaculares por los alcornoques.
            * **Emergencias:** Llama al **112**.
            
            ---
            *Ayuntamiento de Pavías - Turismo*
            """)
            
    else:
        st.error("Error leyendo el archivo GPX. Verifica que no esté corrupto.")
