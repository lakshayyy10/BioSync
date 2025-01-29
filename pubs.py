import time
import json
import zmq
import board
import adafruit_dht
import random

# Initialize ZMQ publisher
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")

# Initialize DHT11 sensor
try:
    dht_device = adafruit_dht.DHT11(board.D4)
except Exception as e:
    print(f"DHT11 init error: {e}")
    dht_device = None

def read_dht11():
    """Read temperature from DHT11."""
    if dht_device is None:
        return None
    try:
        return dht_device.temperature
    except Exception as e:
        print(f"DHT11 read error: {e}")
        return None

def generate_simulated_data():
    """Generate fake heart rate and SpO2 data within realistic ranges."""
    heart_rate = random.uniform(60, 100)  # Normal heart rate range
    spo2 = random.uniform(95, 100)  # Normal SpO2 range
    return heart_rate, spo2

def main():
    print("Starting sensor readings...")
    try:
        while True:
            # Get real temperature from DHT11
            temperature = read_dht11()
            
            # Generate simulated heart rate and SpO2
            heart_rate, spo2 = generate_simulated_data()
            
            data = {
                "temperature": temperature if temperature else 0,
                "heartrate": round(heart_rate, 1),
                "spo2": round(spo2, 1),
                "timestamp": time.strftime("%H:%M:%S")
            }
            
            message = json.dumps(data)
            socket.send_string("health_metrics", zmq.SNDMORE)
            socket.send_string(message)
            
            print(f"Sent: {message}")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping sensor readings...")
    finally:
        if dht_device:
            dht_device.exit()
        socket.close()
        context.term()

if __name__ == "__main__":
    main()
