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