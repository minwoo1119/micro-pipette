import time
import serial

SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 115200

def _connect():
    return serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

def motor_test(direction, power, duration):
    print(f"[MOTOR TEST] {direction=} {power=} {duration=}")

    ser = _connect()
    cmd = f"TEST {direction} {power}\n"
    ser.write(cmd.encode())

    time.sleep(duration)

    ser.write(b"STOP\n")
    ser.close()

def run_to_target(target_value):
    print(f"[TARGET RUN] target = {target_value}")

    ser = _connect()
    ser.write(f"TARGET {target_value}\n".encode())

    # 실제론 여기서 OCR/TRT feedback loop 들어가면 됨
    time.sleep(3)

    ser.write(b"STOP\n")
    ser.close()
