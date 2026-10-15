import json
import os
import unittest
import zipfile
import io
from wordtemplater import WordTemplate

class TestTemplate(unittest.TestCase):
    def test_in_memory_template(self):
        doc_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>«upper(Customer.Name)»</w:t></w:r></w:p>
    <w:p><w:r><w:t>«currency(Total, 'vi-VN')»</w:t></w:r></w:p>
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:t>«table(Items, 'F0F0F0', 'FFFFFF')»«_index»</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>«Name»«endtable»</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>"""

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("word/document.xml", doc_xml.encode("utf-8"))

        template = WordTemplate.load(buf.getvalue())
        template.set_watermark("CONFIDENTIAL", "C0C0C0", -45, 60)

        data = {
            "Customer": {"Name": "google llc"},
            "Total": 1200000,
            "Items": [{"Name": "Cloud"}, {"Name": "Workspace"}]
        }

        out_bytes = template.export(data)
        out_zip = zipfile.ZipFile(io.BytesIO(out_bytes))
        res_xml = out_zip.read("word/document.xml").decode("utf-8")

        self.assertIn("GOOGLE LLC", res_xml)
        self.assertIn("1.200.000 ₫", res_xml)
        self.assertIn("Cloud", res_xml)
        self.assertIn("Workspace", res_xml)
        # Check watermark header
        self.assertIn("word/header1.xml", out_zip.namelist())

    def test_real_template_file(self):
        template_path = os.path.join("examples", "templates", "Template.docx")
        data_path = os.path.join("examples", "Data.json")
        if not os.path.exists(template_path) or not os.path.exists(data_path):
            return

        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        template = WordTemplate.load(template_path)
        out_bytes = template.export(data)
        self.assertGreater(len(out_bytes), 0)

        out_zip = zipfile.ZipFile(io.BytesIO(out_bytes))
        res_xml = out_zip.read("word/document.xml").decode("utf-8")
        self.assertTrue(
            "Quy trình tiếp nhận" in res_xml or "đăng ký" in res_xml,
            "Exported docx should contain content from Data.json"
        )

if __name__ == "__main__":
    unittest.main()
