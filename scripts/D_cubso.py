import time
import random
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE = "https://prod2.seace.gob.pe"
LISTADO_URL = f"{BASE}/buscador-publico-seace/api/cubso/catalogo/listado"
REFERER = LISTADO_URL

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                  " AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
    "Referer": REFERER,
    "Origin": BASE,
}

def post_listado_por_commodity(session, cat4, titulo_filtro=""):
    """
    Envía el POST y devuelve el HTML cuando detecta al menos una fila con patrón de item.
    No depende de 'class="datatable"'.
    """
    data = [
        ("idPadre", str(cat4)),
        ("titulo", titulo_filtro),
        # token dummy (si el backend no valida recaptcha en server-side)
        ("token", "x_dummy_token"),
        # Rellenos opcionales (puedes omitirlos si quieres)
        ("descripcion", "SEGMENTO"),
        ("descripcion", "FAMILIA"),
        ("descripcion", "CLASE"),
        ("descripcion", "COMMODITY"),
        ("descripcion", "ITEM"),
        ("cat1", ""),
        ("cat2", ""),
        ("cat3", ""),
        ("cat4", str(cat4)),
        ("cat5", ""),
        ("titulo1", ""),
        ("titulo2", ""),
        ("titulo3", ""),
        ("titulo4", ""),
        ("titulo5", titulo_filtro),
    ]

    resp = session.post(LISTADO_URL, headers=HEADERS, data=data, timeout=40)
    if resp.status_code != 200:
        return None

    html = resp.text

    # Validación robusta 1: ¿existe patrón de '8 dígitos - 8 dígitos' en los links de item?
    if re.search(r'\b\d{8}-\d{8}\b', html):
        return html

    # Validación robusta 2: ¿existe una tabla que parezca la de resultados?
    soup = BeautifulSoup(html, "html.parser")
    candidate_tables = soup.select("table.table.table-hover.table-bordered")  # amplio
    for tb in candidate_tables:
        # ¿Tiene encabezados esperados?
        head_text = " ".join(h.get_text(strip=True) for h in tb.select("thead th"))
        expected = ("SEGMENTO" in head_text and "FAMILIA" in head_text and 
                    "CLASE" in head_text and "COMMODITY" in head_text and "ITEM" in head_text)
        # ¿Tiene al menos una fila en tbody?
        has_rows = bool(tb.select("tbody tr"))
        if expected and has_rows:
            return html

    # Si nada calza, no lo tomamos como éxito
    return None

def parse_items_desde_html(html):
    """
    Extrae items como:
    [{'codigo_commodity':'10101601','codigo_item':'00211181','item':'GALLINA DE POSTURA'}, ...]
    """
    soup = BeautifulSoup(html, "html.parser")
    out = []

    # Encuentra cualquier tabla de resultados “larga”; si hay varias, procesamos todas.
    tables = soup.select("table")
    for table in tables:
        # Revisa si el encabezado tiene columnas esperadas (para filtrar)
        thead = table.find("thead")
        if not thead:
            continue
        th_txt = " ".join(th.get_text(strip=True).upper() for th in thead.find_all("th"))
        if not all(x in th_txt for x in ["SEGMENTO", "FAMILIA", "CLASE", "COMMODITY", "ITEM"]):
            continue

        # Recorre filas del tbody
        tbody = table.find("tbody")
        if not tbody:
            continue

        for tr in tbody.find_all("tr", recursive=False):
            tds = tr.find_all("td", recursive=False)
            if len(tds) < 5:
                continue

            td_item = tds[4]

            # Busca el patrón 8d-8d en cualquier texto dentro de la celda item
            full_text = td_item.get_text(" ", strip=True)
            m = re.search(r'\b(\d{8})-(\d{8})\b', full_text)
            if not m:
                continue

            codigo_commodity, codigo_item = m.group(1), m.group(2)

            # Descripción: generalmente es el segundo <td> de la tabla interna
            item_desc = ""
            inner_tr = td_item.select_one("table tr")
            if inner_tr:
                inner_tds = inner_tr.find_all("td", recursive=False)
                if len(inner_tds) >= 2:
                    item_desc = inner_tds[1].get_text(strip=True)
            if not item_desc:
                # Fallback: tomar el último texto no vacío después del código
                texts = [t.strip() for t in td_item.stripped_strings if t.strip()]
                # Si encontramos el string '10101601-00211181', la desc suele estar después
                try:
                    idx = next(i for i, t in enumerate(texts) if re.fullmatch(r'\d{8}-\d{8}', t))
                    if idx + 1 < len(texts):
                        item_desc = texts[idx + 1]
                except StopIteration:
                    # Último fallback
                    item_desc = texts[-1] if texts else ""

            out.append({
                "codigo_commodity": codigo_commodity,
                "codigo_item": codigo_item,
                "item": item_desc
            })

    return out

def scrape_items_para_lista_de_commodities(df_commodities, pausa=(0.8, 2.0)):
    """
    df_commodities: DF que contenga al menos col 'codigo_commodity' y, si quieres,
                    las columnas de contexto (segmento/familia/clase/commodity).
    Devuelve un DF con las columnas:
      ['codigo_segmento','segmento','codigo_familia','familia','codigo_clase','clase',
       'codigo_commodity','commodity','codigo_item','item','codigo_cubso']
    """
    session = requests.Session()
    resultados = []

    # Si tienes muchas filas, considera cachear e ir guardando en CSV incrementalmente
    for idx, row in df_commodities.iterrows():
        cat4 = str(row["codigo_commodity"])
        # Pequeña pausa aleatoria para no golpear el sitio
        time.sleep(random.uniform(*pausa))

        html = post_listado_por_commodity(session, cat4)
        if not html:
            print(f"[WARN] No se pudo obtener listado para commodity {cat4}. Intentar luego o usar Selenium.")
            continue

        items = parse_items_desde_html(html)
        if not items:
            print(f"[INFO] Commodity {cat4} sin items o no parseable.")
            continue

        # Agrega contexto de categorías si lo tienes en df_commodities
        for it in items:
            fila = {
                "codigo_segmento": row.get("codigo_segmento"),
                "segmento": row.get("segmento"),
                "codigo_familia": row.get("codigo_familia"),
                "familia": row.get("familia"),
                "codigo_clase": row.get("codigo_clase"),
                "clase": row.get("clase"),
                "codigo_commodity": it["codigo_commodity"],
                "commodity": row.get("commodity"),
                "codigo_item": it["codigo_item"],
                "item": it["item"],
            }
            fila["codigo_cubso"] = f"{fila['codigo_commodity']}-{fila['codigo_item']}"
            resultados.append(fila)

    return pd.DataFrame(resultados)

df = pd.read_pickle('../data/interim/cubso.pickle')
df.codigo_commodity = df.codigo_commodity.astype(int)

df_items = scrape_items_para_lista_de_commodities(df)
df_items.to_csv("../data/processed/D_cubso.csv", sep='|', index=False)