import unittest
from wordtemplater.evaluators import (
    UpperEvaluator,
    LowerEvaluator,
    TrimEvaluator,
    SubEvaluator,
    LeftEvaluator,
    RightEvaluator,
    ReplaceEvaluator,
    PadLeftEvaluator,
    PadRightEvaluator,
    CurrencyEvaluator,
    NumberEvaluator,
    PercentageEvaluator,
    DateEvaluator,
    DefaultValueEvaluator,
    IfEvaluator,
)
from wordtemplater.utils import resolve_token, parse_expression

class TestEvaluators(unittest.TestCase):
    def test_strings(self):
        upper = UpperEvaluator()
        self.assertEqual(upper.evaluate("hello", []), "HELLO")

        lower = LowerEvaluator()
        self.assertEqual(lower.evaluate("HELLO", []), "hello")

        trim = TrimEvaluator()
        self.assertEqual(trim.evaluate("  hi  ", []), "hi")

        sub = SubEvaluator()
        self.assertEqual(sub.evaluate("WORDTEMPLATER", [0, 4]), "WORD")

        left = LeftEvaluator()
        self.assertEqual(left.evaluate("INV-1234", [3]), "INV")

        right = RightEvaluator()
        self.assertEqual(right.evaluate("INV-1234", [4]), "1234")

        replace = ReplaceEvaluator()
        self.assertEqual(replace.evaluate("2026-10-15", ["-", "/"]), "2026/10/15")

        pad_left = PadLeftEvaluator()
        self.assertEqual(pad_left.evaluate(42, [5, "0"]), "00042")

        pad_right = PadRightEvaluator()
        self.assertEqual(pad_right.evaluate("A1", [6, "_"]), "A1____")

    def test_numbers_and_currency(self):
        currency = CurrencyEvaluator()
        self.assertEqual(currency.evaluate(1500, ["en-US"]), "$1,500.00")
        self.assertEqual(currency.evaluate(1500000, ["vi-VN"]), "1.500.000 ₫")

        number = NumberEvaluator()
        self.assertEqual(number.evaluate(1234567, []), "1,234,567")

        pct = PercentageEvaluator()
        self.assertEqual(pct.evaluate(0.85, []), "85.00%")

    def test_date_and_logic(self):
        date_eval = DateEvaluator()
        self.assertEqual(date_eval.evaluate("2026-10-15T00:00:00", ["dd/MM/yyyy"]), "15/10/2026")

        def_eval = DefaultValueEvaluator()
        self.assertEqual(def_eval.evaluate(None, ["N/A"]), "N/A")
        self.assertEqual(def_eval.evaluate("", ["N/A"]), "N/A")
        self.assertEqual(def_eval.evaluate("Valid", ["N/A"]), "Valid")

        if_eval = IfEvaluator()
        self.assertEqual(if_eval.evaluate(True, ["Yes", "No"]), "Yes")
        self.assertEqual(if_eval.evaluate(False, ["Yes", "No"]), "No")

    def test_resolve_token_and_expression(self):
        data = {
            "customer": {
                "name": "Acme Corp",
                "address": {"city": "Mountain View"}
            },
            "items": [{"name": "Item 1"}]
        }
        self.assertEqual(resolve_token(data, "customer.name"), "Acme Corp")
        self.assertEqual(resolve_token(data, "Customer.Address.City"), "Mountain View")
        self.assertEqual(resolve_token(data, "items[0].name"), "Item 1")

        func, path, args = parse_expression("currency(Total, 'vi-VN')")
        self.assertEqual(func, "currency")
        self.assertEqual(path, "Total")
        self.assertEqual(args, ["vi-VN"])

if __name__ == "__main__":
    unittest.main()
