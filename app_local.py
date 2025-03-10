# import os
# import json
# import base64
# import asyncio
# import websockets
# import requests
# from fastapi import FastAPI, WebSocket, Request
# from fastapi.responses import HTMLResponse, JSONResponse
# from fastapi.websockets import WebSocketDisconnect
# from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
# from dotenv import load_dotenv

# load_dotenv()

# # Configuration
# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# ZOHO_API_TOKEN = os.getenv('ZOHO_API_TOKEN')
# ZOHO_ORG_ID = os.getenv('ZOHO_ORG_ID')
# ZOHO_DESK_DOMAIN = os.getenv('ZOHO_DESK_DOMAIN')
# PORT = int(os.getenv('PORT', 8000))

# SYSTEM_MESSAGE = """
#     "Role: "
#     "For Support queries, collect the customer's details including name, email, and product-related interest, and create a Zoho support ticket. "
#     "If the customer wants to connect with the Support Team, transfer the call accordingly. "
    
#     "User Intent Handling: "

#     "1. Sales Query Handling: "
#     "• Greet the customer and ask how you can assist. "
#     "• Collect the following details: "
#     "  - Full Name "
#     "  - Email Address "
#     "  - Phone Number "
#     "  - E-bike Model or Product of Interest "
#     "• Create a Zoho support ticket with the collected details. "
#     "• Ask the customer if they would like to speak with the Sales Team. "
#     "  - If Yes: Transfer the call to the Sales Team. "
#     "  - If No: Confirm that a ticket has been created and provide the reference number. "

#     "2. Support Query Handling: "
#     "• Greet the customer and ask about their issue. "
#     "• Collect the following details: "
#     "  - Full Name "
#     "  - Email Address "
#     "  - Phone Number "
#     "  - E-bike Model or Product Issue "
#     "• Create a Zoho support ticket with the collected details. "
#     "• Ask the customer if they would like to speak with the Support Team. "
#     "  - If Yes: Transfer the call to the Support Team. "
#     "  - If No: Confirm that a ticket has been created and provide the reference number. "

#     "3. Partnership Query Handling: "
#     "• Greet the customer and ask how you can assist. "
#     "• Collect the following details: "
#     "  - Full Name "
#     "  - Email Address "
#     "  - Phone Number "
#     "  - Nature of the Partnership Inquiry "
#     "• Create a Zoho support ticket with the collected details. "
#     "• Ask if they would like to speak with the Sales Team. "
#     "  - If Yes: Transfer the call to the Sales Team. "
#     "  - If No: Confirm that a ticket has been created and provide the reference number. "

#     "After collecting all necessary information, create a support ticket in Zoho with the following information:
#     - Customer name
#     - Email address
#     - Phone number
#     - Query type (Sales, Support, or Partnership)
#     - Detailed description
    
#     "When you have all required information, tell the customer 'I'll create a ticket for you now' and then create the ticket by sending a JSON object in this format:
#     {
#         'action': 'create_ticket',
#         'data': {
#             'name': 'Customer Name',
#             'email': 'customer@example.com',
#             'phone': '1234567890',
#             'query_type': 'Sales/Support/Partnership',
#             'details': 'Detailed description of their inquiry'
#         }
#     }
    
#     "If the customer wants to be transferred to a team, tell them 'I'll transfer you to our [team name] now' and then transfer the call by sending a JSON object in this format:
#     {
#         'action': 'transfer_call',
#         'data': {
#             'department': 'Sales Team/Support Team'
#         }
#     }

#     "Additional Features: "
#     "• If a customer hesitates, provide reassurance: "
#     "  'Providing your details helps us serve you better and ensures that our team can follow up with the right solution.' "
#     "• If the customer declines to share information, offer general guidance and provide an email for further inquiries. "
#     "• End the call with a polite closing: "
#     "  'Thank you for reaching out to E-bike BC! Your request has been logged, and our team will follow up shortly.' "
# """

# from openai import OpenAI
# client = OpenAI()

# assistant = client.beta.assistants.create(
#   instructions="You are a customer support bot. Use the provided functions to answer questions.",
#   model="gpt-4o",
#   tools = [
#         {
#             "type": "function",
#             "function": {
#                 "name": "create_support_ticket",
#                 "description": "Create a Zoho support ticket for customer queries.",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "name": {"type": "string", "description": "Full Name of the customer"},
#                         "email": {"type": "string", "description": "Email Address of the customer"},
#                         "phone": {"type": "string", "description": "Phone Number of the customer"},
#                         "query_type": {
#                             "type": "string",
#                             "enum": ["Sales", "Support", "Partnership"],
#                             "description": "The type of query the customer has."
#                         },
#                         "details": {"type": "string", "description": "Detailed description of the issue or inquiry"},
#                         "product": {"type": "string", "description": "E-bike model or product of interest (if applicable)"}
#                     },
#                     "required": ["name", "email", "phone", "query_type", "details"]
#                 }
#             }
#         },
#         {
#             "type": "function",
#             "function": {
#                 "name": "transfer_call",
#                 "description": "Transfer the call to the appropriate team based on customer request.",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "department": {
#                             "type": "string",
#                             "enum": ["Sales Team", "Support Team"],
#                             "description": "The team to transfer the call to."
#                         }
#                     },
#                     "required": ["department"]
#                 }
#             }
#         }
#     ]
# )

# thread = client.beta.threads.create()
# message = client.beta.threads.messages.create(
#   thread_id=thread.id,
#   role="user",
#   content="Can you create a ticket for inquiry?",
# )


# VOICE = 'alloy'


# LOG_EVENT_TYPES = [
#     'error', 'response.content.done', 'rate_limits.updated',
#     'response.done', 'input_audio_buffer.committed',
#     'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
#     'session.created','tool_use'
# ]

# SHOW_TIMING_MATH = False

# app = FastAPI()

# if not OPENAI_API_KEY:
#     raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')
# if not ZOHO_API_TOKEN:
#     raise ValueError('Missing the Zoho API key. Please set it in the .env file.')
# if not ZOHO_ORG_ID:
#     raise ValueError('Missing the Zoho organization ID. Please set it in the .env file.')

# from datetime import datetime
# JSON_DATA_DIR = os.getenv('JSON_DATA_DIR', 'ticket_data')
# os.makedirs(JSON_DATA_DIR, exist_ok=True)

# def save_ticket_data(ticket_data):
#     """Save ticket data to a JSON file."""
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"{JSON_DATA_DIR}/ticket_{timestamp}_{ticket_data['name'].replace(' ', '_')}.json"
    
#     with open(filename, 'w') as f:
#         json.dump(ticket_data, f, indent=4)
    
#     print(f"Saved ticket data to {filename}")
#     return filename


# def create_zoho_ticket(ticket_data, filename):
#     """Create a ticket in Zoho Desk API using saved JSON data."""
#     try:
#         # First, update the file to indicate processing has started
#         with open(filename, 'r') as f:
#             saved_data = json.load(f)
        
#         saved_data['status'] = 'processing'
        
#         with open(filename, 'w') as f:
#             json.dump(saved_data, f, indent=4)
        
#         # Transform the data into Zoho's expected format
#         zoho_ticket = {
#             "subject": f"{ticket_data['query_type']} Query from {ticket_data['name']}",
#             "departmentId": "YOUR_DEPARTMENT_ID",  # Set appropriate department ID
#             "contactId": "YOUR_DEFAULT_CONTACT_ID",  # Can be updated to lookup or create contacts
#             "description": ticket_data['details'],
#             "email": ticket_data['email'],
#             "phone": ticket_data['phone'],
#             "status": "Open",
#             "priority": "Medium",
#             "classification": ticket_data['query_type'],
#             "customFields": {
#                 "cf_query_type": ticket_data['query_type']
#             }
#         }
        
#         if 'product' in ticket_data and ticket_data['product']:
#             zoho_ticket["customFields"]["cf_product"] = ticket_data['product']
        
#         # In a real implementation, you would make an API request to Zoho here
#         # For demonstration, we'll just simulate a successful response
        
#         # Simulate API response
#         ticket_id = f"TK{datetime.now().strftime('%Y%m%d%H%M%S')}"
#         ticket_number = f"#{datetime.now().strftime('%Y%m%d%H%M')}"
        
#         # Update the file with the result
#         with open(filename, 'r') as f:
#             saved_data = json.load(f)
        
#         saved_data['status'] = 'completed'
#         saved_data['ticket_id'] = ticket_id
#         saved_data['ticket_number'] = ticket_number
        
#         with open(filename, 'w') as f:
#             json.dump(saved_data, f, indent=4)
        
#         return {
#             "success": True,
#             "ticket_id": ticket_id,
#             "ticket_number": ticket_number,
#             "filename": filename
#         }
#     except Exception as e:
#         print(f"Error creating Zoho ticket: {str(e)}")
        
#         # Update the file with the error
#         try:
#             with open(filename, 'r') as f:
#                 saved_data = json.load(f)
            
#             saved_data['status'] = 'error'
#             saved_data['error'] = str(e)
            
#             with open(filename, 'w') as f:
#                 json.dump(saved_data, f, indent=4)
#         except Exception as write_error:
#             print(f"Error updating ticket file with error: {str(write_error)}")
        
#         return {
#             "success": False,
#             "error": str(e),
#             "filename": filename
#         }


# def process_transfer_call(transfer_data):
#     """Process a call transfer request."""
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"{JSON_DATA_DIR}/transfer_{timestamp}.json"
    
#     with open(filename, 'w') as f:
#         json.dump(transfer_data, f, indent=4)
    
#     print(f"Saved transfer data to {filename}")
    
#     # In a real implementation, you would implement call transfer logic here
#     # For demonstration, we'll just return a success response
    
#     return {
#         "success": True,
#         "department": transfer_data["department"],
#         "message": f"Call will be transferred to {transfer_data['department']}",
#         "filename": filename
#     }




# @app.get("/", response_class=JSONResponse)
# async def index_page():
#     return {"message": "Media Stream Server is running....!"}


# @app.api_route("/incoming-call", methods=["GET", "POST"])
# async def handle_incoming_call(request: Request):
#     """Handle incoming call and return TwiML response to connect to Media Stream."""
#     response = VoiceResponse()
#     response.say("Please wait while we connect your call to the A. I. voice assistant, powered by the Open-A.I.")
#     response.pause(length=1)
#     response.say("O.K. you can start talking!")
#     host = request.url.hostname
#     connect = Connect()
#     connect.stream(url=f'wss://{host}/media-stream')
#     response.append(connect)
#     return HTMLResponse(content=str(response), media_type="application/xml")




# @app.websocket("/media-stream")
# async def handle_media_stream(websocket: WebSocket):
#     """Handle WebSocket connections between Twilio and OpenAI."""
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

#         # Connection specific state
#         stream_sid = None
#         latest_media_timestamp = 0
#         last_assistant_item = None
#         mark_queue = []
#         response_start_timestamp_twilio = None
        
#         async def receive_from_twilio():
#             """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
#             nonlocal stream_sid, latest_media_timestamp
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
#                         print(f"Incoming stream has started {stream_sid}")
#                         response_start_timestamp_twilio = None
#                         latest_media_timestamp = 0
#                         last_assistant_item = None
#                     elif data['event'] == 'mark':
#                         if mark_queue:
#                             mark_queue.pop(0)
#             except WebSocketDisconnect:
#                 print("Client disconnected.")
#                 if openai_ws.open:
#                     await openai_ws.close()

#         async def send_to_twilio():
#             """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
#             nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio
#             try:
#                 async for openai_message in openai_ws:
#                     response = json.loads(openai_message)
#                     if response['type'] in LOG_EVENT_TYPES:
#                         print(f"Received event: {response['type']}", response)

#                     # Handle tool use events
#                     if response.get('type') == 'tool_use.submitted':
#                         tool_id = response.get('tool_use_id')
#                         tool_name = response.get('tool', {}).get('name')
#                         tool_params = response.get('parameters', {})
                        
#                         print(f"Tool use submitted: {tool_name} with params: {tool_params}")
                        
#                         try:
#                             if tool_name == 'create_support_ticket':
#                                 # Save data to file first
#                                 filename = save_ticket_data(tool_params)
                                
#                                 # Then create the ticket
#                                 result = create_zoho_ticket(tool_params, filename)
                                
#                                 # Send tool result back to OpenAI
#                                 if result['success']:
#                                     tool_result = {
#                                         "type": "tool_use.submit_result",
#                                         "tool_use_id": tool_id,
#                                         "result": {
#                                             "ticket_id": result['ticket_id'],
#                                             "ticket_number": result['ticket_number'],
#                                             "status": "success",
#                                             "message": f"Ticket #{result['ticket_number']} has been created successfully."
#                                         }
#                                     }
#                                 else:
#                                     tool_result = {
#                                         "type": "tool_use.submit_result",
#                                         "tool_use_id": tool_id,
#                                         "result": {
#                                             "status": "error",
#                                             "message": f"Failed to create ticket: {result['error']}"
#                                         }
#                                     }
                                
#                                 await openai_ws.send(json.dumps(tool_result))
                                
#                             elif tool_name == 'transfer_call':
#                                 # Process the transfer request
#                                 result = process_transfer_call(tool_params)
                                
#                                 # Send tool result back to OpenAI
#                                 tool_result = {
#                                     "type": "tool_use.submit_result",
#                                     "tool_use_id": tool_id,
#                                     "result": {
#                                         "status": "success",
#                                         "message": result['message']
#                                     }
#                                 }
                                
#                                 await openai_ws.send(json.dumps(tool_result))
#                         except Exception as e:
#                             print(f"Error handling tool use: {e}")
#                             # Send error back to OpenAI
#                             tool_result = {
#                                 "type": "tool_use.submit_result",
#                                 "tool_use_id": tool_id,
#                                 "result": {
#                                     "status": "error",
#                                     "message": f"Error: {str(e)}"
#                                 }
#                             }
#                             await openai_ws.send(json.dumps(tool_result))

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
#                             if SHOW_TIMING_MATH:
#                                 print(f"Setting start timestamp for new response: {response_start_timestamp_twilio}ms")

#                         # Update last_assistant_item safely
#                         if response.get('item_id'):
#                             last_assistant_item = response['item_id']

#                         await send_mark(websocket, stream_sid)

#                     # Trigger an interruption
#                     if response.get('type') == 'input_audio_buffer.speech_started':
#                         print("Speech started detected.")
#                         if last_assistant_item:
#                             print(f"Interrupting response with id: {last_assistant_item}")
#                             await handle_speech_started_event()
#             except Exception as e:
#                 print(f"Error in send_to_twilio: {e}")

#         async def handle_speech_started_event():
#             """Handle interruption when the caller's speech starts."""
#             nonlocal response_start_timestamp_twilio, last_assistant_item
#             print("Handling speech started event.")
#             if mark_queue and response_start_timestamp_twilio is not None:
#                 elapsed_time = latest_media_timestamp - response_start_timestamp_twilio
#                 if SHOW_TIMING_MATH:
#                     print(f"Calculating elapsed time for truncation: {latest_media_timestamp} - {response_start_timestamp_twilio} = {elapsed_time}ms")

#                 if last_assistant_item:
#                     if SHOW_TIMING_MATH:
#                         print(f"Truncating item with ID: {last_assistant_item}, Truncated at: {elapsed_time}ms")

#                     truncate_event = {
#                         "type": "conversation.item.truncate",
#                         "item_id": last_assistant_item,
#                         "content_index": 0,
#                         "audio_end_ms": elapsed_time
#                     }
#                     await openai_ws.send(json.dumps(truncate_event))

#                 await websocket.send_json({
#                     "event": "clear",
#                     "streamSid": stream_sid
#                 })

#                 mark_queue.clear()
#                 last_assistant_item = None
#                 response_start_timestamp_twilio = None

#         async def send_mark(connection, stream_sid):
#             if stream_sid:
#                 mark_event = {
#                     "event": "mark",
#                     "streamSid": stream_sid,
#                     "mark": {"name": "responsePart"}
#                 }
#                 await connection.send_json(mark_event)
#                 mark_queue.append('responsePart')

#         await asyncio.gather(receive_from_twilio(), send_to_twilio())

# async def send_initial_conversation_item(openai_ws):
#     """Send initial conversation item if AI talks first."""
#     initial_conversation_item = {
#         "type": "conversation.item.create",
#         "item": {
#             "type": "message",
#             "role": "user",
#             "content": [
#                 {
#                     "type": "input_text",
#                     "text": "Greet the user with 'Hello there! Thank you for calling E-bike BC. I'm your AI assistant and I'm here to help with your e-bike inquiries. How can I assist you today?'"
#                 }
#             ]
#         }
#     }
#     await openai_ws.send(json.dumps(initial_conversation_item))
#     await openai_ws.send(json.dumps({"type": "response.create"}))


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
#             "tools": assistant
#         }
#     }

#     dumped_data = json.dumps(session_update)
#     print('Sending session update:', dumped_data)
#     await openai_ws.send(dumped_data)

#     # Have the AI speak first
#     await send_initial_conversation_item(openai_ws)


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=PORT)



import uvicorn
import os
import json
import base64
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PORT = int(os.getenv('PORT', 8000))
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

SYSTEM_MESSAGE = """
Role:
You are a customer support assistant responsible for handling Sales, Support, Partnership, and Customer Service queries for E-bike BC. Your tasks include collecting customer details, creating Zoho support tickets, and transferring calls when needed.

**Call Greeting:**
"Hello! Thanks for calling E-bike BC. This call may be recorded for quality and training purposes.
I am Eva. How can I assist you?
I’m here to assist you with sales inquiries, technical support, partnership opportunities, and customer service. How may I help you today?"

User Intent Handling:

1. **Sales Query Handling**
  - AI Agent: "I can help answer your questions. How can I assist you today?"
  - If the question is answered: "Glad I could help! Have a great day!" [End Call]
  - If not answered, ask:
   - "Would you like to speak with a representative or create a support ticket?"
   - If they choose **Representative**:
    - Check for agent availability.
    - If available: "Connecting you now to a sales representative." [Transfer Call]
    - If not picked: "The representative is unavailable. I can create a ticket for you instead." [Proceed to Ticket Creation]
   - If they choose **Ticket Creation**:
    - "I will create a support ticket for you. Please provide your name, email, phone number, and the e-bike model or product of interest."
    - Capture details (voice-to-text).
    - "Your ticket has been successfully created. Someone will get back to you shortly. Have a great day!" [End Call]
  - **Once a sales query is resolved, end the call.**

2. **Support Query Handling**
  - Greet the customer and ask about their issue.
  - Collect the following details:
   - Full Name
   - Email Address
   - Phone Number
   - E-bike Model or Product Issue
  - Create a Zoho support ticket with the collected details.
  - Ask if they would like to speak with the Support Team:
   - **If Yes:** Transfer the call to the Support Team.
   - **If No:** Confirm that a ticket has been created and provide the reference number.
  - **Once a support query is resolved, end the call.**

3. **Partnership Query Handling**
  - AI Agent: "How can I assist you with partnerships or general inquiries?"
  - If the question is answered: "Glad I could help! Have a great day!" [End Call]
  - If not answered, ask:
   - "Would you like to speak with a representative or create a ticket?"
   - If they choose **Representative**:
    - Check for availability.
    - If available: "Connecting you now." [Transfer Call]
    - If not picked: "The representative is currently unavailable. I will create a ticket for you." [Proceed to Ticket Creation]
   - If they choose **Ticket Creation**:
    - "I will create a support ticket for you. Please provide your name, email, and a brief description of your query."
    - Capture details (voice-to-text).
    - "Your ticket has been successfully created. Someone will get back to you shortly. Have a great day!"
  - **Once a partnership query is resolved, end the call.**

4. **Customer Service Query Handling**
  - AI Agent: "I can assist with customer service queries. How can I help?"
  - If the question is answered: "Glad I could help! Have a great day!" [End Call]
  - If not answered, say:
   - "Our customer service is ticket-based. Let me help you create a support ticket."
   - "Please provide your name, email, and a brief description of your issue."
   - Capture details (voice-to-text).
   - "Your ticket has been created successfully. Our team will reach out to you soon. Have a great day!" [End Call]
  - **Once a customer service query is resolved, end the call.**

Additional Guidelines:
- **Reassurance for Hesitant Customers:**
  - If a customer hesitates to share details, reassure them:
   *"Providing your details helps us serve you better and ensures that our team can follow up with the right solution."*
- **Handling Refusals:**
  - If a customer declines to share information, provide general guidance and offer an email for further inquiries.
- **Polite Call Closure:**
  - End each call with:
   *"Thank you for reaching out to E-bike BC! Your request has been logged, and our team will follow up shortly."*

IMPORTANT: After saying the final closure message "Thank you for reaching out to E-bike BC! Your request has been logged, and our team will follow up shortly." always include the special phrase "[HANGUP_CALL]" at the end of your response to signal that the call should be ended automatically.
"""

VOICE = 'shimmer'

LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created'
]

SHOW_TIMING_MATH = False

app = FastAPI()

if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')

if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
    print('Warning: Twilio credentials not set. Call hangup functionality will not work.')

# Data Storage
call_data = {}

def add_call_data(call_sid, key, value):
    if call_sid not in call_data:
        call_data[call_sid] = {}
    call_data[call_sid][key] = value

def get_call_data(call_sid, key):
    if call_sid in call_data and key in call_data[call_sid]:
        return call_data[call_sid][key]
    return None

def extract_ticket_data(call_sid):
    if call_sid in call_data:
        return call_data[call_sid]
    return {}

async def create_ticket(ticket_data):
    """Placeholder for ticket creation."""
    print(f"Creating ticket with data: {ticket_data}")
    # Replace this with your actual Zoho API integration
    await asyncio.sleep(1)  # Simulate API call
    print("Ticket created successfully.")

@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Media Stream Server is running....!"}

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()
    host = request.url.hostname
    connect = Connect()
    connect.stream(url=f'wss://{host}/media-stream')
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
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

        # Connection specific state
        stream_sid = None
        call_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None
        response_content = ""
        should_hang_up = False
        collecting_data = None # Tracks what data to collect

        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid, call_sid, latest_media_timestamp
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media' and openai_ws.open:
                        latest_media_timestamp = int(data['media']['timestamp'])
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))

                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        call_sid = data['start'].get('callSid')  # Store the call SID for hangup
                        print(f"Incoming stream has started {stream_sid} for call {call_sid}")
                        response_start_timestamp_twilio = None
                        latest_media_timestamp = 0
                        last_assistant_item = None
                        call_data[call_sid] = {} # Initialize call data
                    elif data['event'] == 'mark':
                        if mark_queue:
                            mark_queue.pop(0)
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid, call_sid, last_assistant_item, response_start_timestamp_twilio, response_content, should_hang_up, collecting_data
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)

                    # Collect response content to check for hangup trigger
                    if response.get('type') == 'response.content.delta' and 'delta' in response:
                        if 'text' in response['delta']:
                            response_content += response['delta']['text']
                            # Check if the response contains the hangup trigger
                            if "[HANGUP_CALL]" in response_content:
                                print("Hangup trigger detected in response")
                                should_hang_up = True
                                # Remove the trigger from the processed text
                                response_content = response_content.replace("[HANGUP_CALL]", "")

                            # Data collection logic
                            if collecting_data:
                                add_call_data(call_sid, collecting_data, response['delta']['text'].strip())
                                collecting_data = None  # Reset after collecting

                            # Check for data requests
                            if "Please provide your name" in response_content:
                                collecting_data = "name"
                            elif "Please provide your email" in response_content:
                                collecting_data = "email"
                            elif "Please provide your phone number" in response_content:
                                collecting_data = "phone"
                            elif "E-bike Model" in response_content or "description of your query" in response_content or "description of your issue" in response_content:
                                collecting_data = "details"

                    if response.get('type') == 'response.audio.delta' and 'delta' in response:
                        audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                        audio_delta = {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {
                                "payload": audio_payload
                            }
                        }
                        await websocket.send_json(audio_delta)

                        if response_start_timestamp_twilio is None:
                            response_start_timestamp_twilio = latest_media_timestamp
                            if SHOW_TIMING_MATH:
                                print(f"Setting start timestamp for new response: {response_start_timestamp_twilio}ms")

                        # Update last_assistant_item safely
                        if response.get('item_id'):
                            last_assistant_item = response['item_id']

                        await send_mark(websocket, stream_sid)

                    # Check if we should hang up after response is complete
                    if response.get('type') == 'response.done' and should_hang_up and call_sid:
                        print(f"Hanging up call {call_sid} after final message")
                        await hang_up_call(call_sid)
                        should_hang_up = False  # Reset flag

                        # Create ticket after hangup
                        ticket_data = extract_ticket_data(call_sid)
                        if ticket_data:
                            await create_ticket(ticket_data)

                    # Trigger an interruption. Your use case might work better using `input_audio_buffer.speech_stopped`, or combining the two.
                    if response.get('type') == 'input_audio_buffer.speech_started':
                        print("Speech started detected.")
                        if last_assistant_item:
                            print(f"Interrupting response with id: {last_assistant_item}")
                            await handle_speech_started_event()

            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        async def handle_speech_started_event():
            """Handle interruption when the caller's speech starts."""
            nonlocal response_start_timestamp_twilio, last_assistant_item
            print("Handling speech started event.")
            if mark_queue and response_start_timestamp_twilio is not None:
                elapsed_time = latest_media_timestamp - response_start_timestamp_twilio
                if SHOW_TIMING_MATH:
                    print(f"Calculating elapsed time for truncation: {latest_media_timestamp} - {response_start_timestamp_twilio} = {elapsed_time}ms")

                if last_assistant_item:
                    if SHOW_TIMING_MATH:
                        print(f"Truncating item with ID: {last_assistant_item}, Truncated at: {elapsed_time}ms")

                    truncate_event = {
                        "type": "conversation.item.truncate",
                        "item_id": last_assistant_item,
                        "content_index": 0,
                        "audio_end_ms": elapsed_time
                    }
                    await openai_ws.send(json.dumps(truncate_event))

                await websocket.send_json({
                    "event": "clear",
                    "streamSid": stream_sid
                })

                mark_queue.clear()
                last_assistant_item = None
                response_start_timestamp_twilio = None

        async def send_mark(connection, stream_sid):
                    if stream_sid:
                        mark_event = {
                            "event": "mark",
                            "streamSid": stream_sid,
                            "mark": {"name": "responsePart"}
                        }
                        await connection.send_json(mark_event)
                        mark_queue.append('responsePart')        

        async def hang_up_call(call_sid):
            """Hang up the Twilio call."""
            if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and call_sid:
                try:
                    # Use Twilio REST API to hang up the call
                    twilio_client.calls(call_sid).update(status="completed")
                    print(f"Successfully hung up call {call_sid}")
                except Exception as e:
                    print(f"Error hanging up call: {e}")
            else:
                print("Cannot hang up call: Missing Twilio credentials or call_sid")

        await asyncio.gather(receive_from_twilio(), send_to_twilio())

async def send_initial_conversation_item(openai_ws):
            """Send initial conversation item if AI talks first."""
            initial_conversation_item = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Greet the user with 'Hello! Thanks for calling E-bike BC. This call may be recorded for quality and training purposes. I am Eva. How can I assist you?'"
                        }
                    ]
                }
            }
            await openai_ws.send(json.dumps(initial_conversation_item))
            await openai_ws.send(json.dumps({"type": "response.create"}))       

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
                }
            }

            dumped_data = json.dumps(session_update)
            print("duped_Data-------------->", dumped_data)
            loaded_data = json.dumps(session_update)
            print("loaded_Data-------------->", loaded_data)
            print('Sending session update:', json.dumps(session_update))
            await openai_ws.send(loaded_data)

            # Uncomment the next line to have the AI speak first
            await send_initial_conversation_item(openai_ws)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
                

