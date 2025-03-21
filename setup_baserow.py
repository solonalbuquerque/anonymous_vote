import requests
import os
from dotenv import load_dotenv
import json

"""
This script helps you create the necessary tables in Baserow for the Anonymous Vote application.
It requires a Baserow account and API token.

Usage:
1. Create a .env file with the following content:
   BASEROW_API_TOKEN=your_api_token
   BASEROW_DATABASE_ID=your_database_id
   BASEROW_API_URL=your_baserow_api_url (optional, defaults to https://api.baserow.io/api/database)

2. Run this script:
   python setup_baserow.py
"""

# Load environment variables
load_dotenv()

# Baserow API configuration
API_TOKEN = os.getenv("BASEROW_API_TOKEN")
DATABASE_ID = os.getenv("BASEROW_DATABASE_ID")
BASE_URL = os.getenv("BASEROW_API_URL", "https://api.baserow.io/api/database")

headers = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

def create_votes_table():
    """Create the Votes table in Baserow"""
    table_data = {
        "name": "Votes",
        "data": []
    }
    
    response = requests.post(
        f"{BASE_URL}/tables/database/{DATABASE_ID}/", 
        headers=headers,
        json=table_data
    )
    
    if response.status_code == 200:
        table_id = response.json()["id"]
        print(f"✅ Votes table created with ID: {table_id}")
        
        # Create fields
        create_field(table_id, "question", "text", {"name": "Question"})
        create_field(table_id, "max_selections", "number", {"name": "Max Selections", "number_decimal_places": 0})
        create_field(table_id, "created_at", "date", {"name": "Created At", "date_include_time": True})
        create_field(table_id, "uuid", "text", {"name": "UUID"})
        
        return table_id
    else:
        print(f"❌ Failed to create Votes table: {response.text}")
        return None

def create_options_table(votes_table_id):
    """Create the Options table in Baserow"""
    table_data = {
        "name": "Options",
        "data": []
    }
    
    response = requests.post(
        f"{BASE_URL}/tables/database/{DATABASE_ID}/", 
        headers=headers,
        json=table_data
    )
    
    if response.status_code == 200:
        table_id = response.json()["id"]
        print(f"✅ Options table created with ID: {table_id}")
        
        # Create fields
        create_field(table_id, "vote", "link_row", {
            "name": "Vote", 
            "link_row_table_id": votes_table_id
        })
        create_field(table_id, "option_text", "text", {"name": "Option Text"})
        create_field(table_id, "count", "number", {
            "name": "Count", 
            "number_decimal_places": 0,
            "number_negative": False
        })
        
        return table_id
    else:
        print(f"❌ Failed to create Options table: {response.text}")
        return None

def create_responses_table(votes_table_id):
    """Create the Responses table in Baserow"""
    table_data = {
        "name": "Responses",
        "data": []
    }
    
    response = requests.post(
        f"{BASE_URL}/tables/database/{DATABASE_ID}/", 
        headers=headers,
        json=table_data
    )
    
    if response.status_code == 200:
        table_id = response.json()["id"]
        print(f"✅ Responses table created with ID: {table_id}")
        
        # Create fields
        create_field(table_id, "vote", "link_row", {
            "name": "Vote", 
            "link_row_table_id": votes_table_id
        })
        create_field(table_id, "selected_options", "long_text", {"name": "Selected Options"})
        create_field(table_id, "submitted_at", "date", {"name": "Submitted At", "date_include_time": True})
        
        return table_id
    else:
        print(f"❌ Failed to create Responses table: {response.text}")
        return None

def create_field(table_id, field_name, field_type, field_params):
    """Create a field in a Baserow table"""
    field_data = {
        "name": field_params["name"],
        "type": field_type
    }
    
    # Add field-specific parameters
    for key, value in field_params.items():
        if key != "name":
            field_data[key] = value
    
    response = requests.post(
        f"{BASE_URL}/fields/table/{table_id}/", 
        headers=headers,
        json=field_data
    )
    
    if response.status_code == 200:
        print(f"  ✅ Field '{field_params['name']}' created")
    else:
        print(f"  ❌ Failed to create field '{field_params['name']}': {response.text}")

def create_secrets_file(votes_table_id, options_table_id, responses_table_id):
    """Create the Streamlit secrets.toml file"""
    secrets_dir = ".streamlit"
    secrets_file = os.path.join(secrets_dir, "secrets.toml")
    
    if not os.path.exists(secrets_dir):
        os.makedirs(secrets_dir)
    
    # Get the API URL for the rows endpoint from environment variable or use the default
    api_url = os.getenv("BASEROW_API_URL", "https://api.baserow.io/api/database/rows/table/")
    
    secrets_content = f"""# Baserow API Configuration
baserow_api_token = "{API_TOKEN}"
votes_table_id = "{votes_table_id}"
options_table_id = "{options_table_id}"
responses_table_id = "{responses_table_id}"
baserow_api_url = "{api_url}"
"""
    
    with open(secrets_file, "w") as f:
        f.write(secrets_content)
    
    print(f"✅ Created {secrets_file} with configuration")

def main():
    if not API_TOKEN or not DATABASE_ID:
        print("❌ Please set BASEROW_API_TOKEN and BASEROW_DATABASE_ID in a .env file.")
        return
    
    print("🚀 Setting up Baserow database for Anonymous Vote")
    
    # Create tables
    votes_table_id = create_votes_table()
    if not votes_table_id:
        return
    
    options_table_id = create_options_table(votes_table_id)
    if not options_table_id:
        return
    
    responses_table_id = create_responses_table(votes_table_id)
    if not responses_table_id:
        return
    
    # Create secrets.toml file
    create_secrets_file(votes_table_id, options_table_id, responses_table_id)
    
    print("\n✨ Setup completed successfully! You can now run the application with:")
    print("streamlit run app.py")

if __name__ == "__main__":
    main() 