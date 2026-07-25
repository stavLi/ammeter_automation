# Ammeter Emulators

This project provides emulators for different types of ammeters: Greenlee, ENTES, and CIRCUTOR. Each ammeter emulator runs on a separate thread and can respond to current measurement requests. On top of them sits a **config-driven test framework** that samples each ammeter and reports statistics.

## How to run

Requires Python 3.9+.

```sh
# 1. Set up a virtualenv and install dependencies
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt        # runtime (pyyaml)
.venv/bin/pip install -r requirements-dev.txt     # dev tools (pytest, pyright)

# 2. Run the framework — starts the emulators, samples each ammeter, prints a stats report
.venv/bin/python main.py
.venv/bin/python main.py --ammeter entes          # a single ammeter
.venv/bin/python main.py --verbose                # with per-measurement logging
.venv/bin/python main.py --no-save                # run without archiving the result

# 3. Retrieve and compare archived runs (no emulators needed)
.venv/bin/python main.py --list                   # list archived run IDs
.venv/bin/python main.py --show <run_id>          # print one archived run
.venv/bin/python main.py --compare <run_a> <run_b>  # per-ammeter, per-stat deltas

# 4. Run the test suite / type-check
.venv/bin/pytest
.venv/bin/pyright
```

### With Docker

```sh
docker compose up --build --abort-on-container-exit --exit-code-from tests
```

Runs the emulators as a service and executes the full test suite against them.

Configuration — ports, commands, sampling `count` / `frequency` / `duration`, and which
statistics to report — lives in `config/config.yaml`.

## Project Structure

- `Ammeters/`
  - `main.py`: Main script to start the ammeter emulators and request current measurements.
  - `Circutor_Ammeter.py`: Emulator for the CIRCUTOR ammeter.
  - `Entes_Ammeter.py`: Emulator for the ENTES ammeter.
  - `Greenlee_Ammeter.py`: Emulator for the Greenlee ammeter.
  - `base_ammeter.py`: Base class for all ammeter emulators.
  - `client.py`: Client to request current measurements from the ammeter emulators.
- `config/`
  - `config.yaml`: Configuration file for the ammeter emulators.
- `examples/`
  - `run_test.py`: super lyze example for run test **don't use it**.
- `src/`
  - `testing/`
    - `AmmeterTester.py`: Class to test the ammeter emulators.
  - `utils/`
    - `config.py`: Configuration settings.
    - `logger.py`: Logging setup.
    - `Utils.py`: Utility functions, including `generate_random_float`.

## Usage

# Ammeter Emulators

## Greenlee Ammeter

- **Port**: 5001
- **Command**: `MEASURE_GREENLEE -get_measurement`
- **Measurement Logic**: Calculates current using voltage (1V - 10V) and (0.1Ω - 100Ω).
- **Measurement method** : Ohm's Law: I = V / R

## ENTES Ammeter

- **Port**: 5002
- **Command**: `MEASURE_ENTES -get_data`
- **Measurement Logic**: Calculates current using magnetic field strength (0.01T - 0.1T) and calibration factor (500 - 2000).
- **Measurement method** : Hall Effect: I = B * K

## CIRCUTOR Ammeter

- **Port**: 5003
- **Command**: `MEASURE_CIRCUTOR -get_measurement -current`
- **Measurement Logic**: Calculates current using voltage values (0.1V - 1.0V) over a number of samples and a random time step (0.001s - 0.01s).
- **Measurement method** : Rogowski Coil Integration: I = ∫V dt

To start the ammeter emulators and request current measurements, run the `main.py` script:
```sh
python main.py
```