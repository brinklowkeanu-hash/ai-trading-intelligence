
import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(
    page_title="AI Trading Intelligence",
    page_icon="📈",
    layout="wide"
)

MARKETS = {
    "EUR/USD": ("EURUSD=X", "OANDA:EURUSD", "Forex"),
    "GBP/USD": ("GBPUSD=X", "OANDA:GBPUSD", "Forex"),
    "USD/JPY": ("JPY=X", "OANDA:USDJPY", "Forex"),
    "Gold Futures": ("GC=F", "COMEX:GC1!", "Commodity"),
    "Silver Futures": ("SI=F", "COMEX:SI1!", "Commodity"),
    "S&P 500": ("^GSPC", "SP:SPX", "Index"),
    "NASDAQ 100": ("^NDX", "NASDAQ:NDX", "Index"),
    "Dow Jones": ("^DJI", "DJ:DJI", "Index"),
    "Apple": ("AAPL", "NASDAQ:AAPL", "Stock"),
    "NVIDIA": ("NVDA", "NASDAQ:NVDA", "Stock"),
    "Tesla": ("TSLA", "NASDAQ:TSLA", "Stock"),
    "Microsoft": ("MSFT", "NASDAQ:MSFT", "Stock"),
    "Bitcoin": ("BTC-USD", "COINBASE:BTCUSD", "Crypto"),
    "Ethereum": ("ETH-USD", "COINBASE:ETHUSD", "Crypto"),
    "Solana": ("SOL-USD", "COINBASE:SOLUSD", "Crypto")
}

TIMEFRAMES = {
    "5 Minutes": ("5m", "5d"),
    "15 Minutes": ("15m", "5d"),
    "30 Minutes": ("30m", "5d"),
    "1 Hour": ("60m", "1mo"),
    "1 Day": ("1d", "1y"),
    "1 Week": ("1wk", "5y")
}

st.title("📈 AI Trading Intelligence")
st.caption("Version 1.0 | Multi-market research terminal")

st.info(
    "Research prototype. All signals are technical observations, "
    "not guaranteed trading predictions."
)

# Sidebar controls
st.sidebar.header("Market controls")

market_name = st.sidebar.selectbox(
    "Select market",
    list(MARKETS.keys())
)

timeframe_name = st.sidebar.selectbox(
    "Select timeframe",
    list(TIMEFRAMES.keys()),
    index=4
)

refresh = st.sidebar.button(
    "🔄 Refresh market data"
)

ticker, tv_symbol, category = MARKETS[market_name]
interval, period = TIMEFRAMES[timeframe_name]

st.sidebar.markdown("---")
st.sidebar.caption("Data source: Yahoo Finance via yfinance")
st.sidebar.caption("Refresh manually when required.")

@st.cache_data(ttl=300)
def get_market_data(symbol, period, interval, refresh_id):
    stock = yf.Ticker(symbol)

    data = stock.history(
        period=period,
        interval=interval,
        auto_adjust=True
    )

    return data

if refresh:
    st.cache_data.clear()

try:
    data = get_market_data(
        ticker,
        period,
        interval,
        int(refresh)
    )

    if data.empty or len(data) < 55:
        st.warning(
            "Insufficient market data. Try another timeframe "
            "or refresh later."
        )
        st.stop()

    # Technical calculations
    data["EMA20"] = data["Close"].ewm(
        span=20, adjust=False
    ).mean()

    data["EMA50"] = data["Close"].ewm(
        span=50, adjust=False
    ).mean()

    delta = data["Close"].diff()

    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    average_gain = gains.ewm(
        alpha=1/14, min_periods=14, adjust=False
    ).mean()

    average_loss = losses.ewm(
        alpha=1/14, min_periods=14, adjust=False
    ).mean()

    rs = average_gain / average_loss.replace(0, float("nan"))

    data["RSI14"] = 100 - (100 / (1 + rs))

    latest = data.iloc[-1]

    price = float(latest["Close"])
    ema20 = float(latest["EMA20"])
    ema50 = float(latest["EMA50"])
    rsi = float(latest["RSI14"])

    # Technical alignment score, NOT win probability
    bullish_score = 0
    bearish_score = 0

    if price > ema20:
        bullish_score += 25
    else:
        bearish_score += 25

    if ema20 > ema50:
        bullish_score += 35
    else:
        bearish_score += 35

    if rsi >= 50:
        bullish_score += 20
    else:
        bearish_score += 20

    if price > ema50:
        bullish_score += 20
    else:
        bearish_score += 20

    if bullish_score >= 75:
        bias = "BULLISH"
    elif bearish_score >= 75:
        bias = "BEARISH"
    else:
        bias = "MIXED"

    # Main market display
    st.subheader(f"{market_name} | {timeframe_name}")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Latest price",
        f"{price:,.4f}"
    )

    col2.metric(
        "RSI (14)",
        f"{rsi:.2f}"
    )

    col3.metric(
        "Technical bias",
        bias
    )

    st.markdown("---")

    # Alignment display
    st.subheader("Technical alignment")

    col1, col2 = st.columns(2)

    col1.metric(
        "Bullish alignment",
        f"{bullish_score}/100"
    )

    col2.metric(
        "Bearish alignment",
        f"{bearish_score}/100"
    )

    st.caption(
        "These are rule-based indicator alignment scores, "
        "not probabilities of a profitable trade."
    )

    # Price chart
    st.subheader("Price and moving averages")

    chart_data = data[["Close", "EMA20", "EMA50"]].copy()

    st.line_chart(chart_data)

    # Indicator interpretation
    st.subheader("Technical observations")

    if price > ema20 > ema50:
        st.success(
            "Price is above both moving averages. "
            "The short and medium-term trend structure is bullish."
        )

    elif price < ema20 < ema50:
        st.error(
            "Price is below both moving averages. "
            "The short and medium-term trend structure is bearish."
        )

    else:
        st.warning(
            "Moving averages are not fully aligned. "
            "The trend structure is mixed."
        )

    if rsi >= 70:
        st.warning("RSI indicates potentially overbought conditions.")

    elif rsi <= 30:
        st.warning("RSI indicates potentially oversold conditions.")

    else:
        st.info("RSI is between 30 and 70.")

    # Market information
    st.subheader("Latest market candles")

    st.dataframe(
        data.tail(10).sort_index(ascending=False),
        use_container_width=True
    )

    # TradingView
    st.link_button(
        "Open this market on TradingView",
        f"https://www.tradingview.com/chart/?symbol={tv_symbol}"
    )

    st.caption(
        f"Data timestamp: {data.index[-1]} | "
        "Yahoo Finance data may be delayed or unavailable. "
        "Gold and silver use futures proxies, not spot CFD prices."
    )

except Exception as error:
    st.error(
        "Could not retrieve market data. "
        "Please try again later."
    )
    st.caption(str(error))

st.markdown("---")
st.caption(
    "AI Trading Intelligence V1 | Research only | "
    "No automatic trading or financial advice."
)
