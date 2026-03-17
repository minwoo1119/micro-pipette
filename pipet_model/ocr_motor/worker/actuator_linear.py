from worker.serial_controller import SerialController
import time


class LinearActuator:
    """
    MightyZap Linear Actuator controller

    Used for:
    - Pipetting (흡인/분주)
    - Tip change (팁 교체)
    - Volume linear movement (용량 리니어)

    This class is a semantic wrapper over SerialController.
    """

    def __init__(
        self,
        serial: SerialController,
        actuator_id: int,
    ):
        """
        actuator_id examples (from CEO firmware):
        - 0x0A : Volume Linear
        - 0x0B : Tip & Pipetting Linear
        """
        self.serial = serial
        self.actuator_id = actuator_id

    # -------------------------------------------------
    # Core low-level move
    # -------------------------------------------------
    def move_to(self, position: int):
        self.serial.send_mightyzap_set_position(self.actuator_id, position)
        time.sleep(0.6)  # 물리 이동 시간
        return True



    # -------------------------------------------------
    # Pipetting (흡인 / 분주)
    # -------------------------------------------------
    def pipetting_up(self, pos_max: int):
        """
        흡인분주 상승
        """
        self.move_to(pos_max)

    def pipetting_down(self, pos_min: int):
        """
        흡인분주 하강
        """
        self.move_to(pos_min)

    # -------------------------------------------------
    # Tip change
    # -------------------------------------------------
    def tip_change_up(self, pos_max: int):
        """
        팁 교체 상승
        """
        self.move_to(pos_max)

    def tip_change_down(self, pos_min: int):
        """
        팁 교체 하강
        """
        self.move_to(pos_min)

    # -------------------------------------------------
    # Volume linear (optional)
    # -------------------------------------------------
    def volume_up(self, pos_max: int):
        """
        용량 리니어 상승
        """
        self.move_to(pos_max)

    def volume_down(self, pos_min: int):
        """
        용량 리니어 하강
        """
        self.move_to(pos_min)
