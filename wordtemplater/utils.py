import re
from typing import Any, List, Tuple

def resolve_token(data: Any, path: str) -> Any:
    """
    Resolves property path from dictionary, object, or list case-insensitively,
    supporting dot notation and array indexing (e.g. 'Customer.Address.City', 'Items[0].Name').
    """
    if data is None or not path:
        return None

    normalized_path = path.strip()
    if not normalized_path:
        return None

    # Match tokens: either words or [index]
    pattern = re.compile(r"([^[.\]]+)|\[(\d+)\]")
    parts = []
    for match in pattern.finditer(normalized_path):
        if match.group(1) is not None:
            parts.append(match.group(1))
        elif match.group(2) is not None:
            parts.append(match.group(2))

    current = data
    for part in parts:
        if current is None:
            return None

        # Check list index
        if isinstance(current, (list, tuple)):
            try:
                idx = int(part)
                if 0 <= idx < len(current):
                    current = current[idx]
                    continue
                return None
            except ValueError:
                return None

        # Check dict (case-insensitive)
        if isinstance(current, dict):
            if part in current:
                current = current[part]
                continue
            lower_part = part.lower()
            matched_key = next((k for k in current.keys() if str(k).lower() == lower_part), None)
            if matched_key is not None:
                current = current[matched_key]
            else:
                return None
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            # Check attributes case-insensitively
            lower_part = part.lower()
            matched_attr = next((a for a in dir(current) if a.lower() == lower_part), None)
            if matched_attr:
                current = getattr(current, matched_attr)
            else:
                return None

    return current


def parse_expression(raw_expr: str) -> Tuple[str, str, List[Any]]:
    """
    Parses placeholder expressions such as:
    - 'Customer.Name' -> ('', 'Customer.Name', [])
    - 'upper(Name)' -> ('upper', 'Name', [])
    - "currency(Total, 'vi-VN')" -> ('currency', 'Total', ['vi-VN'])
    - "table(Items, 'F9FAFB', 'FFFFFF')" -> ('table', 'Items', ['F9FAFB', 'FFFFFF'])
    Returns: (func_name, field_path, args)
    """
    clean = raw_expr.strip().strip("«»").strip()
    func_match = re.match(r"^([a-zA-Z0-9_]+)\s*\((.*)\)$", clean)

    if not func_match:
        return ("", clean, [])

    func_name = func_match.group(1).lower()
    raw_args = func_match.group(2).strip()

    if not raw_args:
        return (func_name, "", [])

    parsed_args = _split_args(raw_args)
    field_path = str(parsed_args[0]) if len(parsed_args) > 0 else ""
    remaining_args = parsed_args[1:]

    return (func_name, field_path, remaining_args)


def _split_args(arg_string: str) -> List[Any]:
    args = []
    current = []
    in_quotes = False
    quote_char = ""

    for c in arg_string:
        if in_quotes:
            if c == quote_char:
                in_quotes = False
            else:
                current.append(c)
        else:
            if c in ("'", '"'):
                in_quotes = True
                quote_char = c
            elif c == ",":
                val = "".join(current).strip()
                args.append(_parse_val(val))
                current = []
            else:
                current.append(c)

    if current:
        val = "".join(current).strip()
        args.append(_parse_val(val))

    return args


def _parse_val(val: str) -> Any:
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    if val.lower() == "null" or val.lower() == "none":
        return None
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        return val
