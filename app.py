# import os
# import json
# import base64
# import asyncio
# import requests
# import websockets
# import re
# from fastapi import FastAPI, HTTPException, WebSocket, Request
# import httpx
# from fastapi.responses import HTMLResponse, JSONResponse
# from fastapi.websockets import WebSocketDisconnect
# from twilio.twiml.voice_response import VoiceResponse, Connect, Say
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv
# from enum import Enum, auto


# load_dotenv()

# # Configuration
# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# ZOHO_API_TOKEN = os.getenv('ZOHO_API_TOKEN')
# ZOHO_DESK_DOMAIN = os.getenv('ZOHO_DESK_DOMAIN', 'desk.zoho.com')
# ZOHO_ORG_ID = os.getenv('ZOHO_ORG_ID')
# PORT = int(os.getenv('PORT', 8000))

# #Call flow states - Updated to match flowchart
# class CallState(Enum):
#     GREETING = auto()
#     DEPARTMENT_SELECTION = auto()
#     SALES = auto()
#     CUSTOMER_SERVICE = auto()
#     PARTNERSHIP = auto()
#     QUESTION_ANSWERED = auto()
#     TICKET_OFFER = auto()
#     CREATE_TICKET = auto()
#     COLLECT_INFO = auto()
#     AVAILABILITY_CHECK = auto()
#     CONNECT_REPRESENTATIVE = auto()
#     GOODBYE = auto()
#     END_CALL = auto()


# # System prompts for different stages
# SYSTEM_MESSAGE = """
# Role:
# You are an AI assistant for E-bike BC, handling customer inquiries via phone. Your main responsibilities are to collect customer details, understand their needs, create support tickets in Zoho, and transfer calls when necessary.

# User Intent Handling:

# 1. Sales Query Handling:
#     • Greet the customer warmly: "Thank you for calling E-bike BC. My name is [AI Assistant]. How can I help you with our e-bikes today?"
#     • When customer expresses interest in purchasing, collect the following details:
#         - Full Name: "May I have your full name, please?"
#         - Email Address: "What's the best email address to reach you at?"
#         - Phone Number: "Could I get your phone number for our records?"
#         - E-bike Model or Product of Interest: "Which e-bike model or product are you interested in?"
#     • Once all details are collected, inform the customer: "Thank you for providing that information. I'm creating a ticket in our system now."
#     • Ask: "Would you like me to transfer you to our Sales Team who can provide more specific information about pricing and availability?"
#         - If Yes: "I'll transfer you to our Sales Team right away. Please hold."
#         - If No: "I've created a ticket with your inquiry. Our sales team will contact you within 24 hours. Your reference number is [TICKET_ID]."

            
# Tools Available:
# 1. **Sales Query Handling Tool**:
#     - **Purpose**: Handles sales-related customer inquiries and collects necessary details for follow-up.
#     - **Functionality**:
#         • Captures the customer's name, email, phone number, and query.
#         • Creates a support ticket in the Zoho system.
#         • Optionally transfers the call to a sales representative if requested by the customer.
#     - **Parameters**:
#         - `name` (string): Customer's full name.
#         - `email` (string): Customer's email address.
#         - `query` (string): The specific sales inquiry.
#         - `phone` (string): Customer's phone number.

        

# 2. Support Query Handling:
#     • Greet the customer: "Thank you for calling E-bike BC Support. My name is [AI Assistant]. How can I assist you today?"
#     • When customer mentions an issue, collect the following details:
#         - Full Name: "May I have your full name, please?"
#         - Email Address: "What's the best email address to reach you at?"
#         - Phone Number: "Could I get your phone number for our records?"
#         - E-bike Model: "Which e-bike model are you having an issue with?"
#         - Description of Issue: "Could you briefly describe the issue you're experiencing?"
#     • Once all details are collected, inform the customer: "Thank you for providing that information. I'm creating a support ticket now."
#     • Ask: "Would you like me to transfer you to our Technical Support Team who can help troubleshoot this issue?"
#         - If Yes: "I'll transfer you to our Support Team right away. Please hold."
#         - If No: "I've created a support ticket with your issue details. Our support team will contact you within 24 hours. Your reference number is [TICKET_ID]."


# 3. Partnership Query Handling:
#     • Greet the customer: "Thank you for calling E-bike BC. My name is [AI Assistant]. How can I help you today?"
#     • When customer mentions partnership interest, collect the following details:
#         - Full Name: "May I have your full name, please?"
#         - Company Name: "What company are you representing?"
#         - Email Address: "What's the best email address to reach you at?"
#         - Phone Number: "Could I get your phone number for our records?"
#         - Partnership Type: "What type of partnership are you interested in? Retail, distribution, or something else?"
#     • Once all details are collected, inform the customer: "Thank you for providing that information. I'm creating a ticket for our partnerships team now."
#     • Ask: "Would you like me to transfer you to our Business Development Team who handles partnerships?"
#         - If Yes: "I'll transfer you to our Business Development Team right away. Please hold."
#         - If No: "I've created a ticket with your partnership inquiry. Our business development team will contact you within 48 hours. Your reference number is [TICKET_ID]."

# Important Guidelines:
#     • Always confirm each piece of information after the customer provides it.
#     • If a customer is hesitant to provide information, reassure them: "I understand your concern. This information helps us create a proper support ticket and ensures our team can follow up with the right solution. We maintain strict confidentiality of all customer information."
#     • If the customer refuses to provide contact details, say: "I understand. Without contact information, we won't be able to create a support ticket or follow up. I can still provide general information about our products or you can reach us at support@ebikebc.com when you're ready."
#     • For incomplete information, politely ask again: "I'm sorry, I didn't catch your [missing information]. Could you please repeat that?"
#     • End every call with: "Thank you for contacting E-bike BC. Is there anything else I can assist you with today?"

# Remember: You must collect the customer's name, email, phone number, and query details before creating a Zoho ticket. The system will automatically create the ticket once this information is available.
# """


# VOICE = 'alloy'

# LOG_EVENT_TYPES = [
#     'error', 'response.content.done', 'rate_limits.updated',
#     'response.done', 'input_audio_buffer.committed',
#     'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
#     'session.created'
# ]

# app = FastAPI()

# # Enable CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Global state storage for active calls
# caller_sessions = {}


# class CallerSession:
#     def __init__(self, call_sid):
#         self.call_sid = call_sid
#         self.state = CallState.GREETING
#         self.current_prompt = SYSTEM_MESSAGE
#         self.department = None
#         self.name = None
#         self.email = None
#         self.query = None
#         self.ticket_id = None
#         self.representative_available = False  # Flag for representative availability

    
# if not OPENAI_API_KEY:
#     raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')


# @app.get("/", response_class=JSONResponse)
# async def index_page():
#     return {"message": "E-Bike BC Call System is running!"}


# @app.api_route("/incoming-call", methods=["GET", "POST"])
# async def handle_incoming_call(request: Request):
#     """Handle incoming call and return TwiML response to connect to Media Stream."""
#     form_data = await request.form()
#     call_sid = form_data.get("CallSid")
    
#     # Initialize a new session for this call
#     caller_sessions[call_sid] = CallerSession(call_sid)
    
#     response = VoiceResponse()
#     response.say("Hello! Thanks for calling E-bike BC. This call may be recorded for quality and training purposes.")
#     response.pause(length=1)
#     response.say("How can I assist you today?")
#     host = request.url.hostname
#     url = f"http://{host}/create-ticket"
#     print("Hostname-------------->>",host)
#     connect = Connect()
#     connect.stream(url=f'wss://{host}/media-stream')
#     response.append(connect)
    
#     return HTMLResponse(content=str(response), media_type="application/xml")


# @app.post("/create-ticket")
# async def create_ticket(user_info: dict):
#     """Create a Zoho Desk ticket."""
#     try:
#         payload = {
#             "subject": f"Support Request from {user_info['name']}",
#             "email": user_info['email'],
#             "description": user_info.get('query', 'No description provided'),
#             "phone": user_info.get('phone', ""),
#             "departmentId": "185141000000010772",  
#             "contact": {
#                 "firstName": "Bharat",
#                 "lastName": "Patil",
#                 "email": "noreply@samcomtechnologies.com",
#                 "phone": "9825054779 "
#             }
#         }

#         headers = {
#             "Authorization": f"Bearer {ZOHO_API_TOKEN}",
#             "Content-Type": "application/json"
#         }

#         async with httpx.AsyncClient() as client:
#             response = await client.post("https://desk.zoho.in/api/v1/tickets", json=payload, headers=headers)

#         if response.status_code in [200, 201]:
#             return {"message": "Ticket created successfully", "response": response.json()}
#         else:
#             return {
#                 "message": "Failed to create ticket",
#                 "status_code": response.status_code,
#                 "response": response.text
#             }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error creating ticket: {str(e)}")



# # Mock function to connect to a representative
# async def connect_to_representative(call_sid, department):
#     """Mock function to connect caller to a representative"""
#     # In a real system, this would transfer the call to a live agent
#     # For demonstration, just log the transfer request
#     print(f"Call {call_sid} would be transferred to a {department} representative")
#     # Return success flag (always successful in this mock implementation)
#     return True




# @app.websocket("/media-stream")
# async def handle_media_stream(websocket: WebSocket):
#     print("Client connected")
#     await websocket.accept()

#     async with websockets.connect(
#         'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
#         extra_headers={
#             "Authorization": f"Bearer {OPENAI_API_KEY}",
#             "OpenAI-Beta": "realtime=v1"
#         }
#     ) as openai_ws:
#         await initialize_session(openai_ws)

#         stream_sid = None
#         latest_media_timestamp = 0
#         last_assistant_item = None
#         mark_queue = []
#         response_start_timestamp_twilio = None
#         user_info = {}

#         async def receive_from_twilio():
#             nonlocal stream_sid, latest_media_timestamp, user_info
#             try:
#                 async for message in websocket.iter_text():
#                     data = json.loads(message)
                   
#                     if data['event'] == 'media' and openai_ws.open:
#                         latest_media_timestamp = int(data['media']['timestamp'])
#                         audio_append = {
#                             "type": "input_audio_buffer.append",
#                             "audio": data['media']['payload']
#                         }
#                         await openai_ws.send(json.dumps(audio_append))

#                     elif data['event'] == 'start':
#                         stream_sid = data['start']['streamSid']
#                         print(f"Incoming stream started: {stream_sid}")
#                         response_start_timestamp_twilio = None
#                         latest_media_timestamp = 0
#                         last_assistant_item = None
#                     elif data['event'] == 'mark' and mark_queue:
#                         mark_queue.pop(0)

#                     elif data['event'] == 'user_info':
#                         user_info.update({
#                             "name": data.get('name', ''),
#                             "email": data.get('email', ''),
#                             "query": data.get('description', ''),
#                             "phone": data.get('phone', '')
#                         })
#                         print("Updated user info:", user_info)

#             except WebSocketDisconnect:
#                 print("Client disconnected.")
#                 if openai_ws.open:
#                     await openai_ws.close()

#         async def handle_function_calls(response):
#             """Handles function calls from OpenAI to process customer queries."""
#             if response.get("type") == "function_call":
#                 function_name = response["function_call"]["name"]
#                 parameters = response["function_call"]["parameters"]

#                 # Handle sales query handling
#                 if function_name == "sales_query_handling":
#                     print("Handling Sales Query:", parameters)
#                     user_info = {
#                         "name": parameters.get("name", ""),
#                         "email": parameters.get("email", ""),
#                         "phone": parameters.get("phone", ""),
#                         "query": parameters.get("query", "")
#                     }
#                     # Trigger ticket creation
#                     await create_ticket(user_info)

#         async def send_to_twilio():
#             nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio
#             try:
#                 async for openai_message in openai_ws:
#                     response = json.loads(openai_message)
#                     if response['type'] in LOG_EVENT_TYPES:
#                         print(f"-------------------->>> Received event: {response['type']}", response)

#                     if response.get("type") == "function_call":
#                         await handle_function_calls(response)

#                     if response.get('type') == 'response.audio.delta' and 'delta' in response:
#                         audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
#                         audio_delta = {
#                             "event": "media",
#                             "streamSid": stream_sid,
#                             "media": {
#                                 "payload": audio_payload
#                             }
#                         }
#                         await websocket.send_json(audio_delta)

#                         if response_start_timestamp_twilio is None:
#                             response_start_timestamp_twilio = latest_media_timestamp

#                         if response.get('item_id'):
#                             last_assistant_item = response['item_id']

#                         await send_mark(websocket, stream_sid)

#                         if response.get("type") == "response.done":
#                             print("----->>>> Response Done detected. Gathering user info...")
#                             user_info = {
#                                 "name": user_info.get("name", "Unknown"),
#                                 "email": user_info.get("email", "Unknown"),
#                                 "phone": user_info.get("phone", "Unknown"),
#                                 "query": user_info.get("query", "Unknown")
#                             }
#                             print("User Info Collected for Ticket Creation:", user_info)

#                     if user_info.get("email") and user_info.get("name") and user_info.get("phone") and user_info.get("query"):
#                         await create_ticket(user_info)
#                         print("Ticket created successfully.")
#             except Exception as e:
#                 print(f"Error in send_to_twilio: {e}")

#         async def handle_speech_started_event():
#             nonlocal response_start_timestamp_twilio, last_assistant_item
#             print("Handling speech started event.")

#             if mark_queue and response_start_timestamp_twilio is not None:
#                 elapsed_time = latest_media_timestamp - response_start_timestamp_twilio

#                 if last_assistant_item:
#                     truncate_event = {
#                         "type": "conversation.item.truncate",
#                         "item_id": last_assistant_item,
#                         "content_index": 0,
#                         "audio_end_ms": elapsed_time
#                     }
#                     await openai_ws.send(json.dumps(truncate_event))

#                 await websocket.send_json({"event": "clear", "streamSid": stream_sid})
#                 mark_queue.clear()
#                 last_assistant_item = None
#                 response_start_timestamp_twilio = None

#             # If user_info contains necessary details, create the ticket
#             if user_info.get('email') and user_info.get('query') and user_info.get('phone'):
#                 print("----->>>> Creating Zoho Desk ticket with user info:----->>>", user_info)
#                 await create_ticket(user_info)  # Pass the request object

#         async def send_mark(connection, stream_sid):
#             if stream_sid:
#                 mark_event = {"event": "mark", "streamSid": stream_sid, "mark": {"name": "responsePart"}}
#                 await connection.send_json(mark_event)
#                 mark_queue.append('responsePart')

#         async def create_ticket(user_info, request):
#             """Create a Zoho Desk ticket via HTTP POST request."""
#             print("Sending user info to /create-ticket:", user_info)

#             host = request.url.hostname  # Dynamically get host
#             url = f"http://{host}/create-ticket"
            
#             async with httpx.AsyncClient() as client:
#                 response = await client.post(
#                     url,
#                     json=user_info,
#                     headers={"Content-Type": "application/json"}
#                 )

#             if response.status_code in [200, 201]:
#                 print("Ticket created successfully:", response.json())
#             else:
#                 print("Failed to create ticket:", response.text)

#         await asyncio.gather(receive_from_twilio(), send_to_twilio())



# async def initialize_session(openai_ws):
#     """Control initial session with OpenAI."""
#     session_update = {
#         "type": "session.update",
#         "session": {
#             "turn_detection": {"type": "server_vad"},
#             "input_audio_format": "g711_ulaw",
#             "output_audio_format": "g711_ulaw",
#             "voice": VOICE,
#             "instructions": SYSTEM_MESSAGE,
#             "modalities": ["text", "audio"],
#             "temperature": 0.6,
#             "tools": [
#                 {
#                     "type": "function",
#                     "name": "sales_query_handling",
#                     "description": "Handles sales-related queries for customers.",
#                     "parameters": {
#                         "type": "object",
#                         "properties": {
#                             "name": {"type": "string"}
#                         }
#                     }
#                 },
#             ],
#             "tool_choice": "auto"
#         }
#     }

    

#     await openai_ws.send(json.dumps(session_update))


#     # AI speaks first with greeting
#     initial_greeting = {
#         "type": "conversation.item.create",
#         "item": {
#             "type": "message",
#             "role": "user",
#             "content": [
#                 {
#                     "type": "input_text",
#                     "text": "Hello! Thanks for calling E-bike BC. This call may be recorded for quality and training purposes"
#                 }
#             ]
#         }
#     }
#     await openai_ws.send(json.dumps(initial_greeting))
#     await openai_ws.send(json.dumps({"type": "response.create"}))



# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=PORT)



import os
import json
import base64
import asyncio
import requests
import websockets
import re
from fastapi import FastAPI, HTTPException, WebSocket, Request
import httpx
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Say
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from enum import Enum, auto


load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ZOHO_API_TOKEN = os.getenv('ZOHO_API_TOKEN')
ZOHO_DESK_DOMAIN = os.getenv('ZOHO_DESK_DOMAIN', 'desk.zoho.com')
ZOHO_ORG_ID = os.getenv('ZOHO_ORG_ID')
ZOHO_CRM_DOMAIN = os.getenv('ZOHO_CRM_DOMAIN', 'crm.zoho.in')
PORT = int(os.getenv('PORT', 8000))

#Call flow states - Updated to match flowchart
class CallState(Enum):
    GREETING = auto()
    DEPARTMENT_SELECTION = auto()
    SALES = auto()
    CUSTOMER_SERVICE = auto()
    PARTNERSHIP = auto()
    QUESTION_ANSWERED = auto()
    TICKET_OFFER = auto()
    CREATE_TICKET = auto()
    COLLECT_INFO = auto()
    AVAILABILITY_CHECK = auto()
    CONNECT_REPRESENTATIVE = auto()
    GOODBYE = auto()
    END_CALL = auto()


# System prompts for different stages
SYSTEM_MESSAGE = """
Role:
You are an AI assistant for E-bike BC, handling customer inquiries via phone. Your main responsibilities are to collect customer details, understand their needs, create leads in Zoho CRM, and transfer calls when necessary.

User Intent Handling:
            
Tools Available:
1. **Sales Lead Creation Tool**:
    - **Purpose**: Collects necessary customer information and creates a lead in Zoho CRM.
    - **Functionality**:
        • Captures the customer's name, email, phone number, product of interest, and lead source.
        • Creates a lead in the Zoho CRM system.
        • Optionally transfers the call to a sales representative if requested by the customer.
    - **Parameters**:
        - `first_name` (string): Customer's first name.
        - `last_name` (string): Customer's last name.
        - `email` (string): Customer's email address.
        - `phone` (string): Customer's phone number.
        - `product_interest` (string): The specific e-bike model or product the customer is interested in.
        - `lead_source` (string): How the customer heard about E-bike BC.
        - `description` (string): Additional notes or information about the inquiry.
        

2. Support Query Handling:
    • Greet the customer: "Thank you for calling E-bike BC Support. My name is [AI Assistant]. How can I assist you today?"
    • When customer mentions an issue, collect the following details:
        - Full Name: "May I have your full name, please?"
        - Email Address: "What's the best email address to reach you at?"
        - Phone Number: "Could I get your phone number for our records?"
        - E-bike Model: "Which e-bike model are you having an issue with?"
        - Description of Issue: "Could you briefly describe the issue you're experiencing?"
    • Once all details are collected, inform the customer: "Thank you for providing that information. I'm creating a support ticket now."
    • Ask: "Would you like me to transfer you to our Technical Support Team who can help troubleshoot this issue?"
        - If Yes: "I'll transfer you to our Support Team right away. Please hold."
        - If No: "I've created a support ticket with your issue details. Our support team will contact you within 24 hours."


3. Partnership Query Handling:
    • Greet the customer: "Thank you for calling E-bike BC. My name is [AI Assistant]. How can I help you today?"
    • When customer mentions partnership interest, collect the following details:
        - Full Name: "May I have your full name, please?"
        - Company Name: "What company are you representing?"
        - Email Address: "What's the best email address to reach you at?"
        - Phone Number: "Could I get your phone number for our records?"
        - Partnership Type: "What type of partnership are you interested in? Retail, distribution, or something else?"
    • Once all details are collected, inform the customer: "Thank you for providing that information. I'm creating a lead for our partnerships team now."
    • Ask: "Would you like me to transfer you to our Business Development Team who handles partnerships?"
        - If Yes: "I'll transfer you to our Business Development Team right away. Please hold."
        - If No: "I've created a lead with your partnership inquiry. Our business development team will contact you within 48 hours."

Important Guidelines:
    • Always confirm each piece of information after the customer provides it.
    • If a customer is hesitant to provide information, reassure them: "I understand your concern. This information helps us create a proper record and ensures our team can follow up with the right solution. We maintain strict confidentiality of all customer information."
    • If the customer refuses to provide contact details, say: "I understand. Without contact information, we won't be able to create a lead or follow up. I can still provide general information about our products or you can reach us at sales@ebikebc.com when you're ready."
    • For incomplete information, politely ask again: "I'm sorry, I didn't catch your [missing information]. Could you please repeat that?"
    • End every call with: "Thank you for contacting E-bike BC. Is there anything else I can assist you with today?"

Remember: You must collect the customer's name, email, phone number, and product interest details before creating a Zoho CRM lead. The system will automatically create the lead once this information is available.
"""


VOICE = 'alloy'

LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created'
]

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state storage for active calls
caller_sessions = {}


class CallerSession:
    def __init__(self, call_sid):
        self.call_sid = call_sid
        self.state = CallState.GREETING
        self.current_prompt = SYSTEM_MESSAGE
        self.department = None
        self.name = None
        self.email = None
        self.phone = None
        self.product_interest = None
        self.lead_source = None
        self.description = None
        self.representative_available = False  # Flag for representative availability

    
if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')


@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "E-Bike BC Call System is running!"}


@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    
    # Initialize a new session for this call
    caller_sessions[call_sid] = CallerSession(call_sid)
    
    response = VoiceResponse()
    response.say("Hello! Thanks for calling E-bike BC. This call may be recorded for quality and training purposes.")
    response.pause(length=1)
    response.say("How can I assist you today?")
    host = request.url.hostname
    
    connect = Connect()
    connect.stream(url=f'wss://{host}/media-stream')
    response.append(connect)
    
    return HTMLResponse(content=str(response), media_type="application/xml")



@app.post("/create-ticket")
async def create_ticket(user_info: dict):
    """Create a Zoho Desk ticket."""
    try:
        payload = {
            "subject": f"Support Request from {user_info['name']}",
            "email": user_info['email'],
            "description": user_info.get('query', 'No description provided'),
            "phone": user_info.get('phone', ""),
            "departmentId": "185141000000010772",  
            "contact": {
                "firstName": user_info.get('first_name', user_info.get('name', 'Customer')),
                "lastName": user_info.get('last_name', ''),
                "email": user_info['email'],
                "phone": user_info.get('phone', '')
            }
        }

        headers = {
            "Authorization": f"Bearer {ZOHO_API_TOKEN}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post("https://desk.zoho.in/api/v1/tickets", json=payload, headers=headers)

        if response.status_code in [200, 201]:
            return {"message": "Ticket created successfully", "response": response.json()}
        else:
            return {
                "message": "Failed to create ticket",
                "status_code": response.status_code,
                "response": response.text
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating ticket: {str(e)}")


@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    print("Client connected")
    await websocket.accept()

    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
        extra_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        await initialize_session(openai_ws)

        stream_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None
        user_info = {}

        async def receive_from_twilio():
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)

                    if data['event'] == 'media' and openai_ws.open:
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))

                    elif data['event'] == 'text' and openai_ws.open:
                        text_input = {
                            "type": "conversation.item.create",
                            "item": {
                                "type": "message",
                                "role": "user",
                                "content": [{"type": "input_text", "text": data['text']}]
                            }
                        }
                        print("----------------User Input-------------->>",text_input)
                        await openai_ws.send(json.dumps(text_input))
                    

            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

        async def send_to_twilio():
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)

                    if response.get("type") == "response.content.text":
                        text_response = {
                            "event": "text",
                            "streamSid": stream_sid,
                            "text": response.get("text", "")
                        }
                        await websocket.send_json(text_response)

                    elif response.get("type") == "response.audio.delta" and 'delta' in response:
                        audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                        audio_delta = {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {"payload": audio_payload}
                        }
                        await websocket.send_json(audio_delta)

            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        await asyncio.gather(receive_from_twilio(), send_to_twilio())


        async def handle_speech_started_event():
            nonlocal response_start_timestamp_twilio, last_assistant_item
            print("Handling speech started event.")

            if mark_queue and response_start_timestamp_twilio is not None:
                elapsed_time = latest_media_timestamp - response_start_timestamp_twilio

                if last_assistant_item:
                    truncate_event = {
                        "type": "conversation.item.truncate",
                        "item_id": last_assistant_item,
                        "content_index": 0,
                        "audio_end_ms": elapsed_time
                    }
                    await openai_ws.send(json.dumps(truncate_event))

                await websocket.send_json({"event": "clear", "streamSid": stream_sid})
                mark_queue.clear()
                last_assistant_item = None
                response_start_timestamp_twilio = None

            # If user_info contains necessary details, create the lead
            if user_info.get('email') and user_info.get('phone') and (user_info.get('name') or (user_info.get('first_name') and user_info.get('last_name'))):
                print("----->>>> Creating Zoho CRM lead with user info:----->>>", user_info)
                await create_ticket(user_info)

        async def send_mark(connection, stream_sid):
            if stream_sid:
                mark_event = {"event": "mark", "streamSid": stream_sid, "mark": {"name": "responsePart"}}
                await connection.send_json(mark_event)
                mark_queue.append('responsePart')

        await asyncio.gather(receive_from_twilio(), send_to_twilio())



async def initialize_session(openai_ws):
    """Control initial session with OpenAI."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.6,
            "tools": [
                {
                    "type": "function",
                    "name": "support_ticket_creation",
                    "description": "Creates a support ticket in Zoho Desk for customer service inquiries",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Customer's full name"},
                            "email": {"type": "string", "description": "Customer's email address"},
                            "phone": {"type": "string", "description": "Customer's phone number"},
                            "description": {"type": "string", "description": "Details of the support issue"}
                        },
                        "required": ["name", "email", "phone", "description"]
                    }
                }
            ],
            "tool_choice": "auto"
        }
    }

    await openai_ws.send(json.dumps(session_update))

    # AI speaks first with greeting
    initial_greeting = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Hello! Thanks for calling E-bike BC. This call may be recorded for quality and training purposes"
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_greeting))
    await openai_ws.send(json.dumps({"type": "response.create"}))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)