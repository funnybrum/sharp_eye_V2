from lib.log import log


class HssZoneState:
    ARMED = "armed"
    DISARMED = "disarmed"
    ARMING = "arming"
    TRIGGERED = "triggered"

    @staticmethod
    def from_string(value):
        if value == "disarmed":
            return HssZoneState.DISARMED
        elif value == "arming":
            return HssZoneState.ARMING
        elif value in ["armed_home", "armed_night", "armed_away", "armed"]:
            return HssZoneState.ARMED
        elif value == "triggered":
            return HssZoneState.TRIGGERED
        else:
            log("Failed to map PAI state %s to HssZoneState" % value)
            return None
