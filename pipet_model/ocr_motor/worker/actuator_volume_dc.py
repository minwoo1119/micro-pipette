from worker.make_packet import MakePacket


class VolumeDCActuator:
    """
    Geared DC Motor for Pipette Volume
    - C# MouseDown / MouseUp 구조 1:1 대응
    """

    def __init__(self, serial, actuator_id: int):
        self.serial = serial
        self.actuator_id = actuator_id

    # ======================================================
    # Start rotating (MouseDown)
    # ======================================================
    def run(self, direction: int, duty: int):
        """
        direction: 1 = CW, 0 = CCW
        duty: 0 ~ 100
        """
        direction = 1 if int(direction) > 0 else 0
        duty = max(0, min(100, int(duty)))

        self.serial.send_pipette_change_volume(
            actuator_id=self.actuator_id,
            direction=direction,
            duty=duty,
        )

    # ======================================================
    # Stop rotating (MouseUp)
    # ======================================================
    def stop(self):
        self.serial.send_pipette_stop(self.actuator_id)
