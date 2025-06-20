import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="💸 Expense Tracker", layout="centered")

CSV_FILE = "expenses.csv"
CATEGORIES = ["Food", "Entertainment", "Medical", "Shopping", "Groceries", "Travel", "Other"]
PEOPLE = ["He", "She"]

# Rerun handler for compatibility
def rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# Password protection
def check_password():
    def password_entered():
        if st.session_state["password"] == "2227":
            st.session_state["authenticated"] = True
        else:
            st.session_state["authenticated"] = False
            st.error("😕 Incorrect password")
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        st.text_input("🔐 Enter password to access the tracker", type="password", key="password", on_change=password_entered)
        return False
    return True

# Load and save data
def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        return df
    return pd.DataFrame(columns=["Amount", "Type", "Person", "Description", "Timestamp"])

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# Data operations
def add_expense(df, amount, category, person, description, timestamp):
    new_row = pd.DataFrame({
        "Amount": [amount],
        "Type": [category],
        "Person": [person],
        "Description": [description],
        "Timestamp": [timestamp]
    })
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    return df

def update_expense(df, idx, amount, category, person, description, timestamp):
    df.at[idx, "Amount"] = amount
    df.at[idx, "Type"] = category
    df.at[idx, "Person"] = person
    df.at[idx, "Description"] = description
    df.at[idx, "Timestamp"] = timestamp
    save_data(df)
    return df

def delete_expense(df, idx):
    df = df.drop(idx).reset_index(drop=True)
    save_data(df)
    return df

def clear_all():
    empty_df = pd.DataFrame(columns=["Amount", "Type", "Person", "Description", "Timestamp"])
    save_data(empty_df)
    return empty_df

# Main app
def main():
    st.title("💸 Expense Tracker")
    if not check_password():
        return

    df = load_data()

    # ➕ Add new
    with st.expander("➕ Add New Expense", expanded=True):
        with st.form("add_form"):
            amount = st.text_input("Amount (₹)", placeholder="Enter amount")
            category = st.selectbox("Select Expense Type", [""] + CATEGORIES)
            if category == "Other":
                category = st.text_input("Enter Custom Type")

            person = st.selectbox("Select Person", [""] + PEOPLE)
            description = st.text_input("Description (optional)", placeholder="e.g. Uber to airport")
            date = st.date_input("Select Date", value=datetime.today())
            time = st.time_input("Select Time", value=datetime.now().time())
            timestamp = datetime.combine(date, time)

            submitted = st.form_submit_button("Add Expense")
            if submitted:
                if not category or not person:
                    st.warning("Please select both Type and Person.")
                else:
                    try:
                        amount = float(amount)
                        df = add_expense(df, amount, category, person, description, timestamp)
                        st.success(f"Added ₹{amount:.2f} for {category} by {person}.")
                        rerun()
                    except ValueError:
                        st.error("Please enter a valid numeric amount.")

    if df.empty:
        st.info("No expenses recorded yet.")
        return

    # 📊 Metrics
    total_spent = df["Amount"].sum()
    today = pd.Timestamp.now().normalize()
    spent_today = df[df["Timestamp"].dt.normalize() == today]["Amount"].sum()
    spent_month = df[(df["Timestamp"].dt.month == today.month) & (df["Timestamp"].dt.year == today.year)]["Amount"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("🧾 Total Spent", f"₹{total_spent:.2f}")
    col2.metric("📅 Today", f"₹{spent_today:.2f}")
    col3.metric("🗓️ This Month", f"₹{spent_month:.2f}")

    # 📜 History
    st.subheader("📜 Expense History")
    display_df = df.sort_values(by="Timestamp", ascending=False).reset_index()
    display_df["Timestamp"] = pd.to_datetime(display_df["Timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(display_df.drop(columns="index"), use_container_width=True)

    # ✏️ Edit/Delete
    st.markdown("---")
    st.subheader("✏️ Edit / Delete Entry")
    idx_options = display_df.index.tolist()
    selected_idx = st.selectbox(
        "Select an entry to edit or delete:",
        options=idx_options,
        format_func=lambda x: f"₹{display_df.at[x, 'Amount']} - {display_df.at[x, 'Type']} by {display_df.at[x, 'Person']} on {display_df.at[x, 'Timestamp']}"
    )

    if selected_idx is not None:
        selected_row = display_df.loc[selected_idx]
        original_idx = display_df.at[selected_idx, "index"]

        with st.form("edit_form"):
            new_amount = st.number_input("Edit Amount (₹)", min_value=0.01, format="%.2f", value=float(selected_row["Amount"]))
            new_category = st.selectbox("Edit Type", CATEGORIES, index=CATEGORIES.index(selected_row["Type"]) if selected_row["Type"] in CATEGORIES else 0)
            if new_category == "Other":
                new_category = st.text_input("Enter Custom Type", value=selected_row["Type"])

            new_person = st.selectbox("Edit Person", PEOPLE, index=PEOPLE.index(selected_row["Person"]) if selected_row["Person"] in PEOPLE else 0)
            new_description = st.text_input("Edit Description", value=selected_row.get("Description", ""))
            old_datetime = pd.to_datetime(selected_row["Timestamp"])
            new_date = st.date_input("Edit Date", value=old_datetime.date())
            new_time = st.time_input("Edit Time", value=old_datetime.time())
            new_timestamp = datetime.combine(new_date, new_time)

            col1, col2 = st.columns([1, 1])
            update_btn = col1.form_submit_button("Update Entry")
            delete_btn = col2.form_submit_button("Delete Entry", help="Warning: This will delete the entry!")

            if update_btn:
                df = update_expense(df, original_idx, new_amount, new_category, new_person, new_description, new_timestamp)
                st.success("Entry updated successfully!")
                rerun()

            if delete_btn:
                df = delete_expense(df, original_idx)
                st.success("Entry deleted successfully!")
                rerun()

    # 🧹 Clear All
    st.markdown("---")
    st.subheader("🧹 Clear All History")
    confirm = st.checkbox("I confirm to clear all expense history")
    if confirm:
        if st.button("Clear History"):
            df = clear_all()
            st.success("All expense history cleared!")
            rerun()

if __name__ == "__main__":
    main()
