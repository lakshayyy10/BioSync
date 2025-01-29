import time
import json
import zmq
import board
import adafruit_dht
import smbus2
import numpy as np
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
    REG_FIFO_WR_PTR = 0x02
    REG_FIFO_RD_PTR = 0x03
    
    def __init__(self, i2c_bus=1):
        """Initialize MAX30100."""
        self.bus = smbus2.SMBus(i2c_bus)
        self.reset()
        self.setup()
        self.ir_buffer = deque(maxlen=100)  # Buffer for heart rate calculation
        self.last_beat = time.time()
        self.beats = deque(maxlen=4)  # Store last 4 beat intervals
    
    def reset(self):
        """Reset the sensor."""
        self.bus.write_byte_data(self.ADDRESS, self.REG_MODE_CONFIG, 0x40)
        time.sleep(0.1)
    
    def setup(self):
        """Configure sensor with optimal settings."""
        # Mode Configuration: HR only mode, high-resolution
        self.bus.write_byte_data(self.ADDRESS, self.REG_MODE_CONFIG, 0x02)
        
        # SpO2 Configuration: Sample rate 100Hz, high-resolution
        self.bus.write_byte_data(self.ADDRESS, self.REG_SPO2_CONFIG, 0x47)
        
        # LED Configuration: Red LED 27.1mA, IR LED 27.1mA
        self.bus.write_byte_data(self.ADDRESS, self.REG_LED_CONFIG, 0x7F)
        
        # FIFO Configuration: Sample averaging 4, FIFO rollover enabled
        self.bus.write_byte_data(self.ADDRESS, self.REG_FIFO_CONFIG, 0x0F)
    
    def read_sensor(self):
        """Read IR and Red LED values with improved error handling."""
        try:
            data = self.bus.read_i2c_block_data(self.ADDRESS, self.REG_FIFO_DATA, 4)
            ir_value = (data[0] << 8) | data[1]
            red_value = (data[2] << 8) | data[3]
            return ir_value, red_value
        except OSError:
            return 0, 0
    
    def calculate_heart_rate(self, ir_value):
        """Calculate heart rate using peak detection algorithm."""
        if ir_value < 5000:  # Ignore noise
            return 0
            
        self.ir_buffer.append(ir_value)
        
        if len(self.ir_buffer) < 100:  # Wait for buffer to fill
            return 0
            
        # Simple peak detection
        ir_mean = np.mean(self.ir_buffer)
        if (ir_value > ir_mean * 1.5 and 
            time.time() - self.last_beat > 0.5):  # Minimum 0.5s between beats
            
            beat_time = time.time()
            interval = beat_time - self.last_beat
            self.last_beat = beat_time
            
            if 0.3 <= interval <= 1.5:  # Valid beat range (40-200 BPM)
                self.beats.append(interval)
                
        if len(self.beats) >= 3:
            avg_interval = np.mean(self.beats)
            heart_rate = int(60 / avg_interval)
            return min(200, max(40, heart_rate))  # Limit to physiological range
        
        return 0

def read_max30100():
    """Read SpO2 and Heart Rate from MAX30100."""
    ir_reading, red_reading = max30100.read_sensor()
    
    if ir_reading > 0 and red_reading > 0:
        # Calculate SpO2
        ratio = red_reading / ir_reading
        spo2 = 110 - 25 * ratio  # Basic SpO2 calculation
        spo2 = min(100, max(0, spo2))
        
        # Calculate heart rate using improved algorithm
        heart_rate = max30100.calculate_heart_rate(ir_reading)
        return spo2, heart_rate
    return None, None

def main():
    print("Starting sensor readings...")
    
    try:
        while True:
            temperature = read_dht11()
            spo2, heart_rate = read_max30100()
            
            data = {
                "temperature": temperature if temperature else 0,
                "heartrate": heart_rate if heart_rate else 0,
                "spo2": spo2 if spo2 else 0,
                "timestamp": time.strftime("%H:%M:%S")
            }
            
            message = json.dumps(data)
            socket.send_string("health_metrics", zmq.SNDMORE)
            socket.send_string(message)
            
            print(f"Sent: {message}")
            time.sleep(0.01)  # Faster sampling rate
            
    except KeyboardInterrupt:
        print("\nStopping sensor readings...")
    finally:
        dht_device.exit()
        socket.close()
        context.term()

if __name__ == "__main__":
    main()
