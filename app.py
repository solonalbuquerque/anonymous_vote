import streamlit as st
import uuid
import pandas as pd
import requests
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Anonymous Vote",
    page_icon="📊",
    layout="wide"
)

# Initialize session state for storing temporary data
if "show_create_modal" not in st.session_state:
    st.session_state.show_create_modal = False
if "current_vote_id" not in st.session_state:
    st.session_state.current_vote_id = None

# Baserow API configuration
# First check if URL is in environment variables, then in secrets, then use default
BASEROW_API_URL = os.getenv("BASEROW_API_URL", 
                          st.secrets.get("baserow_api_url", 
                                       "https://api.baserow.io/api/database/rows/table/"))
BASEROW_API_TOKEN = st.secrets["baserow_api_token"]
VOTES_TABLE_ID = st.secrets["votes_table_id"]
OPTIONS_TABLE_ID = st.secrets["options_table_id"]
RESPONSES_TABLE_ID = st.secrets["responses_table_id"]

headers = {
    "Authorization": f"Token {BASEROW_API_TOKEN}",
    "Content-Type": "application/json"
}

def get_all_votes():
    """Fetch all votes from Baserow"""
    response = requests.get(
        f"{BASEROW_API_URL}{VOTES_TABLE_ID}/", 
        headers=headers
    )
    if response.status_code == 200:
        return response.json()["results"]
    else:
        st.error(f"Failed to fetch votes: {response.text}")
        return []

def get_vote_by_id(vote_id):
    """Fetch a specific vote by its ID"""
    votes = get_all_votes()
    for vote in votes:
        if vote["id"] == vote_id or vote["uuid"] == vote_id:
            return vote
    return None

def get_options_for_vote(vote_id):
    """Fetch all options for a specific vote"""
    params = {
        "filter__field_vote__equal": vote_id
    }
    response = requests.get(
        f"{BASEROW_API_URL}{OPTIONS_TABLE_ID}/", 
        headers=headers,
        params=params
    )
    if response.status_code == 200:
        return response.json()["results"]
    else:
        st.error(f"Failed to fetch options: {response.text}")
        return []

def get_responses_for_vote(vote_id):
    """Fetch all responses for a specific vote"""
    params = {
        "filter__field_vote__equal": vote_id
    }
    response = requests.get(
        f"{BASEROW_API_URL}{RESPONSES_TABLE_ID}/", 
        headers=headers,
        params=params
    )
    if response.status_code == 200:
        return response.json()["results"]
    else:
        st.error(f"Failed to fetch responses: {response.text}")
        return []

def create_vote(question, max_selections):
    """Create a new vote in Baserow"""
    new_vote_uuid = str(uuid.uuid4())
    data = {
        "question": question,
        "max_selections": max_selections,
        "created_at": datetime.now().isoformat(),
        "uuid": new_vote_uuid
    }
    
    response = requests.post(
        f"{BASEROW_API_URL}{VOTES_TABLE_ID}/", 
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to create vote: {response.text}")
        return None

def create_option(vote_id, option_text):
    """Create a new option for a vote"""
    data = {
        "vote": vote_id,
        "option_text": option_text,
        "count": 0
    }
    
    response = requests.post(
        f"{BASEROW_API_URL}{OPTIONS_TABLE_ID}/", 
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to create option: {response.text}")
        return None

def submit_vote(vote_id, selected_options):
    """Submit a vote response"""
    data = {
        "vote": vote_id,
        "selected_options": json.dumps(selected_options),
        "submitted_at": datetime.now().isoformat()
    }
    
    # Record the response
    response = requests.post(
        f"{BASEROW_API_URL}{RESPONSES_TABLE_ID}/", 
        headers=headers,
        json=data
    )
    
    # Update option counts
    for option_id in selected_options:
        option = next((o for o in get_options_for_vote(vote_id) if o["id"] == option_id), None)
        if option:
            update_data = {
                "count": option["count"] + 1
            }
            update_response = requests.patch(
                f"{BASEROW_API_URL}{OPTIONS_TABLE_ID}/{option_id}/", 
                headers=headers,
                json=update_data
            )
    
    if response.status_code == 200:
        return True
    else:
        st.error(f"Failed to submit vote: {response.text}")
        return False

def toggle_create_modal():
    st.session_state.show_create_modal = not st.session_state.show_create_modal

def render_create_vote_modal():
    with st.form("create_vote_form"):
        st.subheader("Create New Vote")
        question = st.text_input("Question")
        max_selections = st.number_input("Maximum selections allowed", min_value=1, value=1)
        
        # Options input (dynamic)
        st.write("Options:")
        options = []
        for i in range(10):  # Allow up to 10 options
            option = st.text_input(f"Option {i+1}", key=f"option_{i}")
            if option:
                options.append(option)
        
        submitted = st.form_submit_button("Create Vote")
        
        if submitted and question and len(options) >= 2:
            new_vote = create_vote(question, max_selections)
            if new_vote:
                vote_id = new_vote["id"]
                for option_text in options:
                    if option_text:
                        create_option(vote_id, option_text)
                st.session_state.show_create_modal = False
                st.rerun()

def display_vote_page(vote_id):
    vote = get_vote_by_id(vote_id)
    if not vote:
        st.error("Vote not found")
        return
    
    st.header(vote["question"])
    
    options = get_options_for_vote(vote_id)
    responses = get_responses_for_vote(vote_id)
    
    # Display voting form
    with st.form("voting_form"):
        selected_options = []
        if vote["max_selections"] == 1:
            option_labels = [opt["option_text"] for opt in options]
            option_ids = [opt["id"] for opt in options]
            selected_index = st.radio("Select your answer:", range(len(option_labels)), 
                                     format_func=lambda i: option_labels[i])
            selected_options = [option_ids[selected_index]]
        else:
            for option in options:
                if st.checkbox(option["option_text"], key=f"opt_{option['id']}"):
                    selected_options.append(option["id"])
                
            # Validate max selections
            if len(selected_options) > vote["max_selections"]:
                st.warning(f"You can select at most {vote['max_selections']} options")
        
        submitted = st.form_submit_button("Submit Vote")
        
        if submitted:
            if len(selected_options) == 0:
                st.warning("Please select at least one option")
            elif len(selected_options) > vote["max_selections"]:
                st.warning(f"You can select at most {vote['max_selections']} options")
            else:
                success = submit_vote(vote_id, selected_options)
                if success:
                    st.success("Your vote has been recorded!")
                    st.rerun()
    
    # Display results
    st.subheader("Current Results")
    results_data = []
    total_votes = sum(option["count"] for option in options)
    
    for option in options:
        percentage = 0
        if total_votes > 0:
            percentage = (option["count"] / total_votes) * 100
        
        results_data.append({
            "Option": option["option_text"],
            "Votes": option["count"],
            "Percentage": f"{percentage:.1f}%"
        })
    
    results_df = pd.DataFrame(results_data)
    st.dataframe(results_df, use_container_width=True)
    
    # Create a bar chart for visualization
    st.bar_chart(results_df.set_index("Option")["Votes"])
    
    # Display shareable link
    st.subheader("Share this vote")
    vote_url = f"{st.experimental_get_query_params().get('vote_id', [''])[0]}"
    st.code(f"{st.get_url()}?vote_id={vote['uuid']}")

def main():
    # Application header with title and create button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🗳️ Anonymous Vote")
    with col2:
        st.button("➕ Create Vote", on_click=toggle_create_modal, use_container_width=True)
    
    # Create vote modal
    if st.session_state.show_create_modal:
        render_create_vote_modal()
    
    # Check if we're viewing a specific vote
    query_params = st.experimental_get_query_params()
    if "vote_id" in query_params:
        vote_id = query_params["vote_id"][0]
        st.session_state.current_vote_id = vote_id
        display_vote_page(vote_id)
    else:
        # List all available votes
        st.header("Available Votes")
        votes = get_all_votes()
        
        if not votes:
            st.info("No votes available. Create one to get started!")
        
        for vote in votes:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"### {vote['question']}")
                st.write(f"Created: {vote['created_at'][:10]}")
            with col2:
                if st.button("Vote", key=f"vote_{vote['id']}"):
                    st.experimental_set_query_params(vote_id=vote["uuid"])
                    st.rerun()

if __name__ == "__main__":
    main() 