#!/usr/bin/env python3
"""
Unused Code Remover Script
Analyzes JavaScript and CSS files to identify and remove unused code.
Saves changes to a log file for review.
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Set, List, Dict, Tuple

class UnusedCodeRemover:
    def __init__(self, root_directory: str, log_file: str = "unused_code_changes.txt"):
        self.root_dir = Path(root_directory)
        self.log_file = log_file
        self.changes_log = []
        self.js_files = []
        self.css_files = []
        self.html_files = []

        # Patterns for finding references
        self.css_class_pattern = re.compile(r'\.([a-zA-Z_-][a-zA-Z0-9_-]*)')
        self.css_id_pattern = re.compile(r'#([a-zA-Z_-][a-zA-Z0-9_-]*)')
        self.js_function_pattern = re.compile(r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)')
        self.js_var_pattern = re.compile(r'(?:var|let|const)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)')

    def scan_files(self):
        """Scan directory for JS, CSS, and HTML files."""
        print(f"Scanning directory: {self.root_dir}")

        for file_path in self.root_dir.rglob('*'):
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                if suffix == '.js':
                    self.js_files.append(file_path)
                elif suffix == '.css':
                    self.css_files.append(file_path)
                elif suffix in ['.html', '.htm']:
                    self.html_files.append(file_path)

        print(f"Found {len(self.js_files)} JS files, {len(self.css_files)} CSS files, {len(self.html_files)} HTML files")

    def read_file_safe(self, file_path: Path) -> str:
        """Safely read file content with multiple encoding attempts."""
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        print(f"Warning: Could not read {file_path} with any encoding")
        return ""

    def get_css_selectors(self, css_content: str) -> Set[str]:
        """Extract CSS selectors (classes and IDs) from CSS content."""
        selectors = set()

        # Remove comments
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)

        # Find class selectors
        classes = self.css_class_pattern.findall(css_content)
        selectors.update(f".{cls}" for cls in classes)

        # Find ID selectors
        ids = self.css_id_pattern.findall(css_content)
        selectors.update(f"#{id_}" for id_ in ids)

        return selectors

    def get_js_identifiers(self, js_content: str) -> Set[str]:
        """Extract JavaScript function and variable names."""
        identifiers = set()

        # Remove comments
        js_content = re.sub(r'//.*?$', '', js_content, flags=re.MULTILINE)
        js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)

        # Find function declarations
        functions = self.js_function_pattern.findall(js_content)
        identifiers.update(functions)

        # Find variable declarations
        variables = self.js_var_pattern.findall(js_content)
        identifiers.update(variables)

        return identifiers

    def find_references_in_content(self, content: str, selectors: Set[str]) -> Set[str]:
        """Find which selectors are referenced in the content."""
        referenced = set()
        content_lower = content.lower()

        for selector in selectors:
            # For CSS classes, check for class="..." or className="..."
            if selector.startswith('.'):
                class_name = selector[1:]
                patterns = [
                    rf'class\s*=\s*["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\']',
                    rf'className\s*=\s*["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\']',
                    rf'classList\.(?:add|remove|toggle|contains)\s*\(\s*["\']' + re.escape(class_name) + r'["\']',
                ]
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        referenced.add(selector)
                        break

            # For CSS IDs, check for id="..."
            elif selector.startswith('#'):
                id_name = selector[1:]
                patterns = [
                    rf'id\s*=\s*["\']' + re.escape(id_name) + r'["\']',
                    rf'getElementById\s*\(\s*["\']' + re.escape(id_name) + r'["\']',
                    rf'querySelector\s*\(\s*["\']#' + re.escape(id_name) + r'["\']',
                ]
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        referenced.add(selector)
                        break

        return referenced

    def find_js_references(self, content: str, identifiers: Set[str]) -> Set[str]:
        """Find which JavaScript identifiers are referenced in the content."""
        referenced = set()

        for identifier in identifiers:
            # Look for function calls or variable usage
            patterns = [
                rf'\b{re.escape(identifier)}\s*\(',  # Function call
                rf'\b{re.escape(identifier)}\b(?!\s*[=:])',  # Variable usage (not declaration)
            ]
            for pattern in patterns:
                if re.search(pattern, content):
                    referenced.add(identifier)
                    break

        return referenced

    def remove_unused_css_rules(self, css_content: str, unused_selectors: Set[str]) -> str:
        """Remove unused CSS rules from content."""
        if not unused_selectors:
            return css_content

        lines = css_content.split('\n')
        new_lines = []
        in_rule = False
        brace_count = 0
        current_rule_selectors = []
        rule_start_line = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not in_rule and '{' in line:
                # Start of a new rule
                rule_start_line = i
                selector_part = line[:line.find('{')]
                current_rule_selectors = [s.strip() for s in selector_part.split(',')]
                in_rule = True
                brace_count = line.count('{') - line.count('}')

                # Check if any selector in this rule is unused
                has_used_selector = False
                for sel in current_rule_selectors:
                    # Clean selector (remove pseudo-classes, etc.)
                    clean_sel = re.sub(r':.*$', '', sel.strip())
                    if not any(unused in clean_sel for unused in unused_selectors):
                        has_used_selector = True
                        break

                if has_used_selector:
                    new_lines.append(line)
                elif brace_count == 0:
                    # Single line rule that's unused
                    in_rule = False

            elif in_rule:
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    # End of rule
                    in_rule = False
                    # Only add the line if the rule has used selectors
                    has_used_selector = False
                    for sel in current_rule_selectors:
                        clean_sel = re.sub(r':.*$', '', sel.strip())
                        if not any(unused in clean_sel for unused in unused_selectors):
                            has_used_selector = True
                            break

                    if has_used_selector:
                        new_lines.append(line)
                elif any(unused in line for unused in unused_selectors):
                    # Skip lines that contain unused selectors
                    continue
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        return '\n'.join(new_lines)

    def remove_unused_js_code(self, js_content: str, unused_identifiers: Set[str]) -> str:
        """Remove unused JavaScript functions and variables."""
        if not unused_identifiers:
            return js_content

        lines = js_content.split('\n')
        new_lines = []

        for line in lines:
            should_remove = False

            for unused in unused_identifiers:
                # Check for function declarations
                if re.search(rf'^\s*function\s+{re.escape(unused)}\s*\(', line):
                    should_remove = True
                    break
                # Check for variable declarations
                elif re.search(rf'^\s*(?:var|let|const)\s+{re.escape(unused)}\s*[=;]', line):
                    should_remove = True
                    break

            if not should_remove:
                new_lines.append(line)

        return '\n'.join(new_lines)

    def process_files(self):
        """Main processing function."""
        print("Processing files...")

        # Collect all content for reference checking
        all_content = ""

        # Read all HTML files
        for html_file in self.html_files:
            content = self.read_file_safe(html_file)
            all_content += f"\n{content}"

        # Read all JS files
        js_contents = {}
        for js_file in self.js_files:
            content = self.read_file_safe(js_file)
            js_contents[js_file] = content
            all_content += f"\n{content}"

        # Process CSS files
        for css_file in self.css_files:
            print(f"Processing CSS: {css_file}")
            css_content = self.read_file_safe(css_file)

            if not css_content:
                continue

            # Get all selectors in this CSS file
            selectors = self.get_css_selectors(css_content)

            # Find which selectors are referenced
            referenced_selectors = self.find_references_in_content(all_content, selectors)

            # Find unused selectors
            unused_selectors = selectors - referenced_selectors

            if unused_selectors:
                print(f"  Found {len(unused_selectors)} unused CSS selectors")

                # Remove unused CSS rules
                new_content = self.remove_unused_css_rules(css_content, unused_selectors)

                # Log changes
                self.log_changes(css_file, "CSS", unused_selectors, len(css_content), len(new_content))

                # Write back to file
                try:
                    with open(css_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                except Exception as e:
                    print(f"Error writing {css_file}: {e}")

        # Process JS files
        for js_file in self.js_files:
            print(f"Processing JS: {js_file}")
            js_content = js_contents[js_file]

            if not js_content:
                continue

            # Get all identifiers in this JS file
            identifiers = self.get_js_identifiers(js_content)

            # Find which identifiers are referenced
            referenced_identifiers = self.find_js_references(all_content, identifiers)

            # Find unused identifiers
            unused_identifiers = identifiers - referenced_identifiers

            if unused_identifiers:
                print(f"  Found {len(unused_identifiers)} unused JS identifiers")

                # Remove unused JS code
                new_content = self.remove_unused_js_code(js_content, unused_identifiers)

                # Log changes
                self.log_changes(js_file, "JavaScript", unused_identifiers, len(js_content), len(new_content))

                # Write back to file
                try:
                    with open(js_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                except Exception as e:
                    print(f"Error writing {js_file}: {e}")

    def log_changes(self, file_path: Path, file_type: str, unused_items: Set[str],
                   original_size: int, new_size: int):
        """Log changes made to files."""
        change_entry = {
            'timestamp': datetime.now().isoformat(),
            'file': str(file_path),
            'type': file_type,
            'unused_items': list(unused_items),
            'original_size': original_size,
            'new_size': new_size,
            'bytes_saved': original_size - new_size
        }
        self.changes_log.append(change_entry)

    def save_log(self):
        """Save changes log to file."""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("UNUSED CODE REMOVAL LOG\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            total_bytes_saved = 0

            for change in self.changes_log:
                f.write(f"File: {change['file']}\n")
                f.write(f"Type: {change['type']}\n")
                f.write(f"Timestamp: {change['timestamp']}\n")
                f.write(f"Original size: {change['original_size']} bytes\n")
                f.write(f"New size: {change['new_size']} bytes\n")
                f.write(f"Bytes saved: {change['bytes_saved']}\n")
                f.write("Removed items:\n")
                for item in change['unused_items']:
                    f.write(f"  - {item}\n")
                f.write("-" * 40 + "\n\n")
                total_bytes_saved += change['bytes_saved']

            f.write(f"SUMMARY\n")
            f.write(f"Total files processed: {len(self.changes_log)}\n")
            f.write(f"Total bytes saved: {total_bytes_saved}\n")

        print(f"Changes log saved to: {self.log_file}")

    def run(self):
        """Execute the unused code removal process."""
        print("Starting unused code removal process...")

        if not self.root_dir.exists():
            print(f"Error: Directory {self.root_dir} does not exist")
            return

        self.scan_files()

        if not self.js_files and not self.css_files:
            print("No JavaScript or CSS files found")
            return

        # Create backup notification
        print("\nWARNING: This script will modify your files.")
        print("Make sure you have backups before proceeding!")
        response = input("Continue? (y/N): ")

        if response.lower() != 'y':
            print("Operation cancelled")
            return

        self.process_files()
        self.save_log()

        print(f"\nProcess completed! Check {self.log_file} for details.")

def main():
    """Main entry point."""
    print("Unused Code Remover")
    print("=" * 30)

    # Get directory from user
    directory = input("Enter the root directory to scan (or '.' for current): ").strip()
    if not directory:
        directory = "."

    # Get log file name
    log_file = input("Enter log file name (or press Enter for 'unused_code_changes.txt'): ").strip()
    if not log_file:
        log_file = "unused_code_changes.txt"

    # Create and run the remover
    remover = UnusedCodeRemover(directory, log_file)
    remover.run()

if __name__ == "__main__":
    main()