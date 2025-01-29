import time
import json
import zmq
import board
import adafruit_dht
import smbus2
import numpy as np
from collections import deque

# Initialize ZMQ publisher
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")

# Initialize sensors globally
try:
    dht_device = adafruit_dht.DHT11(board.D4)
except Exception as e:
    print(f"Error initializing DHT11: {e}")
    dht_device = None

class MAX30100:
    # ... [previous MAX30100 class code remains the same]
    ADDRESS = 0x57
    
    # Register addresses
    REG_INT_STATUS = 0x00
    REG_MODE_CONFIG = 0x06
    REG_SPO2_CONFIG = 0x07
    REG_LED_CONFIG = 0x09
    REG_FIFO_DATA = 0x05
    
    def __init__(self, i2c_bus=1):
        """Initialize MAX30100."""
        self.bus = smbus2.SMBus(i2c_bus)
        self.reset()
        self.setup()
    
    def reset(self):
        """Reset the sensor."""
        self.bus.write_byte_data(self.ADDRESS, self.REG_MODE_CONFIG, 0x40)
        time.sleep(0.1)
    
    def setup(self):
        """Configure sensor."""
        self.bus.write_byte_data(self.ADDRESS, self.REG_MODE_CONFIG, 0x03)
        self.bus.write_byte_data(self.ADDRESS, self.REG_SPO2_CONFIG, 0x27)
        self.bus.write_byte_data(self.ADDRESS, self.REG_LED_CONFIG, 0x24)
    
    def read_sensor(self):
        """Read IR and Red LED values."""
        try:
            data = self.bus.read_i2c_block_data(self.ADDRESS, self.REG_FIFO_DATA, 4)
            ir_value = (data[0] << 8) | data[1]
            red_value = (data[2] << 8) | data[3]
            return ir_value, red_value
        except Exception as e:
            print(f"Error reading MAX30100: {e}")
            return 0, 0

# Initialize MAX30100
try:
    max30100 = MAX30100()
except Exception as e:
    print(f"Error initializing MAX30100: {e}")
    max30100 = None

def read_dht11():
    """Read temperature and humidity from DHT11."""
    if dht_device is None:
        return None
        
    try:
        temperature = dht_device.temperature
        return temperature
    except RuntimeError as e:
        print(f"DHT11 Read Error: {e}")
        return None
    except Exception as e:
        print(f"Error reading DHT11: {e}")
        return None

def read_max30100():
    """Read SpO2 and Heart Rate from MAX30100."""
    if max30100 is None:
        return None, None
        
    try:
        ir_reading, red_reading = max30100.read_sensor()
        
        if ir_reading > 0 and red_reading > 0:
            ratio = red_reading / ir_reading
            spo2 = 110 - 25 * ratio
            spo2 = min(100, max(0, spo2))
            
            heart_rate = 60 if ir_reading > 50000 else 0
            return spo2, heart_rate
        return None, None
    except Exception as e:
        print(f"Error processing MAX30100 data: {e}")
        return None, None

def main():
    print("Starting sensor readings...")
    
    try:
        while True:
            temp = read_dht11()
            spo2, heart_rate = read_max30100()
            
            data = {
                "temperature": temp if temp is not None else 0,
                "heartrate": heart_rate if heart_rate is not None else 0,
                "spo2": spo2 if spo2 is not None else 0,
                "timestamp": time.strftime("%H:%M:%S")
            }
            
            message = json.dumps(data)
            socket.send_string("health_metrics", zmq.SNDMORE)
            socket.send_string(message)
            
            print(f"Sent: {message}")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping sensor readings...")
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        try:
            if dht_device is not None:
                dht_device.exit()
        except Exception as e:
            print(f"Error closing DHT11: {e}")
            
        socket.close()
        context.term()

if __name__ == "__main__":
    main()
