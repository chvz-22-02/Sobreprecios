import requests
import pandas as pd
from io import StringIO

URL = "https://prod2.seace.gob.pe/buscador-publico-seace/api/cubso/buscador/modalBuscador2/1/0/0/SEGMENTO"

# Cabeceras tipo navegador (las sec-*, gpc, etc. no son necesarias para requests)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                  " AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
    "Referer": "https://prod2.seace.gob.pe/buscador-publico-seace/api/cubso/catalogo/listado",
}

resp = requests.get(URL, headers=HEADERS, timeout=30)
resp.raise_for_status()

# Extrae todas las tablas del HTML y localiza la que tiene columnas 'Codigo' y 'Titulo'
html_io = StringIO(resp.text)
tables = pd.read_html(html_io)
df_segmento = next(t for t in tables if {'Codigo', 'Titulo'}.issubset(set(t.columns)))

# Limpieza y selección de columnas
df_segmento = df_segmento[['Codigo', 'Titulo']].dropna().reset_index(drop=True).rename(columns={'Codigo': 'codigo_segmento', 'Titulo': 'segmento'})

lista = []
for i in df_segmento.codigo_segmento:
    URL = f"https://prod2.seace.gob.pe/buscador-publico-seace/api/cubso/buscador/modalBuscador2/2/{i}/0/FAMILIA"

    # Cabeceras tipo navegador (las sec-*, gpc, etc. no son necesarias para requests)
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    " AppleWebKit/537.36 (KHTML, like Gecko)"
                    " Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
        "Referer": "https://prod2.seace.gob.pe/buscador-publico-seace/api/cubso/catalogo/listado",
    }

    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    # Extrae todas las tablas del HTML y localiza la que tiene columnas 'Codigo' y 'Titulo'
    df_familia = pd.DataFrame()
    html_io = StringIO(resp.text) 
    tables = pd.read_html(html_io)
    df_familia = next(t for t in tables if {'Codigo', 'Titulo'}.issubset(set(t.columns)))

    # Limpieza y selección de columnas
    df_familia = df_familia[['Codigo', 'Titulo']].dropna().reset_index(drop=True).rename(columns={'Codigo': 'codigo_familia', 'Titulo': 'familia'})
    df_familia = df_segmento[df_segmento['codigo_segmento']==i].join(df_familia, how='cross')
    
    for j in df_familia.codigo_familia:
        URL = f'https://prod2.seace.gob.pe/buscador-publico-seace/api/cubso/buscador/modalBuscador2/3/{j}/0/CLASE'
        
        # Cabeceras tipo navegador (las sec-*, gpc, etc. no son necesarias para requests)
        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                        " AppleWebKit/537.36 (KHTML, like Gecko)"
                        " Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
            "Referer": "https://prod2.seace.gob.pe/buscador-publico-seace/api/cubso/catalogo/listado",
        }

        resp = requests.get(URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()

        # Extrae todas las tablas del HTML y localiza la que tiene columnas 'Codigo' y 'Titulo'
        df_clase = pd.DataFrame()
        html_io = StringIO(resp.text) 
        tables = pd.read_html(html_io)
        df_clase = next(t for t in tables if {'Codigo', 'Titulo'}.issubset(set(t.columns)))

        # Limpieza y selección de columnas
        df_clase = df_clase[['Codigo', 'Titulo']].dropna().reset_index(drop=True).rename(columns={'Codigo': 'codigo_clase', 'Titulo': 'clase'})
        df_clase = df_familia[df_familia['codigo_familia']==j].join(df_clase, how='cross')
        
        for k in df_clase.codigo_clase:
            URL = f'https://prod2.seace.gob.pe/buscador-publico-seace/api/cubso/buscador/modalBuscador2/4/{k}/0/ITEM'
            
            # Cabeceras tipo navegador (las sec-*, gpc, etc. no son necesarias para requests)
            HEADERS = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                            " AppleWebKit/537.36 (KHTML, like Gecko)"
                            " Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
                "Referer": "https://prod2.seace.gob.pe/buscador-publico-seace/api/cubso/catalogo/listado",
            }

            resp = requests.get(URL, headers=HEADERS, timeout=30)
            resp.raise_for_status()

            # Extrae todas las tablas del HTML y localiza la que tiene columnas 'Codigo' y 'Titulo'
            df_commodity = pd.DataFrame()
            html_io = StringIO(resp.text) 
            tables = pd.read_html(html_io)
            df_commodity = next(t for t in tables if {'Codigo', 'Titulo'}.issubset(set(t.columns)))

            # Limpieza y selección de columnas
            df_commodity = df_commodity[['Codigo', 'Titulo']].dropna().reset_index(drop=True).rename(columns={'Codigo': 'codigo_commodity', 'Titulo': 'commodity'})
            df_commodity = df_clase[df_clase['codigo_clase']==k].join(df_commodity, how='cross')
            lista.append(df_commodity)

pd.concat(lista).to_csv('../data/processed/D_cubso.csv', sep='|', index=False)