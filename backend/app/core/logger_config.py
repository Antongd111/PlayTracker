# core/logging_config.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Configuración del directorio y archivos de logs
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "api.log"


def get_logger(name: str | None = None) -> logging.Logger:

    logger_name = "playtracker"
    if name:
        logger_name = f"playtracker.{name}"

    logger = logging.getLogger(logger_name)

    if logger.handlers:
        # Ya está configurado, no añadimos handlers otra vez
        return logger

    logger.setLevel(logging.INFO)

    # Formato de los mensajes de logs
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # Configuramos rotación para no saturar un solo archivo de logs (Máximo de 5MB por archivo, 3 backups)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )

    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
