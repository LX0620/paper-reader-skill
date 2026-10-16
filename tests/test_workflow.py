from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/paper-reader'
spec = importlib.util.spec_from_file_location('installer_workflow', ROOT / 'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class WorkflowTests(unittest.TestCase):
    """Static contract checks, NOT actual Codex/model invocation tests."""

    def test_trigger_keywords_are_frontloaded(self):
        text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        description = text.split('description:', 1)[1].split('\n---', 1)[0]
        self.assertIn('阅读', description[:60])
        self.assertIn('论文', description[:60])
        self.assertIn('阅读这篇论文', description)
        self.assertIn('不逐步等待确认', description)

    def test_exact_five_stages(self):
        state = json.loads((SKILL / 'assets/reading-state.template.json').read_text(encoding='utf-8'))
        self.assertEqual(list(state['stages']), [
            'research_map', 'innovation', 'limitations', 'research_ideas', 'five_question_recap'])
        self.assertEqual(state['mode'], 'full_reading')
        self.assertEqual(state['skill_version'], '0.2.0')
        self.assertTrue(all(v == 'pending' for v in state['stages'].values()))
        self.assertIn('source_coverage', state)

    def test_required_report_sections(self):
        report = (SKILL / 'assets/report-template.md').read_text(encoding='utf-8')
        titles = ['## 一、研究地图', '## 二、创新拆解', '## 三、局限分析',
                  '## 四、5个后续研究问题及评价', '## 五、五问回顾']
        self.assertEqual([report.index(t) for t in titles], sorted(report.index(t) for t in titles))
        self.assertEqual(report.count('### 想法'), 5)
        self.assertEqual(sum(f'### {i}. ' in report for i in range(1, 8)), 7)

    def test_idea_fields_and_ratings(self):
        text = (SKILL / 'references/research-ideas.md').read_text(encoding='utf-8')
        for field in ['研究问题', '核心假设', '为什么原文没有解决', '最小可行实验',
                      '需要的数据', '预期风险', '如果实验失败还能得到什么结论',
                      '创新性', '可行性', '工作量', '发表潜力']:
            self.assertIn(field, text)

    def test_removed_old_transfer_module(self):
        self.assertFalse((SKILL / 'references/transfer.md').exists())
        self.assertTrue((SKILL / 'references/research-ideas.md').is_file())
        report = (SKILL / 'assets/report-template.md').read_text(encoding='utf-8')
        for heading in ['## 写引言', '## 引言写作', '## 引言骨架', '## 下一步阅读']:
            self.assertNotIn(heading, report)

    def test_automatic_execution_and_honest_limits(self):
        text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        for term in ['不在五个步骤之间等待确认', '实际阅读范围', '材料不足/待核查',
                     '分析推测，待验证', '不擅改模型或数据', 'partial']:
            self.assertIn(term, text)


class UpgradeTests(unittest.TestCase):
    def test_upgrade_preserves_entire_backup_outside_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            dest = base / '.agents' / 'skills'
            installed = installer.install(dest)
            (installed / 'my-private-note.txt').write_text('keep me', encoding='utf-8')
            (installed / '.venv').mkdir()
            (installed / '.venv' / 'marker').write_text('keep env', encoding='utf-8')
            (installed / 'SKILL.md').write_text('old version', encoding='utf-8')
            installer.install(dest, update=True)
            backups = list((dest.parent / 'paper-reader-backups').glob('paper-reader-*'))
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / 'SKILL.md').read_text(encoding='utf-8'), 'old version')
            self.assertTrue((backups[0] / 'my-private-note.txt').exists())
            self.assertTrue((backups[0] / '.venv/marker').exists())
            self.assertFalse((installed / 'my-private-note.txt').exists())
            self.assertIn('paper-reader', (installed / 'SKILL.md').read_text(encoding='utf-8'))
            self.assertEqual(len(list(dest.glob('*/SKILL.md'))), 1)

    def test_update_is_valid_for_first_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue((installer.install(Path(tmp) / 'skills', update=True) / 'SKILL.md').exists())

    def test_unrelated_target_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'skills'
            target = dest / 'paper-reader'
            target.mkdir(parents=True)
            (target / 'keep.txt').write_text('keep', encoding='utf-8')
            with self.assertRaises(ValueError):
                installer.install(dest, update=True)
            self.assertTrue((target / 'keep.txt').is_file())

    def test_failed_stage_copy_leaves_old_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'skills'
            target = installer.install(dest)
            before = (target / 'SKILL.md').read_bytes()
            with mock.patch.object(installer.shutil, 'copytree', side_effect=OSError('synthetic disk failure')):
                with self.assertRaises(OSError):
                    installer.install(dest, update=True)
            self.assertEqual((target / 'SKILL.md').read_bytes(), before)
            self.assertFalse(list(dest.glob('.paper-reader-stage-*')))

    def test_install_alone_does_not_modify_codex_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            installer.install(home / 'skills')
            self.assertFalse((home / '.codex').exists())


class RouterTests(unittest.TestCase):
    def test_merge_retains_surrounding_text(self):
        block = installer.START + '\nNEW\n' + installer.END
        before = 'KEEP BEFORE\r\n' + installer.START + '\nOLD\n' + installer.END + '\r\nKEEP AFTER'
        result = installer.merge_router(before, block)
        self.assertEqual(result, 'KEEP BEFORE\r\n' + block + '\r\nKEEP AFTER')

    def test_merge_is_idempotent(self):
        block = installer.START + '\nRULE\n' + installer.END
        once = installer.merge_router('existing instructions', block)
        self.assertEqual(installer.merge_router(once, block), once)

    def test_merge_rejects_malformed_markers(self):
        block = installer.START + '\nRULE\n' + installer.END
        for original in [installer.START, installer.END,
                         installer.END + installer.START,
                         installer.START + installer.START + installer.END]:
            with self.assertRaises(ValueError):
                installer.merge_router(original, block)

    def test_configure_router_preserves_old_bytes_and_keeps_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            installed = installer.install(base / 'skills')
            home = base / 'codex'
            home.mkdir()
            original = b'\xef\xbb\xbf# Existing user rules\r\nKeep this.\r\n'
            (home / 'AGENTS.md').write_bytes(original)
            target = installer.configure_router(installed, home)
            actual = target.read_bytes()
            self.assertTrue(actual.startswith(original))
            self.assertIn('阅读'.encode(), actual)
            self.assertIn(str((installed / 'SKILL.md').as_posix()).encode(), actual)
            backups = list(home.glob('AGENTS.md.paper-reader-backup-*'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), original)
            installer.configure_router(installed, home)
            self.assertEqual(target.read_bytes(), actual)
            self.assertEqual(len(list(home.glob('AGENTS.md.paper-reader-backup-*'))), 1)

    def test_nonempty_override_is_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            installed = installer.install(base / 'skills')
            home = base / 'codex'
            home.mkdir()
            (home / 'AGENTS.md').write_text('base', encoding='utf-8')
            (home / 'AGENTS.override.md').write_text('override', encoding='utf-8')
            target = installer.configure_router(installed, home)
            self.assertEqual(target.name, 'AGENTS.override.md')
            self.assertEqual((home / 'AGENTS.md').read_text(encoding='utf-8'), 'base')
            self.assertTrue(target.read_text(encoding='utf-8').startswith('override'))

    def test_empty_override_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / 'AGENTS.override.md').write_text(' \n', encoding='utf-8')
            self.assertEqual(installer.active_agents_file(home).name, 'AGENTS.md')

    def test_invalid_router_keeps_instructions_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            installed = installer.install(base / 'skills')
            home = base / 'codex'
            home.mkdir()
            target = home / 'AGENTS.md'
            target.write_text(installer.START, encoding='utf-8')
            before = target.read_bytes()
            with self.assertRaises(ValueError):
                installer.configure_router(installed, home)
            self.assertEqual(target.read_bytes(), before)

    def test_oversize_router_keeps_instructions_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            installed = installer.install(base / 'skills')
            home = base / 'codex'
            home.mkdir()
            target = home / 'AGENTS.md'
            target.write_text('x' * (32 * 1024), encoding='utf-8')
            with self.assertRaises(ValueError):
                installer.configure_router(installed, home)
            self.assertEqual(target.stat().st_size, 32 * 1024)


if __name__ == '__main__':
    unittest.main()
