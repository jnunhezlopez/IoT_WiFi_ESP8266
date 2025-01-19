import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from PIL import Image, ImageTk
import paho.mqtt.client as mqtt
import time
from datetime import datetime

# MQTT Configuration
BROKER = "192.168.12.1"
PORT = 1883
TOPIC_SENSOR = "SENSOR_DATA"
TOPIC_RELAY = "RELAY"
TOPIC_CONFIG = "CONFIG/"

# Global variables to store sensor data and timestamps
sensor_data = {
    "living_room": {"temperature": None, "humidity": None, "last_update": None},
    "bedroom": {"temperature": None, "humidity": None, "last_update": None},
}
UPDATE_THRESHOLD = 10 * 60  # 10 minutes in seconds

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(TOPIC_SENSOR)

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        zone, temp, hum = payload.split(",")  # Example: "living_room,22.5,55.0"
        if zone in sensor_data:
            sensor_data[zone]["temperature"] = float(temp)
            sensor_data[zone]["humidity"] = float(hum)
            sensor_data[zone]["last_update"] = time.time()
            update_sensor_display(zone)
    except Exception as e:
        print(f"Error processing message: {e}")

# Function to check for outdated sensor data
def check_all_alarms():
    now = time.time()
    for zone, data in sensor_data.items():
        last_update = data["last_update"]
        # Alarm is red if never updated or last update exceeds threshold
        if not last_update or (now - last_update > UPDATE_THRESHOLD):
            sensor_indicator[zone].config(bg="red")
        else:
            sensor_indicator[zone].config(bg="green")
    # Schedule the next check
    root.after(1000, check_all_alarms)  # Check every second

# Function to update sensor displays
def update_sensor_display(zone):
    data = sensor_data[zone]
    temperature_label[zone].config(text=f"Temp: {data['temperature']} °C" if data['temperature'] else "Temp: --")
    humidity_label[zone].config(text=f"Hum: {data['humidity']} %" if data['humidity'] else "Hum: --")
    if data["last_update"]:
        last_update_label[zone].config(
            text=f"Updated: {datetime.fromtimestamp(data['last_update']).strftime('%H:%M:%S')}"
        )
    # Check if alarm needs to be cleared
    check_all_alarms()

# Function to control relays
def control_relay(zone, state):
    mqtt_client.publish(TOPIC_RELAY, f'{{"zone":"{zone}","state":"{state}"}}')

# Function to configure a device
def configurar_dispositivo():
    device_id = simpledialog.askstring("Device Configuration", "Enter Device ID:")
    zone = simpledialog.askstring("Device Configuration", "Enter Zone:")
    device_type = simpledialog.askstring("Device Configuration", "Enter Device Type:")
    if device_id and zone and device_type:
        config_payload = f'{{"zone":"{zone}","type":"{device_type}"}}'
        mqtt_client.publish(f"{TOPIC_CONFIG}{device_id}", config_payload)
        print(f"Configuration sent: {config_payload}")
    else:
        print("Configuration cancelled or incomplete!")

# Tkinter GUI setup
root = tk.Tk()
root.title("Smart Home Control")
root.geometry("800x480")  #("800x600")

# Load house image
house_image = Image.open("house.png")  # Replace with your image file
house_image = house_image.resize((600,400), Image.ANTIALIAS)
house_photo = ImageTk.PhotoImage(house_image)
background_label = tk.Label(root, image=house_photo)
background_label.place(x=0, y=0, relwidth=1, relheight=1)

# Place sensor indicators and labels
zones = ["living_room", "bedroom"]
positions = {"living_room": (200, 300), "bedroom": (500, 300)}

sensor_indicator = {}
temperature_label = {}
humidity_label = {}
last_update_label = {}

for zone, pos in positions.items():
    sensor_indicator[zone] = tk.Label(root, bg="green", width=5, height=2)
    sensor_indicator[zone].place(x=pos[0], y=pos[1])

    temperature_label[zone] = tk.Label(root, text="Temp: --", bg="white")
    temperature_label[zone].place(x=pos[0] + 50, y=pos[1] - 20)

    humidity_label[zone] = tk.Label(root, text="Hum: --", bg="white")
    humidity_label[zone].place(x=pos[0] + 50, y=pos[1])

    last_update_label[zone] = tk.Label(root, text="Updated: --", bg="white")
    last_update_label[zone].place(x=pos[0] + 50, y=pos[1] + 20)

# Add relay control buttons
for i, zone in enumerate(zones):
    tk.Button(
        root,
        text=f"{zone.capitalize()} ON",
        command=lambda z=zone: control_relay(z, "ON"),
    ).place(x=200 + i *300, y=100)

    tk.Button(
        root,
        text=f"{zone.capitalize()} OFF",
        command=lambda z=zone: control_relay(z, "OFF"),
    ).place(x=200 + i *300, y=150)

# Add menu for configuration
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

config_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Configuration", menu=config_menu)
config_menu.add_command(label="Configure Device", command=configurar_dispositivo)

# MQTT client setup
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, PORT, 60)

# Start MQTT loop in a separate thread
mqtt_client.loop_start()
check_all_alarms()
root.mainloop()
