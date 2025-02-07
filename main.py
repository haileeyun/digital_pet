import tkinter as tk
from tkwebview2.tkwebview2 import WebView2  # WebView for rendering HTML
from tkinter import messagebox
from PIL import Image, ImageTk
import datetime, timedelta
import os
import pickle
import pyautogui  # For screen size detection
import pytz # time zone

# Google API Imports
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Google API Scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',  # For Calendar
    'https://www.googleapis.com/auth/tasks.readonly'  # For Google Tasks
]

# ---------------- Google Calendar Integration ----------------
def get_google_calendar_events():
    creds = None
    token_path = "token.pickle"

    # Load credentials if available
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for future use
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    # Connect to Google Calendar
    service = build('calendar', 'v3', credentials=creds)

    # Get local timezone from Google Calendar settings
    calendar_settings = service.settings().get(setting="timezone").execute()
    local_tz = pytz.timezone(calendar_settings["value"])  # Convert to local timezone

    # Get today's date in local timezone
    now = datetime.datetime.now(local_tz)
    tomorrow = now + datetime.timedelta(days=1)

    # Format time range correctly
    time_min = local_tz.localize(datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)).isoformat()
    time_max = local_tz.localize(datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 23, 59, 59)).isoformat()

    # Fetch events
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    # print("🔍 Raw API Response:", events_result)
    # calendar_list = service.calendarList().list().execute()
    # for calendar in calendar_list['items']:
    #     print(calendar['id'])



    return [event['summary'] for event in events] if events else ["No tasks due tomorrow!"]

# ---------------- Google Tasks Integration ----------------
def get_google_tasks():
    creds = None
    token_path = "token.pickle"

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    service = build('tasks', 'v1', credentials=creds)

    # Get the default task list (first one returned)
    tasklists = service.tasklists().list().execute()
    if not tasklists.get('items', []):
        return ["No task lists found!"]

    default_tasklist_id = tasklists['items'][0]['id']

    # Get all tasks from the default task list
    tasks = service.tasks().list(tasklist=default_tasklist_id).execute()
    task_result = [task['title'] for task in tasks.get('items', [])]

    return task_result if task_result else ["No tasks found!"]

# ---------------- Digital Pet GUI ----------------

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import pyautogui

# ---------------- Digital Pet GUI ----------------
class DigitalPet:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)  # Remove window borders
        
        # Get screen dimensions
        screen_width, screen_height = pyautogui.size()
        window_width, window_height = 200, 200  # Set window size

        # Position at bottom-right corner
        x_pos = screen_width - window_width - 20  # 20px padding from right
        y_pos = screen_height - window_height - 50  # 50px padding from bottom
        
        self.root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")

        # Load pixel art cat
        self.image = Image.open("cat_idle.png")  
        self.image = self.image.resize((150, 150), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.image)

        self.label = tk.Label(root, image=self.photo, bg="white")
        self.label.pack()

        # Make window draggable
        self.label.bind("<ButtonPress-1>", self.start_drag)
        self.label.bind("<B1-Motion>", self.dragging)

        # Fetch tasks and show reminder
        self.show_reminders()

    def start_drag(self, event):
        self.x = event.x
        self.y = event.y

    def dragging(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

    def show_reminders(self):
        calendar_tasks = get_google_calendar_events()
        task_tasks = get_google_tasks()

        reminder_text = "Calendar Tasks:\n" + "\n".join(calendar_tasks) + "\n\nTasks:\n" + "\n".join(task_tasks)
        messagebox.showinfo("🐈 Reminder!", reminder_text)


if __name__ == "__main__":
    root = tk.Tk()
    pet = DigitalPet(root)
    root.mainloop()