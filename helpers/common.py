import argparse
import json
import os
import configparser
from datetime import datetime, timezone
from typing import Dict, Any, Optional


def load_config(
    default_config: Dict[str, Any],
    config_file_path: Optional[str] = None,
    env_prefix: str = "APP_",
) -> Dict[str, Any]:
    """
    Загружает конфигурацию из нескольких источников с приоритетом:
    Аргументы командной строки > Переменные окружения > Файл конфигурации > Значения по умолчанию

    :param default_config: Словарь с значениями по умолчанию
    :param config_file_path: Путь к файлу конфигурации (JSON/INI)
    :param env_prefix: Префикс для переменных окружения
    :return: Объединенный словарь конфигурации
    """
    config = default_config.copy()

    # 1. Загрузка из файла конфигурации
    if config_file_path:
        try:
            if config_file_path.endswith(".json"):
                with open(config_file_path, "r") as f:
                    file_config = json.load(f)
                config.update(file_config)
            elif config_file_path.endswith(".ini"):
                parser = configparser.ConfigParser()
                parser.read(config_file_path)
                file_config = {
                    k: v
                    for section in parser.sections()
                    for k, v in parser[section].items()
                }
                config.update(file_config)
        except Exception as e:
            print(f"⚠️ Ошибка загрузки конфиг-файла: {e}")

    # 2. Загрузка из переменных окружения
    for key in list(config.keys()):
        env_var = f"{env_prefix}{key.upper()}"
        if env_var in os.environ:
            # Автоматическое преобразование типов
            value = os.environ[env_var]
            if isinstance(config[key], bool):
                # Обработка булевых значений
                config[key] = value.lower() in ("true", "1", "yes", "y")
            elif isinstance(config[key], int):
                config[key] = int(value)
            elif isinstance(config[key], float):
                config[key] = float(value)
            else:
                config[key] = value

    # 3. Загрузка из аргументов командной строки
    parser = argparse.ArgumentParser()
    for key, value in config.items():
        arg_name = f"--{key.replace('_', '-')}"
        if isinstance(value, bool):
            # Булевы флаги
            parser.add_argument(
                arg_name,
                action=f"store_{str(not value).lower()}",
                dest=key,
                default=value,
            )
        else:
            parser.add_argument(arg_name, type=type(value), default=value, dest=key)

    args = parser.parse_args()
    config.update(vars(args))

    return config


def format_errors(data):
    """
    Formats received errors into a structured JSON document.
    Handles:
    - Multiple errors in a single report
    - Timestamp conversion
    - Missing fields
    """
    try:
        errors = []
        i = 0

        # Iterate through errors (format: errors[0][type], errors[1][type], ...)
        while True:
            prefix = f"errors[{i}]"
            if f"{prefix}[type]" not in data:
                break

            # Build a dictionary with error data (with key existence checks)
            error_data = {
                "type": data.get(f"{prefix}[type]", "unknown"),
                "message": data.get(f"{prefix}[log_message]", ""),
                "file": data.get(f"{prefix}[log_extra]", ""),
                "line": data.get(f"{prefix}[line]", "0"),
                "date": data.get(f"{prefix}[date]", "0"),
            }

            # Convert timestamp to human-readable format
            try:
                dt = datetime.utcfromtimestamp(int(error_data["date"]))
                error_data["human_date"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                error_data["human_date"] = "invalid_timestamp"

            errors.append(error_data)
            i += 1

        # Build the final JSON
        return json.dumps(
            {
                "errors": errors,
                "version": data.get("version", ""),
                "received_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
            ensure_ascii=False,
        )

    except Exception as e:
        # Return raw data if formatting fails
        return f"Formatting error: {str(e)}\n\nRaw data:\n{json.dumps(dict(data), indent=2)}"
