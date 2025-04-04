import time
import json
import zmq
import board
import adafruit_dht
import random

# Initialize ZMQ publisher
context = zmq.Context()

# Create two publisher sockets
local_socket = context.socket(zmq.PUB)
remote_socket = context.socket(zmq.PUB)

# Bind/connect sockets
local_socket.bind("tcp://*:5555")
remote_socket.connect("tcp://192.168.61.23:5556")  # Connect to remote IP

# Initialize DHT11 sensor
try:
    dht_device = adafruit_dht.DHT11(board.D4)
except Exception as e:
    print(f"DHT11 init error: {e}")
    dht_device = None

def read_dht11():
    """Read temperature from DHT11, fallback to fake data if error occurs."""
    if dht_device is None:
        return round(random.uniform(27, 36), 1)  # Simulated temperature
    
    try:
        temp = dht_device.temperature
        if temp is None:
            raise ValueError("Invalid reading")
        return temp
    except Exception as e:
        print(f"DHT11 read error: {e}")
        return round(random.uniform(20, 35), 1)  # Simulated temperature

def generate_simulated_data():
    """Generate fake heart rate and SpO2 data within realistic ranges."""
    heart_rate = random.uniform(60, 100)  # Normal heart rate range
    spo2 = random.uniform(95, 100)  # Normal SpO2 range
    return heart_rate, spo2

def send_message(socket, topic, message):
    """Helper function to send messages with topic."""
    socket.send_string(topic, zmq.SNDMORE)
    socket.send_string(message)

def main():
    print("Starting sensor readings...")
    try:
        while True:
            # Get real or fake temperature
            temperature = read_dht11()
            
            # Generate simulated heart rate and SpO2
            heart_rate, spo2 = generate_simulated_data()
            
            data = {
                "temperature": temperature,
                "heartrate": round(heart_rate, 1),
                "spo2": round(spo2, 1),
                "timestamp": time.strftime("%H:%M:%S")
            }
            
            message = json.dumps(data)
            
            # Send to both local and remote sockets
            send_message(local_socket, "health_metrics", message)
            send_message(remote_socket, "health_metrics", message)
            
            print(f"Sent locally and to remote IP: {message}")
            time.sleep(2.5)  # Increased delay for better stability
            
    except KeyboardInterrupt:
        print("\nStopping sensor readings...")
    finally:
        if dht_device:
            dht_device.exit()
        local_socket.close()
        remote_socket.close()
        context.term()

if __name__ == "__main__":
    main()

