# 1) SIEMPRE PRIMERO
import streamlit as st
st.set_page_config(layout="wide", page_title="Observatorio de Licitaciones - Drill Down")

# 2) Imports
import pandas as pd
import numpy as np
import plotly.express as px
import json
import datetime
import base64
import math
import altair as alt

# 3) Estilos
st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        border: 1px solid #d6d6d6;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
    }
    #vg-tooltip-element {
        font-size: 16px !important;
        font-family: "Source Sans Pro", sans-serif !important;
        padding: 10px !important;
        opacity: 0.95 !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: #fff;
        border-radius: 5px; border: 1px solid #e0e0e0; font-weight: 600;
    }
    .stTabs [aria-selected="true"] { background-color: #ff4b4b !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 1. Cache utilidades
# -----------------------------
@st.cache_data(show_spinner=False)
def logo_base64(ruta_imagen: str) -> str:
    with open(ruta_imagen, "rb") as f:
        return base64.b64encode(f.read()).decode()

def agregar_logo_flotante(ruta_imagen):
    try:
        data64 = logo_base64(ruta_imagen)
        st.markdown(
            f"""
            <style>
                .logo-flotante {{
                    position: fixed;
                    top: 25px;         /* Distancia desde arriba */
                    right: 20px;       /* Distancia desde la derecha */
                    width: 150px;      /* Ajusta el tamaño aquí */
                    z-index: 999;      /* Asegura que quede encima de todo */
                    opacity: 0.9;
                }}
                /* En móviles se oculta para no estorbar */
                @media (max-width: 600px) {{
                    .logo-flotante {{ display: none; }}
                }}
            </style>
            <img src="data:image/png;base64,{data64}" class="logo-flotante">
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.warning(f"No se encontró la imagen: {ruta_imagen}")

agregar_logo_flotante("../logo1.jpg")

# -----------------------------
# 2. Carga y Limpieza de Datos
# -----------------------------
@st.cache_data(show_spinner=True)
def cargar_datos():
    D_detalle_postores = pd.read_csv('../data/processed/D_detalle_postores.csv', sep='|', dtype={'RUC': str,
                                                                                                'RUC_ind': str,
                                                                                                'proveedor_ind': str,
                                                                                                'registro': str,
                                                                                                'departamento': str,
                                                                                                'provincia': str,
                                                                                                'distrito': str,
                                                                                                'consorcio_flag': int})
    F_postores = pd.read_csv('../data/processed/F_postores.csv', sep='|', dtype={'ruc_proveedor': str,
                                                                                'codigo_convocatoria': object,
                                                                                'n_item': object,
                                                                                'ruc_codigo_postor': str,
                                                                                'postor': str,
                                                                                'ganador_flag': int})
    D_entidades = pd.read_csv('../data/processed/D_entidades.csv', sep='|', dtype={'ruc_proveedor': str,
                                                                                'codigo_convocatoria': object,
                                                                                'n_item': object,
                                                                                'ruc_codigo_postor': str,
                                                                                'postor': str,
                                                                                'ganador_flag': int})
    F_adjudicaciones = pd.read_csv('../data/processed/F_adjudicaciones.csv', sep='|', dtype={'codigoconvocatoria': str,
                                                                                            'n_item': object,
                                                                                            'codigoentidad': str,
                                                                                            'ruc_proveedor': str,
                                                                                            'objetocontractual': str,
                                                                                            'tipoprocesoseleccion': str,
                                                                                            'proceso': str,
                                                                                            'descripcion_proceso': str,
                                                                                            'unidad_medida': str,
                                                                                            'cantidad_adjudicado_item': float,
                                                                                            'estado_item': str,
                                                                                            'descripcion_item': str,
                                                                                            'fecha_convocatoria': object,
                                                                                            'fecha_buenapro': object,
                                                                                            'fecha_consentimiento_bp': object,
                                                                                            'monto_referencial_item_soles': float,
                                                                                            'monto_adjudicado_item_soles': float,
                                                                                            'departamento_item': str,
                                                                                            'provincia_item': str,
                                                                                            'distrito_item': str,
                                                                                            'codigoitem': object,
                                                                                            'itemcubso': str})
    D_cubso = pd.read_csv('../data/processed/D_cubso.csv', sep='|', dtype={'codigo_segmento': int,
                                                                        'segmento': str,
                                                                        'codigo_familia': int,
                                                                        'familia': str,
                                                                        'codigo_clase': int,
                                                                        'clase': str,
                                                                        'codigo_commodity': int,
                                                                        'commodity': str,
                                                                        'codigo_item': object,
                                                                        'item': str,
                                                                        'codigo_cubso': object})
    
    F_adjudicaciones['fecha_convocatoria'] = pd.to_datetime(F_adjudicaciones['fecha_convocatoria'], dayfirst=True, format="%d/%m/%Y")
    F_adjudicaciones['fecha_buenapro'] = pd.to_datetime(F_adjudicaciones['fecha_buenapro'], dayfirst=True, format="%d/%m/%Y")
    F_adjudicaciones['fecha_consentimiento_bp'] = pd.to_datetime(F_adjudicaciones['fecha_consentimiento_bp'], dayfirst=True, format="%d/%m/%Y")

    F_adjudicaciones = F_adjudicaciones[F_adjudicaciones['monto_referencial_item_soles']>0]
    F_adjudicaciones['ratio'] = F_adjudicaciones['monto_adjudicado_item_soles'] / F_adjudicaciones['monto_referencial_item_soles']

    # df_F_adjudicaciones = F_adjudicaciones[F_adjudicaciones['monto_adjudicado_item_soles']>F_adjudicaciones['monto_referencial_item_soles']]
    # df_F_postores = F_postores[F_postores['codigo_convocatoria'].isin(df_F_adjudicaciones['codigoconvocatoria'])]

    return F_adjudicaciones, F_postores, D_cubso, D_entidades, D_detalle_postores


    

df_F_adjudicaciones, df_F_postores, df_D_cubso, df_D_entidades, df_D_detalle_postores = cargar_datos()

# -----------------------------
# 3. Carga GeoJSONs (cache)
# -----------------------------
@st.cache_data(show_spinner=False)
def cargar_geojsons():
    try:
        with open('../data/external/peru_departamental_simple.geojson', 'r', encoding='utf-8') as f:
            geo_dept = json.load(f)
        with open('../data/external/peru_provincial_simple.geojson', 'r', encoding='utf-8') as f:
            geo_prov = json.load(f)
        with open('../data/external/peru_distrital_simple.geojson', 'r', encoding='utf-8') as f:
            geo_dist = json.load(f)
        return geo_dept, geo_prov, geo_dist
    except Exception as e:
        st.error(f"No se pudieron cargar los geojson: {e}")
        return None, None, None

geo_dept, geo_prov, geo_dist = cargar_geojsons()


# -----------------------------
# 4. Estado y utilidades
# -----------------------------
if 'selected_dept' not in st.session_state: st.session_state.selected_dept = None
if 'selected_prov' not in st.session_state: st.session_state.selected_prov = None
if 'selected_dist' not in st.session_state: st.session_state.selected_dist = None
if 'map_center' not in st.session_state: st.session_state.map_center = (-9.19, -75.0152)  # Centro de Perú
if 'map_zoom' not in st.session_state: st.session_state.map_zoom = 4
if 'selected_segmento' not in st.session_state: st.session_state.selected_segmento = None
if 'selected_familia' not in st.session_state: st.session_state.selected_familia = None
if 'selected_clase' not in st.session_state: st.session_state.selected_clase = None
if 'selected_commodity' not in st.session_state: st.session_state.selected_commodity = None
if 'metrica_segmento' not in st.session_state: st.session_state.metrica_segmento = []
if 'metrica_familia' not in st.session_state: st.session_state.metrica_familia = []
if 'metrica_clase' not in st.session_state: st.session_state.metrica_clase = []
if 'metrica_commodity' not in st.session_state: st.session_state.metrica_commodity = []

if 'rango_i' not in st.session_state or 'rango_f' not in st.session_state:
    # Inicializar rango con extremos del índice
    if df_F_adjudicaciones.shape[0] > 0:
        st.session_state.rango_i = df_F_adjudicaciones.fecha_convocatoria.min().date()
        st.session_state.rango_f = df_F_adjudicaciones.fecha_convocatoria.max().date()
    else:
        hoy = datetime.date.today()
        st.session_state.rango_i = hoy
        st.session_state.rango_f = hoy

def reset_national():
    st.session_state.selected_dept = None
    st.session_state.selected_prov = None
    st.session_state.selected_dist = None

def reset_dept():
    st.session_state.selected_prov = None
    st.session_state.selected_dist = None

def reset_dist():
    st.session_state.selected_dist = None   

# Filtrado rápido por fecha usando índice
def filtrar_por_fecha(df: pd.DataFrame, ini: datetime.date, fin: datetime.date) -> pd.DataFrame:
    if df.index.dtype == 'datetime64[ns]':
        return df.loc[pd.to_datetime(ini):pd.to_datetime(fin)]
    # fallback
    return df[(df['fecha_convocatoria'] >= pd.to_datetime(ini)) & (df['fecha_convocatoria'] <= pd.to_datetime(fin))]

# -----------------------------
# 5. Filtrado de Datos
# -----------------------------
ini, fin = st.session_state.rango_i, st.session_state.rango_f

# if isinstance(st.session_state.rango, list) and len(st.session_state.rango) == 2:
#     ini, fin = st.session_state.rango
#     raise ValueError("flg1")
# else:
#     ini = fin = st.session_state.rango  # caso de una sola fecha
#     raise ValueError(st.session_state.rango)

df_nacional = filtrar_por_fecha(df_F_adjudicaciones, ini, fin)

# Máscara geográfica
def aplicar_mascara_geo(df: pd.DataFrame):
    rep_geo = df
    if st.session_state.selected_dept:
        rep_geo = rep_geo.query("departamento_item == @st.session_state.selected_dept")
    if st.session_state.selected_prov:
        rep_geo = rep_geo.query("provincia_item == @st.session_state.selected_prov")
    return rep_geo

def aplicar_mascara_cat(df: pd.DataFrame):
    masc = df_D_cubso.copy()
    if st.session_state.metrica_segmento:
        masc = masc.query("segmento == @st.session_state.metrica_segmento")
    if st.session_state.metrica_familia:
        masc = masc.query("familia == @st.session_state.metrica_familia")
    if st.session_state.metrica_clase:
        masc = masc.query("clase == @st.session_state.metrica_clase")
    if st.session_state.metrica_commodity:
        masc = masc.query("commodity == @st.session_state.metrica_commodity")
    return df[df['codigoitem'].isin(masc['codigo_item'])]


# if df_filtrado_cat.empty:
#     st.warning("No hay datos para esta selección.")
#     st.stop()

# -----------------------------
# 7. Breadcrumbs y título
# -----------------------------

st.markdown("""
    <style>
    .titulo-box { background-color: #002B5B; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; }
    .titulo-box h1 { color: white !important; margin: 0; font-family: 'Source Sans Pro', sans-serif; }
    </style>
    <div class="titulo-box"><h1>Monitor de Sobreprecio</h1></div>
""", unsafe_allow_html=True)

# st.markdown("---")

# -----------------------------
# 8. KPIs + Rango de Fechas
# -----------------------------

df_nacional = filtrar_por_fecha(df_F_adjudicaciones, ini, fin)
df_filtrado_geo = aplicar_mascara_geo(df_nacional)
kpi1, kpi2, blanco, fechai, fechaf = st.columns([1, 1, 2, 1, 1])
with kpi1:
    st.metric("N° de Adjudicaciones", f"{len(df_filtrado_geo.drop_duplicates(['codigoconvocatoria','n_item'])):,.0f}")
with kpi2:
    st.metric("Ratio de precios adjudicado sobre referencial", f"{df_filtrado_geo.drop_duplicates(['codigoconvocatoria','n_item']).ratio.mean():,.2f}")
with fechai:
    # rango_fecha = st.date_input(
    #     "Rango de fechas:",
    #     value=st.session_state.rango,
    #     min_value=df_F_adjudicaciones.fecha_convocatoria.min().date(),
    #     max_value=df_F_adjudicaciones.fecha_convocatoria.max().date(),
    #     key="rango"
    # )
    rango_i = st.date_input(
        "Fecha de inicio:",
        value=df_F_adjudicaciones.fecha_convocatoria.min().date(),
        min_value=df_F_adjudicaciones.fecha_convocatoria.min().date(),
        max_value=df_F_adjudicaciones.fecha_convocatoria.max().date(),
        key="rango_i"
    )
with fechaf:
    rango_f = st.date_input(
        "Fecha de fin:",
        value=df_F_adjudicaciones.fecha_convocatoria.max().date(),
        min_value=df_F_adjudicaciones.fecha_convocatoria.min().date(),
        max_value=df_F_adjudicaciones.fecha_convocatoria.max().date(),
        key="rango_f"
    )
    # if st.button("Reiniciar fechas"): 
    #     st.session_state.rango_i = df_F_adjudicaciones.fecha_convocatoria.min().date()
    #     st.session_state.rango_f = df_F_adjudicaciones.fecha_convocatoria.max().date()
# -----------------------------
# 8. Mapa + Barras horizontales
# -----------------------------

# --- Geo utilidades cacheadas ---
def _iter_coords(geometry):
    gtype = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if gtype == "Polygon":
        for ring in coords:
            for lon, lat in ring: yield lon, lat
    elif gtype == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                for lon, lat in ring: yield lon, lat

def bounds_from_geojson(geojson):
    min_lon = min_lat = float("inf")
    max_lon = max_lat = float("-inf")
    for feat in geojson.get("features", []):
        for lon, lat in _iter_coords(feat.get("geometry", {})):
            min_lon = min(min_lon, lon); max_lon = max(max_lon, lon)
            min_lat = min(min_lat, lat); max_lat = max(max_lat, lat)
    return min_lon, min_lat, max_lon, max_lat

def center_from_bounds(bounds):
    min_lon, min_lat, max_lon, max_lat = bounds
    return (min_lat + max_lat) / 2.0, (min_lon + max_lon) / 2.0

def _lat_to_mercator_y(lat_deg):
    lat_rad = math.radians(lat_deg)
    return math.log(math.tan((math.pi / 4.0) + (lat_rad / 2.0)))

def zoom_from_bounds(bounds, map_width_px=800, map_height_px=450, padding_frac=0.08):
    min_lon, min_lat, max_lon, max_lat = bounds
    width_deg = max((max_lon - min_lon), 1e-6)
    height_deg = max((max_lat - min_lat), 1e-6)
    pad_w, pad_h = width_deg * padding_frac, height_deg * padding_frac
    min_lon_p, max_lon_p = min_lon - pad_w, max_lon + pad_w
    min_lat_p, max_lat_p = min_lat - pad_h, max_lat + pad_h
    width_deg_p = max_lon_p - min_lon_p
    height_deg_p = max_lat_p - min_lat_p
    z_lon = math.log2((360.0 * map_width_px) / (256.0 * width_deg_p))
    y_min = _lat_to_mercator_y(min_lat_p); y_max = _lat_to_mercator_y(max_lat_p)
    merc_span = max(y_max - y_min, 1e-9)
    z_lat = math.log2((2.0 * math.pi * map_height_px) / (merc_span * 256.0))
    z = max(2.0, min(16.0, min(z_lon, z_lat) * 0.8))
    return z

@st.cache_data(show_spinner=False)
def filtrar_geojson(geojson, nombre_objetivo, campo_nombre):
    features = geojson.get("features", [])
    filtered_features = [feat for feat in features if feat.get("properties", {}).get(campo_nombre) == nombre_objetivo]
    return {"type": "FeatureCollection", **({"crs": geojson.get("crs")} if geojson.get("crs") else {}), "features": filtered_features}

@st.cache_data(show_spinner=False)
def geo_context(selected_dept, selected_prov):
    # Devuelve geojson + featureidkey + nivel_actual + labels
    if selected_dept and selected_prov:
        gj = filtrar_geojson(geo_dist, selected_dept, 'NOMBDEP')
        gj = filtrar_geojson(gj, selected_prov, 'NOMBPROV')
        return gj, "properties.NOMBDIST", "distrito_item", "Distrito"
    elif selected_dept:
        # OJO: valida el campo que realmente existe en tu geo_prov
        gj = filtrar_geojson(geo_prov, selected_dept, 'FIRST_NOMB')  # si tu geo usa 'FIRST_NOMB', cámbialo aquí
        return gj, "properties.NOMBPROV", "provincia_item", "Provincia"
    else:
        return geo_dept, "properties.NOMBDEP", "departamento_item", "Departamento"
geo_data, feat_key, nivel_actual, loc_col = geo_context(st.session_state.selected_dept, st.session_state.selected_prov)

@st.cache_data(show_spinner=False)
def cubso_context(df, nivel_cubso):
    # if st.session_state.selected_segmento and st.session_state.selected_familia and st.session_state.selected_clase:
    #     df = df.query("segmento == @st.session_state.selected_segmento and familia == @st.session_state.selected_familia and clase == @st.session_state.selected_clase")
    #     return df
    # if st.session_state.selected_segmento and st.session_state.selected_familia:
    #     df = df.query("segmento == @st.session_state.selected_segmento and familia == @st.session_state.selected_familia")
    #     return df
    # if st.session_state.selected_segmento:
    #     df = df.query("segmento == @st.session_state.selected_segmento")
    #     return df
    df_join = df.set_index('codigoitem').join(df_D_cubso.set_index('codigo_item'), how='left').reset_index()
    df_agrupado_cubso = (df_join.groupby(nivel_cubso, observed=True)
                .agg(prom_ratio=('ratio', 'mean'))
                .astype({
                    'prom_ratio': 'float32'
                })  
                .reset_index())
    return df_agrupado_cubso

@st.cache_data(show_spinner=False)
def crear_ranking_nacional(nivel_tipo, color_scale, ascending, top_n=10, mantener=False):
    dataframe = df_nacional.copy()
    
    # A. DEFINIR AGREGACIONES DINÁMICAMENTE
    # Empezamos con las métricas base
    agg_config = {
        'cuenta': ('generico', 'count')
    }

    # Si estamos en Provincia, agregamos el Departamento (tomamos el primero que aparezca)
    if nivel_tipo == 'especifico':
        agg_config['generico'] = ('generico', 'first')

    # B. AGRUPAR (Usando el diccionario dinámico)
    dataframe['especifico'] = dataframe['especifico'].str.capitalize()
    dataframe['generico'] = dataframe['generico'].str.capitalize()
    
    df_agg = dataframe.groupby(nivel_tipo).agg(**agg_config).reset_index()

    # 4. Ordenar y Top N
    df_sorted = df_agg.sort_values('cuenta', ascending=ascending).head(top_n)

    # 5. DEFINIR TOOLTIPS DINÁMICAMENTE
    # Tooltips base
    lista_tooltips = [
        alt.Tooltip("cuenta", format=",", title="Total por Nivel")
    ]

    # Añadir contexto geográfico extra al tooltip si existe en el dataframe
    if "generico" in df_sorted.columns and nivel_tipo != "generico":
        lista_tooltips.insert(1, alt.Tooltip("generico", title="Generico"))
    if "especifico" in df_sorted.columns and nivel_tipo != "especifico":
        lista_tooltips.insert(1, alt.Tooltip("especifico", title="Especifico"))

    # 6. Gráfico
    chart = alt.Chart(df_sorted).mark_bar().encode(
        x=alt.X('cuenta', title=""),
        y=alt.Y(nivel_tipo, sort=None, title="", axis=alt.Axis(labelLimit=1000)), 
        color=alt.Color('cuenta', scale=alt.Scale(scheme=color_scale), legend=None),
        tooltip=lista_tooltips # <--- la lista dinámica
        
    ).properties(title="Ranking Categorías Genéricas" 
                        if nivel_tipo == 'generico' 
                        else f"Ranking Categorías Específicas ({metrica_generico[0]})" 
                        if (len(metrica_generico)>0 and mantener)
                        else "Ranking Categorías Específicas")
    
    return chart

bounds_full = bounds_from_geojson(geo_data)
c_lat, c_lon = center_from_bounds(bounds_full)
z = zoom_from_bounds(bounds_full, map_width_px=500, map_height_px=450, padding_frac=0.08)
st.session_state.map_center = (c_lat, c_lon)
st.session_state.map_zoom = z

df_agrupado_mapa = (df_filtrado_geo.groupby(nivel_actual, observed=True)
                  .agg(prom_ratio=('ratio', 'mean'))
                    .astype({
                        'prom_ratio': 'float32'
                    })  
                  .reset_index())

df_agrupado_ag_dist = df_agrupado_mapa
if st.session_state.selected_dist is not None:
    df_agrupado_ag_dist = (df_filtrado_geo[df_filtrado_geo['distrito_item']==st.session_state.selected_dist].groupby(nivel_actual, observed=True)
                            .agg(prom_ratio=('ratio', 'mean')
                                )
                                .astype({
                                    'prom_ratio': 'float32'
                                })  
                            .reset_index())

# nivel_cubso = 'segmento'
# N = 10

col_mapa, col_barra = st.columns([1, 1])

with col_mapa:
    c1, c2, c3 = st.columns([1, 1, 4])
    with c1:
        if st.session_state.selected_dept:
            st.button("🏠 Inicio (Nacional)", on_click=reset_national, use_container_width=True)
    with c2:
        if st.session_state.selected_prov:
            st.button("⬅ Volver a Depto", on_click=reset_dept, use_container_width=True)
    with c3:
        ruta = "Perú"
        if st.session_state.selected_dept: ruta += f"  ▸  {st.session_state.selected_dept}"
        if st.session_state.selected_prov: ruta += f"  ▸  {st.session_state.selected_prov}"
        st.markdown(f"### 📍 Ubicación: {ruta}")

    st.markdown(f"### 🌍 Mapa de Ratio de Precios Adjudicado sobre Referencial")
    
     # Mapa coroplético
    # df_agrupado_mapa = df_F_adjudicaciones.groupby(nivel_actual).agg(prom_ratio=('ratio', 'mean'))
    # df_agrupado_mapa['Ratio de precios'] = df_agrupado_mapa.prom_ratio
    # df_agrupado_mapa = df_agrupado_mapa.reset_index()

    fig_map = px.choropleth_mapbox(
        df_agrupado_mapa, geojson=geo_data, locations=nivel_actual,
        featureidkey=feat_key, color=('prom_ratio'),
        color_continuous_scale='Reds',
        mapbox_style="carto-positron",
        zoom=st.session_state.map_zoom,
        center={"lat": st.session_state.map_center[0], "lon": st.session_state.map_center[1]},
        opacity=0.7,
        labels={nivel_actual: loc_col, 'prom_ratio': 'Ratio de precios'}
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    evento = st.plotly_chart(fig_map, on_select="rerun", use_container_width=True, key='mapa')

    seleccion = None
    rerun_dist = False

    if evento:
        if "selection" in evento and evento["selection"]["points"]:
            punto = evento["selection"]["points"][0]
            seleccion = punto.get("location")
            if seleccion:
                if st.session_state.selected_dept is None:
                    st.session_state.selected_dept = seleccion
                    st.rerun()
                elif st.session_state.selected_prov is None:
                    st.session_state.selected_prov = seleccion
                    st.rerun()
                elif st.session_state.selected_dist is None:
                    st.session_state.selected_dist = seleccion
                    st.rerun()
                elif (st.session_state.selected_dist != seleccion) & (st.session_state.selected_dist is not None):
                    st.session_state.selected_dist = seleccion
                    st.rerun()
                elif len(evento["selection"]["points"])==0:
                    st.session_state.selected_dist = None
                    st.rerun()
with col_barra:
    Cubso_char, N_char = st.columns([1, 1])
    with Cubso_char:
        nivel_cubso = st.selectbox(
            "Selecciona un nivel:",
            options=[
                'segmento',
                'familia',
                'clase',
                'commodity'
            ],
            index=0,
            key="valor_cubso",  # clave en session_state
            format_func=lambda x: x.capitalize(),
        )
    with N_char:
        filtro_cant = st.number_input(
            "Registros a mostrar:",
            min_value=0,
            max_value=100,
            value=10,
            step=1,
            key="filtro_n_form"
        )
    
    st.markdown(f"### 📊 Top {filtro_cant} por {nivel_cubso.capitalize()} (Ratio de precios adjudicado sobre referencial)")

    df_agrupado_cubso = cubso_context(df_filtrado_geo, nivel_cubso)
    df_sorted = df_agrupado_cubso.sort_values('prom_ratio', ascending=False).head(filtro_cant)

    chart = alt.Chart(df_sorted.head(filtro_cant)).mark_bar().encode(
        x=alt.X('prom_ratio', title=""),
        y=alt.Y(nivel_cubso, sort=None, title="", axis=alt.Axis(labelLimit=1000)), 
        color=alt.Color('prom_ratio', scale=alt.Scale(scheme='reds'), legend=None),
        # tooltip=lista_tooltips # <--- la lista dinámica
        
    )
    st.altair_chart(chart, use_container_width=True)


segmento, familia, clase, commododity = st.columns([1,1,1,1])

with segmento:
    st.markdown("### 📋 Segmento")
    metrica_generico = st.multiselect(
        "Selecciona  uno o varios segmentos:",
        options=(
            df_D_cubso['segmento'].dropna().drop_duplicates().to_list()
        ),
        key="metrica_segmento",  # clave en session_state
    )
with familia:
    # Construye dinámicamente las opciones de 'familia' según 'segmento'
    if st.session_state.get("metrica_segmento"):
        opciones_familia = (
            df_D_cubso[df_D_cubso['segmento'].isin(st.session_state["metrica_segmento"])]
            ['familia'].dropna().drop_duplicates().to_list()
        )
    else:
        opciones_familia = [] 
    # seleccion_filtrada = [x for x in seleccion_prev if x in opciones_familia]
    st.markdown(f"### 🔍 Familia específica")
    metrica_familia = st.multiselect(
        f"Selecciona categorías específicas:",
        options=opciones_familia,
        # default=seleccion_filtrada,
        key="metrica_familia",
        disabled=(len(opciones_familia) == 0)
    )
with clase:
    # Construye dinámicamente las opciones de 'clase' según 'familia'
    if st.session_state.get("metrica_familia"):
        opciones_clase = (
            df_D_cubso[df_D_cubso['familia'].isin(st.session_state["metrica_familia"])]
            ['clase'].dropna().drop_duplicates().to_list()
        )
    else:
        opciones_clase = [] 
    # seleccion_filtrada = [x for x in seleccion_prev if x in opciones_clase]
    st.markdown(f"### 🔍 Clase específica")
    metrica_clase = st.multiselect(
        f"Selecciona clases específicas:",
        options=opciones_clase,
        # default=seleccion_filtrada,
        key="metrica_clase",
        disabled=(len(opciones_clase) == 0)
    )
with commododity:
    # Construye dinámicamente las opciones de 'commodity' según 'clase'
    if st.session_state.get("metrica_clase"):
        opciones_commodity = (
            df_D_cubso[df_D_cubso['clase'].isin(st.session_state["metrica_clase"])]
            ['commodity'].dropna().drop_duplicates().to_list()
        )
    else:
        opciones_commodity = [] 
    # seleccion_filtrada = [x for x in seleccion_prev if x in opciones_commodity]
    st.markdown(f"### 🔍 Commodity específico")
    metrica_commodity = st.multiselect(
        f"Selecciona commodities específicos:",
        options=opciones_commodity,
        # default=seleccion_filtrada,
        key="metrica_commodity",
        disabled=(len(opciones_commodity) == 0)
    )

df_agrupado_kpi1 = df_F_postores.groupby(['codigo_convocatoria', 'n_item']).agg(cuenta=('ruc_codigo_postor', 'count'))
df_join_kpi2 = df_F_postores.set_index('ruc_codigo_postor').join(df_D_detalle_postores.set_index('RUC'), how='left').reset_index(drop=False)

df_join_kpi2.consorcio_flag = df_join_kpi2.consorcio_flag.fillna(0)
df_join_dd_kpi23 = df_join_kpi2.drop_duplicates(['ruc_proveedor'])

df_F_adjudicaciones_tiempo_kpi4 = df_filtrado_geo.copy()
df_F_adjudicaciones_tiempo_kpi4['Tiempo'] = df_F_adjudicaciones_tiempo_kpi4['fecha_buenapro'] - df_F_adjudicaciones_tiempo_kpi4['fecha_convocatoria']

ruc = '20108983583' # RUC de ejemplo, cambiar por el que se quiera analizar
df_F_postores_kpi5 = df_F_postores.copy()
df_F_postores_kpi5['key'] = df_F_postores_kpi5['codigo_convocatoria'].astype(str) + '-' + df_F_postores_kpi5['n_item'].astype(str)
df_F_adjudicaciones_kpi_5 = df_F_adjudicaciones.copy()
df_F_adjudicaciones_kpi_5['key'] = df_F_adjudicaciones_kpi_5['codigoconvocatoria'].astype(str) + '-' + df_F_adjudicaciones_kpi_5['n_item'].astype(str)
df_join_kpi5 = df_F_adjudicaciones_kpi_5.set_index('key').join(df_F_postores_kpi5.set_index('key'), how='left', lsuffix='_adj').reset_index(drop=False)
df_join_g_kpi5 = df_join_kpi5[df_join_kpi5['ruc_codigo_postor']==ruc] # Cambiar el filtro por el filtro de un ruc
df_join_ng_kpi5 = df_join_kpi5[df_join_kpi5['ruc_codigo_postor']!=ruc] # Cambiar el filtro por el filtro de un ruc
pxc, cxp, cxa, tpbp = st.columns([1, 1, 1, 1])
with pxc:
    st.markdown("### 📈 Precio por CUBSO")
    st.metric('kpi 1 | Cantidad promedio de postores por convocatoria:',df_agrupado_kpi1['cuenta'].mean())
    
with cxp:
    st.markdown("### 📈 Precio por CUBSO")
    st.metric('kpi 2 | cantidad de consorcios por postores concursantes:', df_join_dd_kpi23.consorcio_flag.mean())

with cxa:
    st.markdown("### 📈 Precio por CUBSO")
    st.metric('kpi 3 | cantidad de consorcios por adjudicados:', df_join_dd_kpi23[df_join_dd_kpi23['ganador_flag']==1].consorcio_flag.mean())
with tpbp:
    st.markdown("### 📈 Precio por CUBSO")
    st.metric('kpi 4 | promedio de días de adjudicación:', df_F_adjudicaciones_tiempo_kpi4.Tiempo.mean())

popr, popref, cec, rex = st.columns([1, 1, 1, 1]) 
with popr:
    st.markdown("### 📈 Precio por CUBSO")
    st.metric('kpi 5 | promedio de oferta propia contra otros', df_agrupado.diferencia_otros.mean())
    
with popref:
    st.markdown("### 📈 Precio por CUBSO")
    st.metric('kpi 6 | cantidad de consorcios por postores concursantes:', df_join_dd.consorcio_flag.mean())
with cec:
    st.markdown("### 📈 Precio por CUBSO")
    st.metric('kpi 7 | cuenta de postores coincidentes:',len(df_F_postores_agg[df_F_postores_agg['cuenta']/df_F_postores_agg['cuenta'].max()>umbral])-1,'(con umbral',f'{umbral})')
with rex:
    st.markdown("### 📈 Precio por CUBSO")
    st.metric('kpi 8 | ratio de éxito:', df_F_postores_seleccionado.ganador_flag.mean())