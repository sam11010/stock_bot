import os
import pandas as pd
import yfinance as yf
from tqdm import tqdm
from robocorp.tasks import task

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def ensure_csv(csv_file):
    """Skapar CSV-fil med header 'ticker' om den inte finns."""
    if not os.path.exists(csv_file):
        df = pd.DataFrame(columns=["ticker"])
        df.to_csv(csv_file, index=False)
        print(f"✅ Skapade {csv_file} med header 'ticker'. Fyll i tickers i filen.")

def load_ticker_list(csv_file):
    """Läser in tickers från CSV-fil."""
    return pd.read_csv(csv_file)

def save_ticker_list(csv_file, df):
    """Sparar DataFrame med tickers till CSV-fil."""
    df.to_csv(csv_file, index=False)
    print(f"✅ Uppdaterad tickerlista sparad till {csv_file}.")

def analyze_ticker(symbol):
    """Hämtar data, beräknar SMA, RSI och bestämmer signalen (för senaste dagen)."""
    try:
        data = yf.download(symbol, period="5y", interval="1d", progress=False)
        if data.empty:
            return None
        data['SMA_20'] = data['Close'].rolling(window=20, min_periods=1).mean()
        data['RSI'] = calculate_rsi(data)
        latest = data.iloc[-1]
        # Konvertera till skalära värden
        close = float(latest['Close'])
        rsi = float(latest['RSI'])
        sma = float(latest['SMA_20'])
        if rsi < 30 and close > sma:
            signal = "KÖP"
        elif rsi > 70 and close < sma:
            signal = "SÄLJ"
        else:
            signal = "AVVAKTA"
        return {"symbol": symbol, "close": close, "rsi": rsi, "sma": sma, "signal": signal}
    except Exception as e:
        print(f"Fel vid analys av {symbol}: {e}")
        return None

@task
def run_stock_analysis():
    csv_file = "tickers.csv"
    ensure_csv(csv_file)
    df = load_ticker_list(csv_file)
    tickers = df["ticker"].tolist()

    if not tickers:
        print("❌ Inga tickers hittades i CSV-filen. Fyll i filen med tickers och kör igen.")
        return

    working_results = []
    tickers_to_keep = []
    tickers_removed = []

    print("🔄 Startar analys av tickers (senaste dagen)...")
    for ticker in tqdm(tickers, desc="Analyserar tickers"):
        result = analyze_ticker(ticker)
        if result is None:
            print(f"❌ Ingen data hittades för {ticker}.")
            tickers_removed.append(ticker)
        else:
            working_results.append(result)
            tickers_to_keep.append(ticker)
            print(f"📊 {ticker}: Stängning={result['close']:.2f}, RSI={result['rsi']:.2f}, SMA_20={result['sma']:.2f} - Signal: {result['signal']}")

    # Uppdatera CSV-filen med tickers som fungerar
    updated_df = pd.DataFrame({"ticker": tickers_to_keep})
    save_ticker_list(csv_file, updated_df)
    print(f"\n✅ Analys klar! Totalt fungerande tickers: {len(tickers_to_keep)} / {len(tickers)}")

    # Spara analysresultaten med signal
    results_df = pd.DataFrame(working_results)
    analysis_csv = "analysis_results.csv"
    results_df.to_csv(analysis_csv, index=False)
    print(f"📄 Resultaten sparade i '{analysis_csv}'.")