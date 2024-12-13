# File: project_management.py
import streamlit as st
import pandas as pd
from database_config import get_snowflake_connection, execute_query

def create_project_management_page():
    st.header('Project Management')
    
    # Tabs for different project management actions
    tab1, tab2, tab3 = st.tabs([
        'Create New Project', 
        'Assign Project Roles', 
        'Update Project Roles'
    ])
    
    with tab1:
        create_new_project()
    
    with tab2:
        assign_project_roles()
    
    with tab3:
        update_project_roles()

def create_new_project():
    st.subheader('Create New Project')
    
    # Fetch templates
    templates_query = """
    SELECT template_id, template_name 
    FROM templates
    """
    templates_df = execute_query(templates_query)
    
    # Fetch currencies
    currencies_query = """
    SELECT currency_id, currency_name 
    FROM currency
    """
    currencies_df = execute_query(currencies_query)
    
    # Fetch epoch types
    epoch_query = """
    SELECT epoch_id, epoch_name 
    FROM epoch_type
    """
    epoch_df = execute_query(epoch_query)
    
    # Project creation form
    with st.form('new_project_form'):
        # Basic project details
        project_name = st.text_input('Project Name/Number')
        
        # Dropdown selections
        template = st.selectbox(
            'Select Project Template', 
            templates_df['template_name'].tolist()
        )
        currency = st.selectbox(
            'Select Currency', 
            currencies_df['currency_name'].tolist()
        )
        epoch_type = st.selectbox(
            'Select Epoch Type', 
            epoch_df['epoch_name'].tolist()
        )
        
        # Additional project parameters
        rate_variance = st.number_input(
            'Rate Variance', 
            min_value=0.0, 
            max_value=1.0, 
            step=0.01, 
            format='%f'
        )
        number_epochs = st.number_input(
            'Number of Epochs', 
            min_value=1, 
            max_value=4, 
            value=2
        )
        
        # Submit button
        submit_button = st.form_submit_button('Create Project')
        
        if submit_button:
            try:
                # Get IDs for foreign key references
                template_id = templates_df[templates_df['template_name'] == template]['template_id'].iloc[0]
                currency_id = currencies_df[currencies_df['currency_name'] == currency]['currency_id'].iloc[0]
                epoch_id = epoch_df[epoch_df['epoch_name'] == epoch_type]['epoch_id'].iloc[0]
                
                # Snowflake connection for insertion
                conn = get_snowflake_connection()
                cursor = conn.cursor()
                
                # Insert project
                insert_query = f"""
                INSERT INTO projects 
                (project_name, rate_variance, currency_id, status_id, 
                is_template, epoch_id, number_epochs)
                VALUES 
                ({project_name}, {rate_variance}, {currency_id}, 1, 
                FALSE, {epoch_id}, {number_epochs})
                RETURNING project_id;
                """
                
                # Execute and fetch the new project ID
                cursor.execute(insert_query)
                new_project_id = cursor.fetchone()[0]
                
                # Commit transaction
                conn.commit()
                
                st.success(f'Project created successfully! Project ID: {new_project_id}')
            
            except Exception as e:
                st.error(f'Error creating project: {e}')
            
            finally:
                # Close connection
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()

def assign_project_roles():
    st.subheader('Assign Project Roles')
    
    # Fetch active projects
    projects_query = """
    SELECT project_id, project_name 
    FROM projects 
    WHERE is_template = FALSE
    """
    projects_df = execute_query(projects_query)
    
    # Fetch available personnel
    personnel_query = """
    SELECT personnel_id, 
           first_name || ' ' || last_name AS full_name, 
           level_name
    FROM personnel p
    JOIN consultant_level cl ON p.consultant_level_id = cl.consultant_level_id
    WHERE p.is_active = TRUE
    """
    personnel_df = execute_query(personnel_query)
    
    # Fetch roles
    roles_query = """
    SELECT role_id, role_name 
    FROM roles
    """
    roles_df = execute_query(roles_query)
    
    # Role assignment form
    with st.form('role_assignment_form'):
        # Dropdown selections
        project = st.selectbox(
            'Select Project', 
            projects_df['project_name'].tolist()
        )
        personnel = st.selectbox(
            'Select Personnel', 
            personnel_df['full_name'].tolist()
        )
        role = st.selectbox(
            'Select Role', 
            roles_df['role_name'].tolist()
        )
        
        # Additional role details
        epoch_number = st.number_input(
            'Epoch Number', 
            min_value=1, 
            max_value=4, 
            value=1
        )
        epoch_percentage = st.number_input(
            'Epoch Percentage', 
            min_value=0.0, 
            max_value=100.0, 
            value=100.0, 
            step=1.0
        )
        
        # Submit button
        submit_button = st.form_submit_button('Assign Role')
        
        if submit_button:
            try:
                # Get IDs for foreign key references
                project_id = projects_df[projects_df['project_name'] == project]['project_id'].iloc[0]
                personnel_id = personnel_df[personnel_df['full_name'] == personnel]['personnel_id'].iloc[0]
                role_id = roles_df[roles_df['role_name'] == role]['role_id'].iloc[0]
                
                # Snowflake connection for insertion
                conn = get_snowflake_connection()
                cursor = conn.cursor()
                
                # Insert project role
                insert_query = f"""
                INSERT INTO projects_detail 
                (project_id, role_id, personnel_id, 
                epoch_number, epoch_value, epoch_percentage)
                VALUES 
                ({project_id}, {role_id}, {personnel_id}, 
                {epoch_number}, 1, {epoch_percentage})
                """
                
                # Execute insertion
                cursor.execute(insert_query)
                
                # Commit transaction
                conn.commit()
                
                st.success('Role assigned successfully!')
            
            except Exception as e:
                st.error(f'Error assigning role: {e}')
            
            finally:
                # Close connection
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()

def update_project_roles():
    st.subheader('Update Project Roles')
    
    # Fetch existing project roles
    project_roles_query = """
    SELECT 
        p.project_name,
        r.role_name,
        pe.first_name || ' ' || pe.last_name AS full_name,
        pd.epoch_number,
        pd.epoch_percentage,
        pd.project_role_mapping_id
    FROM projects_detail pd
    JOIN projects p ON pd.project_id = p.project_id
    JOIN roles r ON pd.role_id = r.role_id
    JOIN personnel pe ON pd.personnel_id = pe.personnel_id
    """
    project_roles_df = execute_query(project_roles_query)
    
    # Display existing roles
    st.dataframe(project_roles_df)
    
    # Role update form
    with st.form('update_role_form'):
        # Select role to update
        selected_role = st.selectbox(
            'Select Role to Update', 
            project_roles_df['project_role_mapping_id'].astype(str).tolist()
        )
        
        # New role details
        new_epoch_number = st.number_input(
            'New Epoch Number', 
            min_value=1, 
            max_value=4, 
            value=1
        )
        new_epoch_percentage = st.number_input(
            'New Epoch Percentage', 
            min_value=0.0, 
            max_value=100.0, 
            value=100.0, 
            step=1.0
        )
        
        # Submit button
        submit_button = st.form_submit_button('Update Role')
        
        if submit_button:
            try:
                # Snowflake connection for update
                conn = get_snowflake_connection()
                cursor = conn.cursor()
                
                # Update project role
                update_query = f"""
                UPDATE projects_detail
                SET 
                    epoch_number = {new_epoch_number}, 
                    epoch_percentage = {new_epoch_percentage}
                WHERE project_role_mapping_id = {selected_role}
                """
                
                # Execute update
                cursor.execute(update_query)
                
                # Commit transaction
                conn.commit()
                
                st.success('Role updated successfully!')
            
            except Exception as e:
                st.error(f'Error updating role: {e}')
            
            finally:
                # Close connection
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()

# Update the main app to include this page
def add_project_management_to_main_app(main_func):
    def modified_main():
        st.sidebar.selectbox('Menu', [
            'Project Overview', 
            'Consultant Rates', 
            'Project Staffing', 
            'Currency Analysis',
            'Project Management'  # New menu item
        ])
        
        # Existing menu logic
        menu = st.sidebar.selectbox('Select Page', [
            'Project Overview', 
            'Consultant Rates', 
            'Project Staffing', 
            'Currency Analysis',
            'Project Management'
        ])
        
        if menu == 'Project Management':
            create_project_management_page()
        
        # Rest of the existing main function logic
        else:
            # Call the original main function logic for other pages
            main_func()
    
    return modified_main
