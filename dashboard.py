import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Equity Research Dashboard", layout="wide")

st.title("Equity Research & Portfolio Analytics Dashboard")
st.write("Live NSE Stock Data — Built by Kshitiz Sharma")
# Sidebar
st.sidebar.header("Portfolio Settings")

tickers = st.sidebar.multiselect(
    "Select Stocks",
    ["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS", "WIPRO.NS", "ITC.NS", "BAJFINANCE.NS"],
    default=["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS"]
)

period = st.sidebar.selectbox(
    "Select Period",
    ["1mo", "3mo", "6mo", "1y", "2y"],
    index=3
)
# Pull live data
if len(tickers) > 0:
    data = yf.download(tickers, period=period)["Close"]
    returns = data.pct_change() * 100
    st.success(f"Loaded data for {len(tickers)} stocks")
else:
    st.warning("Please select at least one stock from the sidebar")
    # Metric cards
risk_free_rate = 6.5 / 252

st.subheader("Portfolio Analytics Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_volatility = returns.std().mean()
    st.metric("Avg Volatility", f"{avg_volatility:.2f}%")

with col2:
    sharpe = ((returns.mean() - risk_free_rate) / returns.std()).mean()
    st.metric("Avg Sharpe Ratio", f"{sharpe:.2f}")

with col3:
    nifty = yf.download("^NSEI", period=period)["Close"]
    nifty_returns = nifty.pct_change() * 100
    betas = [returns[t].cov(nifty_returns["^NSEI"]) / nifty_returns["^NSEI"].var() for t in returns.columns]
    avg_beta = sum(betas) / len(betas)
    st.metric("Avg Beta", f"{avg_beta:.2f}")

with col4:
    avg_return = returns.mean().mean()
    st.metric("Avg Daily Return", f"{avg_return:.2f}%")
    # Price chart
st.subheader("Price Performance vs Nifty 50")

import plotly.express as px

# Normalize to 100 so all stocks start at same point
normalized = (data / data.iloc[0]) * 100

fig = px.line(normalized, 
              title="Normalized Price Performance (Base = 100)",
              labels={"value": "Price (Normalized)", "Date": "Date"})

st.plotly_chart(fig, use_container_width=True)
# Analytics Summary Table
st.subheader("Stock Analytics Summary")

risk_free_rate = 6.5 / 252

summary_data = []
for ticker in returns.columns:
    vol = returns[ticker].std()
    sharpe = (returns[ticker].mean() - risk_free_rate) / vol
    beta = returns[ticker].cov(nifty_returns["^NSEI"]) / nifty_returns["^NSEI"].var()
    avg_ret = returns[ticker].mean()
    summary_data.append({
        "Stock": ticker,
        "Avg Daily Return": f"{avg_ret:.2f}%",
        "Volatility": f"{vol:.2f}%",
        "Sharpe Ratio": f"{sharpe:.2f}",
        "Beta": f"{beta:.2f}"
    })

summary_df = pd.DataFrame(summary_data)
st.dataframe(summary_df, use_container_width=True)
# Sector Allocation Pie Chart
st.subheader("Sector Allocation")

sectors = {
    "TCS.NS": "IT",
    "INFY.NS": "IT", 
    "WIPRO.NS": "IT",
    "HDFCBANK.NS": "Banking",
    "RELIANCE.NS": "Energy",
    "BAJFINANCE.NS": "Finance",
    "ITC.NS": "FMCG"
}

selected_sectors = [sectors.get(t, "Other") for t in returns.columns]

sector_df = pd.DataFrame({
    "Stock": list(returns.columns),
    "Sector": selected_sectors
})
sector_counts = sector_df["Sector"].value_counts().reset_index()
sector_counts.columns = ["Sector", "Count"]

fig2 = px.pie(sector_counts, 
              values="Count", 
              names="Sector",
              title="Portfolio Sector Allocation")

st.plotly_chart(fig2, use_container_width=True)
# Individual Stock Deep Dive
st.subheader("Individual Stock Analysis")

selected_stock = st.selectbox("Select a stock to analyse", returns.columns)

col1, col2 = st.columns(2)

with col1:
    # Closing price chart
    fig3 = px.line(data[selected_stock], 
                   title=f"{selected_stock} Closing Price")
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    # Daily returns distribution
    fig4 = px.histogram(returns[selected_stock].dropna(),
                        title=f"{selected_stock} Daily Returns Distribution",
                        nbins=50)
    st.plotly_chart(fig4, use_container_width=True)
    # Financial Ratios
st.subheader("Key Financial Ratios")

try:
    ticker_info = yf.Ticker(selected_stock).info
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pe = ticker_info.get("trailingPE", "N/A")
        st.metric("P/E Ratio", f"{pe:.2f}" if isinstance(pe, float) else pe)
    
    with col2:
        pb = ticker_info.get("priceToBook", "N/A")
        st.metric("P/B Ratio", f"{pb:.2f}" if isinstance(pb, float) else pb)
    
    with col3:
        de = ticker_info.get("debtToEquity", "N/A")
        st.metric("Debt/Equity", f"{de:.2f}" if isinstance(de, float) else de)
    
    with col4:
        roe = ticker_info.get("returnOnEquity", "N/A")
        st.metric("ROE", f"{roe:.2%}" if isinstance(roe, float) else roe)

except:
    st.warning("Financial ratios unavailable for this stock")
# DCF Model
st.subheader("DCF Valuation Model")

dcf_col1, dcf_col2 = st.columns(2)

with dcf_col1:
    try:
        stock_info = yf.Ticker(selected_stock).info
        default_eps = stock_info.get("trailingEps", 50)
    except:
        default_eps = 50

    eps = st.number_input("Current EPS (₹)", value=float(default_eps) if default_eps else 50.0)
    growth_rate = st.slider("Growth Rate (%)", 5, 30, 15) / 100
    discount_rate = st.slider("Discount Rate (%)", 8, 20, 12) / 100
    terminal_growth = st.slider("Terminal Growth Rate (%)", 2, 8, 4) / 100
    years = st.slider("Projection Years", 3, 10, 5)

with dcf_col2:
    cash_flows = []
    for year in range(1, years + 1):
        cf = eps * ((1 + growth_rate) ** year)
        pv = cf / ((1 + discount_rate) ** year)
        cash_flows.append(pv)

    terminal_value = (cash_flows[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
    dcf_value = sum(cash_flows) + terminal_value

    try:
        current_price = yf.Ticker(selected_stock).info.get("currentPrice", 0)
    except:
        current_price = 0

    st.metric("DCF Intrinsic Value", f"₹{dcf_value:.2f}")
    st.metric("Current Market Price", f"₹{current_price:.2f}")

    if current_price > 0:
        margin = ((dcf_value - current_price) / current_price) * 100
        if margin > 0:
            st.success(f"Undervalued by {margin:.1f}% — potential BUY")
        else:
            st.error(f"Overvalued by {abs(margin):.1f}% — potential SELL")