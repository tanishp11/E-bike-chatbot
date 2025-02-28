import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import twilio
from twilio.rest import Client
from fastapi.responses import HTMLResponse
import json
import websockets
import asyncio
from dotenv import load_dotenv
import base64
from datetime import datetime, timedelta

load_dotenv()

openai_ws = None

# Load environment variables from .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
# TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
# TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
# YOUR_PHONE_NUMBER = os.getenv("YOUR_PHONE_NUMBER")
PORT = int(os.getenv("PORT", 8000))

# if not all([OPENAI_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, YOUR_PHONE_NUMBER]):
#     print("Missing environment variables. Check .env file.")
#     exit(1)

# Initialize FastAPI app
app = FastAPI()

# Initialize Twilio client
# twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

VOICE = 'sage'

SYSTEM_MESSAGE = '''
 "Role: "
    "For Support queries, collect the customer's details including name, email, and product-related interest, and create a Zoho support ticket. "
    "If the customer wants to connect with the Support Team, transfer the call accordingly. "
    
    "User Intent Handling: "

    "1. Sales Query Handling: "
    "• Greet the customer and ask how you can assist. "
    "• Collect the following details: "
    "  - Full Name "
    "  - Email Address "
    "  - Phone Number "
    "  - E-bike Model or Product of Interest "
    "• Create a Zoho support ticket with the collected details. "
    "• Ask the customer if they would like to speak with the Sales Team. "
    "  - If Yes: Transfer the call to the Sales Team. "
    "  - If No: Confirm that a ticket has been created and provide the reference number. "

    "2. Support Query Handling: "
    "• Greet the customer and ask about their issue. "
    "• Collect the following details: "
    "  - Full Name "
    "  - Email Address "
    "  - Phone Number "
    "  - E-bike Model or Product Issue "
    "• Create a Zoho support ticket with the collected details. "
    "• Ask the customer if they would like to speak with the Support Team. "
    "  - If Yes: Transfer the call to the Support Team. "
    "  - If No: Confirm that a ticket has been created and provide the reference number. "

    "3. Partnership Query Handling: "
    "• Greet the customer and ask how you can assist. "
    "• Collect the following details: "
    "  - Full Name "
    "  - Email Address "
    "  - Phone Number "
    "  - Nature of the Partnership Inquiry "
    "• Create a Zoho support ticket with the collected details. "
    "• Ask if they would like to speak with the Sales Team. "
    "  - If Yes: Transfer the call to the Sales Team. "
    "  - If No: Confirm that a ticket has been created and provide the reference number. "

    "Additional Features: "
    "• If a customer hesitates, provide reassurance: "
    "  'Providing your details helps us serve you better and ensures that our team can follow up with the right solution.' "
    "• If the customer declines to share information, offer general guidance and provide an email for further inquiries. "
    "• End the call with a polite closing: "
    "  'Thank you for reaching out to E-bike BC! Your request has been logged, and our team will follow up shortly.' "
'''

# Home Route
@app.get("/")
async def home():
    return {"message": "Twilio Media Stream Server is running!"}

# Route for initiating a call to YOUR_PHONE_NUMBER
@app.get("/initiate-call")
async def initiate_call():
    try:
        url = f"http://{os.getenv('HOST', 'localhost')}/incoming-call"
        # call = twilio_client.calls.create(
        #     to=YOUR_PHONE_NUMBER,
        #     from_=TWILIO_PHONE_NUMBER,
        #     url=url
        # )
        #return {"message": "Call initiated", "callSid": call.sid}
    except Exception as e:
        print(f"Error initiating call: {e}")
        return {"error": "Failed to initiate call"}, 500

# Route for handling incoming call from Twilio
@app.post("/incoming-call")
async def incoming_call():
    host = os.getenv('HOST', 'localhost')
    return f"""<?xml version="1.0" encoding="UTF-8"?>
                <Response>
                    <Pause length="1"/>
                    <Connect>
                        <Stream url="wss://{host}/media-stream" />
                    </Connect>
                </Response>"""

# WebSocket route for handling media stream
@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    await websocket.accept()

    # Initialize WebSocket connection to OpenAI
    async with websockets.connect(
        f"wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01",
        extra_headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "OpenAI-Beta": "realtime=v1"}
    ) as openai_ws:

        # Session initialization with OpenAI API
        session_update = {
            "type": "session.update",
            "session": {
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 200
                },
                "input_audio_format": 'g711_ulaw',
                "output_audio_format": 'g711_ulaw',
                "voice": VOICE,
                "instructions": SYSTEM_MESSAGE,
                "modalities": ["text", "audio"],
                "temperature": 0.8,
                "tools": [
                    {
                        "type": "function",
                        "name": "confirm_mobile_number",
                        "description": "Confirm the customer's mobile number and send an OTP for verification.",
                        "parameters": {"type": "object", "properties": {"phone_number": {"type": "string"}}}
                    },
                    {
                        "type": "function",
                        "name": "verify_otp",
                        "description": "Verify the OTP entered by the customer.",
                        "parameters": {"type": "object", "properties": {"phone_number": {"type": "string"}, "otp": {"type": "string"}}}
                    },
                    {
                        "type": "function",
                        "name": "track_order",
                        "description": "Track the customer's last order.",
                        "parameters": {"type": "object", "properties": {"phone_number": {"type": "string"}}}
                    }
                ],
                "tool_choice": "auto"
            }
        }
        await openai_ws.send(json.dumps(session_update))

        # Handle incoming media and responses from OpenAI
        async for message in websocket.iter_json():
            if message.get("event") == "media":
                # Forward media data to OpenAI
                await openai_ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": message['media']['payload']}))

            elif message.get("event") == "start":
                stream_sid = message["start"]["streamSid"]

            elif message.get("event") == "mark":
                # Handle marks (AI's responses)
                pass

        # Handle responses from OpenAI
        async for message in openai_ws:
            response = json.loads(message)
            if response['type'] == 'response.audio.delta' and 'delta' in response:
                audio_delta = {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {"payload": base64.b64encode(response['delta'].encode()).decode()}
                }
                await websocket.send_json(audio_delta)

            if response['type'] == 'response.function_call_arguments.done':
                await handle_function_calls(response)

# Function to handle OpenAI function calls
async def handle_function_calls(response):
    function_name = response["name"]
    args = json.loads(response["arguments"])

    if function_name == "confirm_mobile_number":
        await send_otp_response("123456")
    elif function_name == "verify_otp":
        if args["otp"] == "123456":
            await send_function_response("OTP verified successfully!")
        else:
            await send_function_response("Incorrect OTP. Please try again.")
    elif function_name == "track_order":
        order_status = f"Your order is in process and will be delivered by {calculate_delivery_date()}."
        await send_function_response(order_status)

# Function to send OTP response
async def send_otp_response(otp):
    otp_message = f"Your OTP is: {otp}"
    await send_function_response(otp_message)

# Function to send function response to OpenAI
async def send_function_response(message):
    function_output_event = {
        "type": "conversation.item.create",
        "item": {
            "type": "function_call_output",
            "role": "system",
            "output": message
        }
    }
    await openai_ws.send(json.dumps(function_output_event))

    # Request AI response
    await openai_ws.send(json.dumps({
        "type": "response.create",
        "response": {
            "modalities": ["text", "audio"],
            "instructions": f"Inform the user: {message}. Be concise and friendly."
        }
    }))

# Calculate the delivery date (3 working days)
def calculate_delivery_date():
    current_date = datetime.now()
    working_days_to_add = 3
    delivery_date = current_date

    while working_days_to_add > 0:
        delivery_date += timedelta(days=1)
        if delivery_date.weekday() < 5:  # Monday to Friday are working days
            working_days_to_add -= 1

    return delivery_date.strftime("%A, %B %d, %Y")


# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
