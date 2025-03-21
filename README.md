# Anonymous Vote

A simple anonymous voting system built with Streamlit and Baserow.

## Features

- Create and manage voting polls
- Anonymous voting system
- Individual voting pages with unique UUIDs
- Real-time results visualization

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Baserow Setup**:
   - Create an account at [Baserow](https://baserow.io/)
   - Create a new database with the following tables:

   **Votes Table**:
   - id (Auto-increment)
   - question (Text)
   - max_selections (Number)
   - created_at (Date/Time)
   - uuid (Text)

   **Options Table**:
   - id (Auto-increment)
   - vote (Link to Votes Table)
   - option_text (Text)
   - count (Number)

   **Responses Table**:
   - id (Auto-increment)
   - vote (Link to Votes Table)
   - selected_options (Long Text - stores JSON)
   - submitted_at (Date/Time)

3. **Configure Baserow API**:
   - Get your Baserow API token
   - Update `.streamlit/secrets.toml` with your API token and table IDs:
     ```toml
     baserow_api_token = "YOUR_BASEROW_API_TOKEN"
     votes_table_id = "YOUR_VOTES_TABLE_ID"
     options_table_id = "YOUR_OPTIONS_TABLE_ID"
     responses_table_id = "YOUR_RESPONSES_TABLE_ID"
     ```

## Running the Application

Run the Streamlit app with:

```bash
streamlit run app.py
```

## Deploying to Streamlit Cloud

1. Push your code to a GitHub repository
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Link your GitHub repository
4. Configure the secrets in the Streamlit Cloud dashboard (same as in secrets.toml)
5. Deploy!

## How to Use

1. **Create a Vote**:
   - Click the "Create Vote" button
   - Enter the question and maximum selections allowed
   - Add options (at least 2)
   - Submit the form

2. **Share a Vote**:
   - Each vote has a unique UUID-based URL
   - Share the link with participants

3. **View Results**:
   - Results are displayed in real-time
   - Both tabular data and a chart are available
