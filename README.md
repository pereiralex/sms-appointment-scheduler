# SMS appointment reminders with natural language rescheduling

This application provides an AI-powered SMS appointment reminder and scheduling system using Azure Communication Services and Azure OpenAI. When customers text your number, they automatically receive appointment reminders and can reschedule through natural conversation.


## Features

- **Automatic appointment reminders**: First-time texters get instant appointment reminders
- **AI-powered rescheduling**: Natural conversation for appointment changes using Azure OpenAI
- **Mock calendar system**: 30-day calendar with realistic 80% occupancy simulation
- **Smart availability**: AI assistant offers real available time slots when rescheduling
- **Conversation context**: Maintains conversation history for natural interactions
- **Business hours**: Realistic 9 AM - 5 PM, Monday-Friday scheduling

## How It Works

1. **Customer texts** your Azure Communication Services number
2. **Instant reminder** sent with their upcoming appointment details
3. **Natural conversation** for confirming or rescheduling appointments
4. **Real-time availability** shown from the mock calendar system
5. **Professional responses** like a human medical receptionist would provide

## Setup Instructions

### Prerequisites

- Python 3.13 or higher
- Azure account with Azure Communication Services configured
- Azure Communication Services phone number with SMS capabilities
- Azure OpenAI service configured with GPT-4 deployment

### 1. Environment Variables

Set up the following environment variables in a `.env` file:

```bash
# Azure Communication Services (use connection string for simplicity)
AZURE_COMMUNICATION_SERVICE_CONNECTION_STRING="your_connection_string"

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT="https://your-openai-resource.openai.azure.com/"
AZURE_OPENAI_KEY="your_openai_api_key"
AZURE_OPENAI_MODEL="gpt-4"  # Your deployed model name

# Your Azure Communication Services phone number
PHONE_NUMBER="+1234567890"
```

### 2. Install Dependencies & Run Server

```bash
# Install dependencies and run the FastAPI server
uv run fastapi dev
```

The server will start on `http://127.0.0.1:8000` with automatic calendar generation.

### 3. Create & Host Dev Tunnel

For local development, expose your server to Azure Event Grid:

```bash
# Create a tunnel (one-time setup)
devtunnel create --allow-anonymous

# Create port mapping
devtunnel port create -p 8000

# Start hosting the tunnel
devtunnel host
```

Note the public dev tunnel URL (format: `https://<tunnel-id>-8000.<region>.devtunnels.ms`)

### 4. Configure Azure Event Grid Webhook

Set up SMS event forwarding to your API:

1. Go to your Azure Communication Services resource in Azure portal
2. Navigate to **Events** → **Event Subscriptions** → **Add Event Subscription**
3. Configure:
   - **Name**: "AppointmentSMSWebhook"
   - **Event Schema**: Event Grid Schema
   - **Event Types**: Select "SMS Received" and "SMS Delivery Report Received"
   - **Endpoint Type**: Web Hook
   - **Endpoint**: `https://your-tunnel-url.devtunnels.ms/api/sms/webhook`
4. Click **Create**

## Usage Examples

### First Contact - Appointment Reminder
**Customer texts**: "Hi"
**System responds**: "Hi! This is a reminder that you have a consultation scheduled for Tuesday, June 17 at 9:30 AM. Can you confirm you'll be able to make it, or would you like to reschedule?"

### Rescheduling Request
**Customer**: "I'd like to reschedule"
**System**: "Of course! Could you please let me know which date works better for you? We're open Monday to Friday from 9 AM to 5 PM."

### Specific Date Request
**Customer**: "Is there any availability next Monday afternoon?"
**System**: "Next Monday, we have the following afternoon time slots available:
- 1:00 PM
- 1:30 PM  
- 3:30 PM

Please let me know which time works best for you!"

### Appointment Confirmation
**Customer**: "3:30 works great"
**System**: "Perfect! I have rescheduled your consultation to Monday, June 23 at 3:30 PM. Please remember to arrive 15 minutes early. Have a great day!"

## API Endpoints

- `GET /`: Health check endpoint
- `GET /appointments`: View all customer appointments
- `GET /calendar`: View the entire mock calendar
- `GET /calendar/{date}`: View available slots for specific date (YYYY-MM-DD)
- `POST /api/sms/webhook`: Webhook endpoint for SMS events from Azure Communication Services

## Mock Calendar System

The application generates a realistic 30-day calendar:
- **Business hours**: 9:00 AM - 5:00 PM
- **Days**: Monday through Friday only
- **Slots**: 30-minute appointment intervals
- **Occupancy**: 80% pre-booked (20% available for realistic scheduling)
- **Appointment types**: All consultations

## AI Assistant Behavior

The AI receptionist:
- Provides immediate appointment reminders to new contacts
- Offers specific available time slots when rescheduling
- Maintains professional, friendly tone
- Handles natural language requests
- Confirms appointment details clearly
- Provides business hour information

## Development

Run in development mode with hot reloading:

```bash
uvicorn main:app --reload
```

## Event Structure

Azure Event Grid delivers SMS events in this format:

```json
{
  "id": "unique-event-id",
  "eventType": "Microsoft.Communication.SMSReceived",
  "data": {
    "from": "+11234567890",
    "message": "Hello, I'd like to reschedule",
    "to": "+10987654321",
    "receivedTimestamp": "2023-01-01T00:00:00Z"
  },
  "eventTime": "2023-01-01T00:00:00Z"
}
```

The application handles both single events and batch arrays automatically.

## Architecture

```
Customer SMS → Azure Communication Services → Azure Event Grid → Your API → Azure OpenAI → SMS Response
```

## Next Steps

- Add appointment confirmation system
- Integrate with real calendar systems (Outlook, Google Calendar)
- Add appointment types and duration options
- Implement customer preference storage
- Add timezone support for multi-location practices
