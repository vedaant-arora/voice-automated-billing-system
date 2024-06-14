import speech_recognition as sr
import os
import functools
import pyttsx3
import mysql.connector
import customtkinter as ctk
from tkinter import messagebox
from datetime import *
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

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
        speak("speak now")
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

# Function to generate PDF bill
def generate_pdf_bill(order_items, total_price):
    # Create a list of data for the table
    data = [["Item", "Quantity", "Price"]]
    for item_name, quantity, price in order_items:
        data.append([item_name, str(quantity), str(price)])
    data.append(["", "", ""])
    data.append(["Total", "", str(total_price)])

    # Create a PDF document
    doc = SimpleDocTemplate("bill.pdf", pagesize=letter)
    elements = []

    # Create a table from the data
    table = Table(data)
    style = TableStyle([('BACKGROUND', (0,0), (-1,0), colors.grey),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0,0), (-1,0), 12),
                        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                        ('GRID', (0,0), (-1,-1), 1, colors.black)])
    table.setStyle(style)
    elements.append(table)

    # Build the PDF document
    doc.build(elements)
    speak(f"PDF bill generated for your order with a total price of {total_price} rupees.")

    # Open the generated PDF file
    os.startfile("bill.pdf")

# Function to handle voice input
def handle_voice_input():
    global order_items, total_order_price  # Declare global variables
    speak("The system is now active. Please say the item name and quantity to make a purchase.")
    order_items = []
    total_order_price = 0
    while True:
        command = listen()
        if command:
            if command.lower() in ["stop", "no"]:
                if order_items:
                    update_bill_preview(order_items, total_order_price)
                    generate_pdf_bill(order_items, total_order_price)
                break
            try:
                items = command.split()  
                item_name = ' '.join(items[:-1])
                quantity = int(items[-1])
                price = get_item_price(item_name)
                if price:
                    item_total_price = price * quantity
                    total_order_price += item_total_price
                    order_items.append((item_name, quantity, item_total_price))
                    record_sale(item_name, quantity, item_total_price)
                    speak(f"Added {quantity} {item_name}(s) to the order.")
                else:
                    speak(f"Item {item_name} not found.")
                speak(f"The current total price for your order is {total_order_price} rupees.")
                speak("Do you want to add anything else?")
            except ValueError:
                speak("Please provide both item names and quantities correctly.")

def update_bill_preview(order_items, total_price):
    bill_preview.delete("1.0", "end")  # Clear the previous bill preview
    bill_preview.insert("end", "Bill Preview:\n\n")
    bill_preview.insert("end", "Item\tQuantity\tPrice\n")
    bill_preview.insert("end", "-" * 30 + "\n")
    for item_name, quantity, price in order_items:
        bill_preview.insert("end", f"{item_name}\t{quantity}\t\t{price}\n")
    bill_preview.insert("end", "-" * 30 + "\n")
    bill_preview.insert("end", f"Total:\t\t\t{total_price}\n")
    
def trigger_voice_input(button, event):
    button.invoke()

# Function to display daily sales
def display_daily_sales():
    total_sales = calculate_daily_sales()
    speak(f"The total sales for today are {total_sales} rupees.")
    messagebox.showinfo("Daily Sales", f"The total sales for today are {total_sales} rupees.")

# Create the main window
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

root = ctk.CTk()
root.title("Cafeteria Billing System")
root.geometry("600x400")
root.configure(bg="black")

# Create a frame for side buttons
side_frame = ctk.CTkFrame(root, width=150)
side_frame.pack(side="left", fill="y", padx=10, pady=10)

# Create a frame for the bill preview and "Generate Bill" button
right_frame = ctk.CTkFrame(root)
right_frame.pack(side="right", fill="both", padx=10, pady=10, expand=True)

# Create a Text widget for the bill preview
bill_preview = ctk.CTkTextbox(right_frame, width=300, height=300)
bill_preview.pack(pady=10)

# Create a label for displaying "Listening..." and "User said:"
status_label = ctk.CTkLabel(root, text="", font=("Arial", 12))
status_label.pack(pady=10)

# Create buttons and add them to the side frame
voice_input_button = ctk.CTkButton(side_frame, text="Start Voice Input", command=handle_voice_input, font=("Arial", 12), fg_color="white", text_color="black")
voice_input_button.pack(pady=10)
root.bind('<space>', functools.partial(trigger_voice_input, voice_input_button))

daily_sales_button = ctk.CTkButton(side_frame, text="Calculate Daily Sales", command=display_daily_sales, font=("Arial", 12), fg_color="white", text_color="black")
daily_sales_button.pack(pady=10)

exit_button = ctk.CTkButton(side_frame, text="Exit", command=root.quit, font=("Arial", 12), fg_color="white", text_color="black")
exit_button.pack(pady=10)

# Create the "Generate Bill" button
generate_bill_button = ctk.CTkButton(right_frame, text="Generate Bill", command=lambda: generate_pdf_bill(order_items, total_order_price), font=("Arial", 12), fg_color="white", text_color="black")
generate_bill_button.pack(pady=10)

# Run the main loop
root.mainloop()