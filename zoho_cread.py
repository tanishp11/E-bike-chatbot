import requests
import os
import json
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fetch values from environment variables
ORG_ID = os.getenv("ORG_ID")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def get_access_token(refresh_token: str, client_id: str, client_secret: str) -> str:
    """Fetches a new access token using the refresh token."""
    ZOHO_TOKEN_URL = "https://accounts.zoho.in/oauth/v2/token"

    payload = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token"
    }

    response = requests.post(ZOHO_TOKEN_URL, data=payload)
    if response.ok:
        response_data = response.json()
        return response_data.get("access_token", None)
    
    print(f"❌ Failed to get a new access token: {response.text}")
    return None

def create_ticket(access_token: str, org_id: str, ticket_data: dict):
    """Creates a new ticket in Zoho Desk."""
    ZOHO_TICKET_URL = "https://desk.zoho.in/api/v1/tickets"  # Adjust based on Zoho region
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "orgId": org_id,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(ZOHO_TICKET_URL, headers=headers, json=ticket_data, timeout=10)
        response.raise_for_status()  # Raise error for bad responses (4xx, 5xx)
        
        print("✅ Ticket Created Successfully!")
        print("Response:", response.json())

    except requests.exceptions.RequestException as e:
        print(f"❌ Zoho Desk API request failed: {e}")
        try:
            print("Response:", response.json())  # Print response if available
        except:
            print("No JSON response available.")

def extract_all_info(response_text: str) -> list:
    """
    Extracts multiple user details (name, email, phone, issue) from the response text dynamically.
    """
    extracted_users = []
    
    # Extract all JSON objects in the response text
    json_matches = re.findall(r'```json\s*\n?({.*?})\n?```', response_text, re.DOTALL)
    
    for json_str in json_matches:
        try:
            info = json.loads(json_str)  # Convert extracted JSON string to dictionary
            user_info = info.get("info", {})
            
            if user_info:
                extracted_users.append(user_info)  # Append extracted user info

        except json.JSONDecodeError:
            print("❌ Error parsing JSON data.")

    return extracted_users

access_token = get_access_token(REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET)

response_text = """Hello! Thank you for calling E-Bike BC. This call may be recorded for quality and training purposes. I’m Eva, your virtual assistant. I’m here to assist you with sales inquiries, technical support, partnership opportunities, and customer service. How may I help you today?

Certainly, I can help with that. May I please have your full name, email address, phone number, and a brief description of the issue with your e-bike model or product? This information will help me create a support ticket for you.

Thank you, Matthew. Thank you, Rahul.

Thank you. Could you please provide a brief description of the issue you're experiencing with your e-bike model or product? This will help us address your concern more effectively.

That's alright, Rahul. Even if you're not sure about the specific issue, we can still create a support ticket for you. Our team will reach out to gather more details and assist you further. Here is the information we have:

```json
{
    "info": {
    "name": "Rahul",
    "email": "rohan.kumar@gmail.com",
    "phone": "1234567890",
    "issue": "Not specified"
    }
}
```"""

users_info = extract_all_info(response_text)

def process_and_create_tickets(users_info, access_token, department_id):
    """Processes user information and creates Zoho Desk tickets."""
    for user_info in users_info:
        ticket_data = {
            "subject": user_info.get("issue", "General Inquiry"),
            "email": user_info.get("email", ""),
            "description": user_info.get("issue", "No issue specified."),
            "phone": user_info.get("phone", ""),
            "departmentId": department_id,  # Ensure correct Department ID
            "contact": {
                "firstName": user_info.get("name", "").split()[0] if user_info.get("name") else "Unknown",
                "lastName": user_info.get("name", "").split()[1] if len(user_info.get("name", "").split()) > 1 else "",
                "email": user_info.get("email", ""),
                "phone": user_info.get("phone", "")
            }
        }
        create_ticket(access_token, ORG_ID, ticket_data)  # Call the API function

# # Usage
# DEPARTMENT_ID = "185141000000010772"
# process_and_create_tickets(users_info, access_token, DEPARTMENT_ID)

