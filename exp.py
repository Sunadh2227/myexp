import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="💸 Expense Tracker", layout="centered")

# Constants
CSV_FILE = "expenses.csv"
CATEGORIES = ["Food", "Entertainment", "Medical", "Shopping", "Groceries", "Travel"]
PEOPLE = ["He", "She"]

# Load or create data
def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        return df
    else:
        return pd.DataFrame(columns=["Amount", "Type", "Person", "Timestamp"])

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# Add new entry
def add_expense(df, amount, category, person):
    new_row = pd.DataFrame({
        "Amount": [amount],
        "Type": [category],
        "Person": [person],
        "Timestamp": [datetime.now()]
    })
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    return df

# Update existing entry
def update_expense(df, idx, amount, category, person):
    df.at[idx, "Amount"] = amount
    df.at[idx, "Type"] = category
    df.at[idx, "Person"] = person
    save_data(df)
    return df

# Delete entry
def delete_expense(df, idx):
    df = df.drop(idx).reset_index(drop=True)
    save_data(df)
    return df

# Clear all entries
def clear_all():
    empty_df = pd.DataFrame(columns=["Amount", "Type", "Person", "Timestamp"])
    save_data(empty_df)
    return empty_df

# Main app
def main():
    st.title("💸 Expense Tracker")

    df = load_data()

    # 1. Add new expense
    with st.expander("➕ Add New Expense", expanded=True):
        with st.form("add_form"):
            amount = st.text_input("Amount (₹)", placeholder="Enter amount")
            category = st.selectbox("Select Expense Type", [""] + CATEGORIES)
            person = st.selectbox("Select Person", [""] + PEOPLE)
            submitted = st.form_submit_button("Add Expense")

            if submitted:
                if not category or not person:
                    st.warning("Please select both Type and Person.")
                else:
                    df = add_expense(df, amount, category, person)
                    st.success(f"Added ₹{amount:.2f} for {category} by {person}.")
                    st.experimental_rerun()

    if df.empty:
        st.info("No expenses recorded yet.")
        return

    # 2. Show summary metrics
    total_spent = df["Amount"].sum()
    today = pd.Timestamp.now().normalize()
    month = today.month
    year = today.year

    spent_today = df[df["Timestamp"].dt.normalize() == today]["Amount"].sum()
    spent_month = df[(df["Timestamp"].dt.month == month) & (df["Timestamp"].dt.year == year)]["Amount"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("🧾 Total Spent", f"₹{total_spent:.2f}")
    col2.metric("📅 Today", f"₹{spent_today:.2f}")
    col3.metric("🗓️ This Month", f"₹{spent_month:.2f}")

    # 3. Expense history with edit/delete
    st.subheader("📜 Expense History")

    # Show dataframe without index and in descending order (newest first)
    display_df = df.sort_values(by="Timestamp", ascending=False).reset_index(drop=True)
    display_df["Timestamp"] = display_df["Timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(display_df, use_container_width=True)

    # Select entry to edit or delete
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
        original_idx = df.index[df["Timestamp"] == pd.to_datetime(selected_row["Timestamp"])][0]

        with st.form("edit_form"):
            new_amount = st.number_input("Edit Amount (₹)", min_value=0.01, format="%.2f", value=float(selected_row["Amount"]))
            new_category = st.selectbox("Edit Type", CATEGORIES, index=CATEGORIES.index(selected_row["Type"]) if selected_row["Type"] in CATEGORIES else 0)
            new_person = st.selectbox("Edit Person", PEOPLE, index=PEOPLE.index(selected_row["Person"]) if selected_row["Person"] in PEOPLE else 0)

            col1, col2 = st.columns([1,1])
            update_btn = col1.form_submit_button("Update Entry")
            delete_btn = col2.form_submit_button("Delete Entry", help="Warning: This will delete the entry!")

            if update_btn:
                df = update_expense(df, original_idx, new_amount, new_category, new_person)
                st.success("Entry updated successfully!")
                st.experimental_rerun()

            if delete_btn:
                df = delete_expense(df, original_idx)
                st.success("Entry deleted successfully!")
                st.experimental_rerun()

    # 4. Clear all history
    st.markdown("---")
    st.subheader("🧹 Clear All History")
    confirm = st.checkbox("I confirm to clear all expense history")

    if confirm:
        if st.button("Clear History"):
            df = clear_all()
            st.success("All expense history cleared!")
            st.experimental_rerun()

if __name__ == "__main__":
    main()
