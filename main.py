import threading
import time

from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from Ammeters.client import request_current_from_ammeter


def run_greenlee_emulator():
    greenlee = GreenleeAmmeter(5001)
    greenlee.start_server()

def run_entes_emulator():
    entes = EntesAmmeter(5002)
    entes.start_server()

def run_circutor_emulator():
    circutor = CircutorAmmeter(5003)
    circutor.start_server()

if __name__ == "__main__":
    # Start each ammeter in a separate thread
    threading.Thread(target=run_greenlee_emulator, daemon=True).start()
    threading.Thread(target=run_entes_emulator, daemon=True).start()
    threading.Thread(target=run_circutor_emulator, daemon=True).start()

    # Wait for the servers to start, if you have problem restarting the servers between runs try increasing sleep time.
    time.sleep(2)

    # FIX: each emulator matches the FULL command exactly (see each Ammeter's
    # `get_current_command`). The original commented-out calls sent truncated
    # commands (e.g. b'MEASURE_GREENLEE'), so `data == self.get_current_command`
    # was never True and the server never replied. Sending the exact command
    # bytes makes the emulators respond with a measurement.
    request_current_from_ammeter(5001, b'MEASURE_GREENLEE -get_measurement')          # Greenlee
    request_current_from_ammeter(5002, b'MEASURE_ENTES -get_data')                    # ENTES
    request_current_from_ammeter(5003, b'MEASURE_CIRCUTOR -get_measurement -current') # CIRCUTOR
