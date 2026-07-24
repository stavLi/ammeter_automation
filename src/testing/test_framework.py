from typing import Dict

from ..utils.config import load_config


class AmmeterTestFramework:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = load_config(config_path)

    def run_test(self, ammeter_type: str) -> Dict:
        # TODO(config-driven framework, task #2): implement the unified test run.
        raise NotImplementedError("AmmeterTestFramework.run_test is not implemented yet")
