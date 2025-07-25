# AI SMS Appointment Scheduler

An AI-powered SMS appointment scheduler that demonstrates how to build intelligent conversation flows using Azure Communication Services and Azure OpenAI. When customers text your business number, they get automatic appointment reminders and can reschedule through natural conversation.

## What This Demo Shows

- **Real SMS Integration**: Uses actual Azure Communication Services phone numbers
- **AI Conversations**: Natural language appointment scheduling with Azure OpenAI
- **Event-Driven Architecture**: SMS events trigger AI responses via Azure Event Grid
- **FastAPI Backend**: Modern Python web framework handling webhooks and APIs
- **Mock Business Logic**: Realistic 30-day calendar with 80% occupancy simulation

## Quick Start

### Step 1: Clone and Configure

```bash
git clone https://github.com/pereiralex/sms-appointment-scheduler.git
cd sms-appointment-scheduler

# Copy environment template and add your Azure credentials
cp .env.example .env
# Edit .env with your Azure details (see detailed instructions below)
```

### Step 2: Install and Run

**Option A: Using uv (recommended)**
```bash
uv run fastapi dev
```

**Option B: Using pip**
```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Step 3: Expose for Testing

```bash
# Create dev tunnel for Azure webhooks
devtunnel create --allow-anonymous
devtunnel port create -p 8000
devtunnel host
# Note the public URL for Azure Event Grid configuration
```

Your SMS appointment scheduler is now running at `http://127.0.0.1:8000`

## Detailed Setup Instructions

### Prerequisites

**Local Development**:
- **Python 3.12 or higher** - Required for running the FastAPI application

**Azure Resources**:
- **Azure Communication Services** - For SMS phone number and messaging
- **Azure OpenAI** - For conversational AI (GPT-4 recommended)
- **Azure Event Grid** - For SMS webhook delivery (included with ACS)

### Environment Configuration

1. **Copy the environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Fill in your Azure credentials** in the `.env` file:

   ```bash
   # Get this from Azure Portal → Communication Services → Keys
   AZURE_COMMUNICATION_SERVICE_CONNECTION_STRING="endpoint=https://your-acs.communication.azure.com/;accesskey=your-key"
   
   # Get these from Azure Portal → Azure OpenAI → Keys and Endpoint
   AZURE_OPENAI_ENDPOINT="https://your-openai-resource.openai.azure.com/"
   AZURE_OPENAI_KEY="your_openai_api_key"
   AZURE_OPENAI_MODEL="gpt-4"  # Your deployed model name
   
   # Get this from Azure Portal → Communication Services → Phone numbers
   PHONE_NUMBER="+1234567890"
   ```

The `.env.example` file contains step-by-step instructions for creating these Azure resources and finding the required values.

### Azure Event Grid Webhook Configuration

You need to configure Azure Event Grid to forward SMS events to your local server.

1. **Get your dev tunnel URL** from the previous step (format: `https://xyz-8000.region.devtunnels.ms`)

2. **Configure the webhook in Azure Portal**:
   - Go to your Azure Communication Services resource
   - Navigate to **Events** → **Event Subscriptions** → **+ Event Subscription**
   - Fill in:
     - **Name**: `AppointmentSMSWebhook`
     - **Event Schema**: `Event Grid Schema`
     - **Event Types**: Select `SMS Received` and `SMS Delivery Report Received`
     - **Endpoint Type**: `Web Hook`
     - **Endpoint**: `https://your-tunnel-url.devtunnels.ms/api/sms/webhook`
   - Click **Create**

3. **Test it**: Send an SMS to your Azure phone number to see the AI respond.

## Example Conversations

### First Contact
```
Customer: "Hi"
AI: "Hi! This is a reminder that you have a consultation scheduled for 
     Tuesday, June 17 at 9:30 AM. Can you confirm you'll be able to make it, 
     or would you like to reschedule?"
```

### Natural Rescheduling
```
Customer: "I need to reschedule for next week"
AI: "Of course! For next week, I have these time slots available:
     Monday: 10:00 AM, 2:30 PM, 4:00 PM
     Tuesday: 9:00 AM, 11:30 AM, 3:30 PM
     Which would work best for you?"

Customer: "Tuesday 11:30 works"
AI: "Perfect! I've rescheduled your consultation to Tuesday, June 24 at 11:30 AM. 
     Please arrive 15 minutes early. See you then!"
```

## API Endpoints

Once running, explore these endpoints:

- **`GET /`** - Health check and welcome message
- **`GET /appointments`** - View all mock customer appointments
- **`GET /calendar`** - See the full 30-day generated calendar
- **`GET /calendar/2024-01-15`** - Check availability for a specific date
- **`POST /api/sms/webhook`** - Webhook endpoint (used by Azure Event Grid)

## Mock Calendar System

The demo generates a realistic business calendar:

- **30 days starting from today**
- **Business hours**: 9:00 AM - 5:00 PM  
- **Days**: Monday through Friday only
- **Intervals**: 30-minute appointment slots
- **Occupancy**: 80% pre-booked (realistic availability)
- **Type**: All appointments are "consultations"

Each customer gets assigned a random existing appointment when they first text.

## AI Assistant Behavior

The AI receptionist is designed to:

- Provide immediate appointment reminders to new contacts
- Offer specific available time slots when rescheduling  
- Maintain professional, friendly medical office tone
- Handle natural language requests ("next week", "Monday afternoon")
- Confirm appointment details clearly
- Remember conversation context for follow-up questions

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
Customer SMS → Azure Communication Services → Azure Event Grid → Your FastAPI App → Azure OpenAI → SMS Response
```

**Event Flow**:
1. Customer sends SMS to your Azure phone number
2. Azure Communication Services receives the message
3. Event Grid forwards SMS event to your webhook
4. FastAPI processes the event and calls Azure OpenAI
5. AI generates intelligent response based on calendar data
6. Response sent back via Azure Communication Services

## Troubleshooting

**SMS not working?**
- Check your `.env` file has correct Azure credentials
- Verify your dev tunnel is running and publicly accessible
- Confirm Azure Event Grid webhook is configured with correct URL
- Check Azure portal for Event Grid delivery failures

**AI responses seem off?**
- Verify your Azure OpenAI deployment name matches `AZURE_OPENAI_MODEL` in `.env`
- Check console logs for OpenAI API errors
- Try with a different model (GPT-3.5-turbo vs GPT-4)

**Calendar showing weird dates?**
- The calendar generates 30 days from today - this is normal
- Only business days (Mon-Fri) have appointments
