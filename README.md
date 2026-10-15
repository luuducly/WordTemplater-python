# WordTemplater-python

[![PyPI Version](https://img.shields.io/badge/pypi-v1.0.0-blue.svg?style=flat-square)](https://pypi.org)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg?style=flat-square)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

**WordTemplater-python** is a lightweight, zero-dependency Python library that turns Microsoft Word (`.docx`) documents into dynamic report templates.

Design templates visually in Microsoft Word using standard **MergeFields** or `«field»` tags, and populate them with Python dictionaries and objects in milliseconds.

---

## Key Features

- 🚀 **Zero Mandatory External Dependencies**: Built entirely using Python's standard library (`zipfile`, `xml.etree.ElementTree`).
- ⚡ **Lightweight & High Performance**: Ultra-fast execution with minimal memory footprint.
- 🧭 **Deep Dict/Object Navigation**: Dot notation (`Customer.Address.City`) and list indexing (`Items[0].Name`) case-insensitively.
- 🔁 **Nested Loops & Tables**: Full support for hierarchical loops (`«loop(items)»`...`«endloop»`) and table row cloning with alternating zebra-striping.
- 📊 **Built-in Loop Metadata**: Automatically provides `_index`, `_first`, `_last`, `_even`, and `_odd` in every loop and table row.
- 🛡️ **Dynamic Watermarking**: Inject customizable text watermarks directly into Word headers.
- 🧩 **Extensible**: Easily register custom evaluators and formatters.

---

## Multi-Language Ecosystem

WordTemplater is available across multiple programming languages with matching template syntax and feature parity:

| Language | Repository | Package / Install |
| :--- | :--- | :--- |
| **Python** *(This repository)* | [WordTemplater-python](https://github.com/luuducly/WordTemplater-python) | `pip install wordtemplater` |
| **C# (.NET)** | [WordTemplater](https://github.com/luuducly/WordTemplater) | `dotnet add package WordTemplater` |
| **TypeScript / JavaScript** | [WordTemplater-ts](https://github.com/luuducly/WordTemplater-ts) | `npm install wordtemplater-ts` |
| **Java** | [WordTemplater-java](https://github.com/luuducly/WordTemplater-java) | `com.github.luuducly:wordtemplater` |

---

## Installation

```bash
pip install wordtemplater
```

Or install from source:
```bash
git clone https://github.com/luuducly/WordTemplater-python.git
cd WordTemplater-python
pip install -e .
```

---

## Quick Start

```python
import json
from wordtemplater import WordTemplate

# 1. Prepare data
data = {
    "InvoiceNumber": "INV-2026-001",
    "Customer": {
        "Name": "Acme Corporation",
        "Address": {"City": "San Francisco", "Country": "USA"}
    },
    "Items": [
        {"Description": "Cloud Hosting", "Qty": 1, "Price": 1200.00},
        {"Description": "Domain Registration", "Qty": 2, "Price": 15.00}
    ]
}

# 2. Load template
template = WordTemplate.load("Templates/Invoice.docx")

# 3. Optional configurations
template.set_watermark("PAID", color="22C55E", angle=-45, font_size=80)
template.enable_table_zebra_striping(odd_color="F8FAFC", even_color="FFFFFF")

# 4. Export document
template.export(data, output_file="Output/Invoice.docx")
```

---

## Template Syntax & Evaluators Cheat Sheet

| Placeholder Syntax | Description | Example Input | Example Output |
| :--- | :--- | :--- | :--- |
| `«upper(Name)»` | Converts text to uppercase | `"acme corp"` | `ACME CORP` |
| `«lower(Code)»` | Converts text to lowercase | `"PROD-XYZ"` | `prod-xyz` |
| `«trim(Note)»` | Trims whitespace | `"  hello  "` | `hello` |
| `«sub(Text, 0, 4)»` | Substring `(start, length)` | `"WORDTEMPLATER"` | `WORD` |
| `«left(Code, 3)»` | First `N` characters | `"INV-9988"` | `INV` |
| `«right(Code, 4)»` | Last `N` characters | `"INV-9988"` | `9988` |
| `«replace(Text, '-', '/')»` | Replaces occurrences of string | `"2026-10-15"` | `2026/10/15` |
| `«padleft(Number, 6, '0')»` | Left-pads string to target width | `42` | `000042` |
| `«padright(Code, 8, '_')»` | Right-pads string to target width | `"A1"` | `A1______` |
| `«currency(Amount, 'en-US')»` | Formats as currency with culture | `1500000` | `$1,500,000.00` |
| `«currency(Amount, 'vi-VN')»` | Vietnamese currency format | `1500000` | `1.500.000 ₫` |
| `«number(Score)»` | Formats numbers with thousand separators | `1234567` | `1,234,567` |
| `«percentage(Ratio)»` | Formats number as percentage | `0.85` | `85.00%` |
| `«date(CreatedAt, 'dd/MM/yyyy')»` | Formats date with pattern | Date / ISO string | `15/10/2026` |
| `«default(Phone, 'N/A')»` | Fallback value if None or empty | `None` | `N/A` |
| `«if(IsVIP, 'Gold', 'Standard')»` | Conditional text based on boolean | `True` | `Gold` |

---

## Repeating Tables & Zebra Striping

Repeat rows in a Word table:

| No. | Description | Qty | Unit Price |
| :--- | :--- | :--- | :--- |
| `«table(Items)»«_index»` | `«Description»` | `«Qty»` | `«currency(Price)»«endtable»` |

### Alternating Row Shading
Inside Word Template:
```text
«table(Items, 'F8FAFC', 'FFFFFF')»
```
Or via Python API:
```python
template.enable_table_zebra_striping(odd_color="F8FAFC", even_color="FFFFFF")
```

---

## Custom Evaluators

```python
from wordtemplater import Evaluator, WordTemplate

class SlugifyEvaluator(Evaluator):
    def evaluate(self, value, parameters):
        if value is None:
            return ""
        return str(value).lower().strip().replace(" ", "-")

template = WordTemplate.load("Template.docx")
template.register_evaluator("slugify", SlugifyEvaluator())
```

In Word template:
```text
«slugify(ProductTitle)»
```

---

## Running Tests

```bash
python3 -m unittest discover tests
```

---

## License

MIT License. Copyright (c) 2026 Lưu Đức Ly.
