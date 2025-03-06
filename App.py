import streamlit as st
import pandas as pd

def read_file(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    elif file.name.endswith(('.xlsx', '.xls')):
        return pd.read_excel(file)
    else:
        st.error("Unsupported file format")
        return None

# Function to filter users
def filter_users(df, user_types, matching_columns):
    filtered = {user_type: df[df["User Type"] == user_type].copy() for user_type in user_types}
    
    no_access = {
        user_type: filtered[user_type][(filtered[user_type][matching_columns] == 0).all(axis=1)]
        for user_type in user_types
    }

    downgrade = {
        user_type: filtered[user_type][(filtered[user_type][matching_columns[0]] != 0) & 
                                       (filtered[user_type][matching_columns[2]] == 0) & 
                                       (filtered[user_type][matching_columns[3]] == 0)]
        for user_type in user_types if user_type not in ["Viewer", "Guest"]
    }

    return (filtered, no_access, downgrade) if downgrade else (filtered, no_access)

# Streamlit UI
st.title("Security Data Analysis")

# File upload
file = st.file_uploader("Upload an Excel or CSV file", type=["csv", "xlsx", "xls"])

if file:
    df = read_file(file)
    
    if df is not None:
        # Filter DataFrame based on 'User domain'
        df_internal = df[df["User domain"] == "Internal"]
        df_external = df[df["User domain"] == "External"]

        # Check column names based on keywords
        keywords = ["90"]  # Replace with actual keywords
        matching_columns = [col for col in df.columns if any(keyword.lower() in col.lower() for keyword in keywords)]

        # Define user types
        user_types = {
            "internal": ["Member", "Provisional Member", "Viewer"],
            "external": ["Guest", "Provisional Member", "Viewer"]
        }

        # Apply filtering for internal users
        result_internal = filter_users(df_internal, user_types["internal"], matching_columns)
        if len(result_internal) == 3:
            df_internal_filtered, df_internal_No_access, df_internal_downgrade = result_internal
        else:
            df_internal_filtered, df_internal_No_access = result_internal
            df_internal_downgrade = {}
        
        # Apply filtering for external users
        result_external = filter_users(df_external, user_types["external"], matching_columns)
        if len(result_external) == 3:
            df_external_filtered, df_external_No_access, df_external_downgrade = result_external
        else:
            df_external_filtered, df_external_No_access = result_external
            df_external_downgrade = {}


        # Prepare security data
        External_data = {
            "Guest": [df_external_filtered["Guest"].shape[0] - (df_external_No_access["Guest"].shape[0] if "Guest" in df_external_No_access else 0),
                      "", "", "",
                      df_external_No_access["Guest"].shape[0] if "Guest" in df_external_No_access else 0,
                      df_external_filtered["Guest"].shape[0]]
            if "Guest" in df_external_filtered else ["","","","","",0],
            "Member": [df_external_filtered["Member"].shape[0] - (df_external_No_access["Member"].shape[0] if "Member" in df_external_filtered else 0)
                       , "", "", "", "", df_external_filtered["Member"].shape[0]]
            if "Member" in df_external_filtered else ["", "", "", "", "", 0],
            "Provisional Member": [df_external_filtered["Provisional Member"].shape[0] - (df_external_No_access["Provisional Member"].shape[0] if "Provisional Member" in df_external_No_access else 0),
                                   "", "", "", df_external_No_access["Provisional Member"].shape[0]if "Provisional Member" in df_external_No_access else "", df_external_filtered["Provisional Member"].shape[0]]
            if "Provisional Member" in df_external_filtered else ["", "", "", "", "", 0],
            "Viewer": [df_external_filtered["Viewer"].shape[0] - df_external_No_access["Viewer"].shape[0] if "Viewer" in df_external_No_access else 0,
                       "", "", "", df_external_No_access["Viewer"].shape[0] if "Viewer" in df_external_No_access else "", df_external_filtered["Viewer"].shape[0]]
            if "Viewer" in df_external_filtered else ["", "", "", "", "", ""],
            "No Access": ["", "", "", "", "", ""],
            "Total": ["", "","", "", "", ""]
        }
        
        Internal_data = {
            "Guest": [df_internal_filtered["Guest"].shape[0] - (df_internal_No_access["Guest"].shape[0] if "Guest" in df_internal_No_access else 0),
                      "", "", "",
                      df_internal_No_access["Guest"].shape[0] if "Guest" in df_internal_No_access else 0,
                      df_internal_filtered["Guest"].shape[0]]
            if "Guest" in df_internal_filtered else ["","","","","",0],
            "Member": ["", df_internal_filtered["Member"].shape[0] - (df_internal_No_access["Member"].shape[0] if "Member" in df_internal_filtered else 0)
                       -(df_internal_downgrade["Member"].shape[0] if "Member" in df_internal_downgrade else 0), ""
                       , df_internal_downgrade["Member"].shape[0] if "Member" in df_internal_downgrade else ""
                       , df_internal_No_access["Member"].shape[0] if "Member" in df_internal_filtered else "", df_internal_filtered["Member"].shape[0]]
            if "Member" in df_internal_filtered else ["", "", "", "", "", 0],
            "Provisional Member": ["", "",
                                   df_internal_filtered["Provisional Member"].shape[0] - (df_internal_No_access["Provisional Member"].shape[0] if "Provisional Member" in df_internal_No_access else 0)
                                   - (df_internal_downgrade["Provisional Member"].shape[0] if "Provisional Member" in df_internal_downgrade else 0),
                                   df_internal_downgrade["Provisional Member"].shape[0] if "Provisional Member" in df_internal_downgrade else ""
                                   , df_internal_No_access["Provisional Member"].shape[0]if "Provisional Member" in df_internal_No_access else "", df_internal_filtered["Provisional Member"].shape[0]]
            if "Provisional Member" in df_internal_filtered else ["", "", "", "", "", 0],
            "Viewer": ["","","",df_internal_filtered["Viewer"].shape[0] - df_internal_No_access["Viewer"].shape[0] if "Viewer" in df_internal_No_access else 0,
                       df_internal_No_access["Viewer"].shape[0] if "Viewer" in df_internal_No_access else "", df_internal_filtered["Viewer"].shape[0]]
            if "Viewer" in df_internal_filtered else ["", "", "", "", "", ""],
            "No Access": ["", "", "", "", "", ""],
            "Total": ["", "","", "", "", ""]
        }

        # Create DataFrame
        df_security = pd.DataFrame(External_data, index=["Guest", "Member", "Provisional Member", "Viewer", "No Access", "Total"]).T
        df_security = df_security.drop(["Total", "No Access"], axis=0)
        
        df_savings = pd.DataFrame(Internal_data, index=["Guest", "Member", "Provisional Member", "Viewer", "No Access", "Total"]).T
        df_savings = df_savings.drop(["Total", "No Access"], axis=0)

        # Display results
        st.subheader("External Data Table")
        st.dataframe(df_security)
        st.subheader("Internal Data Table")
        st.dataframe(df_savings)