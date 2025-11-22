"""
Tests for JSON/YAML line number support.

Ensures that JSON and YAML analyzers return real line numbers
from the source file, not fake enumerated positions.
"""

import unittest
from reveal.analyzers.json_analyzer import JSONAnalyzer
from reveal.analyzers.yaml_analyzer import YAMLAnalyzer


class TestJSONLineNumbers(unittest.TestCase):
    """Test JSON analyzer line number extraction."""

    def test_json_returns_line_numbers(self):
        """JSON analyzer should return line numbers for top-level keys."""
        json_lines = [
            '{',
            '  "name": "test",',
            '  "version": "1.0.0",',
            '  "dependencies": {',
            '    "foo": "1.0"',
            '  }',
            '}'
        ]

        analyzer = JSONAnalyzer(json_lines)
        structure = analyzer.analyze_structure()

        # Should have top-level keys
        self.assertIn('top_level_keys', structure)
        keys = structure['top_level_keys']

        # Should have 3 keys
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
        self.assertEqual(key_dict['dependencies'], 4)

    def test_json_with_file_path(self):
        """JSON analyzer should use file_path when provided."""
        json_lines = [
            '{',
            '  "key1": "value1",',
            '  "key2": "value2"',
            '}'
        ]

        analyzer = JSONAnalyzer(json_lines, file_path='/tmp/test.json')
        structure = analyzer.analyze_structure()

        # Verify file_path is stored
        self.assertEqual(analyzer.file_path, '/tmp/test.json')

        # Line numbers should still be found
        keys = structure['top_level_keys']
        self.assertEqual(len(keys), 2)
        self.assertEqual(keys[0]['line'], 2)
        self.assertEqual(keys[1]['line'], 3)

    def test_json_empty_object(self):
        """JSON analyzer should handle empty objects."""
        json_lines = ['{}']

        analyzer = JSONAnalyzer(json_lines)
        structure = analyzer.analyze_structure()

        # Should return empty list, not crash
        self.assertEqual(structure['top_level_keys'], [])

    def test_json_array_top_level(self):
        """JSON analyzer should handle arrays at top level."""
        json_lines = ['[1, 2, 3]']

        analyzer = JSONAnalyzer(json_lines)
        structure = analyzer.analyze_structure()

        # Arrays have no keys
        self.assertEqual(structure['top_level_keys'], [])

    def test_json_parse_error(self):
        """JSON analyzer should handle parse errors gracefully."""
        json_lines = ['{invalid json}']

        analyzer = JSONAnalyzer(json_lines)
        structure = analyzer.analyze_structure()

        # Should have error key
        self.assertIn('error', structure)
        self.assertEqual(structure['top_level_keys'], [])


class TestYAMLLineNumbers(unittest.TestCase):
    """Test YAML analyzer line number extraction."""

    def test_yaml_returns_line_numbers(self):
        """YAML analyzer should return line numbers for top-level keys."""
        yaml_lines = [
            'name: test-project',
            'version: 1.0.0',
            'dependencies:',
            '  foo: 1.0',
            '  bar: 2.0',
            'scripts:',
            '  test: pytest'
        ]

        analyzer = YAMLAnalyzer(yaml_lines)
        structure = analyzer.analyze_structure()

        # Should have top-level keys
        self.assertIn('top_level_keys', structure)
        keys = structure['top_level_keys']

        # Should have 4 keys
        self.assertEqual(len(keys), 4)

        # Each key should be a dict with 'name' and 'line'
        for key in keys:
            self.assertIsInstance(key, dict)
            self.assertIn('name', key)
            self.assertIn('line', key)

        # Check specific line numbers
        key_dict = {k['name']: k['line'] for k in keys}

        self.assertEqual(key_dict['name'], 1)
        self.assertEqual(key_dict['version'], 2)
        self.assertEqual(key_dict['dependencies'], 3)
        self.assertEqual(key_dict['scripts'], 6)

    def test_yaml_with_file_path(self):
        """YAML analyzer should use file_path when provided."""
        yaml_lines = [
            'key1: value1',
            'key2: value2'
        ]

        analyzer = YAMLAnalyzer(yaml_lines, file_path='/tmp/test.yaml')
        structure = analyzer.analyze_structure()

        # Verify file_path is stored
        self.assertEqual(analyzer.file_path, '/tmp/test.yaml')

        # Line numbers should still be found
        keys = structure['top_level_keys']
        self.assertEqual(len(keys), 2)
        self.assertEqual(keys[0]['line'], 1)
        self.assertEqual(keys[1]['line'], 2)

    def test_yaml_with_comments(self):
        """YAML analyzer should find keys despite comments."""
        yaml_lines = [
            '# Configuration file',
            'name: test',
            '# Database settings',
            'database:',
            '  host: localhost'
        ]

        analyzer = YAMLAnalyzer(yaml_lines)
        structure = analyzer.analyze_structure()

        keys = structure['top_level_keys']
        key_dict = {k['name']: k['line'] for k in keys}

        # Should find correct lines despite comments
        self.assertEqual(key_dict['name'], 2)
        self.assertEqual(key_dict['database'], 4)

    def test_yaml_empty_document(self):
        """YAML analyzer should handle empty documents."""
        yaml_lines = ['']

        analyzer = YAMLAnalyzer(yaml_lines)
        structure = analyzer.analyze_structure()

        # Should return empty list, not crash
        self.assertEqual(structure['top_level_keys'], [])

    def test_yaml_list_top_level(self):
        """YAML analyzer should handle lists at top level."""
        yaml_lines = ['- item1', '- item2', '- item3']

        analyzer = YAMLAnalyzer(yaml_lines)
        structure = analyzer.analyze_structure()

        # Lists have no keys
        self.assertEqual(structure['top_level_keys'], [])


class TestLineNumberComposability(unittest.TestCase):
    """Test that line numbers make output composable with other tools."""

    def test_json_format_location_helper(self):
        """JSON analyzer should use format_location helper."""
        json_lines = ['{', '  "test": "value"', '}']

        analyzer = JSONAnalyzer(json_lines, file_path='config.json')

        # Test format_location helper
        loc = analyzer.format_location(2)
        self.assertEqual(loc, 'config.json:2')

        # Without file_path, should use L0000 format
        analyzer_no_path = JSONAnalyzer(json_lines)
        loc = analyzer_no_path.format_location(2)
        self.assertEqual(loc, 'L0002')

    def test_yaml_format_location_helper(self):
        """YAML analyzer should use format_location helper."""
        yaml_lines = ['test: value']

        analyzer = YAMLAnalyzer(yaml_lines, file_path='config.yaml')

        # Test format_location helper
        loc = analyzer.format_location(1)
        self.assertEqual(loc, 'config.yaml:1')

        # Without file_path, should use L0000 format
        analyzer_no_path = YAMLAnalyzer(yaml_lines)
        loc = analyzer_no_path.format_location(1)
        self.assertEqual(loc, 'L0001')


if __name__ == '__main__':
    unittest.main()
