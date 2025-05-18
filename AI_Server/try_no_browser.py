import datetime
import json
import os
import os.path
import webbrowser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# JSON data containing tickets
json_data = '''
{
  "tickets": [
    {
      "title": "Complete login page",
      "assignee": "Bob",
      "due_date": "20-05-2025",
      "priority": "HIGH",
      "description": "Implement login page including password reset functionality"
    }
  ]
}
'''

# If modifying these scopes, delete the file token.json.
# We need write access to create calendar events
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def parse_date(date_str):
    """Convert date string from DD-MM-YYYY format to YYYY-MM-DD."""
    try:
        day, month, year = date_str.split('-')
        return f"{year}-{month}-{day}"
    except ValueError:
        # Return the original if it's not in the expected format
        return date_str

def create_calendar_event(service, ticket):
    """Create a Google Calendar event from a ticket and return the event link."""
    # Parse the due date
    due_date = parse_date(ticket['due_date'])
    
    # Create event details
    event = {
        'summary': f"{ticket['title']} [{ticket['priority']}]",
        'description': f"Assignee: {ticket['assignee']}\nPriority: {ticket['priority']}\n\n{ticket['description']}",
        'start': {
            'date': due_date,  # All-day event on the due date
        },
        'end': {
            'date': due_date,  # All-day event on the due date
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                {'method': 'popup', 'minutes': 120},      # 2 hours before
            ],
        },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    print(f"Event created: {event.get('htmlLink')}")
    
    # Return the event link
    return event.get('htmlLink')

def main():
    """Creates Google Calendar events from ticket data and generates event links."""
    # Parse the JSON data
    tickets_data = json.loads(json_data)
    tickets = tickets_data.get('tickets', [])
    
    if not tickets:
        print("No tickets found in the JSON data.")
        return
    
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            # Use the console flow instead of opening a browser
            flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            print(f"\n\nGo to this URL in your browser to authorize this application:")
            print(f"\n{auth_url}\n")
            
            # Wait for the user to enter the authorization code
            auth_code = input("Enter the authorization code: ")
            flow.fetch_token(code=auth_code)
            
            creds = flow.credentials
            
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        
        # Create calendar events for each ticket
        print(f"Processing {len(tickets)} tickets:")
        
        event_links = []
        for i, ticket in enumerate(tickets):
            print(f"\nTicket {i+1}: {ticket['title']}")
            event_link = create_calendar_event(service, ticket)
            event_links.append({
                'title': ticket['title'],
                'link': event_link
            })
        
        # Display all event links
        print("\nCreated Calendar Events:")
        for event in event_links:
            print(f"- {event['title']}: {event['link']}")
        
        # No browser prompt - just show the links
        
    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()