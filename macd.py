import os
import pandas as pd
import yfinance as yf
from tqdm import tqdm
from robocorp.tasks import task

def calculate_macd(data, short_period=12, long_period=26, signal_period=9):
    """Beräknar MACD, signallinje och histogram."""
    data['EMA_short'] = data['Close'].ewm(span=short_period, adjust=False).mean()
    data['EMA_long'] = data['Close'].ewm(span=long_period, adjust=False).mean()
    data['MACD'] = data['EMA_short'] - data['EMA_long']
    data['Signal'] = data['MACD'].ewm(span=signal_period, adjust=False).mean()
    data['Histogram'] = data['MACD'] - data['Signal']
    return data

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

def analyze_ticker_macd(symbol, prev_values=None):
    """
    Hämtar historisk data för symbolen, beräknar MACD och en 50-dagars SMA.
    Returnerar en signal baserad på MACD-korsning, men endast om den aktuella
    trenden är uppåtgående (d.v.s. stängningspriset ligger över SMA_50).
    """
    try:
        data = yf.download(symbol, period="5y", interval="1d", progress=False)
        if data.empty:
            return None

        # Beräkna MACD och 50-dagars SMA
        data = calculate_macd(data)
        data['SMA_50'] = data['Close'].rolling(window=50, min_periods=1).mean()
        latest = data.iloc[-1]
        
        # Konvertera till skalära värden
        current_macd = float(latest['MACD'])
        current_signal = float(latest['Signal'])
        histogram = float(latest['Histogram'])
        close = float(latest['Close'])
        sma50 = float(latest['SMA_50'])
        
        # Bestäm signal baserat på MACD-korsning
        if prev_values:
            prev_macd = prev_values.get('macd', current_macd)
            prev_signal = prev_values.get('signal', current_signal)
            if prev_macd <= prev_signal and current_macd > current_signal:
                trade_signal = "KÖP"
            elif prev_macd >= prev_signal and current_macd < current_signal:
                trade_signal = "SÄLJ"
            else:
                trade_signal = "AVVAKTA"
        else:
            trade_signal = "KÖP" if current_macd > current_signal else "SÄLJ" if current_macd < current_signal else "AVVAKTA"
        
        # Trendfilter: Vi vill endast köpa om stängningspriset är över SMA_50 (uppåtgående trend)
        if trade_signal == "KÖP" and close <= sma50:
            trade_signal = "AVVAKTA"
        
        return {
            "symbol": symbol,
            "macd": current_macd,
            "signal": current_signal,
            "histogram": histogram,
            "close": close,
            "sma50": sma50,
            "trade_signal": trade_signal,
            "prev": {"macd": current_macd, "signal": current_signal}
        }
    except Exception as e:
        print(f"Fel vid analys av {symbol}: {e}")
        return None

@task
def run_stock_analysis_macd():
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

    print("🔄 Startar MACD-analys av tickers (senaste dagen)...")
    for ticker in tqdm(tickers, desc="Analyserar tickers"):
        result = analyze_ticker_macd(ticker)
        if result is None:
            print(f"❌ Ingen data hittades för {ticker}.")
            tickers_removed.append(ticker)
        else:
            working_results.append(result)
            tickers_to_keep.append(ticker)
            print(f"📊 {ticker}: Close={result['close']:.2f}, MACD={result['macd']:.2f}, Signal={result['signal']:.2f}, SMA50={result['sma50']:.2f} - Trade: {result['trade_signal']}")

    # Uppdatera CSV-filen med tickers som fungerade
    updated_df = pd.DataFrame({"ticker": tickers_to_keep})
    save_ticker_list(csv_file, updated_df)
    print(f"\n✅ Analys klar! Totalt fungerande tickers: {len(tickers_to_keep)} / {len(tickers)}")

    # Spara analysresultaten med signal
    results_df = pd.DataFrame(working_results)
    analysis_csv = "analysis_results_macd.csv"
    results_df.to_csv(analysis_csv, index=False)
    print(f"📄 Resultaten sparade i '{analysis_csv}'.")