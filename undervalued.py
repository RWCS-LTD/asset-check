import requests
import pandas as pd
import streamlit as st

# Function to get all coins' IDs and symbols from CoinGecko
def get_coin_list():
    response = requests.get("https://api.coingecko.com/api/v3/coins/list")
    
    try:
        coins = response.json()
        return coins
    except ValueError:
        st.error("Failed to retrieve the list of coins.")
        return []

# Function to get the Coin ID by symbol
def get_coin_id_by_symbol(symbol, coin_list):
    for coin in coin_list:
        if coin['symbol'].lower() == symbol.lower():
            return coin['id']  # Return the CoinGecko ID
    return None

# Function to get token data from CoinGecko by coin ID
def get_token_by_id(coin_id):
    params = {
        "vs_currency": "usd",
        "ids": coin_id,  # Use CoinGecko ID here
        "sparkline": False,
        "price_change_percentage": "7d,30d"  # Fetch 7-day and 30-day price change
    }
    response = requests.get("https://api.coingecko.com/api/v3/coins/markets", params=params)

    # Try to parse the response as JSON
    try:
        token_data = response.json()
        if len(token_data) == 0:
            return None
        return token_data[0]  # Return the first token data for the specified symbol
    except ValueError:
        st.error("Failed to parse API response.")
        return None

# Function to calculate potential gains (e.g., x2, x5, etc.)
def calculate_potential_gains(current_price, ath_price):
    if current_price > 0:
        return ath_price / current_price  # This calculates the potential gain as a multiple
    return 0  # Avoid division by zero

# Main Streamlit app function
def main():
    st.title("Crypto Asset Metrics: Informed Decision-making")

    # Input field to get the symbol
    symbol = st.text_input("Enter the crypto symbol (e.g., BTC, ETH)", "").strip()

    if symbol:
        with st.spinner('Fetching data...'):
            # Fetch coin list to get the CoinGecko ID
            coin_list = get_coin_list()
            coin_id = get_coin_id_by_symbol(symbol, coin_list)
            
            if coin_id:
                token = get_token_by_id(coin_id)

                if token:
                    token_name = token['name']
                    current_price = token['current_price']
                    ath_price = token['ath']
                    volume = token['total_volume']
                    market_cap = token['market_cap']
                    price_change_7d = token.get('price_change_percentage_7d_in_currency', 0)
                    price_change_30d = token.get('price_change_percentage_30d_in_currency', 0)
                    market_cap_rank = token.get('market_cap_rank', 'N/A')
                    circulating_supply = token.get('circulating_supply', 'N/A')
                    mc_vol_ratio = market_cap / volume if volume > 0 else 0
                    price_to_sales = market_cap / volume if volume > 0 else float('inf')  # Lower is better

                    # Calculate potential gains
                    potential_gains = calculate_potential_gains(current_price, ath_price)

                    # Display the metrics
                    st.write(f"**Token Name**: {token_name}")
                    st.write(f"**Market Cap Rank**: {market_cap_rank}")
                    st.write(f"**Current Price**: ${current_price}")
                    st.write(f"**All-Time High (ATH)**: ${ath_price}")
                    st.write(f"**Potential Gains (x)**: {potential_gains:.2f}")
                    st.write(f"**7-Day Price Change (%)**: {price_change_7d:.2f}%")
                    st.write(f"**30-Day Price Change (%)**: {price_change_30d:.2f}%")
                    st.write(f"**Market Cap**: ${market_cap}")
                    st.write(f"**Circulating Supply**: {circulating_supply}")
                    st.write(f"**Market Cap/Volume Ratio**: {mc_vol_ratio:.2f}")
                    st.write(f"**Price-to-Sales Ratio (MC/Volume)**: {price_to_sales:.2f} (Lower is better)")

                    # Add insights based on metrics
                    if potential_gains > 2:
                        st.write("### Insight: This token has significant upside potential based on the ATH.")

                    if price_to_sales < 1:
                        st.write("### Insight: The price-to-sales ratio suggests this token may be undervalued relative to its trading volume.")

                    if price_change_30d < -20:
                        st.write("### Insight: This token has seen a significant drop in the last 30 days, which could present a buying opportunity.")
                else:
                    st.warning(f"No data found for the symbol: {symbol}")
            else:
                st.warning(f"Symbol '{symbol}' not found in the coin list.")
                
if __name__ == "__main__":
    main()
