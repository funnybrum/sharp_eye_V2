PERIMETER_PARTITION = "PERIMETER"

class HssMode:
    AUTO = "auto"
    MANUAL = "manual"


HSS_STATE = {
    "1ST_FLOOR": {
        "state": None,
        "mode": HssMode.MANUAL,
        "name": "Floor 1"
    },
    "2ND_FLOOR": {
        "state": None,
        "mode": HssMode.MANUAL,
        "name": "Floor 2"
    },
    "SERVICE_ROOM": {
        "state": None,
        "mode": HssMode.MANUAL,
        "name": "Service room"
    },
    "WORKSHOP": {
        "state": None,
        "mode": HssMode.MANUAL,
        "name": "Workshop"
    },
    "PERIMETER": {
        "state": "disarmed",
        "mode": HssMode.MANUAL,
        "name": "Perimeter"
    }
}
