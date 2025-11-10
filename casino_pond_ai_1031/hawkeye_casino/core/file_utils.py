"""File reading and data extraction utilities"""

import os
import gzip
import re
import glob
from typing import Tuple, List, Any, Optional


class FileAnalyzer:
    """Utilities for reading and analyzing files"""

    @staticmethod
    def read_file_content(file_path: str, cache: Optional[dict] = None) -> str:
        """Read file content, handling both regular and gzipped files

        Args:
            file_path: Path to file to read
            cache: Optional dictionary to cache file contents {file_path: content}

        Returns:
            File contents as string
        """
        # OPTIMIZATION: Check cache first
        if cache is not None and file_path in cache:
            print(f"DEBUG: Using cached content for: {file_path}")
            return cache[file_path]

        try:
            print(f"DEBUG: Reading file: {file_path}")
            if file_path.endswith('.gz'):
                print(f"DEBUG: Detected gzipped file: {file_path}")
                with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    print(f"DEBUG: Successfully read gzipped file, content length: {len(content)}")
            else:
                print(f"DEBUG: Reading regular file: {file_path}")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    print(f"DEBUG: Successfully read regular file, content length: {len(content)}")

            # OPTIMIZATION: Store in cache
            if cache is not None:
                cache[file_path] = content

            return content
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return ""

    @staticmethod
    def extract_keyword(files: List[str], pattern: str, data_type: str,
                       keyword_name: str = "", specific_file: Optional[str] = None,
                       keyword_config: dict = None, cache: Optional[dict] = None) -> Any:
        """Extract keyword value from files using regex pattern

        Args:
            files: List of file paths to search
            pattern: Regex pattern to match
            data_type: Type of data to extract
            keyword_name: Name of keyword being extracted
            specific_file: Optional specific file to search in
            keyword_config: Full keyword configuration dict
            cache: Optional file content cache dictionary

        Returns:
            Extracted value or None if not found
        """

        if specific_file:
            target_file = None

            # For STA files with mode/corner in path, use full relative path matching
            # Check if specific_file contains directory separators (indicates relative path)
            if '/' in specific_file or '\\' in specific_file:
                # This is a relative path pattern (e.g., "ssft/ss_0p81v_m40c_Cworst/reports/global_timing.path.rpt")
                # Must match using endswith for full path uniqueness
                print(f"DEBUG: Matching relative path pattern: {specific_file}")

                for file_path in files:
                    # Check if file_path ends with the specific_file pattern
                    if file_path.endswith(specific_file):
                        target_file = file_path
                        print(f"DEBUG: Matched file: {file_path}")
                        break
                    # Also try with normalized path separators
                    elif file_path.replace('\\', '/').endswith(specific_file.replace('\\', '/')):
                        target_file = file_path
                        print(f"DEBUG: Matched file (normalized): {file_path}")
                        break

                if not target_file:
                    print(f"DEBUG: No exact match for '{specific_file}', trying basename fallback")
                    # Fallback: try basename matching only if no relative path match
                    # This handles cases where the path structure differs
                    basename = os.path.basename(specific_file)
                    for file_path in files:
                        if os.path.basename(file_path) == basename:
                            print(f"DEBUG: WARNING - Using basename fallback match: {file_path}")
                            print(f"DEBUG: This may not be the intended file for pattern: {specific_file}")
                            target_file = file_path
                            break
            else:
                # This is just a filename (no directory separators)
                # Safe to use basename matching
                print(f"DEBUG: Matching simple filename: {specific_file}")
                for file_path in files:
                    if os.path.basename(file_path) == specific_file:
                        target_file = file_path
                        print(f"DEBUG: Matched file: {file_path}")
                        break




            if target_file:
                # Check if file exists (handles symlinks correctly)
                if os.path.lexists(target_file):
                    # If it's a symlink, verify target is accessible
                    if os.path.islink(target_file):
                        if not os.path.exists(target_file):
                            print(f"      Broken symlink: {target_file} -> {os.readlink(target_file)}")
                            return None
                    elif not os.path.exists(target_file):
                        print(f"      File does not exist: {target_file}")
                        return None

                    try:
                        content = FileAnalyzer.read_file_content(target_file, cache)
                        return FileAnalyzer._extract_from_content(
                            content, pattern, data_type, keyword_name, specific_file, keyword_config)
                    except Exception as e:
                        print(f"      Error reading specific file {target_file}: {e}")
                        return None
                else:
                    print(f"      File not found: {target_file}")
                    return None
            else:
                print(f"      Specific file {specific_file} not found in available files")
                return None

        # Search in all files
        for file_path in files:
            try:
                content = FileAnalyzer.read_file_content(file_path, cache)
                result = FileAnalyzer._extract_from_content(
                    content, pattern, data_type, keyword_name, specific_file, keyword_config)
                if result is not None:
                    return result
            except Exception:
                continue

        return None

    @staticmethod
    def _extract_from_content(content: str, pattern: str, data_type: str,
                             keyword_name: str = "", specific_file: Optional[str] = None,
                             keyword_config: dict = None) -> Any:
        """Extract value from content using pattern and data type
        Args:
            content: File content to search
            pattern: Regex pattern (string) or pre-compiled pattern object
            data_type: Type of extraction to perform
            keyword_name: Name of keyword
            specific_file: Specific file being searched
            keyword_config: Full keyword configuration dict (may contain '_compiled_pattern')
        Returns:
            Extracted value or None
        """
        # OPTIMIZATION: Use pre-compiled pattern if available
        # This avoids recompiling the same pattern hundreds of times
        compiled_pattern = None
        if keyword_config and '_compiled_pattern' in keyword_config:
            compiled_pattern = keyword_config['_compiled_pattern']

        # Pass compiled pattern to extraction methods
        if data_type == 'dynamic_table_row':
            return FileAnalyzer._extract_dynamic_table(content, pattern, keyword_name, keyword_config, compiled_pattern)
        elif data_type == 'sta_timing_row':
            return FileAnalyzer._extract_sta_timing_row(content, pattern, keyword_config, compiled_pattern)
        elif data_type == 'sta_violation_worst':
            return FileAnalyzer._extract_sta_violation_worst(content, pattern, keyword_config, compiled_pattern)
        elif data_type == 'sta_noise_count':
            return FileAnalyzer._extract_sta_noise_count(content, pattern, keyword_config, compiled_pattern)
        elif data_type == 'sta_noise_worst':
            return FileAnalyzer._extract_sta_noise_worst(content, pattern, keyword_config, compiled_pattern)
        elif data_type == 'perc_rulecheck':
            return FileAnalyzer._extract_perc_rulecheck(content, pattern, keyword_name, keyword_config, compiled_pattern)
        elif data_type == 'perc_rulecheck_summary':
            return FileAnalyzer._extract_perc_rulecheck_summary(content, pattern, keyword_name, keyword_config, compiled_pattern)
        elif data_type == 'count':
            return FileAnalyzer._extract_count(content, pattern, compiled_pattern)
        elif data_type == 'multiple_values':
            return FileAnalyzer._extract_multiple_values(content, pattern, compiled_pattern)
        elif data_type == 'number':
            return FileAnalyzer._extract_number(content, pattern, compiled_pattern)
        elif data_type == 'status':
            return FileAnalyzer._extract_status(content, pattern, compiled_pattern)
        else:
            return FileAnalyzer._extract_string(content, pattern, compiled_pattern)

    @staticmethod
    def _extract_sta_violation_worst(content: str, pattern: str, keyword_config: dict, compiled_pattern=None) -> Optional[float]:
        """Extract worst (maximum absolute value) violation from STA report

        Report format example:
           u_input_core/u_edp_single/u_edp/U_DP/dp_phy/EQ_MON_N   0.1000  30.0306 -29.9306 (VIOLATED)
           u_input_core/u_edp_single/u_edp/U_DP/dp_phy/EQ_MON_P   0.1000  30.0115 -29.9115 (VIOLATED)
           u_output_core/u_UPI_PHY/UPI/UPI1N   0.1000  30.0000    -29.9000  (VIOLATED)
           u_output_core/u_UPI_PHY/UPI/UPI1P   0.1000  30.0000    -29.9000  (VIOLATED)

        The pattern should capture the violation value (second-to-last column before (VIOLATED))
        Pattern example: r'\s+([-\d.]+)\s+\(VIOLATED\)'

        Args:
            content: File content
            pattern: Regex pattern to match violation value
            keyword_config: Full keyword configuration dict with:
                           - violation_type: 'max_tran' or 'max_cap'
                           - mode: mode name
                           - corner: corner name
            compiled_pattern: Pre-compiled regex pattern (optional, for performance)

        Returns:
            Float value of worst (largest absolute value) violation, or 0.0 if no violations
        """
        try:
            violation_type = keyword_config.get('violation_type', 'unknown')
            mode = keyword_config.get('mode', 'unknown')
            corner = keyword_config.get('corner', 'unknown')

            print(f"      DEBUG: Extracting worst {violation_type} violation for {mode}/{corner}")

            # Find all violation values using the pattern - use compiled if available
            if compiled_pattern:
                matches = compiled_pattern.findall(content)
            else:
                matches = re.findall(pattern, content, re.MULTILINE)

            if not matches:
                print(f"      DEBUG: No {violation_type} violations found in report")
                return 0.0

            print(f"      DEBUG: Found {len(matches)} {violation_type} violation entries")

            # Convert to floats
            violation_values = []
            for match in matches:
                try:
                    value = float(match)
                    violation_values.append(value)
                except ValueError:
                    print(f"      WARNING: Could not convert '{match}' to float, skipping")
                    continue

            if not violation_values:
                print(f"      DEBUG: No valid {violation_type} violation values after parsing")
                return 0.0

            # Find worst violation (maximum absolute value)
            # Note: Violations are typically negative, so we want the most negative
            worst_violation = max(violation_values, key=abs)

            print(f"      DEBUG: Violation values range: [{min(violation_values):.4f}, {max(violation_values):.4f}]")
            print(f"      DEBUG: Worst {violation_type} violation (by abs value): {worst_violation:.4f}")

            return worst_violation

        except Exception as e:
            print(f"      ERROR: Exception in _extract_sta_violation_worst: {e}")
            import traceback
            print(f"      Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    def _extract_sta_noise_count(content: str, pattern: str, keyword_config: dict, compiled_pattern=None) -> int:
        """Count noise violations by parsing table data rows

        Report format:
            noise_region: above_low
            pin name (net name)       width    height     slack
            -----------------------------------------------------
            u_top/path (..)           0.284    0.471   -0.045
            u_top/path (..)           1.258    0.447   -0.020

        Args:
            content: File content
            pattern: Regex pattern to match noise_region type (e.g., r'noise_region:\s*above_low')
            keyword_config: Full keyword configuration dict with:
                           - noise_type: 'above_low' or 'below_high'
                           - mode: mode name
                           - corner: corner name

        Returns:
            Integer count of violations (data rows with valid slack values)
        """
        try:
            noise_type = keyword_config.get('noise_type', 'unknown')
            mode = keyword_config.get('mode', 'unknown')
            corner = keyword_config.get('corner', 'unknown')

            print(f"      DEBUG: Counting {noise_type} violations for {mode}/{corner}")

            # Find the section with this noise_region - use compiled pattern if available
            if compiled_pattern:
                section_match = compiled_pattern.search(content)
            else:
                section_match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if not section_match:
                print(f"      DEBUG: No '{noise_type}' section found in report")
                return 0

            section_start = section_match.end()

            # Find the next section boundary (next "noise_region:" or end of file)
            next_section_match = re.search(
                r'noise_region:\s*\w+',
                content[section_start:],
                re.MULTILINE | re.IGNORECASE
            )

            if next_section_match:
                section_end = section_start + next_section_match.start()
                section_content = content[section_start:section_end]
            else:
                section_content = content[section_start:]

            print(f"      DEBUG: Section content length: {len(section_content)}")

            # Skip header lines until we find the dashed separator
            lines = section_content.split('\n')
            data_start_index = 0

            for i, line in enumerate(lines):
                if '-----' in line:
                    data_start_index = i + 1
                    break

            if data_start_index >= len(lines):
                print(f"      DEBUG: No data section found after separator")
                return 0

            # Count valid data rows (rows with numeric values)
            violation_count = 0

            for line in lines[data_start_index:]:
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Skip lines that are just numbers (like page numbers)
                if line.isdigit() and len(line) < 3:
                    continue

                # Check if this line has the expected format:
                # <pin_path> (<net_path>)    width    height   slack
                # We expect at least 3 numeric values in the line
                parts = line.split()

                if len(parts) < 3:
                    continue

                # Try to parse the last value as slack
                try:
                    slack_str = parts[-1]
                    slack_value = float(slack_str)

                    # This is a valid data row (has numeric slack)
                    violation_count += 1
                    print(f"      DEBUG: Found violation with slack: {slack_value}")

                except (ValueError, IndexError):
                    # Not a data line, skip
                    continue

            print(f"      DEBUG: Found {violation_count} {noise_type} noise violations")
            return violation_count

        except Exception as e:
            print(f"      ERROR: Exception in _extract_sta_noise_count: {e}")
            import traceback
            print(f"      Traceback: {traceback.format_exc()}")
            return 0


    @staticmethod
    def _extract_sta_noise_worst(content: str, pattern: str, keyword_config: dict, compiled_pattern=None) -> Optional[float]:
        """Extract worst (maximum absolute value) noise violation slack

        Report format:
            noise_region: above_low
            pin name (net name)       width    height     slack
            -----------------------------------------------------
            u_top/path (..)           0.284    0.471   -0.045
            u_top/path (..)           1.258    0.447   -0.020

        Args:
            content: File content
            pattern: Regex pattern to match noise_region type
            keyword_config: Full keyword configuration dict with:
                           - noise_type: 'above_low' or 'below_high'
                           - mode: mode name
                           - corner: corner name

        Returns:
            Float value of worst (largest absolute value) slack, or 0.0 if no violations
        """
        try:
            noise_type = keyword_config.get('noise_type', 'unknown')
            mode = keyword_config.get('mode', 'unknown')
            corner = keyword_config.get('corner', 'unknown')

            print(f"      DEBUG: Extracting worst {noise_type} violation for {mode}/{corner}")

            # Find the section with this noise_region - use compiled pattern if available
            if compiled_pattern:
                section_match = compiled_pattern.search(content)
            else:
                section_match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if not section_match:
                print(f"      DEBUG: No '{noise_type}' section found in report")
                return 0.0

            section_start = section_match.end()

            # Find the next section boundary
            next_section_match = re.search(
                r'noise_region:\s*\w+',
                content[section_start:],
                re.MULTILINE | re.IGNORECASE
            )

            if next_section_match:
                section_end = section_start + next_section_match.start()
                section_content = content[section_start:section_end]
            else:
                section_content = content[section_start:]

            print(f"      DEBUG: Section content length: {len(section_content)}")

            # Skip header lines until we find the dashed separator
            lines = section_content.split('\n')
            data_start_index = 0

            for i, line in enumerate(lines):
                if '-----' in line:
                    data_start_index = i + 1
                    break

            if data_start_index >= len(lines):
                print(f"      DEBUG: No data section found after separator")
                return 0.0

            # Extract all slack values from data rows
            slack_values = []

            for line in lines[data_start_index:]:
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Skip lines that are just numbers (like page numbers)
                if line.isdigit() and len(line) < 3:
                    continue

                # Parse line - should have at least 3 numeric values (width, height, slack)
                parts = line.split()

                if len(parts) < 3:
                    continue

                try:
                    # Last part should be slack value
                    slack_str = parts[-1]
                    slack_value = float(slack_str)

                    # Add to list of slack values
                    slack_values.append(slack_value)
                    print(f"      DEBUG: Found slack value: {slack_value}")

                except (ValueError, IndexError):
                    # Not a data line, skip
                    continue

            if not slack_values:
                print(f"      DEBUG: No {noise_type} violation slack values found")
                return 0.0

            # Find worst violation (maximum absolute value)
            # Negative slack is worse, so we want the most negative
            worst_violation = min(slack_values)  # Most negative = worst

            print(f"      DEBUG: Slack values range: [{min(slack_values):.6f}, {max(slack_values):.6f}]")
            print(f"      DEBUG: Worst {noise_type} violation slack: {worst_violation:.6f}")

            return worst_violation

        except Exception as e:
            print(f"      ERROR: Exception in _extract_sta_noise_worst: {e}")
            import traceback
            print(f"      Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    def _extract_noise_violation_count(content: str, pattern: str, keyword_config: dict) -> int:
        """Extract noise violation count from PrimeTime gnoise report

        Report format:
            noise_region: above_low
            pin name (net name)       width    height     slack
            -----------------------------------------------------
            <pin_path> (<net_path>)    0.374    0.468   -0.075
            <pin_path> (<net_path>)    0.356    0.447   -0.044
            ...

            noise_region: below_high
            pin name (net name)       width    height     slack
            -----------------------------------------------------
            <pin_path> (<net_path>)    0.628    0.544   -0.014
            ...

        Args:
            content: File content
            pattern: Section header pattern (e.g., "noise_region: above_low")
            keyword_config: Full keyword configuration dict with:
                           - noise_type: 'above_low' or 'below_high'
                           - mode: mode name
                           - corner: corner name

        Returns:
            Integer count of violations (lines with negative slack), or 0 if no violations
        """
        try:
            noise_type = keyword_config.get('noise_type', 'unknown')
            mode = keyword_config.get('mode', 'unknown')
            corner = keyword_config.get('corner', 'unknown')

            print(f"      DEBUG: Extracting {noise_type} noise violations for {mode}/{corner}")

            # Find the section with this noise_region
            section_match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if not section_match:
                print(f"      DEBUG: No '{noise_type}' section found in report")
                return 0

            section_start = section_match.end()

            # Find the next section boundary (next "noise_region:" or end of file)
            next_section_match = re.search(
                r'noise_region:\s*\w+',
                content[section_start:],
                re.MULTILINE | re.IGNORECASE
            )

            if next_section_match:
                section_end = section_start + next_section_match.start()
                section_content = content[section_start:section_end]
            else:
                section_content = content[section_start:]

            print(f"      DEBUG: Section content length: {len(section_content)}")

            # Skip header lines (until we find the dashed separator)
            lines = section_content.split('\n')
            data_start_index = 0

            for i, line in enumerate(lines):
                if '-----' in line:
                    data_start_index = i + 1
                    break

            if data_start_index >= len(lines):
                print(f"      DEBUG: No data section found after separator")
                return 0

            # Count lines with negative slack
            # Format: <pin_path> (<net_path>)    width    height   slack
            # We look for lines with numbers and negative slack (last column)
            violation_count = 0

            for line in lines[data_start_index:]:
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Parse line - should have at least 3 numeric values (width, height, slack)
                # Split by whitespace and look for the last numeric value (slack)
                parts = line.split()

                if len(parts) < 3:
                    continue

                try:
                    # Last part should be slack value
                    slack_str = parts[-1]
                    slack_value = float(slack_str)

                    # Count if slack is negative
                    if slack_value < 0:
                        violation_count += 1

                except (ValueError, IndexError):
                    # Not a data line, skip
                    continue

            print(f"      DEBUG: Found {violation_count} {noise_type} noise violations")
            return violation_count

        except Exception as e:
            print(f"      ERROR: Exception in _extract_noise_violation_count: {e}")
            import traceback
            print(f"      Traceback: {traceback.format_exc()}")
            return 0

    @staticmethod
    def _extract_sta_timing_row(content: str, pattern: str, keyword_config: dict, compiled_pattern=None) -> Optional[float]:
        """Extract STA timing value from simplified report format

        Reports have format:
        Setup violations
        --------------------------------------------------------------
                  Total   reg->reg    in->reg   reg->out    in->out
        --------------------------------------------------------------
        WNS     -3.5870    -2.7229    -0.5422    -3.5870     0.0000
        TNS  -2747.4203  -755.0064   -76.1588 -1916.2551     0.0000
        NUM        7688       5416        280       1992          0

        Hold violations
        ---------------------------------------------------------
                 Total  reg->reg   in->reg  reg->out   in->out
        ---------------------------------------------------------
        WNS    -0.0140   -0.0140    0.0000    0.0000    0.0000
        TNS    -1.2453   -1.2453    0.0000    0.0000    0.0000
        NUM        572       572         0         0         0

        Args:
            content: File content
            pattern: Regex pattern for metric line (WNS, TNS, NUM)
            keyword_config: Full keyword configuration with path_type, timing_type

        Returns:
            Float value for the specific metric and path type, or None if not found
        """
        try:
            path_type = keyword_config.get('path_type', 'Total')
            timing_type = keyword_config.get('timing_type', 'setup')

            print(f"      DEBUG: Extracting STA timing - path_type: {path_type}, timing_type: {timing_type}")

            # Build section header pattern (simplified - no path groups)
            section_pattern = f"{timing_type.capitalize()} violations"

            print(f"      DEBUG: Looking for section: {section_pattern}")

            # Find the section
            section_match = re.search(section_pattern, content, re.IGNORECASE)
            if not section_match:
                print(f"      DEBUG: Section not found: {section_pattern}")
                # Check for "No {timing_type} violations found"
                no_viol_pattern = f"No {timing_type} violations found"
                if re.search(no_viol_pattern, content, re.IGNORECASE):
                    print(f"      DEBUG: Found 'No {timing_type} violations' - returning 0.0")
                    return 0.0
                return None

            section_start = section_match.end()

            # Find the next section boundary
            content_after_section = content[section_start:]

            # Look for next section (either "Setup violations", "Hold violations", or "Report :")
            next_section_match = re.search(
                r"(Setup violations|Hold violations|Report :|\*\*\*\*\*\*\*\*)",
                content_after_section[50:],  # Skip first 50 chars to avoid same section
                re.IGNORECASE
            )

            if next_section_match:
                section_end = section_start + 50 + next_section_match.start()
                section_content = content[section_start:section_end]
            else:
                section_content = content_after_section

            print(f"      DEBUG: Section content length: {len(section_content)}")

            # Extract the metric line - use compiled pattern if available
            if compiled_pattern:
                metric_match = compiled_pattern.search(section_content)
            else:
                metric_match = re.search(pattern, section_content, re.MULTILINE)

            if not metric_match:
                print(f"      DEBUG: Metric pattern not found in section")
                return 0.0

            # Extract all values from the line
            values = metric_match.groups()
            print(f"      DEBUG: Extracted values: {values}")

            # Map path type to column index
            # Columns: Total, reg->reg, in->reg, reg->out, in->out
            path_type_map = {
                'Total': 0,
                'reg->reg': 1,
                'in->reg': 2,
                'reg->out': 3,
                'in->out': 4
            }

            if path_type not in path_type_map:
                print(f"      WARNING: Unknown path type: {path_type}")
                return None

            col_index = path_type_map[path_type]

            if col_index >= len(values):
                print(f"      WARNING: Column index {col_index} out of range")
                return None

            value_str = values[col_index].strip()

            try:
                value = float(value_str)
                print(f"      DEBUG: Extracted value for {path_type}: {value}")
                return value
            except ValueError:
                print(f"      WARNING: Could not convert '{value_str}' to float")
                return 0.0

        except Exception as e:
            print(f"      ERROR: Exception in _extract_sta_timing_row: {e}")
            import traceback
            print(f"      Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    def _extract_dynamic_table(content: str, pattern: str, keyword_name: str,
                              keyword_config: dict = None, compiled_pattern=None) -> Optional[dict]:
        """Extract dynamic table row with flexible columns from timing summary table

        Dynamically extracts column names from header row, supporting variable column counts.

        Table format example:
        +--------------------+---------+---------+---------+---------+---------+---------+---------+
        |     Setup mode     |   all   | reg2reg |reg2cgate| in2reg  | reg2out | in2out  | default |
        +--------------------+---------+---------+---------+---------+---------+---------+---------+
        |           WNS (ns):| -16.080 | -16.080 |  4.275  |  0.077  | -0.544  |   N/A   |  0.000  |

        Args:
            content: File content to search
            pattern: Pattern to match data row (e.g., "\\|\\s+WNS \\(ns\\):")
            keyword_name: Name of keyword being extracted
            keyword_config: Full keyword configuration dict (optional, for header_pattern)

        Returns:
            Dictionary mapping column names to values, or None if extraction fails
        """
        try:
            print(f"      DEBUG: Extracting dynamic table for '{keyword_name}'")

            # Step 1: Get header pattern (default or from config)
            header_pattern = r'\|\s+(Setup mode|Hold mode)\s+\|(.+?)\|[\s\r\n]*$'
            if keyword_config and 'header_pattern' in keyword_config:
                print(f"      DEBUG: Using custom header pattern from config")

            # Step 2: Find the data line first to determine search context - use compiled pattern if available
            if compiled_pattern:
                data_match = compiled_pattern.search(content)
            else:
                data_match = re.search(pattern, content, re.MULTILINE)
            if not data_match:
                print(f"      Warning: No data line found for pattern: {pattern}")
                return None

            data_line = data_match.group(0)
            data_line_pos = data_match.start()
            print(f"      DEBUG: Found data line at position {data_line_pos}")

            # Step 3: Search BACKWARDS from data line to find the nearest header
            content_before_data = content[:data_line_pos]

            # Look for header line in reverse (find the closest one before data line)
            header_matches = list(re.finditer(header_pattern, content_before_data, re.MULTILINE))

            if not header_matches:
                print(f"      Warning: No header found before data line for '{keyword_name}'")
                return None

            # Take the LAST match (closest to data line)
            header_match = header_matches[-1]
            header_line = header_match.group(0)
            print(f"      DEBUG: Found header line")

            # Step 4: Extract column names from header dynamically
            mode_and_columns = re.match(r'\|\s+(Setup mode|Hold mode)\s+\|(.+)', header_line)

            if not mode_and_columns:
                print(f"      Warning: Could not parse header format")
                return None

            columns_part = mode_and_columns.group(2)
            columns_part = columns_part.rstrip('|').rstrip()

            column_names = []
            for col in columns_part.split('|'):
                col_clean = col.strip()
                if col_clean:
                    column_names.append(col_clean)

            print(f"      DEBUG: Dynamically extracted {len(column_names)} columns: {column_names}")

            # Step 5: Extract values from data line
            label_match = re.match(r'\|[^|]+\|', data_line)

            if label_match:
                value_part = data_line[label_match.end():]
            else:
                parts = data_line.split('|', 1)
                value_part = parts[1] if len(parts) > 1 else data_line

            value_part = value_part.rstrip('|').rstrip()
            print(f"      DEBUG: Value part extracted")

            # Step 6: Split by pipe and extract values
            raw_values = []
            for val in value_part.split('|'):
                val_clean = val.strip()
                if val_clean:
                    raw_values.append(val_clean)

            print(f"      DEBUG: Extracted {len(raw_values)} raw values")

            # Step 7: Validate column count matches value count
            if len(column_names) != len(raw_values):
                print(f"      Warning: Column count ({len(column_names)}) != "
                      f"Value count ({len(raw_values)})")

                if len(raw_values) < len(column_names):
                    print(f"      Warning: Fewer values than columns, truncating columns")
                    column_names = column_names[:len(raw_values)]
                elif len(raw_values) > len(column_names):
                    print(f"      Warning: More values than columns, truncating values")
                    raw_values = raw_values[:len(column_names)]

            # Step 8: Convert to float, handling N/A and special cases
            values = []
            for val in raw_values:
                val_upper = val.upper()
                if val_upper in ['N/A', 'NA', '-', '', 'NONE']:
                    values.append(0.0)
                else:
                    try:
                        float_val = float(val.strip())
                        values.append(float_val)
                    except ValueError:
                        print(f"      Warning: Could not convert '{val}' to float, using 0.0")
                        values.append(0.0)

            print(f"      DEBUG: Converted values")

            # Step 9: Create result dictionary with normalized column names
            result = {}
            for col_name, value in zip(column_names, values):
                clean_col_name = col_name.lower().replace(' ', '_').replace('-', '_')
                result[clean_col_name] = value

            print(f"      DEBUG: Final result - {len(result)} column-value pairs")
            print(f"      DEBUG: Columns: {list(result.keys())}")

            return result

        except Exception as e:
            print(f"      ERROR: Exception in _extract_dynamic_table: {e}")
            import traceback
            print(f"      Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    def _extract_count(content: str, pattern: str, compiled_pattern=None) -> int:
        """Count occurrences of pattern"""
        if compiled_pattern:
            matches = compiled_pattern.findall(content)
        else:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
        count = len(matches)
        return count if count > 0 else 0

    @staticmethod
    def _extract_multiple_values(content: str, pattern: str, compiled_pattern=None) -> Optional[list]:
        """Extract multiple values from single line"""
        if compiled_pattern:
            all_matches = list(compiled_pattern.finditer(content))
        else:
            all_matches = list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
        if all_matches:
            match = all_matches[-1]  # Get last match
            if match.groups():
                try:
                    values = []
                    for group in match.groups():
                        if group.strip().upper() == 'N/A':
                            values.append(0.0)
                        else:
                            values.append(float(group))
                    return values
                except ValueError:
                    return None
        return None

    @staticmethod
    def _extract_perc_rulecheck(content: str, pattern: str, keyword_name: str, keyword_config: dict, compiled_pattern=None) -> dict:
        """Extract DRC RULECHECK statistics with dynamic keyword generation

        Used for PV tasks: DRC, FlipChip, PERC, and other Calibre verification tasks
        that output per-rule violation counts.

        Report format (section between markers):
            === DRC RULECHECK STATISTICS
            ===
            RULECHECK LUP.7.6.0U ... TOTAL Result Count = 0   (0)
            RULECHECK ESD.43.1gU ... TOTAL Result Count = 0   (0)
            RULECHECK LUP.2 ........ TOTAL Result Count = 104 (6450)
            RULECHECK LUP.1 ........ TOTAL Result Count = 40  (783)
            ===

        Pattern captures: (rule_name, cell_count, flatten_count)
        Pattern example: r'RULECHECK\\s+(\\S+)\\s+\\.+\\s+TOTAL Result Count\\s+=\\s+(\\d+)\\s+\\((\\d+)\\)'

        Args:
            content: File content
            pattern: Regex pattern to match RULECHECK lines
            keyword_name: Base keyword name used as prefix for generated keywords
            keyword_config: Full keyword configuration dict with:
                           - section_start: Start marker (e.g., "=== DRC RULECHECK STATISTICS")
                           - section_end: End marker (e.g., "===")
                           - skip_zero: Skip rules with "0 (0)" if True
            compiled_pattern: Pre-compiled regex pattern (optional, for performance)

        Returns:
            Dictionary with dynamic keywords using keyword_name as prefix: {
                '{keyword_name}_{rule}_cell': cell_count,
                '{keyword_name}_{rule}_flatten': flatten_count
            }
            Examples:
                'perc_ldl_violations_LUP.2_cell': 104
                'drc_detailed_M1.W.1_flatten': 6450
        """
        try:
            section_start_marker = keyword_config.get('section_start', '')
            section_end_marker = keyword_config.get('section_end', '')
            skip_zero = keyword_config.get('skip_zero', False)

            print(f"      DEBUG: Extracting '{keyword_name}' rulecheck statistics")
            print(f"      DEBUG: Section markers: start='{section_start_marker}', end='{section_end_marker}'")
            print(f"      DEBUG: Skip zero violations: {skip_zero}")

            # Extract section content between markers
            section_content = content

            if section_start_marker:
                section_start_match = re.search(re.escape(section_start_marker), content, re.MULTILINE)
                if not section_start_match:
                    print(f"      DEBUG: Section start marker not found")
                    return {}

                section_start_pos = section_start_match.end()

                # Find section end marker (after start marker)
                if section_end_marker:
                    # Search for the SECOND occurrence of section_end_marker
                    # (first one is part of the start marker line)
                    remaining_content = content[section_start_pos:]
                    section_end_match = re.search(re.escape(section_end_marker), remaining_content, re.MULTILINE)

                    if section_end_match:
                        section_end_pos = section_start_pos + section_end_match.start()
                        section_content = content[section_start_pos:section_end_pos]
                    else:
                        section_content = remaining_content
                else:
                    section_content = content[section_start_pos:]

            print(f"      DEBUG: Section content length: {len(section_content)} characters")

            # Find all RULECHECK matches in the section
            if compiled_pattern:
                matches = list(compiled_pattern.finditer(section_content))
            else:
                matches = list(re.finditer(pattern, section_content, re.MULTILINE))

            if not matches:
                print(f"      DEBUG: No RULECHECK entries found in section")
                return {}

            print(f"      DEBUG: Found {len(matches)} RULECHECK entries")

            # Build result dictionary with dynamic keywords
            result = {}
            rules_processed = 0
            rules_skipped = 0

            for match in matches:
                if len(match.groups()) != 3:
                    print(f"      WARNING: RULECHECK match doesn't have 3 groups, skipping")
                    continue

                rule_name = match.group(1)
                cell_count = int(match.group(2))
                flatten_count = int(match.group(3))

                # Skip zero violations if requested
                if skip_zero and cell_count == 0 and flatten_count == 0:
                    rules_skipped += 1
                    continue

                # Generate dynamic keywords using keyword_name as prefix
                # Format: {keyword_name}_{rule_name}_cell and {keyword_name}_{rule_name}_flatten
                cell_keyword = f"{keyword_name}_{rule_name}_cell"
                flatten_keyword = f"{keyword_name}_{rule_name}_flatten"

                result[cell_keyword] = float(cell_count)
                result[flatten_keyword] = float(flatten_count)

                rules_processed += 1
                print(f"      DEBUG: Processed rule '{rule_name}': cell={cell_count}, flatten={flatten_count}")

            print(f"      DEBUG: '{keyword_name}' extraction complete: {rules_processed} rules processed, {rules_skipped} rules skipped")
            print(f"      DEBUG: Generated {len(result)} dynamic keywords")

            return result

        except Exception as e:
            print(f"      ERROR: Exception in _extract_perc_rulecheck: {e}")
            import traceback
            print(f"      Traceback: {traceback.format_exc()}")
            return {}

    @staticmethod
    def _extract_perc_rulecheck_summary(content: str, pattern: str, keyword_name: str, keyword_config: dict, compiled_pattern=None) -> dict:
        """Extract PERC RULECHECK SUMMARY statistics with dual-column format

        Used for perc.rep RULECHECK SUMMARY section with two possible count columns:
        - Result Count column (left): Normal violations
        - Info Count column (right): Info entries (usually skipped)

        Report format:
            Status      Result Count  Info Count    Rule
            ---------   ------------  ------------  --------------
            COMPLETED   7 (7)                       ESD.NET.1gu (description...)
            COMPLETED                 41 (41)       INFO_Power_Clamp (description...)

        Pattern captures 5 groups: (result_cell, result_flatten, info_cell, info_flatten, rule_name)
        - Groups 1-2: Result Count column (cell, flatten)
        - Groups 3-4: Info Count column (cell, flatten)
        - Group 5: Rule name

        Args:
            content: File content
            pattern: Regex pattern to match COMPLETED lines
            keyword_name: Base keyword name used as prefix for generated keywords
            keyword_config: Full keyword configuration dict with:
                           - section_start: Start marker
                           - section_end: End marker
                           - skip_zero: Skip rules with "0 (0)" if True
                           - skip_info: Skip rules starting with "INFO_" if True
            compiled_pattern: Pre-compiled regex pattern (optional, for performance)

        Returns:
            Dictionary with dynamic keywords using keyword_name as prefix
        """
        try:
            section_start_marker = keyword_config.get('section_start', '')
            section_end_marker = keyword_config.get('section_end', '')
            skip_zero = keyword_config.get('skip_zero', False)
            skip_info = keyword_config.get('skip_info', False)

            print(f"      DEBUG: Extracting '{keyword_name}' PERC summary statistics")
            print(f"      DEBUG: Section markers: start='{section_start_marker}', end='{section_end_marker}'")
            print(f"      DEBUG: Skip zero: {skip_zero}, Skip INFO_: {skip_info}")

            # Extract section content between markers
            section_content = content

            if section_start_marker:
                section_start_match = re.search(re.escape(section_start_marker), content, re.MULTILINE)
                if not section_start_match:
                    print(f"      DEBUG: Section start marker not found")
                    return {}

                section_start_pos = section_start_match.end()

                if section_end_marker:
                    remaining_content = content[section_start_pos:]
                    section_end_match = re.search(re.escape(section_end_marker), remaining_content, re.MULTILINE)

                    if section_end_match:
                        section_end_pos = section_start_pos + section_end_match.start()
                        section_content = content[section_start_pos:section_end_pos]
                    else:
                        section_content = remaining_content
                else:
                    section_content = content[section_start_pos:]

            print(f"      DEBUG: Section content length: {len(section_content)} characters")

            # Find all COMPLETED matches in the section
            if compiled_pattern:
                matches = list(compiled_pattern.finditer(section_content))
            else:
                matches = list(re.finditer(pattern, section_content, re.MULTILINE))

            if not matches:
                print(f"      DEBUG: No COMPLETED entries found in section")
                return {}

            print(f"      DEBUG: Found {len(matches)} COMPLETED entries")

            # Build result dictionary with dynamic keywords
            result = {}
            rules_processed = 0
            rules_skipped = 0

            for match in matches:
                groups = match.groups()
                if len(groups) != 5:
                    print(f"      WARNING: Match doesn't have 5 groups, skipping: {groups}")
                    continue

                # Extract values from either Result Count or Info Count column
                result_cell = groups[0]
                result_flatten = groups[1]
                info_cell = groups[2]
                info_flatten = groups[3]
                rule_name = groups[4]

                # Determine which column has data
                if result_cell and result_flatten:
                    cell_count = int(result_cell)
                    flatten_count = int(result_flatten)
                elif info_cell and info_flatten:
                    cell_count = int(info_cell)
                    flatten_count = int(info_flatten)
                else:
                    print(f"      WARNING: No valid counts found, skipping")
                    continue

                # Skip INFO_ rules if requested
                if skip_info and rule_name.startswith('INFO_'):
                    rules_skipped += 1
                    print(f"      DEBUG: Skipping INFO_ rule: {rule_name}")
                    continue

                # Skip zero violations if requested
                if skip_zero and cell_count == 0 and flatten_count == 0:
                    rules_skipped += 1
                    continue

                # Generate dynamic keywords using keyword_name as prefix
                cell_keyword = f"{keyword_name}_{rule_name}_cell"
                flatten_keyword = f"{keyword_name}_{rule_name}_flatten"

                result[cell_keyword] = float(cell_count)
                result[flatten_keyword] = float(flatten_count)

                rules_processed += 1
                print(f"      DEBUG: Processed rule '{rule_name}': cell={cell_count}, flatten={flatten_count}")

            print(f"      DEBUG: '{keyword_name}' extraction complete: {rules_processed} rules processed, {rules_skipped} rules skipped")
            print(f"      DEBUG: Generated {len(result)} dynamic keywords")

            return result

        except Exception as e:
            print(f"      ERROR: Exception in _extract_perc_rulecheck_summary: {e}")
            import traceback
            print(f"      Traceback: {traceback.format_exc()}")
            return {}

    @staticmethod
    def _extract_number(content: str, pattern: str, compiled_pattern=None) -> Optional[float]:
        """Extract numeric value"""
        if compiled_pattern:
            all_matches = list(compiled_pattern.finditer(content))
        else:
            all_matches = list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
        if all_matches:
            match = all_matches[-1]  # Get last match
            value = match.group(1) if match.groups() else match.group(0)
            try:
                if value.strip().upper() == 'N/A':
                    return 0.0
                else:
                    return float(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def _extract_status(content: str, pattern: str, compiled_pattern=None) -> Optional[str]:
        """Extract status string"""
        if compiled_pattern:
            all_matches = list(compiled_pattern.finditer(content))
        else:
            all_matches = list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
        if all_matches:
            match = all_matches[-1]
            value = match.group(1) if match.groups() else match.group(0)
            return value.upper()
        return None

    @staticmethod
    def _extract_string(content: str, pattern: str, compiled_pattern=None) -> Optional[str]:
        """Extract string value"""
        if compiled_pattern:
            all_matches = list(compiled_pattern.finditer(content))
        else:
            all_matches = list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
        if all_matches:
            match = all_matches[-1]
            value = match.group(1) if match.groups() else match.group(0)
            return value
        return None

    @staticmethod
    def find_files_by_patterns(base_path: str, patterns: List[str]) -> Tuple[List[str], List[str]]:
        """Find files matching patterns

        Args:
            base_path: Base directory to search in
            patterns: List of file patterns (can include wildcards)

        Returns:
            Tuple of (found_files, errors)
        """
        found_files = []
        errors = []

        for pattern in patterns:
            if pattern.startswith('/'):
                search_path = pattern
            else:
                search_path = os.path.join(base_path, pattern)

            matches = glob.glob(search_path)
            if matches:
                found_files.extend(matches)
            else:
                errors.append(f"No files found for pattern: {pattern}")

        return found_files, errors


