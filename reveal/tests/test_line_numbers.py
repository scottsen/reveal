"""Tests for line number functionality."""

import unittest
from pathlib import Path
from reveal.cli import parse_file_location
from reveal.analyzers import SQLAnalyzer, PythonAnalyzer, JSONAnalyzer, YAMLAnalyzer


class TestFileLocationParsing(unittest.TestCase):
    """Test file:line parsing."""

    def test_plain_file(self):
        """Test plain filename without line number."""
        path, start, end = parse_file_location("test.sql")
        self.assertEqual(path, "test.sql")
        self.assertIsNone(start)
        self.assertIsNone(end)

    def test_file_with_single_line(self):
        """Test file:32 syntax."""
        path, start, end = parse_file_location("test.sql:32")
        self.assertEqual(path, "test.sql")
        self.assertEqual(start, 32)
        self.assertEqual(end, 32)

    def test_file_with_range(self):
        """Test file:10-50 syntax."""
        path, start, end = parse_file_location("test.sql:10-50")
        self.assertEqual(path, "test.sql")
        self.assertEqual(start, 10)
        self.assertEqual(end, 50)

    def test_file_with_open_range(self):
        """Test file:10- syntax (from line 10 to end)."""
        path, start, end = parse_file_location("test.sql:10-")
        self.assertEqual(path, "test.sql")
        self.assertEqual(start, 10)
        self.assertIsNone(end)


class TestAnalyzerParameters(unittest.TestCase):
    """Test that all analyzers accept the new parameters."""

    def test_sql_analyzer_accepts_kwargs(self):
        """SQL analyzer should accept file_path and focus parameters."""
        lines = ["CREATE TABLE test (id INT);"]
        analyzer = SQLAnalyzer(
            lines,
            file_path="test.sql",
            focus_start=1,
            focus_end=10
        )
        self.assertEqual(analyzer.file_path, "test.sql")
        self.assertEqual(analyzer.focus_start, 1)
        self.assertEqual(analyzer.focus_end, 10)

    def test_python_analyzer_accepts_kwargs(self):
        """Python analyzer should accept file_path and focus parameters."""
        lines = ["def test(): pass"]
        analyzer = PythonAnalyzer(
            lines,
            file_path="test.py",
            focus_start=1,
            focus_end=10
        )
        self.assertEqual(analyzer.file_path, "test.py")

    def test_json_analyzer_accepts_kwargs(self):
        """JSON analyzer should accept file_path and focus parameters."""
        lines = ['{"key": "value"}']
        analyzer = JSONAnalyzer(
            lines,
            file_path="test.json",
            focus_start=1
        )
        self.assertEqual(analyzer.file_path, "test.json")

    def test_yaml_analyzer_accepts_kwargs(self):
        """YAML analyzer should accept file_path and focus parameters."""
        lines = ["key: value"]
        analyzer = YAMLAnalyzer(
            lines,
            file_path="test.yaml"
        )
        self.assertEqual(analyzer.file_path, "test.yaml")


class TestPythonAnalyzerLineNumbers(unittest.TestCase):
    """Test Python analyzer returns line numbers."""

    def test_function_has_line_number(self):
        """Functions should include line numbers."""
        lines = [
            "# comment",
            "def test_func():",
            "    pass",
        ]
        analyzer = PythonAnalyzer(lines)
        structure = analyzer.analyze_structure()

        self.assertEqual(len(structure['functions']), 1)
        func = structure['functions'][0]
        self.assertIsInstance(func, dict)
        self.assertEqual(func['name'], 'test_func')
        self.assertEqual(func['line'], 2)

    def test_class_has_line_number(self):
        """Classes should include line numbers."""
        lines = [
            "# comment",
            "",
            "class TestClass:",
            "    pass",
        ]
        analyzer = PythonAnalyzer(lines)
        structure = analyzer.analyze_structure()

        self.assertEqual(len(structure['classes']), 1)
        cls = structure['classes'][0]
        self.assertIsInstance(cls, dict)
        self.assertEqual(cls['name'], 'TestClass')
        self.assertEqual(cls['line'], 3)


class TestFormatLocation(unittest.TestCase):
    """Test BaseAnalyzer format_location helper."""

    def test_format_location_with_file_path(self):
        """Should return filename:line when file_path is set."""
        lines = ["CREATE TABLE test (id INT);"]
        analyzer = SQLAnalyzer(lines, file_path="/path/to/test.sql")
        loc = analyzer.format_location(32)
        self.assertEqual(loc, "/path/to/test.sql:32")

    def test_format_location_without_file_path(self):
        """Should return L0000 format when no file_path."""
        lines = ["CREATE TABLE test (id INT);"]
        analyzer = SQLAnalyzer(lines)
        loc = analyzer.format_location(32)
        self.assertEqual(loc, "L0032")

    def test_format_location_none(self):
        """Should return empty string for None."""
        lines = ["CREATE TABLE test (id INT);"]
        analyzer = SQLAnalyzer(lines)
        loc = analyzer.format_location(None)
        self.assertEqual(loc, "")


if __name__ == '__main__':
    unittest.main()
