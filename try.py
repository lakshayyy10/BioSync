import time
import max30100
import adafruit_dht
import RPi.GPIO as GPIO
import zmq
import json

# Set GPIO mode
GPIO.setmode(GPIO.BCM)

# DHT sensor setup
# Use GPIO pin number 4 (which corresponds to board.D4)
DHT_PIN = 4
dht_device = adafruit_dht.DHT11(DHT_PIN)

# ZMQ setup
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")

# MAX30100 sensor setup
mx30 = max30100.MAX30100()
mx30.enable_spo2()

# Initialize variables to store last valid readings
last_temperature = None
last_humidity = None

try:
    while True:
        try:
            # Read MAX30100 sensor data
            mx30.read_sensor()
            
            # Calculate heartbeat and SPO2
            hb = int(mx30.ir / 100)
            spo2 = int(mx30.red / 100)
            
            # Read DHT11 temperature and humidity
            try:
                temperature = dht_device.temperature
                humidity = dht_device.humidity
                
                # Update last valid readings if new data is available
                if temperature is not None:
                    last_temperature = temperature
                if humidity is not None:
                    last_humidity = humidity
            
            except RuntimeError as error:
                # Print error but use last valid reading
                print(f"DHT Sensor Error: {error}")
                temperature = last_temperature
                humidity = last_humidity
            
            # Prepare data payload
            sensor_data = {
                "timestamp": time.time(),
                "heartrate": hb,
                "spo2": spo2,
                "temperature": temperature
            }
            
            # Print local data for debugging
            if mx30.ir != mx30.buffer_ir:
                print("Pulse:", hb)
            if mx30.red != mx30.buffer_red:
                print("SPO2:", spo2)
            if temperature is not None:
                print(f"Temperature: {temperature}°C, Humidity: {humidity}%")
            
            # Send data via ZMQ
            socket.send_string(json.dumps(sensor_data))
            
            # Wait before next reading
            time.sleep(2)
        
        except Exception as e:
            print(f"General Error occurred: {e}")
            time.sleep(2)

except KeyboardInterrupt:
    print("Measurement stopped by User")
finally:
    # Clean up GPIO
    GPIO.cleanup()
    # Close ZMQ socket
    socket.close()
    context.term()
