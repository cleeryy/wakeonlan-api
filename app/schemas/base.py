"""Base schema configuration."""
from pydantic import ConfigDict

__all__ = ["BaseConfig"]

BaseConfig = ConfigDict(from_attributes=True)
