import streamlit as st
import pandas as pd
import datetime
import os
import random
import string

# File paths
data_file = 'data/finance_data.csv'
categories_file = 'data/categories.csv'
fixed_file = 'data/fixed_transactions.csv'

# Load data
def load_data(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    else:
        return pd.DataFrame(columns=columns)

# Save data
def save_data(df, file):
    df.to_csv(file, index=False)

# Initialize data
df = load_data(data_file, ['Type', 'Amount', 'Date', 'Description', 'Category', 'Fixed'])
categories = load_data(categories_file, ['Category', 'Type'])
fixed_transactions = load_data(fixed_file, ['Type', 'Amount', 'Description', 'Category', 'Start Date', 'End Date', 'Frequency'])

# Function to generate random confirmation word
def generate_confirmation_word():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# Function to add fixed transactions
def add_fixed_transactions():
    global df
    today = pd.Timestamp(datetime.date.today())
    
    for index, row in fixed_transactions.iterrows():
        start_date = pd.Timestamp(row['Start Date'])
        end_date = row['End Date'] 
        if end_date is not None:
            end_date = pd.Timestamp(end_date)
        frequency = row['Frequency']

        while start_date <= today and (end_date is None or start_date <= end_date):
            if start_date not in df['Date'].values:
                new_entry = pd.DataFrame({
                    'Type': [row['Type']],
                    'Amount': [row['Amount']],
                    'Date': [start_date.date()],  # Ensure start_date is a date object
                    'Description': [row['Description']],
                    'Category': [row['Category']],
                    'Fixed': [True]
                })
                df = pd.concat([df, new_entry], ignore_index=True)

            # Increment start_date based on frequency
            if frequency == "Daily":
                start_date += pd.DateOffset(days=1)
            elif frequency == "Weekly":
                start_date += pd.DateOffset(weeks=1)
            elif frequency == "Monthly":
                start_date += pd.DateOffset(months=1)
            elif frequency == "Yearly":
                start_date += pd.DateOffset(years=1)

    save_data(df, data_file)

# Function to reset data
def reset_data():
    st.sidebar.subheader("Reset Data")
    if st.sidebar.button("Reset Data"):
        confirmation_word = generate_confirmation_word()
        user_input = st.sidebar.text_input("Type the following word to confirm: {}".format(confirmation_word))

        if user_input == confirmation_word:
            # Reset all data
            try:
                os.remove(data_file)
                st.write(f"{data_file} has been removed successfully.")
            except FileNotFoundError:
                st.sidebar.warning(f"{data_file} does not exist.")
            except Exception as e:
                st.sidebar.warning(f"An error occurred: {e}")
            #df = pd.DataFrame(columns=['Type', 'Amount', 'Date', 'Description', 'Category', 'Fixed'])
            #save_data(df, data_file)
            st.sidebar.success("Data reset successfully!")
        else:
            st.sidebar.warning("Confirmation word incorrect. Data not reset.")

# Call the function to add fixed transactions
add_fixed_transactions()

# Call the function to reset data
#reset_data()

# Tabs for navigation
tab = st.sidebar.radio("Go to", ["Dashboard", "Manage Categories", "Manage Fixed Transactions","View or Add Records"], key="tab")

if tab == "Dashboard":
    st.title("Finance Dashboard")
    
    # Month and year selectors
    month_selector = st.sidebar.selectbox("Month", ["Select a Month","January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
    year_selector = st.sidebar.slider("Year", 2020, 2030, datetime.date.today().year)  # default to current year
    
    # Calculate current month income and expense
    transactions = df.copy()  # Create a copy of df to avoid modifying the original dataframe
    transactions['Date'] = pd.to_datetime(transactions['Date'])
    if month_selector == 'Select a Month':
        current_month = datetime.datetime.strptime(datetime.date.today().strftime("%B"), "%B").month
        month_in_string = datetime.date.today().strftime("%B")
    else:
        current_month = datetime.datetime.strptime(month_selector, "%B").month
        month_in_string = month_selector
    
    current_year = year_selector
    current_month_income = transactions[(transactions['Date'].dt.month == current_month) & (transactions['Date'].dt.year == current_year) & (transactions['Type'] == 'Income')]['Amount'].sum()
    current_month_expense = transactions[(transactions['Date'].dt.month == current_month) & (transactions['Date'].dt.year == current_year) & (transactions['Type'] == 'Expense')]['Amount'].sum()
    
    # Calculate last month income and expense
    last_month = ((current_month - 1) % 12 +1) -1
    #st.write("last_month",last_month)
    last_month_year = current_year - 1 if last_month == 12 else current_year
    #st.write("last_month_year",last_month_year)
    last_month_income = transactions[(transactions['Date'].dt.month == last_month) & (transactions['Date'].dt.year == last_month_year) & (transactions['Type'] == 'Income')]['Amount'].sum()
    #st.write("last_month_income",last_month_income)
    last_month_expense = transactions[(transactions['Date'].dt.month == last_month) & (transactions['Date'].dt.year == last_month_year) & (transactions['Type'] == 'Expense')]['Amount'].sum()
    #st.write("last_month_expense",last_month_expense)

   # Calculate percentage change from last month
    if last_month_income != 0:
        income_change = ((current_month_income - last_month_income) / last_month_income) * 100
    else:
        income_change = 0

    if last_month_expense != 0:
        expense_change = ((current_month_expense - last_month_expense) / last_month_expense) * 100
        
    else:
        expense_change = 0

    # Calculate total income and expense
    total_income = transactions[transactions['Type'] == 'Income']['Amount'].sum()
    total_expense = transactions[transactions['Type'] == 'Expense']['Amount'].sum()

    # Create KPIs
    st.header(f"KPIs for {month_in_string}")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Month Income",f"₹{current_month_income:.2f}",f"{income_change:.2f}%" if income_change >= 0 else f"-{abs(income_change):.2f}%",delta_color="normal")  # Shows green for positive, red for negative)
    with col2:
        st.metric("Current Month Expense",f"₹{current_month_expense:.2f}",f"{expense_change:.2f}%" if expense_change > 0 else f"-{abs(expense_change):.2f}%",delta_color="inverse")
    with col3:
        st.metric("Total Income", f"₹{total_income:.2f}")
    with col4:
        st.metric("Total Expense", f"₹{total_expense:.2f}")
    
    

elif tab == "View or Add Records":
    st.title("Finance Dashboard")
    transaction_type = st.sidebar.radio("Type", ["Expense", "Income"], key="transaction_type")
    filtered_categories = categories[categories['Type'] == transaction_type]['Category'].tolist()
    category = st.sidebar.selectbox("Category", ["Select a category"] + filtered_categories, key="category")
    amount = st.sidebar.number_input("Amount", min_value=0.0, format="%.2f", key="amount",step=1.0)
    date = st.sidebar.date_input("Date", datetime.date.today(), key="date")
    #date = datetime.date(st.sidebar.date_input("Date", datetime.date.today()).year, st.sidebar.date_input("Date", datetime.date.today()).month, st.sidebar.date_input("Date", datetime.date.today()).day, key="date")
    description = st.sidebar.text_input("Description", key="description")
    if st.sidebar.button("Add Entry", key="add_entry"):
        if amount == 0:
            st.sidebar.warning("Amount must be greater than 0.")
        elif category == "Select a category":
            st.sidebar.warning("Please select a category.")
        else:
            new_entry = pd.DataFrame({
                'Type': [transaction_type],
                'Amount': [amount],
                'Date': [date],
                'Description': [description],
                'Category': [category],
                'Fixed': [False]
            })
            df = pd.concat([df, new_entry], ignore_index=True)
            save_data(df, data_file)
            st.sidebar.success("Entry added successfully!")
    st.write("### Current Data")
    st.dataframe(df,use_container_width=True)
elif tab == "Manage Categories":
    st.title("Manage Categories")
    new_category = st.text_input("Add new category", key="new_category")
    category_type = st.selectbox("Category Type", ["Expense", "Income"], key="category_type")

    if st.button("Add Category", key="add_category"):
        if new_category and new_category not in categories['Category'].values:
            new_cat_entry = pd.DataFrame({'Category': [new_category], 'Type': [category_type]})
            categories = pd.concat([categories, new_cat_entry], ignore_index=True)
            save_data(categories, categories_file)
            st.success("Category added successfully!")
        elif new_category in categories['Category'].values:
            st.warning("Category already exists.")

    if st.button("Delete Selected Categories", key="delete_categories"):
        selected_categories = st.multiselect("Select categories to delete", categories['Category'].tolist(), key="selected_categories")
        categories = categories[~categories['Category'].isin(selected_categories)]  # Use boolean indexing to delete rows
        save_data(categories, categories_file)
        st.success("Selected categories deleted successfully.")

    st.write("### Current Categories")
    st.dataframe(categories)

elif tab == "Manage Fixed Transactions":
    st.title("Manage Fixed Income/Expenses")
    fixed_type = st.selectbox("Type", ["Expense", "Income"], key="fixed_type")
    fixed_category = st.selectbox("Category", categories[categories['Type'] == fixed_type]['Category'].tolist(), key="fixed_category")
    fixed_amount = st.number_input("Amount", min_value=0.0, format="%.2f", key="fixed_amount")
    fixed_description = st.text_input("Description", key="fixed_description")
    start_date = st.date_input("Start Date", datetime.date.today(), key="start_date")
    end_date = st.date_input("End Date (Optional)", key="end_date")
    frequency = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly", "Yearly"], key="frequency")

    if st.button("Add Fixed Transaction", key="add_fixed"):
        if fixed_amount == 0:
            st.warning("Amount must be greater than 0.")
        elif not fixed_category:
            st.warning("Please select a category.")
        else:
            new_fixed_entry = pd.DataFrame({
                'Type': [fixed_type],
                'Amount': [fixed_amount],
                'Description': [fixed_description],
                'Category': [fixed_category],
                'Start Date': [start_date],
                'End Date': [end_date] if end_date else [None],
                'Frequency': [frequency]
            })
            fixed_transactions = pd.concat([fixed_transactions, new_fixed_entry], ignore_index=True)
            save_data(fixed_transactions, fixed_file)
            st.success("Fixed transaction added successfully!")

    if st.button("Delete Selected Fixed Transactions", key="delete_fixed"):
        selected_fixed = st.multiselect("Select transactions to delete", fixed_transactions['Description'].tolist(), key="selected_fixed")
        fixed_transactions.drop(fixed_transactions[fixed_transactions['Description'].isin(selected_fixed)].index, inplace=True)
        save_data(fixed_transactions, fixed_file)
        st.success("Selected transactions deleted successfully.")

    st.write("### Current Fixed Transactions")
    st.dataframe(fixed_transactions)
