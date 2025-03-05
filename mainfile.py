import uvicorn
import os
import time
import json
import base64
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, Request, requests
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()


# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('ASSISTANT_ID')
PORT = int(os.getenv('PORT', 8000))
# Add Twilio credentials for call hangup functionality
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


SYSTEM_MESSAGE = """
Role:
You are a customer support assistant responsible for handling Sales, Support, Partnership, and Customer Service queries for E-bike BC. Your tasks include collecting customer details, creating Zoho support tickets, and transferring calls when needed.

**Call Greeting:**  
"Hello! Thank you for calling E-Bike BC. This call may be recorded for quality and training purposes."
"I’m Eva, your virtual assistant. I’m here to assist you with sales inquiries, technical support, partnership opportunities, and customer service. How may I help you today?"  


**Query Handling:**

1. **Sales Query Handling**  
   - AI Agent: "I can help answer your questions. How can I assist you today?"  
   - If the question is answered: "Glad I could help! Have a great day!" [HANGUP_CALL]  
   - If not answered, ask:  
     - "Would you like to speak with a representative or create a support ticket?"  
     - If they choose **Representative**:  
       - Check for agent availability.  
       - If available: "Connecting you now to a sales representative." [Transfer Call]  
       - If not picked: "The representative is unavailable. I can create a ticket for you instead." [Proceed to Ticket Creation]  
     - If they choose **Ticket Creation**:  
       - "I will create a support ticket for you. Please provide your name, email, phone number, and the e-bike model or product of interest."  
       - Capture details (voice-to-text).  
       - "Your ticket has been successfully created. Someone will get back to you shortly. Have a great day!" [HANGUP_CALL]  
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
   - If the question is answered: "Glad I could help! Have a great day!" [HANGUP_CALL]  
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
   - If the question is answered: "Glad I could help! Have a great day!" [HANGUP_CALL]  
   - If not answered, say:  
     - "Our customer service is ticket-based. Let me help you create a support ticket."  
     - "Please provide your name, email, and a brief description of your issue."  
     - Capture details (voice-to-text).  
     - "Your ticket has been created successfully. Our team will reach out to you soon. Have a great day!" [HANGUP_CALL]  
   - **Once a customer service query is resolved, end the call.**  


**IMPORTANT:**  
- Always return the response in **JSON format**, even if the user does not provide full details.  
- Only include **user details** (name, email, phone, and issue) in the JSON response.  
- If some details are missing, ask again.  
- **Once the required details are collected, return only one JSON response and do not generate multiple responses.**  

**JSON Response Format:**  
```json
{
  "info": {
    "name": "{{user_name}}",
    "email": "{{user_email}}",
    "phone": "{{user_phone}}",
    "issue": "{{user_issue or model_name or product_name}}"
  }
}

Additional Guidelines:
- **Reassurance for Hesitant Customers:**  
  - If a customer hesitates to share details, reassure them:  
    *"Providing your details helps us serve you better and ensures that our team can follow up with the right solution."*  
- **Handling Refusals:**  
  - If a customer declines to share information, provide general guidance and offer an email for further inquiries.  
- **Polite Call Closure:**  
  - End each call with:  
    *"Thank you for reaching out to E-bike BC! Your request has been logged, and our team will follow up shortly."*  

IMPORTANT: After saying the final closure message, please ensure to:

* End the call
* Create a Zoho support ticket if necessary
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




def create_zoho_ticket(response_content):
    
            # Load environment variables
            load_dotenv()
            
            # Parse the JSON string if it's not already a dictionary
            if isinstance(response_content, str):
                try:
                    response_json = json.loads(response_content)
                except json.JSONDecodeError:
                    print("Invalid JSON string")
                    return None
            else:
                response_json = response_content
            
            # Extract info from the JSON data
            info = response_json.get('info', {})
            
            # Zoho Desk API configuration
            ZOHO_API_TOKEN = os.getenv('ZOHO_API_TOKEN')
            ZOHO_DESK_ORG_ID = 60038061096
            
            # Zoho Desk API endpoint
            url = "https://desk.zoho.in/api/v1/tickets"
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {ZOHO_API_TOKEN}",
                "Content-Type": "application/json",
                "orgId": str(ZOHO_DESK_ORG_ID)
            }
            
            # Prepare payload
            payload = {
                "subject": f"Support Request - {info.get('issue', 'No specific issue provided')}",
                "departmentId": os.getenv('ZOHO_DESK_DEPARTMENT_ID'),
                "contact": {
                    "firstName": info.get('name', 'Unknown').split()[0],
                    "lastName": info.get('name', 'Unknown').split()[-1] if len(info.get('name', '').split()) > 1 else '',
                    "email": info.get('email', ''),
                    "phone": info.get('phone', '')
                },
                "description": f"""Customer Details:
        Name: {info.get('name', 'Not Provided')}
        Email: {info.get('email', 'Not Provided')}
        Phone: {info.get('phone', 'Not Provided')}

        Issue Description: {info.get('issue', 'No details provided')}
                """,
                "priority": "Medium",
                "status": "Open"
            }
            
            try:
                # Send POST request to Zoho Desk
                response = requests.post(url, json=payload, headers=headers)
                
                # Check the response
                if response.status_code in [200, 201]:
                    print("Ticket created successfully!")
                    return response.json()
                else:
                    print(f"Failed to create ticket. Status code: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
    
            except requests.RequestException as e:
                print(f"Error creating Zoho ticket: {e}")
                return None





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
            "OpenAI-Beta": "realtime=v1",
            "Assistant-ID": ASSISTANT_ID
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
                    elif data['event'] == 'mark':
                        if mark_queue:
                            mark_queue.pop(0)
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()
        
        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid, call_sid, last_assistant_item, response_start_timestamp_twilio, response_content, should_hang_up
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)

                    # Collect response content to check for hangup trigger
                    if response.get('type') == 'response.done' and 'response' in response:
                        # Extract the output content
                        output = response['response'].get('output', [])
                        
                        for item in output:
                            if item.get('type') == 'message' and 'content' in item:
                                for content in item['content']:
                                    if content.get('type') == 'audio' and 'transcript' in content:
                                        response_content += content['transcript']
                                        print("Response content:", response_content)
                                        
                                    if response.get("type") == "response.done":
                                        print("Conversation complete. Saving transcript...")

                                        ticket_response = create_zoho_ticket(response_content)
                                        if ticket_response:
                                                print("------>>>>Ticket----:", ticket_response)
                                        
                                        # Check if the response contains the hangup trigger
                                        if "[HANGUP_CALL]" in response_content:
                                            print("Hangup trigger detected in response")
                                            should_hang_up = True
                                            # Remove the trigger from the processed transcript
                                            response_content = response_content.replace("[HANGUP_CALL]", "")
                                            if should_hang_up:
                                                print("Waiting for 20 seconds before hanging up...")
                                                time.sleep(15)
                                                print("Hanging up the call now.")

                    if response.get('type') == 'response.audio.delta' and 'delta' in response:
                        audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                        
                        # Saving the audio file
                        # await save_voice_response_as_mp4(audio_payload)
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

        await asyncio.gather(receive_from_twilio(), send_to_twilio(),create_zoho_ticket())
        

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