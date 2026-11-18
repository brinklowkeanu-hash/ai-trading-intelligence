
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timezone

# --------------------------------------------------
# PAGE SETTINGS
# --------------------------------------------------

st.set_page_config(
    page_title="AI Trading Intelligence V2",
    page_icon="📈",
    layout="wide"
)

st.title("🌍 AI Trading Intelligence")
st.caption("Version 2.0 | Global Market Intelligence")

st.info(
    "Research prototype. News sentiment is keyword-based, "
    "not an AI prediction or a verified trading signal."
)

# --------------------------------------------------
# MARKET DATABASE
# --------------------------------------------------

MARKETS = {
    "EUR/USD": {
        "ticker": "EURUSD=X",
        "tv": "OANDA:EURUSD",
        "category": "Forex",
        "query": '(euro OR EUR OR "European Central Bank")'
    },
    "GBP/USD": {
        "ticker": "GBPUSD=X",
        "tv": "OANDA:GBPUSD",
        "category": "Forex",
        "query": '(sterling OR "British pound" OR GBP OR "Bank of England")'
    },
    "USD/JPY": {
        "ticker": "JPY=X",
        "tv": "OANDA:USDJPY",
        "category": "Forex",
        "query": '(yen OR "Japanese yen" OR JPY OR "Bank of Japan")'
    },
    "Gold": {
        "ticker": "GC=F",
        "tv": "COMEX:GC1!",
        "category": "Commodity",
        "query": '(gold OR bullion OR XAU OR "precious metals")'
    },
    "Silver": {
        "ticker": "SI=F",
        "tv": "COMEX:SI1!",
        "category": "Commodity",
        "query": '(silver OR XAG OR "silver prices")'
    },
    "S&P 500": {
        "ticker": "^GSPC",
        "tv": "SP:SPX",
        "category": "Index",
        "query": '("S&P 500" OR SP500 OR "US stocks")'
    },
    "NASDAQ 100": {
        "ticker": "^NDX",
        "tv": "NASDAQ:NDX",
        "category": "Index",
        "query": '(NASDAQ OR "Nasdaq 100" OR technology stocks)'
    },
    "Dow Jones": {
        "ticker": "^DJI",
        "tv": "DJ:DJI",
        "category": "Index",
        "query": '("Dow Jones" OR "Dow Jones Industrial Average")'
    },
    "Apple": {
        "ticker": "AAPL",
        "tv": "NASDAQ:AAPL",
        "category": "Stock",
        "query": '(Apple OR AAPL OR "Apple Inc")'
    },
    "NVIDIA": {
        "ticker": "NVDA",
        "tv": "NASDAQ:NVDA",
        "category": "Stock",
        "query": '(NVIDIA OR NVDA)'
    },
    "Tesla": {
        "ticker": "TSLA",
        "tv": "NASDAQ:TSLA",
        "category": "Stock",
        "query": '(Tesla OR TSLA)'
    },
    "Microsoft": {
        "ticker": "MSFT",
        "tv": "NASDAQ:MSFT",
        "category": "Stock",
        "query": '(Microsoft OR MSFT)'
    },
    "Bitcoin": {
        "ticker": "BTC-USD",
        "tv": "COINBASE:BTCUSD",
        "category": "Crypto",
        "query": '(Bitcoin OR BTC OR cryptocurrency)'
    },
    "Ethereum": {
        "ticker": "ETH-USD",
        "tv": "COINBASE:ETHUSD",
        "category": "Crypto",
        "query": '(Ethereum OR ETH)'
    },
    "Solana": {
        "ticker": "SOL-USD",
        "tv": "COINBASE:SOLUSD",
        "category": "Crypto",
        "query": '(Solana OR SOL token)'
    }
}

# --------------------------------------------------
# TIMEFRAMES
# --------------------------------------------------

TIMEFRAMES = {
    "5 Minutes": ("5m", "5d"),
    "15 Minutes": ("15m", "5d"),
    "30 Minutes": ("30m", "5d"),
    "1 Hour": ("60m", "1mo"),
    "1 Day": ("1d", "1y"),
    "1 Week": ("1wk", "5y")
}

# --------------------------------------------------
# NEWS SENTIMENT ENGINE
# --------------------------------------------------

POSITIVE_WORDS = [
    "surge", "surges", "rally", "rallies",
    "gain", "gains", "growth", "strong",
    "record high", "bullish", "upgrade",
    "upgraded", "profit", "profits",
    "beat expectations", "recovery",
    "inflows", "approval", "approved",
    "optimism", "easing", "cuts rates"
]

NEGATIVE_WORDS = [
    "crash", "crashes", "plunge", "plunges",
    "fall", "falls", "decline", "declines",
    "weak", "weakness", "bearish", "downgrade",
    "downgraded", "loss", "losses",
    "missed expectations", "recession",
    "outflows", "ban", "banned",
    "crisis", "default", "inflation surge",
    "hikes rates"
]


def analyse_sentiment(headline):

    text = str(headline).lower()

    positive = sum(
        1 for word in POSITIVE_WORDS
        if word in text
    )

    negative = sum(
        1 for word in NEGATIVE_WORDS
        if word in text
    )

    if positive > negative:
        return "Positive", positive - negative

    if negative > positive:
        return "Negative", negative - positive

    return "Neutral", 0


# --------------------------------------------------
# GDELT NEWS COLLECTION
# --------------------------------------------------

@st.cache_data(ttl=900)

@st.cache_data(ttl=900)

@st.cache_data(ttl=900)
def get_news(search_query):

    import xml.etree.ElementTree as ET

    endpoint = "https://news.google.com/rss/search"

    params = {
        "q": search_query,
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 AITradingIntelligence/2.0"
    }

    try:
        response = requests.get(
            endpoint,
            params=params,
            headers=headers,
            timeout=30
        )

        if response.status_code == 429:
            raise RuntimeError(
                "Google News rate limit reached. "
                "Please wait before retrying."
            )

        response.raise_for_status()

        root = ET.fromstring(response.content)

        articles = []

        for item in root.findall(".//item"):

            title = item.findtext("title", default="")
            url = item.findtext("link", default="")
            pubdate = item.findtext("pubDate", default="")

            source_element = item.find("source")

            domain = (
                source_element.text
                if source_element is not None
                else "Unknown publisher"
            )

            articles.append({
                "title": title,
                "url": url,
                "Date": pubdate,
                "domain": domain,
                "language": "en",
                "sourcecountry": ""
            })

        if not articles:
            return pd.DataFrame()

        news = pd.DataFrame(articles)

        news["Date"] = pd.to_datetime(
            news["Date"],
            errors="coerce",
            utc=True
        )

        sentiment = news["title"].apply(analyse_sentiment)

        news["Sentiment"] = sentiment.apply(
            lambda x: x[0]
        )

        news["Sentiment Score"] = sentiment.apply(
            lambda x: x[1]
        )

        return news[[
            "title",
            "url",
            "Date",
            "domain",
            "language",
            "sourcecountry",
            "Sentiment",
            "Sentiment Score"
        ]]

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Google News connection timed out."
        )

    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Google News connection failed: {error}"
        )

    except ET.ParseError:
        raise RuntimeError(
            "Google News returned an invalid RSS feed."
        )

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "GDELT connection timed out. Try again later."
        )

    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Network connection failed: {error}"
        )


# --------------------------------------------------
# ECONOMIC INTELLIGENCE - FRED
# --------------------------------------------------

FRED_SERIES = {
    "Federal Funds Rate": "FEDFUNDS",
    "US Inflation Index": "CPIAUCSL",
    "US Unemployment": "UNRATE",
    "US 10-Year Treasury Yield": "DGS10"
}


@st.cache_data(ttl=3600)
def get_fred_data(series_id):

    url = (
        "https://fred.stlouisfed.org/graph/"
        "fredgraph.csv"
    )

    response = requests.get(
        url,
        params={"id": series_id},
        timeout=20
    )

    response.raise_for_status()

    from io import StringIO

    data = pd.read_csv(StringIO(response.text))

    if data.empty or len(data.columns) < 2:
        return None

    data.columns = ["Date", "Value"]

    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce"
    )

    data["Value"] = pd.to_numeric(
        data["Value"].replace(".", pd.NA),
        errors="coerce"
    )

    data = data.dropna().sort_values("Date")

    if data.empty:
        return None

    return data


# --------------------------------------------------
# MARKET DATA
# --------------------------------------------------

@st.cache_data(ttl=300)
def get_market_data(symbol, period, interval):

    stock = yf.Ticker(symbol)

    return stock.history(
        period=period,
        interval=interval,
        auto_adjust=True
    )


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("Market controls")

selected_market = st.sidebar.selectbox(
    "Select market",
    list(MARKETS.keys())
)

selected_timeframe = st.sidebar.selectbox(
    "Select timeframe",
    list(TIMEFRAMES.keys())
)

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Intelligence modules",
    [
        "Market Overview",
        "Global News",
        "Economic Intelligence",
        "Sentiment Analysis"
    ]
)

if st.sidebar.button("🔄 Refresh all data"):

    st.cache_data.clear()

    st.rerun()

# --------------------------------------------------
# MARKET OVERVIEW
# --------------------------------------------------

if page == "Market Overview":

    st.header("Market Overview")

    market = MARKETS[selected_market]

    interval, period = TIMEFRAMES[selected_timeframe]

    try:

        data = get_market_data(
            market["ticker"],
            period,
            interval
        )

        if data.empty or len(data) < 55:

            st.warning("Insufficient market data.")

        else:

            data["EMA20"] = data["Close"].ewm(
                span=20,
                adjust=False
            ).mean()

            data["EMA50"] = data["Close"].ewm(
                span=50,
                adjust=False
            ).mean()

            delta = data["Close"].diff()

            gains = delta.clip(lower=0)
            losses = -delta.clip(upper=0)

            avg_gain = gains.ewm(
                alpha=1/14,
                min_periods=14,
                adjust=False
            ).mean()

            avg_loss = losses.ewm(
                alpha=1/14,
                min_periods=14,
                adjust=False
            ).mean()

            rs = avg_gain / avg_loss.replace(0, float("nan"))

            data["RSI14"] = 100 - (100 / (1 + rs))

            latest = data.iloc[-1]

            price = float(latest["Close"])
            rsi = float(latest["RSI14"])

            bullish = sum([
                price > float(latest["EMA20"]),
                float(latest["EMA20"]) >
                float(latest["EMA50"]),
                rsi > 50,
                price > float(latest["EMA50"])
            ])

            score = bullish * 25

            bias = (
                "BULLISH" if score >= 75
                else "BEARISH" if score <= 25
                else "MIXED"
            )

            st.subheader(
                f"{selected_market} | {selected_timeframe}"
            )

            c1, c2, c3 = st.columns(3)

            c1.metric("Latest price", f"{price:,.4f}")
            c2.metric("RSI 14", f"{rsi:.2f}")
            c3.metric("Technical alignment", f"{score}/100")

            st.metric("Technical bias", bias)

            st.line_chart(
                data[["Close", "EMA20", "EMA50"]]
            )

            st.link_button(
                "Open TradingView chart",
                "https://www.tradingview.com/chart/"
                f"?symbol={market['tv']}"
            )

    except Exception as error:

        st.error("Market data could not be retrieved.")
        st.caption(str(error))


# --------------------------------------------------
# GLOBAL NEWS
# --------------------------------------------------

elif page == "Global News":

    st.header("Global Financial News")

    st.write(
        "Researching news related to your selected market."
    )

    query = MARKETS[selected_market]["query"]

    try:

        news = get_news(query)

        if news.empty:

            st.warning(
                "No matching articles were returned."
            )

        else:

            st.caption(
                f"{len(news)} articles returned. "
                "Search window: last 7 days."
            )

            for _, article in news.iterrows():

                title = str(article["title"])
                url = str(article["url"])
                domain = str(article["domain"])
                sentiment = article["Sentiment"]

                if sentiment == "Positive":
                    icon = "🟢"

                elif sentiment == "Negative":
                    icon = "🔴"

                else:
                    icon = "⚪"

                with st.container(border=True):

                    st.markdown(f"### {icon} {title}")

                    st.caption(
                        f"Source: {domain} | "
                        f"Sentiment: {sentiment}"
                    )

                    if pd.notna(article["Date"]):

                        st.caption(
                            "GDELT indexed: "
                            + str(article["Date"])
                        )

                    if url.startswith("https://") or url.startswith("http://"):
                        st.link_button(
                            "Read original article",
                            url
                        )

    except Exception as error:

        st.error("News collection failed.")
        st.caption(str(error))


# --------------------------------------------------
# ECONOMIC INTELLIGENCE
# --------------------------------------------------

elif page == "Economic Intelligence":

    st.header("US Economic Intelligence")

    st.write(
        "Macroeconomic indicators that can influence "
        "forex, gold, indices and other markets."
    )

    for name, series in FRED_SERIES.items():

        try:

            data = get_fred_data(series)

            if data is None or len(data) < 2:

                st.warning(f"{name}: No data available.")
                continue

            latest = data.iloc[-1]
            previous = data.iloc[-2]

            value = float(latest["Value"])
            old_value = float(previous["Value"])

            change = value - old_value

            with st.container(border=True):

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    name,
                    f"{value:.2f}"
                )

                c2.metric(
                    "Change from previous observation",
                    f"{change:+.2f}"
                )

                c3.write(
                    f"Latest observation: "
                    f"{latest['Date'].date()}"
                )

        except Exception as error:

            st.warning(f"{name}: Could not retrieve data.")
            st.caption(str(error))

    st.caption(
        "These are US macroeconomic indicators. "
        "Observation dates vary by release frequency. "
        "The latest observation may not be today's value."
    )


# --------------------------------------------------
# SENTIMENT ANALYSIS
# --------------------------------------------------

elif page == "Sentiment Analysis":

    st.header("Market Sentiment Analysis")

    st.write(
        "Headline-based sentiment for your selected asset."
    )

    try:

        query = MARKETS[selected_market]["query"]

        news = get_news(query)

        if news.empty:

            st.warning("No news available for sentiment analysis.")

        else:

            counts = news["Sentiment"].value_counts()

            positive = int(counts.get("Positive", 0))
            negative = int(counts.get("Negative", 0))
            neutral = int(counts.get("Neutral", 0))

            total = positive + negative + neutral

            c1, c2, c3 = st.columns(3)

            c1.metric("Positive headlines", positive)
            c2.metric("Negative headlines", negative)
            c3.metric("Neutral headlines", neutral)

            sentiment_data = pd.DataFrame({
                "Sentiment": [
                    "Positive",
                    "Negative",
                    "Neutral"
                ],
                "Articles": [
                    positive,
                    negative,
                    neutral
                ]
            })

            st.bar_chart(
                sentiment_data.set_index("Sentiment")
            )

            net_score = (
                (positive - negative) / total * 100
                if total else 0
            )

            st.metric(
                "Net headline sentiment",
                f"{net_score:+.1f}"
            )

            if net_score > 20:

                st.success(
                    "Headline coverage is predominantly positive."
                )

            elif net_score < -20:

                st.error(
                    "Headline coverage is predominantly negative."
                )

            else:

                st.info(
                    "Headline coverage is mixed or neutral."
                )

            st.caption(
                "This is headline keyword sentiment, "
                "not market positioning or a prediction "
                "of future price direction."
            )

    except Exception as error:

        st.error("Sentiment analysis failed.")
        st.caption(str(error))


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "AI Trading Intelligence V2 | "
    "Sources: Yahoo Finance, GDELT and FRED | "
    "Research only. No automated trade execution."
)

st.caption(
    "Data can be delayed, incomplete or revised. "
    "Verify important news and economic releases "
    "against their original sources."
)
