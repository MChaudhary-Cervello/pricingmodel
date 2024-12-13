# File: app.py
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
from database_config import execute_query
from project_management import (
    create_project_management_page, 
    add_project_management_to_main_app
)

# ... (keep existing functions from previous implementation)

@add_project_management_to_main_app
def main():
    st.title('Consulting Pricing Model Dashboard')
    
    # Sidebar for navigation
    menu = st.sidebar.selectbox('Menu', [
        'Project Overview', 
        'Consultant Rates', 
        'Project Staffing', 
        'Currency Analysis',
        'Project Management'
    ])
    
    if menu == 'Project Overview':
        project_overview()
    elif menu == 'Consultant Rates':
        consultant_rates()
    elif menu == 'Project Staffing':
        project_staffing()
    elif menu == 'Currency Analysis':
        currency_analysis()
    elif menu == 'Project Management':
        create_project_management_page()

if __name__ == '__main__':
    main()
