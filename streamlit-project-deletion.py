# File: project_management.py (updated with deletion functions)

import streamlit as st
import pandas as pd
from database_config import get_snowflake_connection, execute_query

def create_deletion_page():
    st.header('Deletion Management')
    
    # Create tabs for different deletion options
    tab1, tab2, tab3 = st.tabs([
        'Delete Project', 
        'Delete Project Role', 
        'Delete Personnel'
    ])
    
    with tab1:
        delete_project()
    
    with tab2:
        delete_project_role()
    
    with tab3:
        delete_personnel()

def delete_project():
    st.subheader('Delete Project')
    
    # Fetch active projects
    projects_query = """
    SELECT project_id, project_name, 
           s.status_name,
           CASE 
               WHEN is_template THEN 'Template' 
               ELSE 'Active Project' 
           END AS project_type
    FROM projects p
    JOIN status s ON p.status_id = s.status_id
    """
    projects_df = execute_query(projects_query)
    
    # Display projects in a filterable dataframe
    st.write("Select Project to Delete:")
    project_to_delete = st.selectbox(
        'Choose Project', 
        projects_df['project_name'].tolist()
    )
    
    # Detailed project information
    selected_project = projects_df[projects_df['project_name'] == project_to_delete]
    st.dataframe(selected_project)
    
    # Confirmation and deletion
    if st.button('Confirm Delete Project'):
        try:
            conn = get_snowflake_connection()
            cursor = conn.cursor()
            
            # Get project ID
            project_id = selected_project['project_id'].iloc[0]
            
            # Check for associated data
            associated_queries = [
                f"SELECT COUNT(*) FROM projects_detail WHERE project_id = {project_id}",
                f"SELECT COUNT(*) FROM project_access WHERE project_id = {project_id}",
                f"SELECT COUNT(*) FROM project_history WHERE project_id = {project_id}"
            ]
            
            # Check associated records
            associated_records = []
            for query in associated_queries:
                cursor.execute(query)
                associated_records.append(cursor.fetchone()[0])
            
            # Confirm deletion
            if sum(associated_records) > 0:
                st.warning("This project has associated records. Deletion may cause data integrity issues.")
                if st.checkbox("I understand and want to proceed with cascading delete"):
                    # Cascading delete
                    delete_queries = [
                        f"DELETE FROM projects_detail WHERE project_id = {project_id}",
                        f"DELETE FROM project_access WHERE project_id = {project_id}",
                        f"DELETE FROM project_history WHERE project_id = {project_id}",
                        f"DELETE FROM projects WHERE project_id = {project_id}"
                    ]
                    
                    for query in delete_queries:
                        cursor.execute(query)
                    
                    conn.commit()
                    st.success(f"Project {project_to_delete} deleted successfully!")
            else:
                # Simple delete if no associated records
                cursor.execute(f"DELETE FROM projects WHERE project_id = {project_id}")
                conn.commit()
                st.success(f"Project {project_to_delete} deleted successfully!")
        
        except Exception as e:
            st.error(f"Error deleting project: {e}")
            conn.rollback()
        
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

def delete_project_role():
    st.subheader('Delete Project Role')
    
    # Fetch existing project roles with details
    project_roles_query = """
    SELECT 
        pd.project_role_mapping_id,
        p.project_name,
        r.role_name,
        pe.first_name || ' ' || pe.last_name AS full_name,
        pd.epoch_number,
        pd.epoch_percentage
    FROM projects_detail pd
    JOIN projects p ON pd.project_id = p.project_id
    JOIN roles r ON pd.role_id = r.role_id
    JOIN personnel pe ON pd.personnel_id = pe.personnel_id
    """
    project_roles_df = execute_query(project_roles_query)
    
    # Create a display string for selection
    project_roles_df['display_string'] = (
        project_roles_df['project_name'] + ' - ' + 
        project_roles_df['role_name'] + ' (' + 
        project_roles_df['full_name'] + ')'
    )
    
    # Role selection
    role_to_delete = st.selectbox(
        'Select Role to Delete', 
        project_roles_df['display_string'].tolist()
    )
    
    # Display selected role details
    selected_role = project_roles_df[project_roles_df['display_string'] == role_to_delete]
    st.dataframe(selected_role)
    
    # Confirmation and deletion
    if st.button('Confirm Delete Role'):
        try:
            conn = get_snowflake_connection()
            cursor = conn.cursor()
            
            # Get project role mapping ID
            role_mapping_id = selected_role['project_role_mapping_id'].iloc[0]
            
            # Delete the role
            cursor.execute(f"""
                DELETE FROM projects_detail 
                WHERE project_role_mapping_id = {role_mapping_id}
            """)
            
            conn.commit()
            st.success("Project role deleted successfully!")
        
        except Exception as e:
            st.error(f"Error deleting project role: {e}")
            conn.rollback()
        
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

def delete_personnel():
    st.subheader('Delete Personnel')
    
    # Fetch active personnel with details
    personnel_query = """
    SELECT 
        personnel_id,
        first_name || ' ' || last_name AS full_name,
        email,
        ten_k_id,
        cl.level_name,
        CASE 
            WHEN is_active THEN 'Active' 
            ELSE 'Inactive' 
        END AS status
    FROM personnel p
    JOIN consultant_level cl ON p.consultant_level_id = cl.consultant_level_id
    """
    personnel_df = execute_query(personnel_query)
    
    # Personnel selection
    personnel_to_delete = st.selectbox(
        'Select Personnel to Delete', 
        personnel_df['full_name'].tolist()
    )
    
    # Display personnel details
    selected_personnel = personnel_df[personnel_df['full_name'] == personnel_to_delete]
    st.dataframe(selected_personnel)
    
    # Check for associated projects
    personnel_id = selected_personnel['personnel_id'].iloc[0]
    associated_projects_query = f"""
    SELECT 
        p.project_name,
        r.role_name
    FROM projects_detail pd
    JOIN projects p ON pd.project_id = p.project_id
    JOIN roles r ON pd.role_id = r.role_id
    WHERE pd.personnel_id = {personnel_id}
    """
    associated_projects_df = execute_query(associated_projects_query)
    
    # Display associated projects
    if not associated_projects_df.empty:
        st.warning("This personnel is associated with the following projects:")
        st.dataframe(associated_projects_df)
    
    # Confirmation and deletion
    if st.button('Confirm Delete Personnel'):
        try:
            conn = get_snowflake_connection()
            cursor = conn.cursor()
            
            # Check for associated project roles
            cursor.execute(f"""
                SELECT COUNT(*) FROM projects_detail 
                WHERE personnel_id = {personnel_id}
            """)
            project_role_count = cursor.fetchone()[0]
            
            if project_role_count > 0:
                st.warning("This personnel has associated project roles.")
                if st.checkbox("I understand and want to proceed with cascading delete"):
                    # Cascading delete
                    delete_queries = [
                        f"DELETE FROM projects_detail WHERE personnel_id = {personnel_id}",
                        f"DELETE FROM project_access WHERE personnel_id = {personnel_id}",
                        f"DELETE FROM personnel WHERE personnel_id = {personnel_id}"
                    ]
                    
                    for query in delete_queries:
                        cursor.execute(query)
                    
                    conn.commit()
                    st.success("Personnel deleted successfully!")
            else:
                # Simple delete if no associated roles
                cursor.execute(f"DELETE FROM personnel WHERE personnel_id = {personnel_id}")
                conn.commit()
                st.success("Personnel deleted successfully!")
        
        except Exception as e:
            st.error(f"Error deleting personnel: {e}")
            conn.rollback()
        
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

# Update the project management page to include deletion
def create_project_management_page():
    st.header('Project Management')
    
    # Tabs for different project management actions
    tab1, tab2, tab3, tab4 = st.tabs([
        'Create New Project', 
        'Assign Project Roles', 
        'Update Project Roles',
        'Deletion Management'
    ])
    
    with tab1:
        create_new_project()
    
    with tab2:
        assign_project_roles()
    
    with tab3:
        update_project_roles()
    
    with tab4:
        delete_deletion_page()
