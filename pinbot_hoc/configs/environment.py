from pydantic import BaseSettings


class Environments(BaseSettings):
    # discord
    discord_token: str

    # Logging
    log_level: str = 'INFO'
    log_format: str = '%(asctime)s | [%(levelname)7s] %(message)s '
