# -*- coding: utf-8 -*-
"""
Keyword Parser for Hawkeye Report Table

Parses keyword names to extract structured information like:
- STA timing keywords (mode, corner, timing type, metric, path type)
- PV keywords (DRC, LVS, PERC, FlipChip - with cell/flatten detection)
- Violation keywords (max_tran, max_cap, noise)
"""

import re
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass


@dataclass
class STAKeyword:
    """Structured representation of STA timing keyword"""
    original_name: str
    name: str
    mode: str
    corner: str
    timing_type: str  # 's' or 'h'
    metric: str  # 'wns', 'tns', 'num'
    path_type: str  # 'all', 'reg2reg', 'in2reg', 'reg2out', 'in2out'


@dataclass
class ViolationKeyword:
    """Structured representation of violation keyword"""
    original_name: str
    name: str
    mode: str
    corner: str
    violation_type: str  # 'max_tran', 'max_cap', 'noise_above_low', 'noise_below_high'
    metric: str  # 'num' or 'worst'
    sub_type: str = ""  # For noise: 'above_low', 'below_high'


@dataclass
class PVKeyword:
    """Structured representation of PV (Physical Verification) keyword"""
    original_name: str
    name: str
    category: str  # 'DRC', 'LVS', 'PERC', 'FlipChip'
    rule: str  # Rule name (e.g., 'LUP.2', 'ESD.43gu')
    check_type: str = ""  # 'cell', 'flatten', or '' for aggregate


@dataclass
class VTHKeyword:
    """Structured representation of VTH ratio keyword"""
    original_name: str
    name: str  # 'HVth', 'RVth', 'LVth', 'ULVth'


@dataclass
class CellUsageKeyword:
    """Structured representation of cell usage keyword"""
    original_name: str
    name: str
    cell_type: str  # 'std_cell', 'comb_cell', 'flip_flop', etc.
    metric: str  # 'inst' or 'area'


@dataclass
class GenericKeyword:
    """Generic keyword that doesn't match specific patterns"""
    original_name: str
    name: str
    group: str = ""


@dataclass
class KeywordGrouping:
    """Grouped keywords by category"""
    sta_keywords: Dict[str, Dict[str, Dict[str, Dict[str, List[STAKeyword]]]]]  # mode -> corner -> timing -> metric -> [keywords]
    violation_keywords: Dict[str, Dict[str, Dict[str, List[ViolationKeyword]]]]  # mode -> corner -> vtype -> [keywords]
    pv_keywords: Dict[str, List[PVKeyword]]  # category -> [keywords]
    vth_keywords: List[VTHKeyword]
    cell_usage_keywords: List[CellUsageKeyword]
    timing_keywords: List[GenericKeyword]  # APR timing (s_wns, h_tns, etc.)
    congestion_keywords: List[GenericKeyword]  # APR congestion
    generic_keywords: List[GenericKeyword]


class KeywordParser:
    """Parser for extracting structured information from keyword names"""

    def __init__(self):
        self.keyword_groups = {}  # YAML-defined groups

    @staticmethod
    def natural_sort_key(text: str):
        """Generate natural sort key for alphanumeric sorting"""
        def atoi(s):
            return int(s) if s.isdigit() else s.lower()
        return [atoi(c) for c in re.split(r'(\d+)', text)]

    def parse_keyword(self, keyword_name: str, value: Any) -> Optional[Any]:
        """
        Parse a keyword name and return structured representation.

        Args:
            keyword_name: Full keyword name (e.g., "misn_ff_0p99v_m40c_Cbest_s_wns_all")
            value: Keyword value (unused for parsing, but included for consistency)

        Returns:
            Parsed keyword object or None if not recognized
        """
        # Try PV keyword patterns first (DRC, LVS, PERC, FlipChip)
        pv_result = self._parse_pv_keyword(keyword_name)
        if pv_result:
            return pv_result

        # Try STA timing keyword pattern
        sta_result = self._parse_sta_keyword(keyword_name)
        if sta_result:
            return sta_result

        # Try violation keyword pattern
        violation_result = self._parse_violation_keyword(keyword_name)
        if violation_result:
            return violation_result

        # Try VTH keyword pattern
        vth_result = self._parse_vth_keyword(keyword_name)
        if vth_result:
            return vth_result

        # Try cell usage keyword pattern
        cell_usage_result = self._parse_cell_usage_keyword(keyword_name)
        if cell_usage_result:
            return cell_usage_result

        # Try APR timing/congestion patterns
        apr_result = self._parse_apr_keyword(keyword_name)
        if apr_result:
            return apr_result

        # Fallback: generic keyword
        return GenericKeyword(original_name=keyword_name, name=keyword_name)

    def _parse_pv_keyword(self, keyword_name: str) -> Optional[PVKeyword]:
        """
        Parse PV keyword names (DRC, LVS, PERC, FlipChip).

        Patterns:
        - drc_detailed_LUP.2_cell
        - drc_detailed_LUP.2_flatten
        - perc_detailed_ESD.43gu_cell
        - perc_detailed_ESD.43gu_flatten
        - flipchip_detailed_FC.1_cell
        - flipchip_detailed_FC.1_flatten
        - lvs (no cell/flatten)
        """
        # Pattern: {category}_detailed_{rule}_{check_type}
        # or: {category}_{rule}_{check_type}
        # or: {category} (simple)

        # Check for common PV prefixes
        pv_categories = {
            'drc': 'DRC',
            'perc': 'PERC',
            'flipchip': 'FlipChip',
            'lvs': 'LVS'
        }

        for prefix, category in pv_categories.items():
            if keyword_name.startswith(prefix):
                # Extract check_type if present (_cell or _flatten)
                check_type = ""
                base_name = keyword_name

                if keyword_name.endswith('_cell'):
                    check_type = 'cell'
                    base_name = keyword_name[:-5]  # Remove '_cell'
                elif keyword_name.endswith('_flatten'):
                    check_type = 'flatten'
                    base_name = keyword_name[:-8]  # Remove '_flatten'

                # Extract rule name
                # Pattern: {prefix}_detailed_{rule} or {prefix}_{subtype}_detailed_{rule} or {prefix}_{rule}
                parts = base_name.split('_')

                # Find 'detailed' keyword in parts
                detailed_idx = -1
                for i, part in enumerate(parts):
                    if part == 'detailed':
                        detailed_idx = i
                        break

                if detailed_idx >= 0 and len(parts) > detailed_idx + 1:
                    # Format: drc_detailed_LUP.2 or perc_ldl_detailed_LUP.2
                    # Rule is everything after 'detailed'
                    rule = '_'.join(parts[detailed_idx + 1:])
                elif len(parts) >= 2:
                    # Format: drc_LUP.2 or just lvs (no 'detailed' keyword)
                    rule = '_'.join(parts[1:]) if len(parts) > 1 else ''
                else:
                    rule = ''

                return PVKeyword(
                    original_name=keyword_name,
                    name=base_name,
                    category=category,
                    rule=rule,
                    check_type=check_type
                )

        return None

    def _parse_sta_keyword(self, keyword_name: str) -> Optional[STAKeyword]:
        """
        Parse STA timing keyword.

        Pattern: {mode}_{corner}_s|h_wns|tns|num_{path_type}
        Example: misn_ff_0p99v_m40c_Cbest_s_wns_all
        """
        # Pattern for STA keywords
        # Look for _s_wns_, _s_tns_, _s_num_, _h_wns_, _h_tns_, _h_num_
        sta_patterns = [
            r'(.+)_([^_]+)_(s|h)_(wns|tns|num)_(.+)',  # Standard pattern
        ]

        for pattern in sta_patterns:
            match = re.match(pattern, keyword_name)
            if match:
                mode_corner_part = match.group(1) + '_' + match.group(2)
                timing_type = match.group(3)
                metric = match.group(4)
                path_type = match.group(5)

                # Try to extract mode and corner from mode_corner_part
                # Pattern: {mode}_{corner}
                # Corner can have underscores (e.g., ff_0p99v_m40c_Cbest)
                parts = mode_corner_part.split('_')
                if len(parts) >= 2:
                    mode = parts[0]
                    corner = '_'.join(parts[1:])
                else:
                    mode = mode_corner_part
                    corner = ''

                return STAKeyword(
                    original_name=keyword_name,
                    name=keyword_name,
                    mode=mode,
                    corner=corner,
                    timing_type=timing_type,
                    metric=metric,
                    path_type=path_type
                )

        return None

    def _parse_violation_keyword(self, keyword_name: str) -> Optional[ViolationKeyword]:
        """
        Parse violation keyword (max_tran, max_cap, noise).

        Patterns:
        - {mode}_{corner}_max_tran_num
        - {mode}_{corner}_max_tran_worst
        - {mode}_{corner}_max_cap_num
        - {mode}_{corner}_max_cap_worst
        - {mode}_{corner}_noise_above_low_num
        - {mode}_{corner}_noise_above_low_worst
        - {mode}_{corner}_noise_below_high_num
        - {mode}_{corner}_noise_below_high_worst
        """
        # Check for violation patterns
        violation_patterns = [
            (r'(.+)_([^_]+)_max_tran_(num|worst)', 'max_tran', ''),
            (r'(.+)_([^_]+)_max_cap_(num|worst)', 'max_cap', ''),
            (r'(.+)_([^_]+)_noise_above_low_(num|worst)', 'noise', 'above_low'),
            (r'(.+)_([^_]+)_noise_below_high_(num|worst)', 'noise', 'below_high'),
        ]

        for pattern, vtype, sub_type in violation_patterns:
            match = re.match(pattern, keyword_name)
            if match:
                mode_corner_part = match.group(1) + '_' + match.group(2)
                metric = match.group(3)

                # Extract mode and corner
                parts = mode_corner_part.split('_')
                if len(parts) >= 2:
                    mode = parts[0]
                    corner = '_'.join(parts[1:])
                else:
                    mode = mode_corner_part
                    corner = ''

                return ViolationKeyword(
                    original_name=keyword_name,
                    name=keyword_name,
                    mode=mode,
                    corner=corner,
                    violation_type=vtype,
                    metric=metric,
                    sub_type=sub_type
                )

        return None

    def _parse_vth_keyword(self, keyword_name: str) -> Optional[VTHKeyword]:
        """Parse VTH ratio keyword (HVth, RVth, LVth, ULVth)"""
        vth_names = ['HVth', 'RVth', 'LVth', 'ULVth']
        if keyword_name in vth_names:
            return VTHKeyword(original_name=keyword_name, name=keyword_name)
        return None

    def _parse_cell_usage_keyword(self, keyword_name: str) -> Optional[CellUsageKeyword]:
        """
        Parse cell usage keyword.

        Patterns:
        - std_cell_inst, std_cell_area
        - comb_cell_inst, comb_cell_area
        - flip_flop_inst, flip_flop_area
        - etc.
        """
        # Pattern: {cell_type}_inst or {cell_type}_area
        if keyword_name.endswith('_inst') or keyword_name.endswith('_area'):
            metric = 'inst' if keyword_name.endswith('_inst') else 'area'
            cell_type = keyword_name[:-5] if metric == 'inst' else keyword_name[:-5]

            # Check if it's a recognized cell type
            recognized_types = [
                'std_cell', 'comb_cell', 'flip_flop', 'latch', 'icg',
                'pad', 'memory', 'ip', 'total'
            ]

            if cell_type in recognized_types:
                return CellUsageKeyword(
                    original_name=keyword_name,
                    name=keyword_name,
                    cell_type=cell_type,
                    metric=metric
                )

        return None

    def _parse_apr_keyword(self, keyword_name: str) -> Optional[GenericKeyword]:
        """Parse APR timing/congestion keywords"""
        # APR timing: s_wns, s_tns, h_wns, h_tns, etc. (simple patterns)
        if re.match(r'^[sh]_(wns|tns|nov)(_\w+)?$', keyword_name):
            return GenericKeyword(original_name=keyword_name, name=keyword_name, group='timing')

        # APR congestion: hotspot, overflow, utilization, etc.
        congestion_keywords = ['hotspot', 'overflow', 'utilization', 'density']
        for cong_kw in congestion_keywords:
            if keyword_name.startswith(cong_kw):
                return GenericKeyword(original_name=keyword_name, name=keyword_name, group='congestion')

        return None

    def group_keywords(self, keyword_names: List[str], keyword_groups: Dict[str, List[str]] = None) -> KeywordGrouping:
        """
        Group a list of keyword names into structured categories.

        Args:
            keyword_names: List of keyword name strings
            keyword_groups: Optional YAML-defined keyword groups

        Returns:
            KeywordGrouping with categorized keywords
        """
        grouping = KeywordGrouping(
            sta_keywords={},
            violation_keywords={},
            pv_keywords={},
            vth_keywords=[],
            cell_usage_keywords=[],
            timing_keywords=[],
            congestion_keywords=[],
            generic_keywords=[]
        )

        for kw_name in keyword_names:
            parsed = self.parse_keyword(kw_name, None)

            if isinstance(parsed, STAKeyword):
                # Group by mode -> corner -> timing -> metric
                mode = parsed.mode
                corner = parsed.corner
                timing = parsed.timing_type
                metric = parsed.metric

                if mode not in grouping.sta_keywords:
                    grouping.sta_keywords[mode] = {}
                if corner not in grouping.sta_keywords[mode]:
                    grouping.sta_keywords[mode][corner] = {}
                if timing not in grouping.sta_keywords[mode][corner]:
                    grouping.sta_keywords[mode][corner][timing] = {}
                if metric not in grouping.sta_keywords[mode][corner][timing]:
                    grouping.sta_keywords[mode][corner][timing][metric] = []

                grouping.sta_keywords[mode][corner][timing][metric].append(parsed)

            elif isinstance(parsed, ViolationKeyword):
                # Group by mode -> corner -> violation_type
                mode = parsed.mode
                corner = parsed.corner
                vtype = parsed.violation_type

                if mode not in grouping.violation_keywords:
                    grouping.violation_keywords[mode] = {}
                if corner not in grouping.violation_keywords[mode]:
                    grouping.violation_keywords[mode][corner] = {}
                if vtype not in grouping.violation_keywords[mode][corner]:
                    grouping.violation_keywords[mode][corner][vtype] = []

                grouping.violation_keywords[mode][corner][vtype].append(parsed)

            elif isinstance(parsed, PVKeyword):
                # Group by category
                category = parsed.category
                if category not in grouping.pv_keywords:
                    grouping.pv_keywords[category] = []
                grouping.pv_keywords[category].append(parsed)

            elif isinstance(parsed, VTHKeyword):
                grouping.vth_keywords.append(parsed)

            elif isinstance(parsed, CellUsageKeyword):
                grouping.cell_usage_keywords.append(parsed)

            elif isinstance(parsed, GenericKeyword):
                if parsed.group == 'timing':
                    grouping.timing_keywords.append(parsed)
                elif parsed.group == 'congestion':
                    grouping.congestion_keywords.append(parsed)
                else:
                    grouping.generic_keywords.append(parsed)

        return grouping
