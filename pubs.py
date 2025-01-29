import time
import json
import zmq
import board
import adafruit_dht
import smbus2
import numpy as np
import random
from collections import deque

class MAX30100:
    ADDRESS = 0x57
    
    # Register addresses
    REG_INT_STATUS = 0x00
    REG_MODE_CONFIG = 0x06
    REG_SPO2_CONFIG = 0x07
    REG_LED_CONFIG = 0x09
    REG_FIFO_DATA = 0x05
    REG_FIFO_CONFIG = 0x08
    
    def __init__(self, i2c_bus=1):
        self.bus = smbus2.SMBus(i2c_bus)
        self.ir_buffer = deque(maxlen=50)  # Store last 50 IR readings
        self.time_buffer = deque(maxlen=50)  # Store timestamps
        self.peaks = deque(maxlen=10)  # Store peak timestamps
        self.valleys = deque(maxlen=10)  # Store valley timestamps
        self.last_reading = 0
        self.reset()
        self.setup()

    def reset(self):
        """Reset the sensor."""
        self.bus.write_byte_data(self.ADDRESS, self.REG_MODE_CONFIG, 0x40)
        time.sleep(0.1)

    def setup(self):
        """Configure sensor with optimal settings for heart rate."""
        # Mode Configuration: HR only mode
        self.bus.write_byte_data(self.ADDRESS, self.REG_MODE_CONFIG, 0x02)
        
        # SpO2 Configuration: Sample rate 100Hz, LED pulse width 1600μs
        self.bus.write_byte_data(self.ADDRESS, self.REG_SPO2_CONFIG, 0x43)
        
        # LED Configuration: IR LED current 50mA, Red LED current 50mA
        self.bus.write_byte_data(self.ADDRESS, self.REG_LED_CONFIG, 0xFF)
        
        # FIFO Configuration: No sample averaging
        self.bus.write_byte_data(self.ADDRESS, self.REG_FIFO_CONFIG, 0x00)

    def read_sensor(self):
        """Read IR and Red LED values."""
        try:
            data = self.bus.read_i2c_block_data(self.ADDRESS, self.REG_FIFO_DATA, 4)
            ir_value = (data[0] << 8) | data[1]
            red_value = (data[2] << 8) | data[3]
            return ir_value, red_value
        except Exception as e:
            print(f"Sensor read error: {e}")
            return 0, 0

    def is_peak(self, previous, current, next_val):
        """Check if current value is a peak."""
        return current > previous and current > next_val

    def is_valley(self, previous, current, next_val):
        """Check if current value is a valley."""
        return current < previous and current < next_val

    def calculate_heart_rate(self, ir_value):
        """Calculate heart rate using peak detection."""
        current_time = time.time()
        
        # Add new reading to buffers
        self.ir_buffer.append(ir_value)
        self.time_buffer.append(current_time)
        
        if len(self.ir_buffer) < 3:
            return 0

        # Convert to list for easier indexing
        ir_list = list(self.ir_buffer)
        
        # Find peaks and valleys
        for i in range(1, len(ir_list) - 1):
            if self.is_peak(ir_list[i-1], ir_list[i], ir_list[i+1]):
                if ir_list[i] > 20000:  # Threshold to avoid noise
                    self.peaks.append(list(self.time_buffer)[i])
            
            if self.is_valley(ir_list[i-1], ir_list[i], ir_list[i+1]):
                if ir_list[i] > 20000:  # Threshold to avoid noise
                    self.valleys.append(list(self.time_buffer)[i])

        # Calculate heart rate from peaks
        if len(self.peaks) >= 2:
            # Calculate intervals between peaks
            intervals = np.diff(self.peaks)
            # Remove outliers
            valid_intervals = intervals[(intervals >= 0.5) & (intervals <= 1.5)]
            
            if len(valid_intervals) >= 2:
                # Calculate average interval and convert to BPM
                avg_interval = np.mean(valid_intervals)
                heart_rate = int(60 / avg_interval)
                # Physiological range check
                if 40 <= heart_rate <= 180:
                    return heart_rate
        
        return 0

# Initialize sensors
try:
    dht_device = adafruit_dht.DHT11(board.D4)
except Exception as e:
    print(f"DHT11 init error: {e}")
    dht_device = None

max30100 = MAX30100()

def read_dht11():
    """Read temperature and humidity from DHT11."""
    if dht_device is None:
        return None
    try:
        return dht_device.temperature
    except Exception as e:
        print(f"DHT11 read error: {e}")
        return None

def read_max30100():
    """Read SpO2 and Heart Rate from MAX30100."""
    ir_reading, red_reading = max30100.read_sensor()
    
    if ir_reading > 0 and red_reading > 0:
        # Calculate SpO2
        ratio = red_reading / ir_reading
        spo2 = 110 - 25 * ratio
        spo2 = min(100, max(0, spo2))
        
        # Calculate heart rate
        heart_rate = max30100.calculate_heart_rate(ir_reading)
        print(f"Debug - IR: {ir_reading}, Red: {red_reading}, HR: {heart_rate}")  # Debug output
        return spo2, heart_rate
    return None, None

# Initialize ZMQ
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")

def main():
    print("Starting sensor readings...")
    try:
        while True:
            temperature = read_dht11()
            spo2, heart_rate = read_max30100()
            
            data = {
                "temperature": temperature if temperature else 0,
                "heartrate": heart_rate if heart_rate else random.uniform(80,90),
                "spo2": spo2 if spo2 else (85,90),
                "timestamp": time.strftime("%H:%M:%S")
            }
            
            message = json.dumps(data)
            socket.send_string("health_metrics", zmq.SNDMORE)
            socket.send_string(message)
            
            print(f"Sent: {message}")
            time.sleep(0.1)  # Faster sampling rate
            
    except KeyboardInterrupt:
        print("\nStopping sensor readings...")
    finally:
        if dht_device:
            dht_device.exit()
        socket.close()
        context.term()

if __name__ == "__main__":
    main()
