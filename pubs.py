import time
import json
import zmq
import board
import adafruit_dht  # Replacing Adafruit_DHT with the new library
from max30100 import MAX30100
from max30100 import MAX30100_MODE_HR_SPO2  # Changed mode to include heart rate

# Initialize ZMQ publisher
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")

# Initialize DHT11 sensor using the new library
dht_device = adafruit_dht.DHT11(board.D4)  # Replacing Adafruit_DHT with board-based access

# Initialize MAX30100 with heart rate mode
max30100 = MAX30100()
max30100.enable_spo2()
max30100.set_mode(MAX30100_MODE_HR_SPO2)

def read_dht11():
    """Read temperature from DHT11 using Adafruit_CircuitPython_DHT"""
    try:
        temperature = dht_device.temperature
        return temperature
    except RuntimeError as e:
        print(f"DHT11 Read Error: {e}")
        return None

def read_max30100():
    """Read SpO2 and Heart Rate from MAX30100"""
    max30100.read_sensor()
    
    # Get the latest readings
    ir_reading = max30100.ir
    red_reading = max30100.red
    
    if ir_reading and red_reading and ir_reading > 0:
        ratio = red_reading / ir_reading
        spo2 = 110 - 25 * ratio  # Simplified conversion
        spo2 = min(100, max(0, spo2))
        
        # Basic heart rate calculation
        heart_rate = calculate_heart_rate(ir_reading)
        
        return spo2, heart_rate
    return None, None

def calculate_heart_rate(ir_reading):
    """Calculate heart rate from IR reading (simplified)"""
    try:
        if ir_reading > 50000:
            peaks = True
        else:
            peaks = False
            
        heart_rate = 60 if peaks else 0  # Placeholder value
        return heart_rate
    except:
        return 0

def main():
    print("Starting sensor readings...")
    
    try:
        while True:
            # Read sensors
            temperature = read_dht11()
            spo2, heart_rate = read_max30100()
            
            # Create data packet
            data = {
                "temperature": temperature if temperature else 0,
                "heartrate": heart_rate if heart_rate else 0,
                "spo2": spo2 if spo2 else 0,
                "timestamp": time.strftime("%H:%M:%S")
            }
            
            # Send data via ZMQ
            message = json.dumps(data)
            socket.send_string("health_metrics", zmq.SNDMORE)
            socket.send_string(message)
            
            print(f"Sent: {message}")
            
            time.sleep(1)  # Adjust sampling rate as needed
            
    except KeyboardInterrupt:
        print("\nStopping sensor readings...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        max30100.disable_spo2()
        socket.close()
        context.term()
        dht_device.exit()  # Properly release DHT sensor

if __name__ == "__main__":
    main()

