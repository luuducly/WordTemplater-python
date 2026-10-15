import datetime
from typing import Any, List

class Evaluator:
    def evaluate(self, value: Any, parameters: List[Any]) -> Any:
        raise NotImplementedError


class UpperEvaluator(Evaluator):
    def evaluate(self, value: Any, parameters: List[Any]) -> str:
        return str(value).upper() if value is not None else ""


class LowerEvaluator(Evaluator):
    def evaluate(self, value: Any, parameters: List[Any]) -> str:
        return str(value).lower() if value is not None else ""


class TrimEvaluator(Evaluator):
    def evaluate(self, value: Any, parameters: List[Any]) -> str:
        return str(value).strip() if value is not None else ""


class SubEvaluator(Evaluator):
    def evaluate(self, value: Any, parameters: List[Any]) -> str:
        if value is None:
            return ""
        s = str(value)
        start = int(parameters[0]) if len(parameters) > 0 else 0
        if len(parameters) > 1:
            length = int(parameters[1])
            return s[start:start + length]
        return s[start:]


class LeftEvaluator(Evaluator):
    def evaluate(self, value: Any, parameters: List[Any]) -> str:
        if value is None:
            return ""
        s = str(value)
        count = int(parameters[0]) if len(parameters) > 0 else 0
        return s[:count]


class RightEvaluator(Evaluator):
    def evaluate(self, value: Any, parameters: List[Any]) -> str:
        if value is None:
            return ""
        s = str(value)
        count = int(parameters[0]) if len(parameters) > 0 else 0
        if count <= 0:
            return ""
        if count >= len(s):
            return s
        return s[-count:]


class ReplaceEvaluator(Evaluator):
    def evaluate(self, value: Any, parameters: List[Any]) -> str:
        if value is None:
            return ""
        s = str(value)
        old_val = str(parameters[0]) if len(parameters) > 0 else ""
        new_val = str(parameters[1]) if len(parameters) > 1 else ""
        return s.replace(old_val, new_val)


class PadLeftEvaluator(Evaluator):
    def evaluate(self, value: Any, parameters: List[Any]) -> str:
        if value is None:
            return ""
        s = str(value)
        width = int(parameters[0]) if len(parameters) > 0 else len(s)
        pad_char = str(parameters[1])[0] if len(parameters) > 1 and str(parameters[1]) else " "
        return s.rjust(width, pad_char)


class PadRightEvaluator(Evaluator):
    def evaluate(self, value: Any, parameters: List[Any]) -> str:
        if value is None:
            return ""
        s = str(value)
        width = int(parameters[0]) if len(parameters) > 0 else len(s)
        pad_char = str(parameters[1])[0] if len(parameters) > 1 and str(parameters[1]) else " "
        return s.ljust(width, pad_char)


class CurrencyEvaluator(Evaluator):
    def evaluate(self, value: Any, parameters: List[Any]) -> str:
        if value is None or value == "":
            return ""
        try:
            val_float = float(value)
        except (ValueError, TypeError):
            return str(value)

        culture = str(parameters[0]).lower() if len(parameters) > 0 else "en-us"
        if culture.startswith("vi"):
            # Vietnamese format: 1.500.000 ₫
            formatted = f"{int(val_float):,}".replace(",", ".")
            return f"{formatted} ₫"
        else:
            # US / standard format: $1,500.00
            return f"${val_float:,.2f}"


class NumberEvaluator(Evaluator):
    def evaluate(self, value: Any, parameters: List[Any]) -> str:
        if value is None or value == "":
            return ""
        try:
            val_float = float(value)
            if val_float.is_integer():
                return f"{int(val_float):,}"
            return f"{val_float:,}"
        except (ValueError, TypeError):
            return str(value)


class PercentageEvaluator(Evaluator):
    def evaluate(self, value: Any, parameters: List[Any]) -> str:
        if value is None or value == "":
            return ""
        try:
            val_float = float(value) * 100
            return f"{val_float:.2f}%"
        except (ValueError, TypeError):
            return str(value)


class DateEvaluator(Evaluator):
    def evaluate(self, value: Any, parameters: List[Any]) -> str:
        if value is None or value == "":
            return ""
        dt = None
        if isinstance(value, (datetime.date, datetime.datetime)):
            dt = value
        elif isinstance(value, str):
            try:
                dt = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return value
        if not dt:
            return str(value)

        fmt = str(parameters[0]) if len(parameters) > 0 else "%Y-%m-%d"
        # Map common .NET format specifiers to Python strftime
        py_fmt = (
            fmt.replace("yyyy", "%Y")
            .replace("MM", "%m")
            .replace("dd", "%d")
            .replace("HH", "%H")
            .replace("mm", "%M")
            .replace("ss", "%S")
        )
        return dt.strftime(py_fmt)


class DefaultValueEvaluator(Evaluator):
    def evaluate(self, value: Any, parameters: List[Any]) -> Any:
        if value is None or value == "":
            return parameters[0] if len(parameters) > 0 else ""
        return value


class IfEvaluator(Evaluator):
    def evaluate(self, value: Any, parameters: List[Any]) -> Any:
        is_truthy = bool(value) and str(value).lower() not in ("false", "0", "")
        if is_truthy:
            return parameters[0] if len(parameters) > 0 else ""
        return parameters[1] if len(parameters) > 1 else ""
