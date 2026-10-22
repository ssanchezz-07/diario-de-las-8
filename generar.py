# -*- coding: utf-8 -*-
"""Diario de las 8: genera docs/index.html con las noticias y los mercados del día.

Solo usa la biblioteca estándar para que GitHub Actions lo ejecute sin instalar nada.
Cada sección toma titulares de varios RSS, quita duplicados y se queda con los más recientes.
"""
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

MADRID = ZoneInfo("Europe/Madrid")
UA = {"User-Agent": "Mozilla/5.0 (DiarioDeLas8; +https://github.com)"}
SALIDA = Path(__file__).parent / "docs" / "index.html"


def google_news(consulta):
    q = urllib.parse.quote(f"{consulta} when:1d")
    return f"https://news.google.com/rss/search?q={q}&hl=es&gl=ES&ceid=ES:es"


# (id, título, ámbito, fuentes, cuántas)
SECCIONES = [
    ("mundo", "Mundo", "Internacional", [
        "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada",
        "https://feeds.bbci.co.uk/mundo/rss.xml",
    ], 6),
    ("espana", "España", "Nacional", [
        "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/espana/portada",
        google_news("España Gobierno OR Congreso"),
    ], 6),
    ("malaga", "Málaga", "Capital y provincia", [
        google_news("Málaga"),
    ], 6),
    ("economia", "Economía y mercados", "Bolsa · tipos · macro", [
        "https://e00-expansion.uecdn.es/rss/portada.xml",
        google_news("Ibex OR BCE OR Euríbor OR bolsa"),
    ], 5),
    ("fiscal", "Fiscal y laboral", "Hacienda · AEAT · Seguridad Social", [
        google_news("Hacienda OR AEAT OR IRPF OR IVA OR Verifactu OR \"Seguridad Social\""),
    ], 5),
    ("tech", "Tecnología e IA", "Tecnología", [
        "https://www.xataka.com/feedburner.xml",
        google_news("\"inteligencia artificial\""),
    ], 5),
    ("cofrade", "Cofrade", "Málaga y Andalucía", [
        google_news("cofradía OR hermandad Málaga"),
    ], 4),
]

MERCADOS = [
    ("IBEX 35", "^IBEX"), ("Euro Stoxx 50", "^STOXX50E"), ("DAX 40", "^GDAXI"),
    ("S&P 500", "^GSPC"), ("Nasdaq", "^IXIC"), ("Nikkei 225", "^N225"),
    ("Brent ($)", "BZ=F"), ("Oro ($/oz)", "GC=F"), ("EUR/USD", "EURUSD=X"),
    ("Bono EE.UU. 10a", "^TNX"), ("Bitcoin ($)", "BTC-USD"), ("VIX", "^VIX"),
]

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def descargar(url, timeout=20):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def limpiar(texto, maximo=320):
    texto = html.unescape(re.sub(r"<[^>]+>", " ", texto or ""))
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto if len(texto) <= maximo else texto[:maximo].rsplit(" ", 1)[0] + "…"


def leer_rss(url):
    """Lista de noticias {t, r, f, u, fecha} de un RSS. Si falla, lista vacía."""
    try:
        raiz = ET.fromstring(descargar(url))
    except Exception as e:  # una fuente caída no debe tumbar el diario
        print(f"[aviso] {url[:70]}: {e}")
        return []
    canal = limpiar(raiz.findtext("channel/title") or "", 60)
    salida = []
    for item in raiz.iter("item"):
        titulo = limpiar(item.findtext("title"), 200)
        fuente = item.findtext("source") or canal
        # Google News pone « - Medio» al final del título
        if "news.google.com" in url and " - " in titulo:
            titulo, fuente = titulo.rsplit(" - ", 1)
        resumen = limpiar(item.findtext("description"))
        if "news.google.com" in url or resumen.startswith(titulo[:40]):
            resumen = ""  # en Google News la descripción solo repite el titular
        try:
            fecha = parsedate_to_datetime(item.findtext("pubDate"))
        except Exception:
            fecha = None
        enlace = (item.findtext("link") or "").strip()
        if urllib.parse.urlparse(enlace).scheme not in ("http", "https"):
            enlace = ""
        salida.append({"t": titulo, "r": resumen, "f": limpiar(fuente, 60),
                       "u": enlace, "fecha": fecha})
    return salida


def clave(titulo):
    return re.sub(r"[^a-z0-9áéíóúñ]", "", titulo.lower())[:45]


def seccion(fuentes, cuantas, vistos):
    limite = datetime.now(timezone.utc) - timedelta(hours=30)
    todas = [n for url in fuentes for n in leer_rss(url)]
    recientes = [n for n in todas if n["fecha"] is None or n["fecha"] >= limite] or todas
    recientes.sort(key=lambda n: n["fecha"] or limite, reverse=True)
    elegidas = []
    for n in recientes:
        k = clave(n["t"])
        if k in vistos or not n["t"]:
            continue
        vistos.add(k)
        elegidas.append(n)
        if len(elegidas) == cuantas:
            break
    return elegidas


def mercados():
    filas = []
    for nombre, simbolo in MERCADOS:
        url = ("https://query1.finance.yahoo.com/v8/finance/chart/"
               + urllib.parse.quote(simbolo) + "?range=5d&interval=1d")
        try:
            meta = json.loads(descargar(url, 15))["chart"]["result"][0]["meta"]
            precio, previo = meta["regularMarketPrice"], meta["chartPreviousClose"]
            cambio = (precio - previo) / previo * 100 if previo else 0.0
            decimales = 4 if simbolo == "EURUSD=X" else 2 if precio < 1000 else 0
            texto = f"{precio:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")
            if simbolo == "^TNX":
                texto += " %"
            filas.append({"n": nombre, "v": texto, "c": round(cambio, 2)})
        except Exception as e:
            print(f"[aviso] mercado {simbolo}: {e}")
    return filas


def aviso_fiscal(hoy):
    """Plazos trimestrales de la AEAT (modelos 303, 111, 115, 130…)."""
    plazos = {1: ("4T y resúmenes anuales (303, 390, 111, 190, 115, 180, 130)", 30),
              4: ("1T (303, 111, 115, 130, 202 si procede)", 20),
              7: ("2T (303, 111, 115, 130)", 20),
              10: ("3T (303, 111, 115, 130, 202)", 20)}
    if hoy.month in plazos and hoy.day <= plazos[hoy.month][1]:
        modelos, fin = plazos[hoy.month]
        quedan = fin - hoy.day
        return (f"Plazo del {modelos} abierto hasta el {fin} de {MESES[hoy.month - 1]}"
                f" ({'último día' if quedan == 0 else f'quedan {quedan} días'}; si se domicilia, unos 5 días antes).")
    return ""


def main():
    ahora = datetime.now(MADRID)
    vistos = set()
    datos = {
        "fecha_texto": f"{DIAS[ahora.weekday()].capitalize()}, {ahora.day} de {MESES[ahora.month - 1]} de {ahora.year}",
        "generado": ahora.strftime("%H:%M"),
        "secciones": [],
        "mercados": mercados(),
        "aviso_fiscal": aviso_fiscal(ahora),
    }
    for sid, titulo, ambito, fuentes, cuantas in SECCIONES:
        noticias = seccion(fuentes, cuantas, vistos)
        for n in noticias:
            n.pop("fecha")
        datos["secciones"].append({"id": sid, "titulo": titulo, "ambito": ambito, "noticias": noticias})
    datos["claves"] = [s["noticias"][0]["t"] for s in datos["secciones"][:3] if s["noticias"]]

    plantilla = (Path(__file__).parent / "plantilla.html").read_text(encoding="utf-8")
    json_seguro = (json.dumps(datos, ensure_ascii=False)
                   .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))
    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(plantilla.replace("__DATOS__", json_seguro), encoding="utf-8")
    total = sum(len(s["noticias"]) for s in datos["secciones"])
    print(f"Diario generado: {total} noticias, {len(datos['mercados'])} mercados -> {SALIDA}")


if __name__ == "__main__":
    main()
