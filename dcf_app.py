
import streamlit as st
import json
import numpy as np
import pandas as pd
from fpdf import FPDF
import io

def generate_pdf(fair_value_per_share, market_price, upside, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="DCF Valuation Report", ln=True, align='C')
    pdf.cell(200, 10, txt="Proprietary Solution - Valuation Buddy", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Professional valuations with your assumptions, not black-box guesses.", ln=True)
    
    pdf.ln(10)

    pdf.cell(200, 10, txt=f"Fair Value per Share (Rs.): {fair_value_per_share:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Current Market Price (Rs.): {market_price}", ln=True)
    pdf.cell(200, 10, txt=f"Upside/Downside: {upside:.2f}%", ln=True)

    pdf.ln(10)

    # Add dataframe table rows
    pdf.cell(0, 10, txt="DCF Forecasts:", ln=True)
    for index, row in df.iterrows():
        pdf.cell(0, 10, txt=f"{row['Year']} | FCF: {row['FCF (Rs. crores)']:.2f} | Discounted: {row['Discounted FCF (Rs. crores)']:.2f}", ln=True)

    # ------------------------------
    # Generate PDF as binary data
    # ------------------------------
    pdf_output = pdf.output(dest='S').encode('latin-1')  # 'S' returns as string, then encode

    return io.BytesIO(pdf_output)




st.set_page_config(
    page_title="DCF Valuation Calculator | ValuationBuddy",
    page_icon="💹",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ✅ Professional header
st.title("💹 Free Intrinsic Valuation Calculator for Stocks")
st.markdown(
    """  
    Smart valuations for smarter investing decisions.


    """
)
st.markdown("##### *Professional valuations with your assumptions, not black-box guesses.*")
st.markdown("---")

# ------------------------------
# 📥 File Upload
# ------------------------------
st.subheader("Upload Company Financials JSON")
uploaded_file = st.file_uploader("Upload company financials JSON file", type="json")

# Sample download link (below uploader)
st.markdown(
    """
    📁 [Download Sample JSON File](https://raw.githubusercontent.com/Sayan92L/dcf-streamlit-app/main/sample_financials.json)
    """
)

if uploaded_file is not None:
    stock_info = json.load(uploaded_file)  # Direct dict structure

    # ------------------------------
    # Extract Market Price
    # ------------------------------
    current_price_section = stock_info.get('currentPrice', {})
    market_price = float(current_price_section.get('NSE', '0').replace(',', ''))

    # ------------------------------
    # Extract Free Cash Flow
    # ------------------------------
    key_metrics = stock_info.get('keyMetrics', {})
    financial_strength = key_metrics.get('financialstrength', [])

    free_cash_flow = next(
        (float(metric.get('value', '0').replace(',', ''))
         for metric in financial_strength
         if metric.get('key') == 'freeCashFlowMostRecentFiscalYear'),
        0
    )

    # ------------------------------
    # Calculate Shares Outstanding
    # ------------------------------
    market_cap = float(stock_info.get('stockDetailsReusableData', {}).get('marketCap', '0').replace(',', ''))

    shares_outstanding = (market_cap * 1e7 / market_price) if market_price > 0 else 0

    # ------------------------------
    # Display Inputs
    # ------------------------------
    st.write(f"✅ Free Cash Flow (Rs. crores): {free_cash_flow}")
    st.write(f"✅ Current Market Price (Rs.): {market_price}")
    st.write(f"✅ Market Cap (Rs. crores): {market_cap}")
    st.write(f"✅ Shares Outstanding (crores): {shares_outstanding:.2f}")

    # ------------------------------
    # DCF Assumptions – User Editable
    # ------------------------------
    st.subheader("DCF Assumptions")
    fcf_growth_rate = st.number_input("FCF Growth Rate (%)", value=15.0) / 100
    terminal_growth_rate = st.number_input("Terminal Growth Rate (%)", value=4.0) / 100
    discount_rate = st.number_input("Discount Rate (%)", value=12.0) / 100
    forecast_years = st.number_input("Forecast Period (Years)", value=5, min_value=1, max_value=10, step=1)

    # ------------------------------
    # Forecast FCFs & Calculate DCF
    # ------------------------------
    fcf_forecast = [free_cash_flow * ((1 + fcf_growth_rate) ** year) for year in range(1, forecast_years + 1)]

    terminal_value = fcf_forecast[-1] * (1 + terminal_growth_rate) / (discount_rate - terminal_growth_rate)

    discounted_fcf = [fcf / ((1 + discount_rate) ** (i + 1)) for i, fcf in enumerate(fcf_forecast)]

    discounted_terminal_value = terminal_value / ((1 + discount_rate) ** forecast_years)

    enterprise_value = sum(discounted_fcf) + discounted_terminal_value
    equity_value = enterprise_value

    # ------------------------------
    # Calculate Fair Value per Share Safely
    # ------------------------------
    fair_value_per_share = (equity_value * 1e7) / shares_outstanding if shares_outstanding > 0 else 0

    # ------------------------------
    # Upside/Downside Calculation
    # ------------------------------
    if market_price > 0:
        upside = ((fair_value_per_share - market_price) / market_price) * 100
    else:
        upside = 0

    # ------------------------------
    # Display Outputs
    # ------------------------------
    df = pd.DataFrame({
        'Year': [f'Year {i+1}' for i in range(forecast_years)] + ['Terminal'],
        'FCF (Rs. crores)': fcf_forecast + [terminal_value],
        'Discounted FCF (Rs. crores)': discounted_fcf + [discounted_terminal_value]
    })

    st.subheader("✅ Discounted Cash Flow Model")
    st.dataframe(df.round(2))

    st.markdown(f"### **Enterprise Value (INR crores): {enterprise_value:,.2f}**")
    st.markdown(f"### **Fair Value per Share (INR): {fair_value_per_share:.2f}**")
    st.markdown(f"### **Current Market Price (INR): {market_price}**")
    st.markdown(f"### **Upside/Downside: {upside:.2f}%**")

    st.markdown("---")
    st.markdown("💡 **Note:** This is a simplified public tool. For detailed valuations, [Contact ValuationBuddy](mailto:valuationbuddy@gmail.com).")
    # PDF download button
    pdf_file = generate_pdf(fair_value_per_share, market_price, upside, df)

    st.download_button(
        label="Download PDF Report",
        data=pdf_file,
        file_name="DCF_Valuation_Report.pdf",
        mime="application/pdf"
    )
else:
    st.info("Please upload a JSON file to proceed.")


st.markdown("---")
st.markdown(
    """
    💼 **Connect for valuation consulting, collaborations, or queries:**  
    📧 [valuationbuddy@gmail.com](mailto:valuationbuddy@gmail.com)  
    (**This is a proprietary valuation solution developed by a CFA & FRM Charterholder.**)
    
    _For educational and informational purposes only_
    """
)