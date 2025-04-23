import yfinance as yf
import pandas as pd
import ta
import streamlit as st
import json
import os

st.set_page_config(page_title="📈 Aktienanalyse Tool", layout="wide")
st.title("📊 Aktienanalyse mit Watchlist & Signalprognose")

# === Watchlist speichern & laden ===
WATCHLIST_DATEI = "watchlist.json"

def lade_watchlist():
    if os.path.exists(WATCHLIST_DATEI):
        with open(WATCHLIST_DATEI, "r") as f:
            return json.load(f)
    return ["AAPL", "MSFT"]

def speichere_watchlist(ticker_liste):
    with open(WATCHLIST_DATEI, "w") as f:
        json.dump(ticker_liste, f)

# === UI: Watchlist bearbeiten ===
st.sidebar.header("⚙️ Einstellungen")
watchlist_input = st.sidebar.text_input("Watchlist (durch Komma getrennt)", ", ".join(lade_watchlist()))

if st.sidebar.button("💾 Watchlist speichern"):
    neue_watchlist = [t.strip().upper() for t in watchlist_input.split(",") if t.strip()]
    speichere_watchlist(neue_watchlist)
    st.sidebar.success("Watchlist gespeichert. Bitte Seite neu laden.")

watchlist = lade_watchlist()

# === Analyse je Aktie ===
for symbol in watchlist:
    st.markdown(f"## 📌 {symbol}")
    try:
        daten = yf.download(symbol, period="6mo", interval="1d")
        if daten.empty:
            st.warning(f"Keine Daten für {symbol} gefunden.")
            continue

        # Indikatoren berechnen
        daten["EMA20"] = ta.trend.ema_indicator(daten["Close"], window=20)
        daten["EMA50"] = ta.trend.ema_indicator(daten["Close"], window=50)
        daten["SMA200"] = ta.trend.sma_indicator(daten["Close"], window=200)
        daten["RSI"] = ta.momentum.RSIIndicator(daten["Close"]).rsi()
        daten["MACD"] = ta.trend.macd_diff(daten["Close"]).values.ravel()

        # Signal-Logik
        def signal(zeile):
            if zeile["EMA20"] > zeile["EMA50"] and zeile["RSI"] < 70:
                return "Kaufen"
            elif zeile["EMA20"] < zeile["EMA50"] and zeile["RSI"] > 30:
                return "Verkaufen"
            elif zeile["Close"] > zeile["SMA200"]:
                return "Langfristig stark"
            else:
                return "Beobachten"

        daten["Signal"] = daten.apply(signal, axis=1)

        # Letzte Werte anzeigen
        st.write("Letzte 7 Handelstage:")
        st.dataframe(daten[["Close", "RSI", "MACD", "Signal"]].tail(7), use_container_width=True)

        # Prognose basierend auf RSI
        letzter_rsi = daten["RSI"].iloc[-1]
        if letzter_rsi < 35:
            st.info("🔮 Möglicher Kauf bald: RSI nähert sich überverkaufter Zone")
        elif letzter_rsi > 65:
            st.warning("⚠️ Möglicher Verkauf bald: RSI über 65")
        else:
            st.success("✅ Keine Extremzone in Sicht")

        # Chart anzeigen
        st.line_chart(daten[["Close", "EMA20", "EMA50"]])

    except Exception as e:
        st.error(f"Fehler bei {symbol}: {e}")
