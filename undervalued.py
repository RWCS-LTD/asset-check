import requests
import streamlit as st
import time

# Function to make an API call with retry on rate limit (429 error)
def make_api_call(url, params=None, retries=5, wait_time=60):
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params)
            if response.status_code == 429:  # Too many requests
                st.warning(f"Rate limit hit, retrying in {wait_time} seconds...")
                time.sleep(wait_time)  # Wait before retrying
            else:
                response.raise_for_status()  # Raise other HTTP errors
                return response.json()  # Return the JSON response
        except requests.RequestException as e:
            st.error(f"API error: {e}")
            return None
    st.error(f"Failed after {retries} attempts.")
    return None

# Function to get all coins' IDs and symbols from CoinGecko
def get_coin_list():
    url = "https://api.coingecko.com/api/v3/coins/list"
    return make_api_call(url)

# Function to get the Coin ID by symbol and offer choices if multiple matches
def get_coin_id_by_symbol(symbol, coin_list):
    if not coin_list:
        return None, None  # Return early if coin_list is empty
    matches = [coin for coin in coin_list if coin['symbol'].lower() == symbol.lower()]
    if len(matches) == 1:
        return matches[0]['id'], matches[0]['name']  # Return the CoinGecko ID and Name
    elif len(matches) > 1:
        st.write("Multiple matches found. Please select the correct token:")
        for i, match in enumerate(matches):
            st.write(f"{i+1}. {match['name']} (ID: {match['id']})")
        selection = st.number_input("Enter the number corresponding to your choice", min_value=1, max_value=len(matches))
        return matches[int(selection)-1]['id'], matches[int(selection)-1]['name']
    else:
        st.error(f"No matches found for symbol: {symbol}")
        return None, None

# Function to get token data from CoinGecko by coin ID
def get_token_by_id(coin_id):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": coin_id,  # Use CoinGecko ID here
        "price_change_percentage": "7d,30d"  # Fetch 7-day and 30-day price change
    }
    return make_api_call(url, params)

# Function to calculate potential gains (e.g., x2, x5, etc.)
def calculate_potential_gains(current_price, ath_price):
    if current_price > 0:
        return ath_price / current_price  # This calculates the potential gain as a multiple
    return 0  # Avoid division by zero

# Function to calculate ATH drawdown percentage
def calculate_ath_drawdown(current_price, ath_price):
    return ((ath_price - current_price) / ath_price) * 100 if ath_price > 0 else 0

# Main Streamlit app function
def main():
    st.title("Crypto Asset Metrics: Informed Decision-making")

    # Explanation for using CoinGecko ID with examples
    st.write("""
    **How to Use:**
    Enter the crypto **symbol** to find the corresponding CoinGecko ID.
    If multiple tokens with the same symbol exist, you will be asked to choose the correct one.
    
    Examples of commonly used symbols:
    - **Bitcoin**: `btc`
    - **Ethereum**: `eth`
    - **Cardano**: `ada`
    - **Dogecoin**: `doge`
    - **Solana**: `sol`
    """)

    # Input field to get the crypto symbol
    symbol = st.text_input("Enter the crypto symbol (e.g., btc, eth)", "").strip()

    if symbol:
        with st.spinner('Fetching data...'):
            # Fetch coin list to get the CoinGecko ID
            coin_list = get_coin_list()
            if coin_list:  # Proceed only if coin list is successfully fetched
                coin_id, token_name = get_coin_id_by_symbol(symbol, coin_list)

                if coin_id:
                    # Fetch the coin data using CoinGecko ID
                    token = get_token_by_id(coin_id)

                    if token:
                        token = token[0]  # Get the first token from the response list
                        current_price = token['current_price']
                        ath_price = token['ath']
                        volume = token['total_volume']
                        market_cap = token['market_cap']
                        price_change_7d = token.get('price_change_percentage_7d_in_currency', 0)
                        price_change_30d = token.get('price_change_percentage_30d_in_currency', 0)
                        market_cap_rank = token.get('market_cap_rank', 'N/A')
                        circulating_supply = token.get('circulating_supply', 'N/A')

                        # Calculate derived metrics
                        potential_gains = calculate_potential_gains(current_price, ath_price)
                        ath_drawdown = calculate_ath_drawdown(current_price, ath_price)
                        mc_vol_ratio = market_cap / volume if volume > 0 else 0

                        # Display the metrics
                        st.write(f"**Token Name**: {token_name}")
                        st.write(f"**Market Cap Rank**: {market_cap_rank}")
                        st.write(f"**Current Price**: ${current_price}")
                        st.write(f"**All-Time High (ATH)**: ${ath_price}")
                        st.write(f"**Potential Gains (x)**: {potential_gains:.2f}")
                        st.write(f"**ATH Drawdown (%)**: {ath_drawdown:.2f}%")
                        st.write(f"**7-Day Price Change (%)**: {price_change_7d:.2f}%")
                        st.write(f"**30-Day Price Change (%)**: {price_change_30d:.2f}%")
                        st.write(f"**Market Cap/Volume Ratio**: {mc_vol_ratio:.2f}")

                        # Add insights based on metrics
                        if potential_gains > 2:
                            st.write("### Insight: This token has significant upside potential based on the ATH.")

                        if mc_vol_ratio < 1:
                            st.write("### Insight: The market cap/volume ratio suggests this token may be undervalued relative to its trading volume.")

                        if price_change_30d < -20:
                            st.write("### Insight: This token has seen a significant drop in the last 30 days, which could present a buying opportunity.")
                    else:
                        st.warning(f"No data found for the CoinGecko ID: {coin_id}")
                else:
                    st.warning(f"Symbol '{symbol}' not found in the coin list.")
                
if __name__ == "__main__":
    main()
