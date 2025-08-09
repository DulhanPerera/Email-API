from pymongo import MongoClient
import configparser
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
import logging

class ConfigSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigSingleton, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._config = self._load_config()
        self._initialized = True

    def _load_config(self):
        # ✅ Safe logger setup
        try:
            from utils.logger import SingletonLogger
            logger = SingletonLogger.get_logger("appLogger")
        except Exception:
            logger = logging.getLogger("fallback_logger")
            if not logger.handlers:
                logging.basicConfig(level=logging.INFO)

        # Load .env file
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

        config = configparser.RawConfigParser()
        ini_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'core_config.ini')
        config.read(ini_path)

        # Get environment from .env
        env = os.getenv("ENV", "development").strip().lower()

        def env_key(base):
            return f"{base.upper()}_{env.upper()}"

        mongo_user = quote_plus(os.getenv(env_key("MONGO_USERNAME")))
        mongo_pass = quote_plus(os.getenv(env_key("MONGO_PASSWORD")))
        mongo_hosts = os.getenv(env_key("MONGO_HOSTS"))
        mongo_replica = os.getenv(env_key("REPLICA_SET"), "rs0")
        mongo_db = os.getenv(env_key("DB_NAME"))

        mongo_uri = (
            f"mongodb://localhost:27017/"
        )

        server_section = f"server_{env}"
        host = config.get(server_section, "host", fallback="127.0.0.1")
        port = config.getint(server_section, "port", fallback=8000)

        logger_section = f"logger_path_{env}"
        log_dir = config.get(logger_section, "log_dir", fallback="/tmp/logs")

        return {
            "env": env,
            "mongo_uri": mongo_uri,
            "mongo_db": mongo_db,
            "host": host,
            "port": port,
            "log_dir": log_dir
        }

    def get_config(self):
        return self._config

    def get_json_template_path(self, template_section_key: str) -> str:
        """
        Returns full path to a JSON template file based on the current environment and section key.
        e.g. get_json_template_path('Case_distribution_drc_transactions') → path to JSON file
        """
        config = configparser.ConfigParser()
        ini_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'core_config.ini')
        config.read(ini_path)

        env = self._config["env"]
        section_name = f"{template_section_key}_{env}"

        if section_name not in config:
            raise ValueError(f"Template section '{section_name}' not found in core_config.ini")

        file_key = list(config[section_name].keys())[0]
        filename = config[section_name][file_key].strip()

        full_path = os.path.join(os.path.dirname(__file__), '..', 'json_template', filename)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"JSON template not found: {full_path}")

        return full_path

# Global function for backward compatibility
def get_config():
    return ConfigSingleton().get_config()

# Global function for backward compatibility
def get_json_template_path(template_section_key: str) -> str:
    return ConfigSingleton().get_json_template_path(template_section_key)