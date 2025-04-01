import time
import max30100

# Initialize MAX30100 sensor
mx30 = max30100.MAX30100()
mx30.enable_spo2()

# Loop to read sensor data
while True:
    mx30.read_sensor()
    
    heart_rate = mx30.ir
    spo2 = mx30.red

    # Ensure valid readings (sometimes the sensor gives 0 or incorrect values)
    if heart_rate > 0 and spo2 > 0:
        print(f"Heart Rate: {heart_rate} BPM")
        print(f"SpO2 Level: {spo2}%")
    else:
        print("Sensor not detecting a valid reading, please adjust placement.")

    time.sleep(2)  # Wait for 2 seconds before the next reading

