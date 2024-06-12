import speech_recognition as sr
import pyttsx3
import mysql.connector
import PySimpleGUI as sg
from datetime import datetime

# Initialize recognizer and TTS engine
recognizer = sr.Recognizer()
tts_engine = pyttsx3.init()

# Connect to MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="abcdefgh",
    database="cafeteria"
)
cursor = db.cursor()

# Function to speak text
def speak(text):
    tts_engine.say(text)
    tts_engine.runAndWait()

# Function to listen to voice input
def listen():
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio)
            print(f"User said: {command}")
            return command
        except sr.UnknownValueError:
            speak("Sorry, I did not understand that.")
            return None

# Function to get item price from database
def get_item_price(item_name):
    cursor.execute("SELECT price FROM items WHERE item_name = %s", (item_name,))
    result = cursor.fetchone()
    return result[0] if result else None

# Function to record sale in database
def record_sale(item_name, quantity, total_price):
    cursor.execute("INSERT INTO sales (item_id, quantity, total_price) VALUES ((SELECT item_id FROM items WHERE item_name = %s), %s, %s)", (item_name, quantity, total_price))
    db.commit()

# Function to calculate daily sales
def calculate_daily_sales():
    cursor.execute("SELECT SUM(total_price) FROM sales WHERE sale_date = CURDATE()")
    result = cursor.fetchone()
    return result[0] if result else 0

# GUI layout
layout = [
    [sg.Text("Cafeteria Billing System")],
    [sg.Button("Start Voice Input"), sg.Button("Calculate Daily Sales"), sg.Button("Exit")]
]

# Create the window
window = sg.Window("Cafeteria Billing System", layout)

# Event loop    
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == "Exit":
        break
    elif event == "Start Voice Input":
        speak("Please say the item name and quantity.")
        command = listen()
        if command:
            try:
                item_name, quantity = command.split()
                quantity = int(quantity)
                price = get_item_price(item_name)
                if price:
                    total_price = price * quantity
                    record_sale(item_name, quantity, total_price)
                    speak(f"The total price is {total_price} dollars.")
                else:
                    speak("Item not found.")
            except ValueError:
                speak("Please provide both item name and quantity.")
    elif event == "Calculate Daily Sales":
        total_sales = calculate_daily_sales()
        speak(f"The total sales for today are {total_sales} dollars.")

window.close()