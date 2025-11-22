"""
Tests for TOML analyzer line number support.

Ensures that TOML analyzer returns real line numbers
from the source file using the find_definition() helper.
"""

import unittest
from reveal.analyzers.toml_analyzer import TOMLAnalyzer


class TestTOMLLineNumbers(unittest.TestCase):
    """Test TOML analyzer line number extraction."""

    def test_toml_returns_line_numbers_for_keys(self):
        """TOML analyzer should return line numbers for top-level keys."""
        toml_lines = [
            '# Configuration file',
            'name = "test-project"',
            'version = "1.0.0"',
            'debug = true',
            '',
            '[server]',
            'host = "localhost"',
            'port = 8080',
        ]

        analyzer = TOMLAnalyzer(toml_lines)
        structure = analyzer.analyze_structure()

        # Should have top-level keys
        self.assertIn('top_level_keys', structure)
        keys = structure['top_level_keys']

        # Should have 3 top-level keys (name, version, debug)
        self.assertEqual(len(keys), 3)

        # Each key should be a dict with 'name' and 'line'
        for key in keys:
            self.assertIsInstance(key, dict)
            self.assertIn('name', key)
            self.assertIn('line', key)

        # Check specific line numbers
        key_dict = {k['name']: k['line'] for k in keys}
        self.assertEqual(key_dict['name'], 2)
        self.assertEqual(key_dict['version'], 3)
        self.assertEqual(key_dict['debug'], 4)

    def test_toml_returns_line_numbers_for_sections(self):
        """TOML analyzer should return line numbers for sections."""
        toml_lines = [
            'name = "test"',
            '',
            '[server]',
            'host = "localhost"',
            '',
            '[database]',
            'driver = "postgresql"',
            '',
            '[logging]',
            'level = "info"',
        ]

        analyzer = TOMLAnalyzer(toml_lines)
        structure = analyzer.analyze_structure()

        # Should have sections
        self.assertIn('sections', structure)
        sections = structure['sections']

        # Should have 3 sections
        self.assertEqual(len(sections), 3)

        # Each section should be a dict with 'name' and 'line'
        for section in sections:
            self.assertIsInstance(section, dict)
            self.assertIn('name', section)
            self.assertIn('line', section)

        # Check specific line numbers
        section_dict = {s['name']: s['line'] for s in sections}
        self.assertEqual(section_dict['server'], 3)
        self.assertEqual(section_dict['database'], 6)
        self.assertEqual(section_dict['logging'], 9)

    def test_toml_with_file_path(self):
        """TOML analyzer should use file_path when provided."""
        toml_lines = [
            'key1 = "value1"',
            'key2 = "value2"'
        ]

        analyzer = TOMLAnalyzer(toml_lines, file_path='/tmp/test.toml')
        structure = analyzer.analyze_structure()

        # Verify file_path is stored
        self.assertEqual(analyzer.file_path, '/tmp/test.toml')

        # Line numbers should still be found
        keys = structure['top_level_keys']
        self.assertEqual(len(keys), 2)
        self.assertEqual(keys[0]['line'], 1)
        self.assertEqual(keys[1]['line'], 2)

    def test_toml_pyproject_example(self):
        """TOML analyzer should handle real pyproject.toml structure."""
        toml_lines = [
            '[build-system]',
            'requires = ["setuptools>=61.0"]',
            '',
            '[project]',
            'name = "reveal"',
            'version = "0.1.0"',
            'description = "Progressive file revelation tool"',
            '',
            '[project.scripts]',
            'reveal = "reveal.cli:main"',
            '',
            '[tool.pytest]',
            'testpaths = ["tests"]',
        ]

        analyzer = TOMLAnalyzer(toml_lines)
        structure = analyzer.analyze_structure()

        sections = structure['sections']
        section_dict = {s['name']: s['line'] for s in sections}

        # Check section line numbers
        self.assertEqual(section_dict['build-system'], 1)
        self.assertEqual(section_dict['project'], 4)
        self.assertEqual(section_dict['tool'], 12)

    def test_toml_nested_sections(self):
        """TOML analyzer should count subsections."""
        toml_lines = [
            '[project]',
            'name = "test"',
            '',
            '[project.dependencies]',
            'pytest = "^7.0"',
            '',
            '[project.scripts]',
            'test = "pytest"',
            '',
            '[tool]',
            'version = "1.0"',
        ]

        analyzer = TOMLAnalyzer(toml_lines)
        structure = analyzer.analyze_structure()

        sections = structure['sections']

        # Find project section
        project_section = next(s for s in sections if s['name'] == 'project')

        # Should have subsections count
        self.assertIn('subsections', project_section)
        # project.dependencies and project.scripts are subsections
        self.assertGreater(project_section['subsections'], 0)

    def test_toml_empty_file(self):
        """TOML analyzer should handle empty files."""
        toml_lines = ['']

        analyzer = TOMLAnalyzer(toml_lines)
        structure = analyzer.analyze_structure()

        # Should return empty lists, not crash
        self.assertEqual(structure['top_level_keys'], [])
        self.assertEqual(structure['sections'], [])

    def test_toml_with_comments(self):
        """TOML analyzer should find keys despite comments."""
        toml_lines = [
            '# Application settings',
            'name = "myapp"',
            '',
            '# Server configuration',
            '[server]',
            'port = 8080',
        ]

        analyzer = TOMLAnalyzer(toml_lines)
        structure = analyzer.analyze_structure()

        keys = structure['top_level_keys']
        sections = structure['sections']

        # Should find keys on correct lines (not comment lines)
        key_dict = {k['name']: k['line'] for k in keys}
        self.assertEqual(key_dict['name'], 2)

        section_dict = {s['name']: s['line'] for s in sections}
        self.assertEqual(section_dict['server'], 5)


class TestTOMLComposability(unittest.TestCase):
    """Test that TOML line numbers make output composable."""

    def test_toml_format_location_helper(self):
        """TOML analyzer should use format_location helper."""
        toml_lines = ['name = "test"']

        analyzer = TOMLAnalyzer(toml_lines, file_path='config.toml')

        # Test format_location helper
        loc = analyzer.format_location(1)
        self.assertEqual(loc, 'config.toml:1')

        # Without file_path, should use L0000 format
        analyzer_no_path = TOMLAnalyzer(toml_lines)
        loc = analyzer_no_path.format_location(1)
        self.assertEqual(loc, 'L0001')


if __name__ == '__main__':
    unittest.main()
