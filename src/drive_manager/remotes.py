"""Discover metadata only; never dump or parse rclone credentials."""
import json
from .process import OperationError
from .providers import ACTIVE_TYPES

def discover(runner, config=None):
    try:
        args = ["rclone", "listremotes", "--json"]
        if config is not None: args.append("--config=" + str(config))
        entries = json.loads(runner.run(args))
        if not isinstance(entries, list):
            raise ValueError()
        return sorted({item["name"].removesuffix(":") for item in entries
                       if item.get("type") in ACTIVE_TYPES and item.get("source") == "file"
                       and isinstance(item.get("name"), str)})
    except (ValueError, TypeError, KeyError, AttributeError):
        raise OperationError("Unsupported rclone metadata format") from None
