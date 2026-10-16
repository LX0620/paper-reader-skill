from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'paper-reader'
spec = importlib.util.spec_from_file_location('skill_install', ROOT / 'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class SkillTests(unittest.TestCase):
    def test_frontmatter(self):
        text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        match = re.match(r'^---\n(.*?)\n---\n', text, flags=re.S)
        self.assertIsNotNone(match)
        header = yaml.safe_load(match.group(1))
        self.assertEqual(header['name'], SKILL.name)
        self.assertTrue(0 < len(header['description']) <= 1024)
        self.assertRegex(header['name'], r'^[a-z0-9-]{1,64}$')
        self.assertLess(len(text.splitlines()), 500)

    def test_invocation_policy(self):
        data = yaml.safe_load((SKILL / 'agents/openai.yaml').read_text(encoding='utf-8'))
        self.assertIs(data['policy']['allow_implicit_invocation'], True)
        self.assertIn('$paper-reader', data['interface']['default_prompt'])
        self.assertTrue(25 <= len(data['interface']['short_description']) <= 64)

    def test_referenced_resources_exist(self):
        text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        paths = re.findall(r'`((?:references|assets|scripts)/[^`]+)`', text)
        self.assertGreater(len(paths), 5)
        for path in paths:
            self.assertTrue((SKILL / path).is_file(), path)

    def test_json_templates(self):
        for path in (SKILL / 'assets').glob('*.json'):
            content = json.loads(path.read_text(encoding='utf-8'))
            self.assertIn(content['schema_version'], ('1.0', '1.1'))

    def test_install_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'test skills with spaces'
            installed = installer.install(dest)
            self.assertTrue((installed / 'SKILL.md').is_file())
            self.assertFalse((installed / 'README.md').exists())
            with self.assertRaises(FileExistsError):
                installer.install(dest)

    def test_reject_destination_inside_source(self):
        with self.assertRaises(ValueError):
            installer.install(SKILL / 'nested-install')

    def test_privacy_ignore_rules(self):
        text = (ROOT / '.gitignore').read_text(encoding='utf-8')
        for rule in ('reading-notes/', 'papers/', '*.pdf', '.env', 'research-context.local.md'):
            self.assertIn(rule, text)

    def test_no_private_papers_in_skill(self):
        self.assertFalse(list(SKILL.rglob('*.pdf')))
        self.assertFalse(list(SKILL.rglob('.env')))


if __name__ == '__main__':
    unittest.main()
