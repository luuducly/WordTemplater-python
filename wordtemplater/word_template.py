import io
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union

from .evaluators import (
    CurrencyEvaluator,
    DateEvaluator,
    DefaultValueEvaluator,
    Evaluator,
    IfEvaluator,
    LeftEvaluator,
    LowerEvaluator,
    NumberEvaluator,
    PadLeftEvaluator,
    PadRightEvaluator,
    PercentageEvaluator,
    ReplaceEvaluator,
    RightEvaluator,
    SubEvaluator,
    TrimEvaluator,
    UpperEvaluator,
)
from .utils import parse_expression, resolve_token

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
V_NS = "urn:schemas-microsoft-com:vml"
ET.register_namespace("w", W_NS)
ET.register_namespace("v", V_NS)


class WordTemplate:
    def __init__(self, docx_bytes: bytes):
        self._docx_bytes = docx_bytes
        self._evaluators: Dict[str, Evaluator] = {}
        self._watermark_text: Optional[str] = None
        self._watermark_color: str = "C0C0C0"
        self._watermark_angle: int = -45
        self._watermark_size: int = 72
        self._table_odd_color: Optional[str] = None
        self._table_even_color: Optional[str] = None
        self._register_default_evaluators()

    @classmethod
    def load(cls, file_or_path: Union[str, bytes, io.BytesIO]) -> "WordTemplate":
        if isinstance(file_or_path, str):
            with open(file_or_path, "rb") as f:
                return cls(f.read())
        elif isinstance(file_or_path, bytes):
            return cls(file_or_path)
        elif isinstance(file_or_path, io.BytesIO):
            return cls(file_or_path.getvalue())
        elif hasattr(file_or_path, "read"):
            return cls(file_or_path.read())
        raise TypeError("Expected file path (str), bytes, or file-like object")

    def register_evaluator(self, name: str, evaluator: Evaluator) -> None:
        self._evaluators[name.lower()] = evaluator

    def set_watermark(
        self,
        text: str,
        color: str = "C0C0C0",
        angle: int = -45,
        font_size: int = 72
    ) -> None:
        self._watermark_text = text
        self._watermark_color = color.lstrip("#")
        self._watermark_angle = angle
        self._watermark_size = font_size

    def enable_table_zebra_striping(
        self,
        odd_color: str = "F9FAFB",
        even_color: str = "FFFFFF"
    ) -> None:
        self._table_odd_color = odd_color.lstrip("#")
        self._table_even_color = even_color.lstrip("#")

    def export(
        self,
        data: Any,
        output_file: Optional[str] = None
    ) -> bytes:
        input_zip = zipfile.ZipFile(io.BytesIO(self._docx_bytes))
        output_buffer = io.BytesIO()
        output_zip = zipfile.ZipFile(output_buffer, "w", zipfile.ZIP_DEFLATED)

        doc_xml_bytes = input_zip.read("word/document.xml")
        root = ET.fromstring(doc_xml_bytes)

        # 1. Process Tables
        self._process_tables(root, data)

        # 2. Process Loops
        body = root.find(f"{{{W_NS}}}body")
        if body is not None:
            self._process_element_loops(body, data)

        # 3. Process Fields
        self._process_fields(root, data)

        modified_doc_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        # Copy archive contents and replace document.xml
        for item in input_zip.infolist():
            if item.filename == "word/document.xml":
                output_zip.writestr(item, modified_doc_xml)
            else:
                output_zip.writestr(item, input_zip.read(item.filename))

        # 4. Inject Watermark if configured
        if self._watermark_text:
            self._inject_watermark(output_zip)

        input_zip.close()
        output_zip.close()

        result_bytes = output_buffer.getvalue()
        if output_file:
            with open(output_file, "wb") as f:
                f.write(result_bytes)

        return result_bytes

    def _register_default_evaluators(self) -> None:
        self.register_evaluator("upper", UpperEvaluator())
        self.register_evaluator("lower", LowerEvaluator())
        self.register_evaluator("trim", TrimEvaluator())
        self.register_evaluator("sub", SubEvaluator())
        self.register_evaluator("left", LeftEvaluator())
        self.register_evaluator("right", RightEvaluator())
        self.register_evaluator("replace", ReplaceEvaluator())
        self.register_evaluator("padleft", PadLeftEvaluator())
        self.register_evaluator("padright", PadRightEvaluator())
        self.register_evaluator("currency", CurrencyEvaluator())
        self.register_evaluator("number", NumberEvaluator())
        self.register_evaluator("percentage", PercentageEvaluator())
        self.register_evaluator("date", DateEvaluator())
        self.register_evaluator("default", DefaultValueEvaluator())
        self.register_evaluator("coalesce", DefaultValueEvaluator())
        self.register_evaluator("if", IfEvaluator())

    def _evaluate_expression(self, expr: str, context: Any) -> Any:
        func_name, field_path, args = parse_expression(expr)
        raw_val = resolve_token(context, field_path) if field_path else None
        if not func_name:
            return raw_val

        evaluator = self._evaluators.get(func_name)
        if not evaluator:
            return raw_val

        return evaluator.evaluate(raw_val, args)

    def _process_fields(self, root: ET.Element, data: Any) -> None:
        # Clean <w:instrText> and <w:fldChar>
        for parent in root.iter():
            for child in list(parent):
                if child.tag in (f"{{{W_NS}}}instrText", f"{{{W_NS}}}fldChar"):
                    parent.remove(child)

        placeholder_regex = re.compile(r"«([^»]+)»")

        # Process all paragraphs
        for p in root.iter(f"{{{W_NS}}}p"):
            t_nodes = list(p.iter(f"{{{W_NS}}}t"))
            if not t_nodes:
                continue

            combined = "".join(t.text or "" for t in t_nodes)
            if placeholder_regex.search(combined):
                evaluated = placeholder_regex.sub(
                    lambda m: str(self._evaluate_expression(m.group(1), data) or ""),
                    combined
                )
                t_nodes[0].text = evaluated
                for t in t_nodes[1:]:
                    t.text = ""

    def _process_tables(self, root: ET.Element, data: Any) -> None:
        placeholder_regex = re.compile(r"«([^»]+)»")
        table_regex = re.compile(r"«table\(([^)]+)\)»", re.IGNORECASE)

        for tbl in root.iter(f"{{{W_NS}}}tbl"):
            rows = list(tbl.findall(f"{{{W_NS}}}tr"))
            for row in rows:
                row_text = "".join(row.itertext())
                table_match = table_regex.search(row_text)

                if table_match:
                    func_name, array_path, args = parse_expression(table_match.group(0))
                    items = resolve_token(data, array_path)

                    odd_color = args[0] if len(args) > 0 else self._table_odd_color
                    even_color = args[1] if len(args) > 1 else self._table_even_color

                    row_idx = list(tbl).index(row)
                    tbl.remove(row)

                    if isinstance(items, (list, tuple)) and len(items) > 0:
                        for idx, item in enumerate(items):
                            cloned_row = ET.fromstring(ET.tostring(row))
                            item_context = dict(item) if isinstance(item, dict) else {"item": item}
                            item_context.update({
                                "_index": idx + 1,
                                "_first": idx == 0,
                                "_last": idx == len(items) - 1,
                                "_even": (idx + 1) % 2 == 0,
                                "_odd": (idx + 1) % 2 != 0,
                            })

                            # Replace placeholders in row paragraphs
                            for p in cloned_row.iter(f"{{{W_NS}}}p"):
                                t_nodes = list(p.iter(f"{{{W_NS}}}t"))
                                if not t_nodes:
                                    continue
                                combined = "".join(t.text or "" for t in t_nodes)
                                combined = re.sub(r"«table\([^)]+\)»", "", combined, flags=re.I)
                                combined = re.sub(r"«endtable»", "", combined, flags=re.I)

                                if placeholder_regex.search(combined):
                                    evaluated = placeholder_regex.sub(
                                        lambda m: str(self._evaluate_expression(m.group(1), item_context) or ""),
                                        combined
                                    )
                                    t_nodes[0].text = evaluated
                                    for t in t_nodes[1:]:
                                        t.text = ""

                            # Apply Zebra Shading
                            if odd_color and (idx + 1) % 2 != 0:
                                self._set_row_shading(cloned_row, str(odd_color))
                            elif even_color and (idx + 1) % 2 == 0:
                                self._set_row_shading(cloned_row, str(even_color))

                            tbl.insert(row_idx + idx, cloned_row)

    def _process_element_loops(self, container: ET.Element, data: Any) -> None:
        loop_regex = re.compile(r"«loop\(([^)]+)\)»", re.I)
        endloop_regex = re.compile(r"«endloop»", re.I)
        placeholder_regex = re.compile(r"«([^»]+)»")

        children = list(container)
        i = 0
        while i < len(children):
            child = children[i]
            text = "".join(child.itertext())
            loop_match = loop_regex.search(text)

            if loop_match:
                loop_path = loop_match.group(1).strip()
                loop_elements = []
                depth = 1
                j = i + 1

                while j < len(children):
                    next_child = children[j]
                    next_text = "".join(next_child.itertext())
                    if loop_regex.search(next_text):
                        depth += 1
                    if endloop_regex.search(next_text):
                        depth -= 1
                        if depth == 0:
                            break
                    loop_elements.append(next_child)
                    j += 1

                items = resolve_token(data, loop_path)
                endloop_child = children[j] if j < len(children) else None

                insert_idx = i
                if isinstance(items, (list, tuple)) and len(items) > 0:
                    for idx, item in enumerate(items):
                        item_context = dict(item) if isinstance(item, dict) else {"item": item}
                        item_context.update({
                            "_index": idx + 1,
                            "_first": idx == 0,
                            "_last": idx == len(items) - 1,
                            "_even": (idx + 1) % 2 == 0,
                            "_odd": (idx + 1) % 2 != 0,
                        })

                        for el in loop_elements:
                            cloned_el = ET.fromstring(ET.tostring(el))
                            # Recursively process nested loops
                            self._process_element_loops(cloned_el, item_context)

                            # Replace placeholders
                            p_list = [cloned_el] if cloned_el.tag == f"{{{W_NS}}}p" else list(cloned_el.iter(f"{{{W_NS}}}p"))
                            for p in p_list:
                                t_nodes = list(p.iter(f"{{{W_NS}}}t"))
                                if not t_nodes:
                                    continue
                                combined = "".join(t.text or "" for t in t_nodes)
                                if placeholder_regex.search(combined):
                                    evaluated = placeholder_regex.sub(
                                        lambda m: str(self._evaluate_expression(m.group(1), item_context) or ""),
                                        combined
                                    )
                                    t_nodes[0].text = evaluated
                                    for t in t_nodes[1:]:
                                        t.text = ""

                            container.insert(insert_idx, cloned_el)
                            insert_idx += 1

                # Clean up loop elements and endloop
                container.remove(child)
                for el in loop_elements:
                    if el in list(container):
                        container.remove(el)
                if endloop_child and endloop_child in list(container):
                    container.remove(endloop_child)

                return self._process_element_loops(container, data)

            i += 1

    def _set_row_shading(self, row: ET.Element, color_hex: str) -> None:
        clean_color = color_hex.lstrip("#")
        for tc in row.iter(f"{{{W_NS}}}tc"):
            tcPr = tc.find(f"{{{W_NS}}}tcPr")
            if tcPr is None:
                tcPr = ET.Element(f"{{{W_NS}}}tcPr")
                tc.insert(0, tcPr)

            shd = tcPr.find(f"{{{W_NS}}}shd")
            if shd is None:
                shd = ET.SubElement(tcPr, f"{{{W_NS}}}shd")

            shd.set(f"{{{W_NS}}}val", "clear")
            shd.set(f"{{{W_NS}}}color", "auto")
            shd.set(f"{{{W_NS}}}fill", clean_color)

    def _inject_watermark(self, zf: zipfile.ZipFile) -> None:
        header_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="{W_NS}" xmlns:v="{V_NS}">
  <w:p>
    <w:pPr><w:pStyle w:val="Header"/></w:pPr>
    <w:r>
      <w:pict>
        <v:shape id="WordTemplaterWatermark" type="#_x0000_t136"
          style="position:absolute;left:0;text-align:left;margin-left:0;margin-top:0;width:412.5pt;height:247.5pt;rotation:{self._watermark_angle};z-index:-251654144;mso-position-horizontal:center;mso-position-horizontal-relative:margin;mso-position-vertical:center;mso-position-vertical-relative:margin"
          fillcolor="#{self._watermark_color}" stroked="f">
          <v:fill opacity="0.3"/>
          <v:textpath style="font-family:'Calibri';font-size:{self._watermark_size}pt" string="{self._watermark_text}"/>
        </v:shape>
      </v:pict>
    </w:r>
  </w:p>
</w:hdr>"""
        zf.writestr("word/header1.xml", header_xml.encode("utf-8"))
