import time
import json
import zmq
import Adafruit_DHT
from max30100 import MAX30100
from max30100 import MAX30100_MODE_HR_SPO2  # Changed mode to include heart rate

# Initialize ZMQ publisher
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")

# Initialize sensors
dht_sensor = Adafruit_DHT.DHT11
dht_pin = 4  # GPIO4 (Pin 7)

# Initialize MAX30100 with heart rate mode
max30100 = MAX30100()
max30100.enable_spo2()
max30100.set_mode(MAX30100_MODE_HR_SPO2)

def read_dht11():
    """Read temperature from DHT11"""
    humidity, temperature = Adafruit_DHT.read_retry(dht_sensor, dht_pin)
    if temperature is not None:
        return temperature
    return None

def read_max30100():
    """Read SpO2 and Heart Rate from MAX30100"""
    max30100.read_sensor()
    
    # Get the latest readings
    ir_reading = max30100.ir
    red_reading = max30100.red
    
    # Basic SpO2 calculation
    # Note: This is a simplified calculation. For medical purposes,
    # you should use the manufacturer's calibrated algorithm
    if ir_reading and red_reading and ir_reading > 0:
        ratio = red_reading / ir_reading
        spo2 = 110 - 25 * ratio  # Simplified conversion
        spo2 = min(100, max(0, spo2))
        
        # Basic heart rate calculation
        # Note: This is a simplified calculation
        # You might want to implement more sophisticated peak detection
        heart_rate = calculate_heart_rate(ir_reading)
        
        return spo2, heart_rate
    return None, None

def calculate_heart_rate(ir_reading):
    """Calculate heart rate from IR reading"""
    # This is a simplified heart rate calculation
    # In a real application, you would need to:
    # 1. Collect multiple samples
    # 2. Apply filtering
    # 3. Detect peaks
    # 4. Calculate time between peaks
    # 5. Convert to BPM
    
    # For demonstration, returning a processed value
    # You should implement proper peak detection and BPM calculation
    try:
        # Simple peak detection
        if ir_reading > 50000:  # Threshold value, adjust based on your sensor
            peaks = True
        else:
            peaks = False
            
        # Calculate BPM based on peaks
        if peaks:
            # This would normally use multiple readings over time
            heart_rate = 60  # Placeholder
        else:
            heart_rate = 0
            
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
            
            # Wait before next reading
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

if __name__ == "__main__":
    main()
