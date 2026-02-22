import json
import os
import sys

class ConfigManager:
    # Default configuration
    _DEFAULTS = {
        "strictness": "strict",
        "spike_mode_allowed": True,
        "context_limit": 100000,
        "context_check_interval": 600,
        "external_state_file": "todo.md",
        "external_state_ttl": 600,
        "scan_ignores": [],
        "skill_base_path": ".lisa/skills",
        "installation_type": "drop-in",
        "hooks_mode": "auto",
        "lifecycle_hooks": {
            "story-kickoff": [],
            "story-in-dev": ["lisa turns"],
            "story-test": ["lisa refactor"],
            "story-complete": ["lisa polish"],
            "context-reset": ["lisa checkpoint"]
        },
        "test_layers": {
            "integration_path_patterns": [
                "tests/integration/",
                "tests/api/",
                "tests/contract/",
                "tests/pact/",
                "tests/component/"
            ],
            "integration_name_patterns": [
                "*_contract_test.py",
                "*_pact_test.py",
                "*_api_test.py",
                "*_component_test.py",
                "test_*_contract.py",
                "test_*_pact.py",
                "test_*_api.py",
                "test_*_component.py"
            ],
            "custom_rules": {}
        }
    }

    def __init__(self, user_config_path=None, project_config_path=None, project_root=None):
        self.user_config_path = user_config_path or os.path.expanduser("~/.lisa/config.json")
        
        if project_config_path:
            self.project_config_path = project_config_path
        else:
            if project_root:
                # Prioritize yaml for Epic 9
                yaml_path = os.path.join(project_root, ".lisa", "config.yaml")
                json_path = os.path.join(project_root, ".lisa", "config.json")
                self.project_config_path = yaml_path if os.path.exists(yaml_path) else json_path
            else:
                # Fallback for backward compatibility / tests without root
                self.project_config_path = os.path.abspath("./.lisa/config.yaml") if os.path.exists("./.lisa/config.yaml") else os.path.abspath("./.lisa/config.json")
                
        self._config = self.load()

    def _load_yaml_safe(self, path):
        """Loads YAML from a file, returns empty dict on failure."""
        if not os.path.exists(path):
            return {}
        try:
            import yaml
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        except (ImportError, Exception) as e:
            # If PyYAML is missing, we can't load YAML. 
            # In a real environment we'd handle this better, but for MVP we assume presence if setup runs.
            return {}

    def _load_json_safe(self, path):
        """Loads JSON from a file, returns empty dict on failure."""
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            # NFR3: Warn and proceed
            print(f"[LISA] [WARNING] Failed to load config from {path}: {e}", file=sys.stderr)
            return {}

    def load(self):
        """Loads and merges configuration: Defaults < User < Project."""
        config = self._DEFAULTS.copy()
        
        # Load User Config
        user_config = {}
        if self.user_config_path.endswith((".yaml", ".yml")):
            user_config = self._load_yaml_safe(self.user_config_path)
        else:
            user_config = self._load_json_safe(self.user_config_path)
        config.update(user_config)
        
        # Load Project Config
        project_config = {}
        if self.project_config_path.endswith((".yaml", ".yml")):
            project_config = self._load_yaml_safe(self.project_config_path)
        else:
            project_config = self._load_json_safe(self.project_config_path)
        config.update(project_config)
        
        return config

    def get(self, key, default=None):
        """Retrieves a configuration value."""
        return self._config.get(key, default)
