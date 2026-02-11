# =============================================================================
# DASHBOARD OPTIMIZADO - OBSERVATORIO DE LICITACIONES
# =============================================================================

import streamlit as st
st.set_page_config(layout="wide", page_title="Observatorio de Licitaciones - Drill Down")

import pandas as pd
import numpy as np
import plotly.express as px
import json
import datetime
import base64
import math
import altair as alt

# =============================================================================
# ESTILOS CSS
# =============================================================================
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
        height: 50px;
        white-space: pre-wrap;
        background-color: #fff;
        border-radius: 5px;
        border: 1px solid #e0e0e0;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    .logo-flotante {
        position: fixed;
        top: 25px;
        right: 20px;
        width: 150px;
        z-index: 999;
        opacity: 0.9;
    }
    @media (max-width: 600px) {
        .logo-flotante { display: none; }
    }
    .titulo-box {
        background-color: #002B5B;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    .titulo-box h1 {
        color: white !important;
        margin: 0;
        font-family: 'Source Sans Pro', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

@st.cache_data(show_spinner=False)
def logo_base64(ruta_imagen: str) -> str:
    """Convierte imagen a base64 para mostrar en HTML"""
    try:
        with open(ruta_imagen, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

def agregar_logo_flotante(ruta_imagen):
    """Agrega logo flotante en esquina superior derecha"""
    data64 = logo_base64(ruta_imagen)
    if data64:
        st.markdown(
            f'<img src="data:image/png;base64,{data64}" class="logo-flotante">',
            unsafe_allow_html=True
        )

agregar_logo_flotante("../logo1.jpg")

# =============================================================================
# CARGA DE DATOS
# =============================================================================

@st.cache_data(show_spinner=True)
def cargar_datos():
    """Carga y preprocesa todos los datasets necesarios"""
    
    # Definir dtypes comunes para optimizar memoria
    dtype_ruc = {'RUC': str, 'RUC_ind': str, 'ruc_proveedor': str, 'ruc_codigo_postor': str}
    dtype_codigo = {'codigo_convocatoria': object, 'codigoconvocatoria': str, 'n_item': object}
    
    # Cargar datasets
    D_detalle_postores = pd.read_csv(
        '../data/processed/D_detalle_postores.csv',
        sep='|',
        dtype={**dtype_ruc, 'proveedor_ind': str, 'registro': str,
               'departamento': str, 'provincia': str, 'distrito': str,
               'consorcio_flag': int}
    )

    D_detalle_postores = D_detalle_postores.drop(columns=['registro']).drop_duplicates()
    
    F_postores = pd.read_csv(
        '../data/processed/F_postores.csv',
        sep='|',
        dtype={**dtype_ruc, **dtype_codigo, 'postor': str, 'ganador_flag': int}
    )
    
    D_entidades = pd.read_csv(
        '../data/processed/D_entidades.csv',
        sep='|',
        dtype={**dtype_ruc, **dtype_codigo, 'postor': str, 'ganador_flag': int}
    )
    
    F_adjudicaciones = pd.read_csv(
        '../data/processed/F_adjudicaciones.csv',
        sep='|',
        dtype={
            **dtype_codigo,
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
            'monto_referencial_item_soles': float,
            'monto_adjudicado_item_soles': float,
            'departamento_item': str,
            'provincia_item': str,
            'distrito_item': str,
            'codigoitem': object,
            'itemcubso': str
        }
    )
    
    D_cubso = pd.read_csv(
        '../data/processed/D_cubso.csv',
        sep='|',
        dtype={
            'codigo_segmento': int,
            'segmento': str,
            'codigo_familia': int,
            'familia': str,
            'codigo_clase': int,
            'clase': str,
            'codigo_commodity': int,
            'commodity': str,
            'codigo_item': object,
            'item': str,
            'codigo_cubso': object
        }
    )
    
    # Convertir fechas
    date_cols = ['fecha_convocatoria', 'fecha_buenapro', 'fecha_consentimiento_bp']
    for col in date_cols:
        F_adjudicaciones[col] = pd.to_datetime(
            F_adjudicaciones[col],
            dayfirst=True,
            format="%d/%m/%Y"
        )
    
    # Filtrar y calcular ratio
    F_adjudicaciones = F_adjudicaciones[F_adjudicaciones['monto_referencial_item_soles'] > 0]
    F_adjudicaciones['ratio'] = (
        F_adjudicaciones['monto_adjudicado_item_soles'] / 
        F_adjudicaciones['monto_referencial_item_soles']
    )
    
    return F_adjudicaciones, F_postores, D_cubso, D_entidades, D_detalle_postores

df_F_adjudicaciones_raw, df_F_postores, df_D_cubso, df_D_entidades, df_D_detalle_postores = cargar_datos()

# =============================================================================
# CARGA DE GEOJSONS
# =============================================================================

@st.cache_data(show_spinner=False)
def cargar_geojsons():
    """Carga archivos GeoJSON para mapas"""
    try:
        geo_files = {
            'dept': '../data/external/peru_departamental_simple.geojson',
            'prov': '../data/external/peru_provincial_simple.geojson',
            'dist': '../data/external/peru_distrital_simple.geojson'
        }
        
        geos = {}
        for key, path in geo_files.items():
            with open(path, 'r', encoding='utf-8') as f:
                geos[key] = json.load(f)
        
        return geos['dept'], geos['prov'], geos['dist']
    except Exception as e:
        st.error(f"Error cargando GeoJSONs: {e}")
        return None, None, None

geo_dept, geo_prov, geo_dist = cargar_geojsons()

# =============================================================================
# INICIALIZACIÓN DE SESSION STATE
# =============================================================================

def init_session_state():
    """Inicializa todas las variables de session_state"""
    defaults = {
        # Navegación geográfica
        'selected_dept': None,
        'selected_prov': None,
        'selected_dist': None,
        'map_center': (-9.19, -75.0152),
        'map_zoom': 4,
        
        # Filtros de métricas geográficas
        'metrica_departamento': [],
        'metrica_provincia': [],
        'metrica_distrito': [],
        
        # Navegación CUBSO
        'selected_segmento': None,
        'selected_familia': None,
        'selected_clase': None,
        'selected_commodity': None,

        # Filtro de outliers
        'filtrar_outliers': False,
        'ratio_maximo': 10.0,
        
        # Filtros de métricas CUBSO
        'metrica_segmento': [],
        'metrica_familia': [],
        'metrica_clase': [],
        'metrica_commodity': [],
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Inicializar rangos de fecha
    if 'rango_i' not in st.session_state or 'rango_f' not in st.session_state:
        if df_F_adjudicaciones_raw.shape[0] > 0:
            st.session_state.rango_i = df_F_adjudicaciones_raw.fecha_convocatoria.min().date()
            st.session_state.rango_f = df_F_adjudicaciones_raw.fecha_convocatoria.max().date()
        else:
            hoy = datetime.date.today()
            st.session_state.rango_i = hoy
            st.session_state.rango_f = hoy

init_session_state()

# =============================================================================
# FUNCIONES DE RESETEO
# =============================================================================

def reset_national():
    """Resetea selección geográfica a nivel nacional"""
    st.session_state.selected_dept = None
    st.session_state.selected_prov = None
    st.session_state.selected_dist = None

def reset_dept():
    """Resetea selección a nivel departamental"""
    st.session_state.selected_prov = None
    st.session_state.selected_dist = None

# =============================================================================
# FUNCIONES DE FILTRADO
# =============================================================================

def filtrar_por_fecha(df: pd.DataFrame, ini: datetime.date, fin: datetime.date) -> pd.DataFrame:
    """Filtra dataframe por rango de fechas"""
    return df[
        (df['fecha_convocatoria'] >= pd.to_datetime(ini)) & 
        (df['fecha_convocatoria'] <= pd.to_datetime(fin))
    ]

def aplicar_mascara_geo(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica filtros geográficos de navegación (mapa)"""
    result = df.copy()
    if st.session_state.selected_dept:
        result = result[result['departamento_item'] == st.session_state.selected_dept]
    if st.session_state.selected_prov:
        result = result[result['provincia_item'] == st.session_state.selected_prov]
    return result

def aplicar_mascara_geo_detalle(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica filtros geográficos de métricas (multiselect)"""
    result = df.copy()
    if st.session_state.metrica_departamento:
        result = result[result['departamento_item'].isin(st.session_state.metrica_departamento)]
    if st.session_state.metrica_provincia:
        result = result[result['provincia_item'].isin(st.session_state.metrica_provincia)]
    if st.session_state.metrica_distrito:
        result = result[result['distrito_item'].isin(st.session_state.metrica_distrito)]
    return result

def aplicar_mascara_cat(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica filtros de categorías CUBSO"""
    masc = df_D_cubso.copy()
    
    if st.session_state.metrica_segmento:
        masc = masc[masc['segmento'].isin(st.session_state.metrica_segmento)]
    if st.session_state.metrica_familia:
        masc = masc[masc['familia'].isin(st.session_state.metrica_familia)]
    if st.session_state.metrica_clase:
        masc = masc[masc['clase'].isin(st.session_state.metrica_clase)]
    if st.session_state.metrica_commodity:
        masc = masc[masc['commodity'].isin(st.session_state.metrica_commodity)]
    
    return df[df['codigoitem'].isin(masc['codigo_item'])]

# =============================================================================
# FUNCIONES DE GEOMETRÍA Y MAPAS
# =============================================================================

def _iter_coords(geometry):
    """Itera sobre coordenadas de una geometría GeoJSON"""
    gtype = geometry.get("type")
    coords = geometry.get("coordinates", [])
    
    if gtype == "Polygon":
        for ring in coords:
            for lon, lat in ring:
                yield lon, lat
    elif gtype == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                for lon, lat in ring:
                    yield lon, lat

def bounds_from_geojson(geojson):
    """Calcula los límites (bounds) de un GeoJSON"""
    min_lon = min_lat = float("inf")
    max_lon = max_lat = float("-inf")
    
    for feat in geojson.get("features", []):
        for lon, lat in _iter_coords(feat.get("geometry", {})):
            min_lon = min(min_lon, lon)
            max_lon = max(max_lon, lon)
            min_lat = min(min_lat, lat)
            max_lat = max(max_lat, lat)
    
    return min_lon, min_lat, max_lon, max_lat

def center_from_bounds(bounds):
    """Calcula el centro a partir de bounds"""
    min_lon, min_lat, max_lon, max_lat = bounds
    return (min_lat + max_lat) / 2.0, (min_lon + max_lon) / 2.0

def _lat_to_mercator_y(lat_deg):
    """Convierte latitud a coordenada Y de Mercator"""
    lat_rad = math.radians(lat_deg)
    return math.log(math.tan((math.pi / 4.0) + (lat_rad / 2.0)))

def zoom_from_bounds(bounds, map_width_px=800, map_height_px=450, padding_frac=0.08):
    """Calcula nivel de zoom óptimo para bounds dados"""
    min_lon, min_lat, max_lon, max_lat = bounds
    
    width_deg = max((max_lon - min_lon), 1e-6)
    height_deg = max((max_lat - min_lat), 1e-6)
    
    pad_w, pad_h = width_deg * padding_frac, height_deg * padding_frac
    min_lon_p, max_lon_p = min_lon - pad_w, max_lon + pad_w
    min_lat_p, max_lat_p = min_lat - pad_h, max_lat + pad_h
    
    width_deg_p = max_lon_p - min_lon_p
    height_deg_p = max_lat_p - min_lat_p
    
    z_lon = math.log2((360.0 * map_width_px) / (256.0 * width_deg_p))
    
    y_min = _lat_to_mercator_y(min_lat_p)
    y_max = _lat_to_mercator_y(max_lat_p)
    merc_span = max(y_max - y_min, 1e-9)
    z_lat = math.log2((2.0 * math.pi * map_height_px) / (merc_span * 256.0))
    
    return max(2.0, min(16.0, min(z_lon, z_lat) * 0.8))

@st.cache_data(show_spinner=False)
def filtrar_geojson(geojson, nombre_objetivo, campo_nombre):
    """Filtra features de un GeoJSON por nombre"""
    features = geojson.get("features", [])
    filtered = [
        feat for feat in features 
        if feat.get("properties", {}).get(campo_nombre) == nombre_objetivo
    ]
    return {
        "type": "FeatureCollection",
        **({"crs": geojson.get("crs")} if geojson.get("crs") else {}),
        "features": filtered
    }

@st.cache_data(show_spinner=False)
def geo_context(selected_dept, selected_prov):
    """Determina contexto geográfico para el mapa"""
    if selected_dept and selected_prov:
        gj = filtrar_geojson(geo_dist, selected_dept, 'NOMBDEP')
        gj = filtrar_geojson(gj, selected_prov, 'NOMBPROV')
        return gj, "properties.NOMBDIST", "distrito_item", "Distrito"
    elif selected_dept:
        gj = filtrar_geojson(geo_prov, selected_dept, 'FIRST_NOMB')
        return gj, "properties.NOMBPROV", "provincia_item", "Provincia"
    else:
        return geo_dept, "properties.NOMBDEP", "departamento_item", "Departamento"

@st.cache_data(show_spinner=False)
def cubso_context(df, nivel_cubso):
    """Agrupa datos por nivel CUBSO seleccionado"""
    df_join = df.set_index('codigoitem').join(
        df_D_cubso.set_index('codigo_item'),
        how='left'
    ).reset_index()
    
    return (df_join.groupby(nivel_cubso, observed=True)
            .agg(prom_ratio=('ratio', 'mean'),
                 codigoitem=('codigoitem', 'first'))
            .astype({'prom_ratio': 'float32', 'codigoitem': 'object'})
            .reset_index())

# =============================================================================
# INTERFAZ DE USUARIO - HEADER
# =============================================================================

st.markdown(
    '<div class="titulo-box"><h1>Monitor de Sobreprecio</h1></div>',
    unsafe_allow_html=True
)

# =============================================================================
# FILTRADO PRINCIPAL
# =============================================================================

ini, fin = st.session_state.rango_i, st.session_state.rango_f
if st.session_state.filtrar_outliers:
    df_F_adjudicaciones = df_F_adjudicaciones_raw[df_F_adjudicaciones_raw['ratio'] < st.session_state.ratio_maximo]
else:
    df_F_adjudicaciones = df_F_adjudicaciones_raw.copy()
df_nacional = filtrar_por_fecha(df_F_adjudicaciones, ini, fin)
df_filtrado_geo = aplicar_mascara_geo(df_nacional)

# =============================================================================
# KPIs, SELECTOR DE FECHAS y Filtro de outliers
# =============================================================================

kpi1, kpi2, blanco, fechai, fechaf, outliers, ratio_outliers = st.columns([1, 1, 2, 1, 1, 1, 1])

with kpi1:
    n_adj = len(df_filtrado_geo.drop_duplicates(['codigoconvocatoria', 'n_item']))
    st.metric("N° de Adjudicaciones", f"{n_adj:,.0f}")

with kpi2:
    ratio_prom = df_filtrado_geo.drop_duplicates(['codigoconvocatoria', 'n_item']).ratio.mean()
    st.metric("Ratio de precios adj/ref", f"{ratio_prom:,.2f}")

with fechai:
    st.date_input(
        "Fecha de inicio:",
        value=df_F_adjudicaciones.fecha_convocatoria.min().date(),
        min_value=df_F_adjudicaciones.fecha_convocatoria.min().date(),
        max_value=df_F_adjudicaciones.fecha_convocatoria.max().date(),
        key="rango_i"
    )

with fechaf:
    st.date_input(
        "Fecha de fin:",
        value=df_F_adjudicaciones.fecha_convocatoria.max().date(),
        min_value=df_F_adjudicaciones.fecha_convocatoria.min().date(),
        max_value=df_F_adjudicaciones.fecha_convocatoria.max().date(),
        key="rango_f"
    )
with outliers:
    filtrar_outliers = st.checkbox("Excluir outliers", value=False, key="filtrar_outliers")
with ratio_outliers:
    if filtrar_outliers:
        ratio_maximo = st.number_input(f"Ratio máximo: {df_F_adjudicaciones_raw['ratio'].max():.1f}", value=10.0, min_value=0.0, step=0.1, format="%.1f", key="ratio_maximo")

# =============================================================================
# MAPA Y GRÁFICO DE BARRAS
# =============================================================================

geo_data, feat_key, nivel_actual, loc_col = geo_context(
    st.session_state.selected_dept,
    st.session_state.selected_prov
)

bounds_full = bounds_from_geojson(geo_data)
c_lat, c_lon = center_from_bounds(bounds_full)
z = zoom_from_bounds(bounds_full, map_width_px=500, map_height_px=450)
st.session_state.map_center = (c_lat, c_lon)
st.session_state.map_zoom = z

df_agrupado_mapa = (df_filtrado_geo.groupby(nivel_actual, observed=True)
                    .agg(prom_ratio=('ratio', 'mean'))
                    .astype({'prom_ratio': 'float32'})
                    .reset_index())

col_mapa, col_barra = st.columns([1, 1])

with col_mapa:
    c1, c2, c3 = st.columns([1, 1, 4])
    
    with c1:
        if st.session_state.selected_dept:
            st.button("🏠 Inicio", on_click=reset_national, use_container_width=True)
    
    with c2:
        if st.session_state.selected_prov:
            st.button("⬅ Volver", on_click=reset_dept, use_container_width=True)
    
    with c3:
        ruta = "Perú"
        if st.session_state.selected_dept:
            ruta += f"  ▸  {st.session_state.selected_dept}"
        if st.session_state.selected_prov:
            ruta += f"  ▸  {st.session_state.selected_prov}"
        st.markdown(f"### 📍 {ruta}")
    
    st.markdown(f"### 🌍 Mapa de Ratio de Precios")
    
    fig_map = px.choropleth_mapbox(
        df_agrupado_mapa,
        geojson=geo_data,
        locations=nivel_actual,
        featureidkey=feat_key,
        color='prom_ratio',
        color_continuous_scale='Reds',
        mapbox_style="carto-positron",
        zoom=st.session_state.map_zoom,
        center={"lat": st.session_state.map_center[0], "lon": st.session_state.map_center[1]},
        opacity=0.7,
        labels={nivel_actual: loc_col, 'prom_ratio': 'Ratio de precios'}
    )
    fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    
    evento = st.plotly_chart(fig_map, on_select="rerun", use_container_width=True, key='mapa')
    
    if evento and "selection" in evento and evento["selection"]["points"]:
        punto = evento["selection"]["points"][0]
        seleccion = punto.get("location")
        
        if seleccion:
            if st.session_state.selected_dept is None:
                st.session_state.selected_dept = seleccion
                st.rerun()
            elif st.session_state.selected_prov is None:
                st.session_state.selected_prov = seleccion
                st.rerun()
            elif st.session_state.selected_dist != seleccion:
                st.session_state.selected_dist = seleccion
                st.rerun()

with col_barra:
    Cubso_char, N_char = st.columns([1, 1])
    
    with Cubso_char:
        nivel_cubso = st.selectbox(
            "Nivel CUBSO:",
            options=['segmento', 'familia', 'clase', 'commodity'],
            index=0,
            key="valor_cubso",
            format_func=lambda x: x.capitalize()
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
    
    df_agrupado_cubso = cubso_context(df_filtrado_geo, nivel_cubso)
    df_agrupado_cubso = (df_agrupado_cubso.set_index('codigoitem')
                         .join(df_D_cubso.set_index('codigo_item'), how='left', rsuffix='_right')
                         .reset_index())
    df_sorted = df_agrupado_cubso.sort_values('prom_ratio', ascending=False).head(filtro_cant)
    
    # Configurar tooltips según nivel
    tooltips_map = {
        'segmento': [
            alt.Tooltip('segmento', title="Segmento"),
            alt.Tooltip('prom_ratio', format=".2f", title="Ratio promedio")
        ],
        'familia': [
            alt.Tooltip('segmento', title="Segmento"),
            alt.Tooltip('familia', title="Familia"),
            alt.Tooltip('prom_ratio', format=".2f", title="Ratio promedio")
        ],
        'clase': [
            alt.Tooltip('segmento', title="Segmento"),
            alt.Tooltip('familia', title="Familia"),
            alt.Tooltip('clase', title="Clase"),
            alt.Tooltip('prom_ratio', format=".2f", title="Ratio promedio")
        ],
        'commodity': [
            alt.Tooltip('segmento', title="Segmento"),
            alt.Tooltip('familia', title="Familia"),
            alt.Tooltip('clase', title="Clase"),
            alt.Tooltip('commodity', title="Commodity"),
            alt.Tooltip('prom_ratio', format=".2f", title="Ratio promedio")
        ]
    }
    
    st.markdown(f"### 📊 Top {filtro_cant} por {nivel_cubso.capitalize()}")
    
    chart = alt.Chart(df_sorted).mark_bar().encode(
        x=alt.X('prom_ratio', title=""),
        y=alt.Y(nivel_cubso, sort=None, title="", axis=alt.Axis(labelLimit=1000)),
        color=alt.Color('prom_ratio', scale=alt.Scale(scheme='reds'), legend=None),
        tooltip=tooltips_map[nivel_cubso]
    )
    st.altair_chart(chart, use_container_width=True)

# =============================================================================
# APLICAR FILTROS DETALLADOS
# =============================================================================

df_filtrado_geo_detalle = aplicar_mascara_geo_detalle(df_nacional)
df_filtrado_cat = aplicar_mascara_cat(df_filtrado_geo_detalle)
df_F_postores_cat = df_F_postores[
    df_F_postores['codigo_convocatoria'].isin(df_filtrado_cat['codigoconvocatoria'])
]

# =============================================================================
# FILTROS DE CATEGORÍAS (MULTISELECT)
# =============================================================================

segmento, familia, clase, commodity = st.columns(4)

with segmento:
    st.markdown("### 📋 Segmento")
    st.multiselect(
        "Selecciona segmento(s):",
        options=df_D_cubso['segmento'].dropna().drop_duplicates().to_list(),
        key="metrica_segmento"
    )

with familia:
    opciones_familia = []
    if st.session_state.get("metrica_segmento"):
        opciones_familia = (df_D_cubso[df_D_cubso['segmento'].isin(st.session_state["metrica_segmento"])]
                            ['familia'].dropna().drop_duplicates().to_list())
    
    st.markdown("### 📋 Familia")
    st.multiselect(
        "Selecciona familia(s):",
        options=opciones_familia,
        key="metrica_familia",
        disabled=(len(opciones_familia) == 0)
    )

with clase:
    opciones_clase = []
    if st.session_state.get("metrica_familia"):
        opciones_clase = (df_D_cubso[df_D_cubso['familia'].isin(st.session_state["metrica_familia"])]
                          ['clase'].dropna().drop_duplicates().to_list())
    
    st.markdown("### 📋 Clase")
    st.multiselect(
        "Selecciona clase(s):",
        options=opciones_clase,
        key="metrica_clase",
        disabled=(len(opciones_clase) == 0)
    )

with commodity:
    opciones_commodity = []
    if st.session_state.get("metrica_clase"):
        opciones_commodity = (df_D_cubso[df_D_cubso['clase'].isin(st.session_state["metrica_clase"])]
                              ['commodity'].dropna().drop_duplicates().to_list())
    
    st.markdown("### 📋 Commodity")
    st.multiselect(
        "Selecciona commodity(s):",
        options=opciones_commodity,
        key="metrica_commodity",
        disabled=(len(opciones_commodity) == 0)
    )

# =============================================================================
# FILTROS GEOGRÁFICOS (MULTISELECT)
# =============================================================================

departamento, provincia, distrito = st.columns(3)

with departamento:
    st.markdown("### 🌍 Departamento")
    st.multiselect(
        "Selecciona departamento(s):",
        options=df_F_adjudicaciones['departamento_item'].dropna().drop_duplicates().to_list(),
        key="metrica_departamento"
    )

with provincia:
    opciones_provincia = []
    if st.session_state.get("metrica_departamento"):
        opciones_provincia = (
            df_F_adjudicaciones[
                df_F_adjudicaciones['departamento_item'].isin(st.session_state["metrica_departamento"])
            ]['provincia_item'].dropna().drop_duplicates().to_list()
        )
    
    st.markdown("### 🌍 Provincia")
    st.multiselect(
        "Selecciona provincia(s):",
        options=opciones_provincia,
        key="metrica_provincia",
        disabled=(len(opciones_provincia) == 0)
    )

with distrito:
    opciones_distrito = []
    if st.session_state.get("metrica_provincia"):
        opciones_distrito = (
            df_F_adjudicaciones[
                (df_F_adjudicaciones['provincia_item'].isin(st.session_state["metrica_provincia"])) &
                (df_F_adjudicaciones['departamento_item'].isin(st.session_state["metrica_departamento"]))
            ]['distrito_item'].dropna().drop_duplicates().to_list()
        )
    
    st.markdown("### 🌍 Distrito")
    st.multiselect(
        "Selecciona distrito(s):",
        options=opciones_distrito,
        key="metrica_distrito",
        disabled=(len(opciones_distrito) == 0)
    )

# =============================================================================
# SERIE DE TIEMPO
# =============================================================================

df_agrupado_st = (df_filtrado_cat.groupby('fecha_convocatoria')
                  .agg(prom_ratio=('ratio', 'mean'))
                  .astype({'prom_ratio': 'float32'}))

ini_dt, fin_dt = df_agrupado_st.index.min(), df_agrupado_st.index.max()

fig = px.line(
    df_agrupado_st,
    x=df_agrupado_st.index,
    y='prom_ratio',
    labels={'prom_ratio': 'Ratio promedio', 'fecha_convocatoria': 'Fecha'}
)
fig.update_xaxes(
    range=[pd.to_datetime(ini_dt), pd.to_datetime(fin_dt)],
    rangeslider=dict(visible=True),
    rangeselector=dict(
        buttons=[
            dict(count=1, label="1m", step="month", stepmode="backward"),
            dict(count=3, label="3m", step="month", stepmode="backward"),
            dict(count=6, label="6m", step="month", stepmode="backward"),
            dict(count=1, label="1y", step="year", stepmode="backward"),
            dict(step="all")
        ]
    )
)
fig.update_layout(hovermode='x unified')
fig.update_traces(line=dict(color="#F17A19"))
st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# MÉTRICAS ADICIONALES
# =============================================================================

# Calcular KPIs
df_agrupado_kpi1 = (df_F_postores_cat.groupby(['codigo_convocatoria', 'n_item'])
                    .agg(cuenta=('ruc_codigo_postor', 'count')))

df_join_kpi2 = df_F_postores_cat.merge(
    df_D_detalle_postores[['RUC', 'consorcio_flag']].drop_duplicates(),
    left_on='ruc_codigo_postor',
    right_on='RUC',
    how='left'
)
df_join_kpi2['consorcio_flag'] = df_join_kpi2['consorcio_flag'].fillna(0)
df_join_dd_kpi23 = df_join_kpi2.drop_duplicates(['ruc_proveedor'])

df_F_adjudicaciones_tiempo_kpi4 = df_filtrado_cat.copy()
df_F_adjudicaciones_tiempo_kpi4['Tiempo'] = (
    df_F_adjudicaciones_tiempo_kpi4['fecha_buenapro'] - 
    df_F_adjudicaciones_tiempo_kpi4['fecha_convocatoria']
)

pxc, cxp, cxa, tpbp = st.columns(4)

with pxc:
    st.markdown("### 📈 Promedio postores/convocatoria")
    st.metric('', f"{df_agrupado_kpi1['cuenta'].mean():,.2f}")

with cxp:
    st.markdown("### 📈 Tasa consorcios concursantes")
    st.metric('', f"{df_join_dd_kpi23.consorcio_flag.mean():.2%}")

with cxa:
    st.markdown("### 📈 Tasa consorcios adjudicados")
    tasa_adj = df_join_dd_kpi23[df_join_dd_kpi23['ganador_flag'] == 1].consorcio_flag.mean()
    st.metric('', f"{tasa_adj:.2%}")

with tpbp:
    st.markdown("### 📈 Días promedio adjudicación")
    st.metric('', df_F_adjudicaciones_tiempo_kpi4.Tiempo.mean().days)

# =============================================================================
# RATIOS DE ÉXITO
# =============================================================================

df_F_postores_kpi5 = df_F_postores_cat[
    ['codigo_convocatoria', 'n_item', 'ruc_codigo_postor', 'ganador_flag', 'postor']
].copy()
df_F_postores_kpi5['key'] = (
    df_F_postores_kpi5['codigo_convocatoria'].astype(str) + '-' + 
    df_F_postores_kpi5['n_item'].astype(str)
)

df_F_adjudicaciones_kpi_5 = df_filtrado_cat.copy()
df_F_adjudicaciones_kpi_5['key'] = (
    df_F_adjudicaciones_kpi_5['codigoconvocatoria'].astype(str) + '-' + 
    df_F_adjudicaciones_kpi_5['n_item'].astype(str)
)

df_join_kpi5 = (df_F_adjudicaciones_kpi_5.set_index('key')
                .join(df_F_postores_kpi5.set_index('key'), how='left', lsuffix='_adj')
                .reset_index()
                .set_index('ruc_codigo_postor')
                .join(df_D_detalle_postores.set_index('RUC'), how='left')
                .reset_index(drop=False))

df_ratio_exito = (df_join_kpi5.groupby('proveedor_ind')
                  .agg(cuenta=('ganador_flag', 'mean'))
                  .reset_index()
                  .sort_values('cuenta', ascending=False))

filtro_cant_re = st.number_input(
    "Registros a mostrar:",
    min_value=0,
    max_value=100,
    value=10,
    step=1,
    key="filtro_n_form_re"
)

df_ratio_exito_top = df_ratio_exito.head(filtro_cant_re)

st.markdown(f"### 📈 Ratios de éxito del mercado (Top {filtro_cant_re})")
chart = alt.Chart(df_ratio_exito_top).mark_bar().encode(
    x=alt.X('cuenta', title="Ratio de éxito"),
    y=alt.Y('proveedor_ind', sort=None, title="RUC"),
    color=alt.Color('cuenta', scale=alt.Scale(scheme='reds'), legend=None),
    tooltip=[
        alt.Tooltip('cuenta', title="Ratio de éxito"),
        alt.Tooltip('proveedor_ind', title="Postor")
    ]
)
st.altair_chart(chart, use_container_width=True)

# =============================================================================
# ANÁLISIS DE COINCIDENCIAS
# =============================================================================

ruc_to_postor = (df_join_kpi5.groupby("RUC_ind")["proveedor_ind"]
                 .first()
                 .str.capitalize()
                 .to_dict())

ruc_coincidencia = st.selectbox(
    "Selecciona un postor para ver coincidencias:",
    options=list(ruc_to_postor.keys()),
    index=0,
    key="ruc_coincidencia",
    format_func=lambda x: str(ruc_to_postor.get(x, x))
)

df_join_g_kpi5 = df_join_kpi5[df_join_kpi5['RUC_ind'] == ruc_coincidencia]
df_join_ng_kpi5 = df_join_kpi5[df_join_kpi5['RUC_ind'] != ruc_coincidencia]
df_join_join_kpi5 = (df_join_g_kpi5.set_index('key')
                     .join(df_join_ng_kpi5.set_index('key'), lsuffix='_g', rsuffix='_ng')
                     .reset_index())

df_agrupado_kpi5 = df_join_join_kpi5.groupby('key').agg(
    monto_g=('monto_referencial_item_soles_g', 'mean'),
    monto_adj_g=('monto_adjudicado_item_soles_g', 'mean'),
    monto_adj_ng=('monto_adjudicado_item_soles_ng', 'mean')
)
df_agrupado_kpi5['diferencia_referencial'] = (
    df_agrupado_kpi5['monto_adj_g'] / df_agrupado_kpi5['monto_g']
)
df_agrupado_kpi5['diferencia_otros'] = (
    df_agrupado_kpi5['monto_adj_g'] / df_agrupado_kpi5['monto_adj_ng']
)

kpis, coincidentes = st.columns(2)

with kpis:
    st.markdown("### 📈 Oferta propia vs otros")
    st.metric('', f"{df_agrupado_kpi5.diferencia_otros.mean():.2f}")
    
    st.markdown("### 📈 Oferta propia vs referencial")
    st.metric('', f"{df_agrupado_kpi5.diferencia_referencial.mean():.2f}")

with coincidentes:
    postor_nombre = df_F_postores[
        df_F_postores['ruc_codigo_postor'] == ruc_coincidencia
    ].iloc[0, 4] if len(df_F_postores[df_F_postores['ruc_codigo_postor'] == ruc_coincidencia]) > 0 else "N/A"
    
    st.markdown(f"### 📈 Postores coincidentes con {postor_nombre} ({ruc_coincidencia})")
    
    df_F_postores_ci = df_join_kpi5[df_join_kpi5['key'].isin(df_join_g_kpi5['key'])]
    pt = (df_F_postores_ci.groupby(["proveedor_ind", "key"])
          .size()
          .unstack(fill_value=0))
    
    def highlight_nonzero(val):
        return 'background-color: lightgreen' if val != 0 else ''
    
    tabla_styled = pt.style.applymap(highlight_nonzero)
    st.dataframe(tabla_styled, use_container_width=True)

# =============================================================================
# TABLA DE DATOS DETALLADA
# =============================================================================

# Preparar columnas para el display final
df_display = df_join_join_kpi5.drop(
    columns=[
        'key', 'codigo_convocatoria_g', 'n_item_g', 'n_item_adj_ng',
        'monto_referencial_item_soles_ng', 'monto_adjudicado_item_soles_ng',
        'codigo_convocatoria_ng', 'n_item_ng', 'ratio_g', 'estado_item_g',
        'ruc_proveedor_g', 'codigoentidad_ng', 'objetocontractual_ng',
        'tipoprocesoseleccion_ng', 'proceso_ng', 'descripcion_proceso_ng',
        'unidad_medida_ng', 'cantidad_adjudicado_item_ng', 'estado_item_ng',
        'descripcion_item_ng', 'fecha_convocatoria_ng', 'fecha_buenapro_ng',
        'fecha_consentimiento_bp_ng', 'departamento_item_ng', 'provincia_item_ng',
        'distrito_item_ng', 'codigoitem_ng', 'itemcubso_ng', 'ratio_ng',
        'ruc_proveedor_ng', 'itemcubso_g', 'codigoconvocatoria_ng'
    ]
).rename(columns={
    'codigoconvocatoria_g': 'codigoconvocatoria',
    'n_item_adj_g': 'n_item',
    'codigoentidad_g': 'CODCONSUCODE',
    'objetocontractual_g': 'objetocontractual',
    'tipoprocesoseleccion_g': 'tipoprocesoseleccion',
    'proceso_g': 'proceso',
    'descripcion_proceso_g': 'descripcion_proceso',
    'unidad_medida_g': 'unidad_medida',
    'descripcion_item_g': 'descripcion_item',
    'fecha_convocatoria_g': 'fecha_convocatoria',
    'fecha_buenapro_g': 'fecha_buenapro',
    'fecha_consentimiento_bp_g': 'fecha_consentimiento_bp',
    'departamento_item_g': 'departamento_item',
    'provincia_item_g': 'provincia_item',
    'distrito_item_g': 'distrito_item',
    'codigoitem_g': 'codigoitem',
    'cantidad_adjudicado_item_g': 'cantidad_adjudicado_item',
    'monto_referencial_item_soles_g': 'monto_referencial_item_soles',
    'ruc_codigo_postor_g': 'ruc_codigo_postor_seleccionado',
    'postor_g': 'postor_seleccionado',
    'RUC_ind_g': 'RUC_ind_seleccionado',
    'proveedor_ind_g': 'proveedor_ind_seleccionado',
    'monto_adjudicado_item_soles_g': 'monto_postor_seleccionado',
    'ganador_flag_g': 'ganador_flag_seleccionado',
    'ruc_codigo_postor_ng': 'ruc_codigo_postor_no_seleccionado',
    'postor_ng': 'postor_no_seleccionado',
    'RUC_ind_ng': 'RUC_ind_no_seleccionado',
    'proveedor_ind_ng': 'proveedor_ind_no_seleccionado',
    'monto_adjudicado_item_soles_ng': 'monto_postor_no_seleccionado',
    'ganador_flag_ng': 'ganador_flag_no_seleccionado',
    'consorcio_flag_g': 'consorcio_flag_seleccionado',
    'consorcio_flag_ng': 'consorcio_flag_no_seleccionado'
})

df_display['CODCONSUCODE'] = df_display['CODCONSUCODE'].astype(int)

df_display = (df_display.set_index('CODCONSUCODE')
              .join(df_D_entidades.set_index('CODCONSUCODE').rename(columns={
                  'RUC': 'ruc_entidad',
                  'DEPARTAMENTO': 'departamento_entidad',
                  'PROVINCIA': 'provincia_entidad',
                  'DISTRITO': 'distrito_entidad'
              }), how='left', rsuffix='_entidad')
              .reset_index(drop=False)
              .set_index('codigoitem')
              .join(df_D_cubso.set_index('codigo_item'), how='left')
              .reset_index(drop=False))

df_display = df_display[[
    'codigoconvocatoria', 'n_item', 'objetocontractual', 'tipoprocesoseleccion',
    'proceso', 'descripcion_proceso', 'unidad_medida', 'cantidad_adjudicado_item',
    'descripcion_item', 'fecha_convocatoria', 'fecha_buenapro',
    'fecha_consentimiento_bp', 'departamento_item', 'provincia_item',
    'distrito_item', 'ruc_entidad', 'CODCONSUCODE', 'NOMBRE_DE_ENTIDAD',
    'departamento_entidad', 'provincia_entidad', 'distrito_entidad', 'tipoentidad',
    'codigo_segmento', 'segmento', 'codigo_familia', 'familia',
    'codigo_clase', 'clase', 'codigo_commodity', 'commodity', 'item',
    'codigo_cubso', 'codigoitem', 'monto_referencial_item_soles',
    'monto_postor_seleccionado', 'ruc_codigo_postor_seleccionado',
    'RUC_ind_seleccionado', 'proveedor_ind_seleccionado',
    'postor_seleccionado', 'ganador_flag_seleccionado', 'consorcio_flag_seleccionado',
    'ruc_codigo_postor_no_seleccionado', 'postor_no_seleccionado',
    'RUC_ind_no_seleccionado', 'proveedor_ind_no_seleccionado',
    'ganador_flag_no_seleccionado', 'consorcio_flag_no_seleccionado'
]]

st.markdown("### 📈 Base consolidada (primeros 500 registros)")
st.dataframe(df_display.head(500), use_container_width=True)

