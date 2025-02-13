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



    return [event['summary'] for event in events] if events else ["No events tomorrow!"]

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
        self.root.attributes('-topmost', True) # keep the cat on top

        # Get screen dimensions
        screen_width, screen_height = pyautogui.size()
        window_width, window_height = 200, 200  # Set window size

        # Position at bottom-right corner
        x_pos = screen_width - window_width - 20  # 20px padding from right
        y_pos = screen_height - window_height - 50  # 50px padding from bottom

        self.root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
        self.root.configure(bg="white")  # Background matching transparency

        # Load pixel art cat with improved transparency
        self.image = Image.open("cat_idle.png").convert("RGBA")
        self.image = self.image.resize((150, 150), Image.Resampling.LANCZOS)
        self.photo = self.remove_white_edges(self.image)

        self.label = tk.Label(root, image=self.photo, bg="white", cursor="hand2")  # Match transparency color
        self.label.pack()

        # Set transparent color for the window
        self.root.attributes('-transparentcolor', 'white')

        # Toggle speech bubble on click
        self.label.bind("<Button-1>", self.toggle_speech_bubble)
        self.speech_bubble = None  # Holds speech bubble reference

        # Create stop button
        self.stop_button = tk.Button(root, text="❌ close", command=self.stop_program, 
                                     font=("Arial", 10), bg="pink", fg="black", 
                                     bd=2, padx=5, pady=2, relief="solid", cursor="hand2")

        self.stop_button.pack()                         
        self.stop_button.place(relx=0.5, y=160, anchor="center")

    
    def make_transparent(self, image, transparent_color):
        """ Converts white background (or any color) to transparent """
        image = image.convert("RGBA")
        data = image.getdata()
        new_data = []
        
        for item in data:
            if item[:3] == transparent_color:  # If pixel matches transparent color, make it fully transparent
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        
        image.putdata(new_data)
        return ImageTk.PhotoImage(image)
    
    def remove_white_edges(self, image):
        """ Removes white edges using alpha blending for better transparency """
        image = image.convert("RGBA")
        data = image.getdata()
        new_data = []

        for item in data:
            r, g, b, a = item
            if r > 200 and g > 200 and b > 200:  # Adjust this threshold if needed
                new_data.append((r, g, b, 0))  # Fully transparent
            else:
                new_data.append(item)  # Keep original pixels

        image.putdata(new_data)
        return ImageTk.PhotoImage(image)

    def toggle_speech_bubble(self, event):
        if self.speech_bubble:
            self.speech_bubble.destroy()
            self.speech_bubble = None
        else:
            self.show_speech_bubble()


    def show_speech_bubble(self):
        calendar_tasks = get_google_calendar_events()
        task_tasks = get_google_tasks()

        reminder_text = "📅 Calendar:\n" + "\n".join(calendar_tasks) + "\n\n📝 Tasks:\n" + "\n".join(task_tasks)

        self.speech_bubble = tk.Toplevel(self.root)
        self.speech_bubble.overrideredirect(True)  # Remove window decorations

        # Get current position of the cat (adjust for better positioning above the cat)
        x_pos = self.root.winfo_x() - 50  # Move 50px to the left
        y_pos = self.root.winfo_y() - 250  # Make speech bubble 180px above the cat
        self.speech_bubble.geometry(f"250x250+{x_pos}+{y_pos}")

        # Create a frame for the speech bubble with rounded corners
        bubble_frame = tk.Frame(self.speech_bubble, bg="white", bd=2, relief="solid")
        bubble_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Create a canvas inside the frame to hold the content
        canvas = tk.Canvas(bubble_frame, bg="white", bd=0, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        # Create a scrollable frame inside the canvas
        scrollable_frame = tk.Frame(canvas, bg="white")
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Add the scroll bar
        scrollbar = tk.Scrollbar(bubble_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.config(yscrollcommand=scrollbar.set)

        # Add the reminder text inside the scrollable frame
        label = tk.Label(scrollable_frame, text=reminder_text, bg="white", fg="black",
                        font=("Arial", 10), justify="left", padx=10, pady=5, wraplength=230)
        label.pack()

        # Update the scrollable frame's scroll region
        scrollable_frame.update_idletasks()  # Updates the scrollable frame's region
        canvas.config(scrollregion=canvas.bbox("all"))  # Set the scroll region based on the content

        # Ensure the speech bubble's height adjusts based on the content size
        content_height = canvas.bbox("all")[3]  # Get height of the content
        bubble_height = min(max(content_height + 20, 200), 400)  # Set a max height limit
        self.speech_bubble.geometry(f"250x{bubble_height}+{x_pos}+{y_pos}")





    def stop_program(self):
        """ Closes the program when the stop button is clicked """
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    pet = DigitalPet(root)
    root.mainloop()