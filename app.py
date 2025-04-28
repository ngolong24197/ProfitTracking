import streamlit as st
import pandas as pd
import os
import datetime

# --- Constants ---
DATA_FILE = "room_data.csv"
PAYMENTS_FILE = "payments_data.csv"

# --- Functions ---
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["Start Date", "End Date", "Due Date"])
    else:
        df = pd.DataFrame({
            "Room": [f"Room {i+1}" for i in range(5)],
            "Tenant Name": [""] * 5,
            "Contact Info": [""] * 5,
            "Rent Price": [0] * 5,
            "Amount Paid": [0] * 5,
            "Contract Term": ["1 month"] * 5,
            "Start Date": [pd.Timestamp.today()] * 5,
            "End Date": [pd.Timestamp.today()] * 5,
            "Due Date": [pd.Timestamp.today()] * 5,
            "Notes": [""] * 5,
        })
        df.to_csv(DATA_FILE, index=False)
        return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def load_payments():
    if os.path.exists(PAYMENTS_FILE):
        return pd.read_csv(PAYMENTS_FILE, parse_dates=["Payment Date"])
    else:
        df = pd.DataFrame(columns=["Room", "Payment Date", "Amount Paid", "Months Paid"])
        df.to_csv(PAYMENTS_FILE, index=False)
        return df

def save_payments(df):
    df.to_csv(PAYMENTS_FILE, index=False)

def format_money(x):
    try:
        return f"{x:,.0f}"
    except:
        return x

# --- Main App ---
st.set_page_config(page_title="Apartment Room Tracker", layout="wide")
st.title("🏢 Apartment Room Rental Tracker")

# Load data
df = load_data()
payments_df = load_payments()

tabs = st.tabs(["🏠 Room Information", "💰 Room Payment & Profit"])

# --- Tab 1: Room Information ---
with tabs[0]:
    st.header("📋 Current Room Status")

    def highlight_due(row):
        if row["Amount Paid"] < row["Rent Price"]:
            return ['background-color: #ffcccc'] * len(row)
        else:
            return ['background-color: #ccffcc'] * len(row)

    df_display = df.copy()
    for col in ["Start Date", "End Date", "Due Date"]:
        df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.strftime("%d-%m-%Y")

    money_cols = ["Rent Price", "Amount Paid"]
    for col in money_cols:
        df_display[col] = df_display[col].apply(format_money)

    st.dataframe(df_display.style.apply(highlight_due, axis=1), use_container_width=True)

    st.markdown("---")

    st.header("✏️ Update Room Info")

    with st.form("edit_form"):
        selected_room = st.selectbox("Select Room", df["Room"])
        room_data = df[df["Room"] == selected_room].iloc[0]

        tenant_name = st.text_input("Tenant Name", value=room_data["Tenant Name"])
        contact_info = st.text_input("Contact Info", value=room_data["Contact Info"])
        rent_price = st.number_input("Rent Price", value=float(room_data["Rent Price"]), min_value=0.0)
        amount_paid = st.number_input("Amount Paid", value=float(room_data["Amount Paid"]), min_value=0.0)
        contract_options = ["1 month", "3 months", "6 months", "1 year"]
        contract_term = st.selectbox(
            "Contract Term",
            contract_options,
            index=contract_options.index(room_data["Contract Term"]) if room_data["Contract Term"] in contract_options else 0
        )
        start_date = st.date_input("Start Date", value=pd.to_datetime(room_data["Start Date"]).date())
        end_date = st.date_input("End Date", value=pd.to_datetime(room_data["End Date"]).date())
        due_date = st.date_input("Due Date", value=pd.to_datetime(room_data["Due Date"]).date())
        notes = st.text_area("Notes", value=room_data["Notes"])

        submitted = st.form_submit_button("💾 Save Changes")

    if submitted:
        idx = df[df["Room"] == selected_room].index[0]
        df.at[idx, "Tenant Name"] = tenant_name
        df.at[idx, "Contact Info"] = contact_info
        df.at[idx, "Rent Price"] = rent_price
        df.at[idx, "Amount Paid"] = amount_paid
        df.at[idx, "Contract Term"] = contract_term
        df.at[idx, "Start Date"] = pd.Timestamp(start_date)
        df.at[idx, "End Date"] = pd.Timestamp(end_date)
        df.at[idx, "Due Date"] = pd.Timestamp(due_date)
        df.at[idx, "Notes"] = notes

        save_data(df)
        st.success(f"Room '{selected_room}' updated successfully!")

# --- Tab 2: Room Payment & Profit ---
with tabs[1]:
    st.header("💰 Add Payment")

    with st.form("payment_form"):
        payment_room = st.selectbox("Select Room for Payment", df["Room"], key="payment_room")
        payment_date = st.date_input("Payment Date", value=pd.Timestamp.today().date(), key="payment_date")
        payment_amount = st.number_input("Payment Amount", min_value=0.0, format="%.2f", key="payment_amount")
        months_paid = st.number_input("Months Paid", min_value=1, max_value=24, step=1, value=1, key="months_paid")

        payment_submitted = st.form_submit_button("Add Payment")

    if payment_submitted:
        new_payment = {
            "Room": payment_room,
            "Payment Date": pd.Timestamp(payment_date),
            "Amount Paid": payment_amount,
            "Months Paid": months_paid,
        }
        payments_df = pd.concat([payments_df, pd.DataFrame([new_payment])], ignore_index=True)
        save_payments(payments_df)
        st.success(f"Payment added for {payment_room}!")
        
        # Update total Amount Paid in main df
        idx = df[df["Room"] == payment_room].index[0]
        df.at[idx, "Amount Paid"] += payment_amount
        
        # Update Due Date by adding months_paid months to current Due Date
        current_due_date = pd.to_datetime(df.at[idx, "Due Date"])
        if isinstance(payment_date, datetime.date) and not isinstance(payment_date, datetime.datetime):
            payment_date = pd.Timestamp(payment_date)
        new_due_date = current_due_date + pd.DateOffset(months=int(months_paid))
        df.at[idx, "Due Date"] = new_due_date
        
        save_data(df)

    st.markdown("---")

    st.header("📅 Payment History")

    selected_room_for_history = st.selectbox("Select Room to View Payment History", df["Room"], key="history_room")

    room_payments = payments_df[payments_df["Room"] == selected_room_for_history].sort_values(by="Payment Date", ascending=False)

    if room_payments.empty:
        st.info("No payment records found for this room.")
    else:
        room_payments_display = room_payments.copy()
        room_payments_display["Payment Date"] = pd.to_datetime(room_payments_display["Payment Date"], errors='coerce').dt.strftime("%d-%m-%Y")
        room_payments_display["Amount Paid"] = room_payments_display["Amount Paid"].apply(format_money)
        st.dataframe(room_payments_display[["Payment Date", "Amount Paid", "Months Paid"]], use_container_width=True)

    st.markdown("---")

    st.header("📊 Monthly Profit Summary")

    if payments_df.empty:
        st.info("No payment data available to calculate profit.")
    else:
        payments_df['Payment Date'] = pd.to_datetime(payments_df['Payment Date'], errors='coerce')
        payments_df['Monthly Profit'] = payments_df['Amount Paid'] / payments_df['Months Paid']
        payments_df['Year-Month'] = payments_df['Payment Date'].dt.to_period('M').astype(str)
        monthly_profit = payments_df.groupby('Year-Month')['Monthly Profit'].sum().reset_index()
        
        # Format monthly profit with commas
        monthly_profit["Monthly Profit"] = monthly_profit["Monthly Profit"].apply(format_money)
        
        st.subheader("Monthly Profit (VND)")
        st.dataframe(monthly_profit, use_container_width=True)
        
        # Use original numeric data for bar chart (no formatting)
        monthly_profit_numeric = payments_df.groupby('Year-Month')['Monthly Profit'].sum()
        st.bar_chart(data=monthly_profit_numeric)

    st.markdown("---")

    st.header("💵 Total Profit per Room")

    if payments_df.empty:
        st.info("No payment data available to calculate total profit.")
    else:
        total_profit_per_room = payments_df.groupby('Room')['Amount Paid'].sum().reset_index()
        total_profit_per_room = total_profit_per_room.rename(columns={"Amount Paid": "Total Amount Paid (VND)"})
        
        # Format total amount paid with commas
        total_profit_per_room["Total Amount Paid (VND)"] = total_profit_per_room["Total Amount Paid (VND)"].apply(format_money)
        
        st.dataframe(total_profit_per_room, use_container_width=True)
