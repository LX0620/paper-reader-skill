from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare_pdf', ROOT / 'skills/paper-reader/scripts/prepare_pdf.py')
prep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)


def fixture(path: Path):
    c = canvas.Canvas(str(path), pagesize=(300, 400))
    c.setTitle('Synthetic test fixture, not a research paper')
    c.drawString(15, 370, 'PAGE ONE: synthetic test text.')
    c.drawString(15, 350, 'This is a generated fixture for extraction.')
    c.showPage()
    c.rect(20, 20, 100, 80, fill=0)
    c.showPage()
    c.drawString(15, 370, 'PAGE THREE: distinct content for indexing.')
    c.save()


class PdfTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.source = self.base / '测试 paper with spaces.pdf'
        fixture(self.source)
        self.original_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def tearDown(self):
        self.temp.cleanup()

    def test_page_selection(self):
        self.assertEqual(prep.parse_pages('3,1-2,2', 3), [1, 2, 3])
        self.assertEqual(prep.parse_pages(None, 3), [1, 2, 3])
        for spec in ('0', '4', '3-2', '', '1,', '1;2', '-1'):
            with self.assertRaises(ValueError, msg=spec):
                prep.parse_pages(spec, 3)

    def test_extract_pages_hash_and_low_text(self):
        out = self.base / 'extract'
        manifest = prep.extract_pdf(self.source, out)
        self.assertEqual(manifest['total_pdf_pages'], 3)
        self.assertIn(2, manifest['low_text_pdf_pages'])
        self.assertFalse(manifest['semantic_reading_performed'])
        data = json.loads((out / 'pages.json').read_text(encoding='utf-8'))
        self.assertIn('PAGE ONE', data['pages'][0]['text'])
        self.assertIn('PAGE THREE', data['pages'][2]['text'])
        self.assertEqual(manifest['sha256'], self.original_hash)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.original_hash)
        self.assertFalse((out / 'INCOMPLETE.txt').exists())

    def test_extract_selected_pages(self):
        out = self.base / 'selected'
        manifest = prep.extract_pdf(self.source, out, '3')
        self.assertEqual(manifest['extracted_pdf_pages'], [3])
        pages = json.loads((out / 'pages.json').read_text(encoding='utf-8'))['pages']
        self.assertEqual(pages[0]['pdf_page'], 3)
        self.assertEqual(len(pages), 1)

    def test_refuse_existing_output(self):
        out = self.base / 'existing'
        out.mkdir()
        sentinel = out / 'keep.txt'
        sentinel.write_text('keep', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            prep.extract_pdf(self.source, out)
        self.assertEqual(sentinel.read_text(encoding='utf-8'), 'keep')

    def test_invalid_input(self):
        fake = self.base / 'not-a-pdf.pdf'
        fake.write_text('not a PDF', encoding='utf-8')
        with self.assertRaises(ValueError):
            prep.extract_pdf(fake, self.base / 'invalid')

    def test_encrypted_input(self):
        encrypted = self.base / 'encrypted.pdf'
        writer = PdfWriter()
        writer.append(PdfReader(self.source))
        writer.encrypt('test-password')
        with encrypted.open('wb') as file:
            writer.write(file)
        with self.assertRaises(ValueError):
            prep.extract_pdf(encrypted, self.base / 'encrypted-out')

    def test_render_selected_pages(self):
        out = self.base / 'images'
        result = prep.render_pdf(self.source, out, '1,3', 100)
        self.assertEqual(result['rendered_pdf_pages'], [1, 3])
        self.assertTrue((out / 'pdf-page-0001.png').is_file())
        self.assertTrue((out / 'pdf-page-0003.png').is_file())
        self.assertFalse((out / 'pdf-page-0002.png').exists())
        self.assertFalse(result['images'][0]['visual_checked'])

    def test_invalid_dpi(self):
        with self.assertRaises(ValueError):
            prep.render_pdf(self.source, self.base / 'bad-dpi', '1', 600)


if __name__ == '__main__':
    unittest.main()
