from azure.communication.sms import SmsClient
from fastapi import FastAPI, Request, BackgroundTasks
from openai import AsyncAzureOpenAI
from datetime import datetime, timedelta, time
import os
import logging
import random
from dotenv import load_dotenv

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Appointment Reminder & Scheduling API")

# Simple storage
conversations = {}
appointments = {}
calendar = {}

def generate_calendar():
    """Generate 30-day mock calendar with 80% occupancy"""
    global calendar
    
    # Business hours: 9 AM to 5 PM (30-minute slots)
    time_slots = []
    current = datetime.combine(datetime.today(), time(9, 0))
    end = datetime.combine(datetime.today(), time(17, 0))
    
    while current < end:
        time_slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=30)
    
    # Generate 30 days (weekdays only)
    start_date = datetime.now().date()
    for i in range(30):
        date = start_date + timedelta(days=i)
        if date.weekday() >= 5:  # Skip weekends
            continue
        
        date_str = date.strftime("%Y-%m-%d")
        # Book 80% randomly, store available 20%
        available = random.sample(time_slots, int(len(time_slots) * 0.2))
        calendar[date_str] = available
    
    logger.info(f"Generated calendar for {len(calendar)} business days")

def get_available_slots(date_str, count=3):
    """Get available slots for a date"""
    if date_str in calendar:
        available = calendar[date_str]
        return random.sample(available, min(count, len(available)))
    return []

def format_date(date_str):
    """Convert YYYY-MM-DD to friendly format"""
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%A, %B %d")

def format_time(time_str):
    """Convert HH:MM to friendly format"""
    return datetime.strptime(time_str, "%H:%M").strftime("%I:%M %p").lstrip('0')

def get_sms_client():
    connection_string = os.environ.get("AZURE_COMMUNICATION_SERVICE_CONNECTION_STRING")
    if connection_string:
        return SmsClient.from_connection_string(connection_string)
    return None

def create_appointment(phone):
    """Create a mock appointment for tomorrow"""
    tomorrow = datetime.now() + timedelta(days=1)
    while tomorrow.weekday() >= 5:  # Skip weekends
        tomorrow += timedelta(days=1)
    
    times = ["09:00", "10:30", "14:00", "15:30"]
    appointments[phone] = {
        "date": tomorrow.strftime("%Y-%m-%d"),
        "time": random.choice(times)
    }
    return appointments[phone]

async def process_sms(event_data):
    events = event_data if isinstance(event_data, list) else [event_data]
    
    for event in events:
        if event.get("eventType") != "Microsoft.Communication.SMSReceived":
            continue
            
        data = event.get("data", {})
        message = data.get("message", "")
        sender = data.get("from", "")
        
        if not message or not sender:
            continue
            
        try:
            # First time caller gets appointment reminder
            if sender not in conversations:
                appt = create_appointment(sender)
                date_friendly = format_date(appt['date'])
                time_friendly = format_time(appt['time'])
                
                reminder = f"Hi! This is a reminder that you have a consultation scheduled for {date_friendly} at {time_friendly}. Can you confirm you'll be able to make it, or would you like to reschedule?"
                
                conversations[sender] = [
                    {"role": "system", "content": f"""You are a friendly and professional medical office receptionist. The customer has a consultation appointment scheduled for {date_friendly} at {time_friendly}.

Your responsibilities:
- Help them confirm their existing appointment or reschedule to a new time
- Be warm, helpful, and professional like a human receptionist would be
- When they want to reschedule, ask what day works better for them
- Offer specific available time slots from the calendar when they mention a day
- Confirm new appointment details clearly
- Keep responses concise but friendly
- Business hours are 9 AM to 5 PM, Monday through Friday
- All appointments are 30-minute consultations

Remember: You're helping with appointment scheduling, not providing medical advice."""},
                    {"role": "assistant", "content": reminder}
                ]
                await send_sms(sender, reminder)
                return
            
            # Continue conversation with context
            conversations[sender].append({"role": "user", "content": message})
            
            # Always provide current calendar context for intelligent responses
            current_prompt = conversations[sender][0]["content"]
            
            # Get next 5 business days with availability for AI context
            available_info = []
            current_date = datetime.now().date() + timedelta(days=1)
            days_checked = 0
            
            while len(available_info) < 5 and days_checked < 14:
                if current_date.weekday() < 5:  # Weekday
                    date_str = current_date.strftime("%Y-%m-%d")
                    slots = get_available_slots(date_str, 3)
                    if slots:
                        slots_friendly = [format_time(slot) for slot in slots]
                        available_info.append(f"- {format_date(date_str)}: {', '.join(slots_friendly)}")
                current_date += timedelta(days=1)
                days_checked += 1
            
            # Always update system prompt with fresh calendar data
            if available_info:
                calendar_context = f"\n\nCURRENT AVAILABLE APPOINTMENTS:\n" + "\n".join(available_info)
                calendar_context += "\n\nUse this information when customer needs to reschedule or asks about availability. Only show specific slots when they're actively looking to reschedule."
                
                # Update the system prompt with calendar info
                conversations[sender][0]["content"] = current_prompt.split("\n\nCURRENT AVAILABLE")[0] + calendar_context
            
            client = AsyncAzureOpenAI(
                azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
                api_key=os.environ.get("AZURE_OPENAI_KEY"),
                api_version="2024-12-01-preview"
            )
            
            response = await client.chat.completions.create(
                model=os.environ.get("AZURE_OPENAI_MODEL"),
                messages=conversations[sender],
                max_tokens=150,
                temperature=0.7
            )
            
            reply = response.choices[0].message.content.strip()
            conversations[sender].append({"role": "assistant", "content": reply})
            
            # Update appointment if AI confirms a new time
            if "rescheduled" in reply.lower() or "confirmed" in reply.lower():
                logger.info(f"Appointment update for {sender}: {reply}")
            
            await send_sms(sender, reply)
            
        except Exception as e:
            logger.error(f"Error processing SMS: {e}")

async def send_sms(to, message):
    phone = os.environ.get("PHONE_NUMBER")
    if not phone:
        return
        
    client = get_sms_client()
    if client:
        try:
            client.send(from_=phone, to=[to], message=message)
            logger.info(f"SMS sent to {to}: {message}")
        except Exception as e:
            logger.error(f"SMS send error: {e}")

@app.get("/")
async def root():
    return {"message": "Appointment Reminder & Scheduling API"}

@app.get("/appointments")
async def get_appointments():
    return {"appointments": appointments}

@app.get("/calendar")
async def get_calendar():
    return {"calendar": calendar}

@app.get("/calendar/{date}")
async def get_calendar_date(date: str):
    if date in calendar:
        return {"date": date, "available_slots": calendar[date]}
    return {"error": "Date not found"}

@app.post("/api/sms/webhook")
async def sms_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        
        # Handle validation
        if isinstance(payload, list):
            for event in payload:
                if event.get("eventType") == "Microsoft.EventGrid.SubscriptionValidationEvent":
                    code = event.get("data", {}).get("validationCode")
                    if code:
                        return {"validationResponse": code}
        elif payload.get("eventType") == "Microsoft.EventGrid.SubscriptionValidationEvent":
            code = payload.get("data", {}).get("validationCode")
            if code:
                return {"validationResponse": code}
        
        background_tasks.add_task(process_sms, payload)
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    generate_calendar()  # Generate calendar on startup
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
