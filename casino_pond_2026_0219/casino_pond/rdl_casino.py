#!/usr/local/bin/python3.12

import sys
import re
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QPlainTextEdit, QGraphicsView, QGraphicsScene,
    QGraphicsPolygonItem, QMessageBox, QTableWidget, QTableWidgetItem,
    QSplitter, QLabel, QTabWidget, QGraphicsTextItem, QLineEdit
)
from PyQt5.QtGui import QPolygonF, QPen, QBrush, QColor, QPainter, QFont
from PyQt5.QtCore import QPointF, Qt

# Import Shapely geometry for union & intersection analysis
try:
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False

class OptimizedPolyAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optimized Polygon Analyzer - Area & Overlap Calculator")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize data storage
        self.pattern1_polys = []
        self.pattern2_polys = []
        self.overlap_data = {}
        
        # Initialize user-provided widths
        self.pattern1_width = 0.0
        self.pattern2_width = 0.0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface with tabs for input and comparison"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Input tab
        input_tab = self.create_input_tab()
        tab_widget.addTab(input_tab, "Input Patterns")
        
        # Analysis tab
        analysis_tab = self.create_analysis_tab()
        tab_widget.addTab(analysis_tab, "Analysis & Comparison")
        
    def create_input_tab(self):
        """Create the input tab with two pattern inputs"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Pattern A input
        pattern1_label = QLabel("Pattern A:")
        pattern1_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(pattern1_label)
        
        self.pattern1_input = QPlainTextEdit()
        self.pattern1_input.setPlaceholderText(
            "Paste Pattern A polyPts here, e.g. {{x1 y1} {x2 y2} ...} {{...}} ..."
        )
        self.pattern1_input.setMaximumHeight(150)
        layout.addWidget(self.pattern1_input)
        
        # Pattern A width input
        width1_layout = QHBoxLayout()
        width1_label = QLabel("Pattern A Width (um):")
        width1_label.setStyleSheet("font-weight: bold;")
        width1_layout.addWidget(width1_label)
        
        self.pattern1_width_input = QLineEdit()
        self.pattern1_width_input.setPlaceholderText("Enter width for Pattern A")
        self.pattern1_width_input.setMaximumWidth(200)
        width1_layout.addWidget(self.pattern1_width_input)
        width1_layout.addStretch()
        layout.addLayout(width1_layout)
        
        # Pattern B input
        pattern2_label = QLabel("Pattern B:")
        pattern2_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(pattern2_label)
        
        self.pattern2_input = QPlainTextEdit()
        self.pattern2_input.setPlaceholderText(
            "Paste Pattern B polyPts here, e.g. {{x1 y1} {x2 y2} ...} {{...}} ..."
        )
        self.pattern2_input.setMaximumHeight(150)
        layout.addWidget(self.pattern2_input)
        
        # Pattern B width input
        width2_layout = QHBoxLayout()
        width2_label = QLabel("Pattern B Width (um):")
        width2_label.setStyleSheet("font-weight: bold;")
        width2_layout.addWidget(width2_label)
        
        self.pattern2_width_input = QLineEdit()
        self.pattern2_width_input.setPlaceholderText("Enter width for Pattern B")
        self.pattern2_width_input.setMaximumWidth(200)
        width2_layout.addWidget(self.pattern2_width_input)
        width2_layout.addStretch()
        layout.addLayout(width2_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("Analyze Patterns")
        self.analyze_btn.clicked.connect(self.analyze_patterns)
        btn_layout.addWidget(self.analyze_btn)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_all)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addLayout(btn_layout)
        
        return widget
        
    def create_analysis_tab(self):
        """Create the analysis tab with visualization and comparison table"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Splitter for visualization and table
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Visualization area
        viz_widget = QWidget()
        viz_layout = QVBoxLayout(viz_widget)
        
        viz_label = QLabel("Visualization (Polygons numbered PA-1, PA-2, etc. and PB-1, PB-2, etc.):")
        viz_label.setStyleSheet("font-weight: bold;")
        viz_layout.addWidget(viz_label)
        
        # Add flip buttons
        flip_btn_layout = QHBoxLayout()
        self.x_flip_btn = QPushButton("Flip X")
        self.x_flip_btn.clicked.connect(self.flip_x)
        flip_btn_layout.addWidget(self.x_flip_btn)
        
        self.y_flip_btn = QPushButton("Flip Y")
        self.y_flip_btn.clicked.connect(self.flip_y)
        flip_btn_layout.addWidget(self.y_flip_btn)
        
        viz_layout.addLayout(flip_btn_layout)
        
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        viz_layout.addWidget(self.view)
        
        splitter.addWidget(viz_widget)
        
        # Comparison table
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        table_label = QLabel("Detailed Comparison Table:")
        table_label.setStyleSheet("font-weight: bold;")
        table_layout.addWidget(table_label)
        
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(6)
        self.comparison_table.setHorizontalHeaderLabels([
            "Metric", "Pattern A", "Pattern B", "Difference", "Overlap", "Notes"
        ])
        
        # Add polygon details table
        polygon_label = QLabel("Individual Polygon Details:")
        polygon_label.setStyleSheet("font-weight: bold;")
        table_layout.addWidget(polygon_label)
        
        self.polygon_table = QTableWidget()
        self.polygon_table.setColumnCount(11)
        self.polygon_table.setHorizontalHeaderLabels([
            "Pattern", "Polygon #", "Individual Area (um²)", "Overlap Depth", "Overlaps With", 
            "Overlap Area (um²)", "Net Area (um²)", "Raw Ratio %", "Net Ratio %", "Efficiency %", "Status"
        ])
        table_layout.addWidget(self.polygon_table)
        
        # Add calculation details area
        calc_label = QLabel("Area Calculation Details:")
        calc_label.setStyleSheet("font-weight: bold;")
        table_layout.addWidget(calc_label)
        
        self.calc_details = QPlainTextEdit()
        self.calc_details.setMaximumHeight(150)
        self.calc_details.setReadOnly(True)
        table_layout.addWidget(self.calc_details)
        table_layout.addWidget(self.comparison_table)
        
        splitter.addWidget(table_widget)
        
        # Set splitter proportions - make table wider (70% table, 30% visualization)
        splitter.setSizes([300, 700])
        
        return widget
        
    def parse_polys(self, text):
        """Parse polygon coordinates from text input"""
        if not text.strip():
            return []
            
        pattern = re.compile(r"\{(?:\s*\{[^\}]+\})+\s*\}")
        polys = []
        for m in pattern.finditer(text):
            coords = re.findall(r"\{\s*([+-]?\d+\.?\d*)\s+([+-]?\d+\.?\d*)\s*\}", m.group(0))
            pts = [(float(x), float(y)) for x, y in coords]
            if len(pts) >= 3:  # Minimum 3 points for a polygon
                polys.append(pts)
        return polys
        
    def calculate_overlap_depth(self, polygons):
        """Calculate overlap depth and overlap area for each polygon using set operations (union of all overlaps)"""
        if not SHAPELY_AVAILABLE or not polygons:
            return {}, {}, {}

        shapely_polys = [Polygon(poly) for poly in polygons]
        overlap_depth = {}
        overlap_details = {}
        overlap_areas = {}

        is_rectangle = [len(poly) == 4 for poly in polygons]

        for i, poly1 in enumerate(shapely_polys):
            depth = 1
            overlaps_with = []
            overlap_geoms = []

            for j, poly2 in enumerate(shapely_polys):
                if i == j:
                    continue
                if poly1.intersects(poly2):
                    intersection = poly1.intersection(poly2)
                    if not intersection.is_empty and intersection.area > 0:
                        depth += 1
                        overlaps_with.append(j)
                        # Smart overlap logic for who "wins" the overlap
                        if is_rectangle[i] and not is_rectangle[j]:
                            # Rectangle keeps its area, complex loses overlap
                            continue
                        elif not is_rectangle[i] and is_rectangle[j]:
                            # Complex loses overlap area
                            overlap_geoms.append(intersection)
                        elif is_rectangle[i] and is_rectangle[j]:
                            area_i = poly1.area
                            area_j = poly2.area
                            if area_i >= area_j:
                                continue  # Larger rectangle keeps area
                            else:
                                overlap_geoms.append(intersection)
                        else:
                            # Both complex, share overlap equally (add half area)
                            # For set-union, just add the intersection, then divide by 2 below
                            overlap_geoms.append(intersection)
            # Union all overlap geometries for this polygon
            if overlap_geoms:
                overlap_union = unary_union(overlap_geoms)
                overlap_area = overlap_union.area
                # If both are complex, divide by 2 (as before)
                if not is_rectangle[i]:
                    overlap_area = overlap_area / 2
            else:
                overlap_area = 0.0
            overlap_depth[i] = depth
            overlap_details[i] = overlaps_with
            overlap_areas[i] = overlap_area
        return overlap_depth, overlap_details, overlap_areas
        
    def calculate_non_overlapping_area(self, polygons):
        """Calculate total area avoiding overlaps"""
        if not SHAPELY_AVAILABLE or not polygons:
            return 0.0
            
        # Convert to Shapely polygons
        shapely_polys = [Polygon(poly) for poly in polygons]
        
        # Use unary_union to merge overlapping areas
        merged = unary_union(shapely_polys)
        
        # Calculate total area
        if hasattr(merged, 'area'):
            return merged.area
        else:
            # If merged is a collection, sum all areas
            try:
                from shapely.geometry import GeometryCollection
                if isinstance(merged, GeometryCollection):
                    return sum(geom.area for geom in merged.geoms)
                else:
                    return merged.area
            except (ImportError, AttributeError):
                return merged.area if hasattr(merged, 'area') else 0.0
            
    def calculate_individual_areas(self, polygons):
        """Calculate individual polygon areas with detailed formulas"""
        if not SHAPELY_AVAILABLE or not polygons:
            return [], []
            
        areas = []
        formulas = []
        for poly in polygons:
            shapely_poly = Polygon(poly)
            area = shapely_poly.area
            
            # Generate calculation formula
            if len(poly) == 3:  # Triangle
                # Calculate using shoelace formula
                x_coords = [p[0] for p in poly]
                y_coords = [p[1] for p in poly]
                formula = self.calculate_triangle_formula(x_coords, y_coords)
            elif len(poly) == 4:  # Rectangle/Quadrilateral
                formula = self.calculate_rectangle_formula(poly)
            else:  # Complex polygon
                formula = self.calculate_complex_polygon_formula(poly)
            
            areas.append(area)
            formulas.append(formula)
        return areas, formulas
        
    def calculate_triangle_formula(self, x_coords, y_coords):
        """Calculate triangle area formula using shoelace formula"""
        # Shoelace formula: A = 1/2 |x1y2 + x2y3 + x3y1 - x1y3 - x2y1 - x3y2|
        x1, x2, x3 = x_coords
        y1, y2, y3 = y_coords
        
        # Calculate individual terms
        term1 = x1 * y2
        term2 = x2 * y3
        term3 = x3 * y1
        term4 = x1 * y3
        term5 = x2 * y1
        term6 = x3 * y2
        
        # Calculate area
        area = abs(term1 + term2 + term3 - term4 - term5 - term6) / 2
        
        formula = f"Triangle: A = 1/2 |{x1}×{y2} + {x2}×{y3} + {x3}×{y1} - {x1}×{y3} - {x2}×{y1} - {x3}×{y2}| = 1/2 |{term1} + {term2} + {term3} - {term4} - {term5} - {term6}| = 1/2 × {abs(term1 + term2 + term3 - term4 - term5 - term6)} = {area:.3f} um²"
        return formula
        
    def calculate_rectangle_formula(self, poly):
        """Calculate rectangle area formula"""
        x_coords = [p[0] for p in poly]
        y_coords = [p[1] for p in poly]
        
        # Check if it's a rectangle (opposite sides parallel)
        width = max(x_coords) - min(x_coords)
        height = max(y_coords) - min(y_coords)
        
        # Use shoelace formula for accuracy
        area = abs(sum(x_coords[i] * y_coords[(i+1) % 4] for i in range(4)) - 
                  sum(y_coords[i] * x_coords[(i+1) % 4] for i in range(4))) / 2
        
        formula = f"Rectangle: A = width × height = {width:.3f} × {height:.3f} = {area:.3f} um²"
        return formula
        
    def calculate_complex_polygon_formula(self, poly):
        """Calculate complex polygon area formula using shoelace formula"""
        n = len(poly)
        x_coords = [p[0] for p in poly]
        y_coords = [p[1] for p in poly]
        
        # Shoelace formula for n-sided polygon
        area = abs(sum(x_coords[i] * y_coords[(i+1) % n] for i in range(n)) - 
                  sum(y_coords[i] * x_coords[(i+1) % n] for i in range(n))) / 2
        
        # Show first few terms for readability
        if n <= 6:
            terms = []
            for i in range(n):
                terms.append(f"{x_coords[i]}×{y_coords[(i+1) % n]}")
            formula = f"Polygon({n}-sided): A = 1/2 |{' + '.join(terms)} - ...| = {area:.3f} um²"
        else:
            formula = f"Polygon({n}-sided): A = 1/2 |Shoelace formula| = {area:.3f} um²"
        
        return formula
        
    def get_color_by_depth(self, depth):
        """Get color based on overlap depth"""
        # Color gradient from light blue to dark red
        colors = [
            QColor(173, 216, 230),  # Light blue (depth 1)
            QColor(135, 206, 235),  # Sky blue (depth 2)
            QColor(100, 149, 237),  # Cornflower blue (depth 3)
            QColor(255, 165, 0),    # Orange (depth 4)
            QColor(255, 69, 0),     # Red-orange (depth 5)
            QColor(139, 0, 0),      # Dark red (depth 6+)
        ]
        
        depth_index = min(depth - 1, len(colors) - 1)
        return colors[depth_index]
        
    def analyze_patterns(self):
        """Analyze both patterns and update visualization and comparison table"""
        if not SHAPELY_AVAILABLE:
            QMessageBox.critical(
                self,
                "Dependency Error",
                "Shapely is not installed.\nPlease install it with:\n  pip install shapely"
            )
            return
            
        # Parse both patterns
        self.pattern1_polys = self.parse_polys(self.pattern1_input.toPlainText())
        self.pattern2_polys = self.parse_polys(self.pattern2_input.toPlainText())
        
        if not self.pattern1_polys and not self.pattern2_polys:
            QMessageBox.warning(self, "Input Error", "No valid polygons found in either pattern.")
            return
            
        # Read user-provided widths
        try:
            self.pattern1_width = float(self.pattern1_width_input.text()) if self.pattern1_width_input.text().strip() else 0.0
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Invalid width value for Pattern A. Please enter a valid number.")
            return
            
        try:
            self.pattern2_width = float(self.pattern2_width_input.text()) if self.pattern2_width_input.text().strip() else 0.0
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Invalid width value for Pattern B. Please enter a valid number.")
            return
            
        # Calculate metrics
        self.calculate_metrics()
        
        # Update visualization
        self.update_visualization()
        
        # Update comparison table
        self.update_comparison_table()
        
        # Switch to Analysis & Comparison tab
        tab_widget = self.centralWidget().findChild(QTabWidget)
        if tab_widget:
            tab_widget.setCurrentIndex(1)  # Switch to the second tab (Analysis & Comparison)
        
    def calculate_metrics(self):
        """Calculate all metrics for both patterns"""
        # Pattern 1 metrics
        self.pattern1_individual_areas, self.pattern1_formulas = self.calculate_individual_areas(self.pattern1_polys)
        self.pattern1_total_area = self.calculate_non_overlapping_area(self.pattern1_polys)
        self.pattern1_overlap_depth, self.pattern1_overlap_details, self.pattern1_overlap_areas = self.calculate_overlap_depth(self.pattern1_polys)
        
        # Pattern 2 metrics
        self.pattern2_individual_areas, self.pattern2_formulas = self.calculate_individual_areas(self.pattern2_polys)
        self.pattern2_total_area = self.calculate_non_overlapping_area(self.pattern2_polys)
        self.pattern2_overlap_depth, self.pattern2_overlap_details, self.pattern2_overlap_areas = self.calculate_overlap_depth(self.pattern2_polys)
        
        # Combined analysis
        all_polys = self.pattern1_polys + self.pattern2_polys
        self.combined_total_area = self.calculate_non_overlapping_area(all_polys)
        
        # Calculate overlap between patterns
        self.pattern_overlap = self.calculate_pattern_overlap()
        
    def calculate_pattern_overlap(self):
        """Calculate overlap between the two patterns"""
        if not self.pattern1_polys or not self.pattern2_polys:
            return 0.0
            
        if not SHAPELY_AVAILABLE:
            return 0.0
            
        # Create union of each pattern
        pattern1_union = unary_union([Polygon(poly) for poly in self.pattern1_polys])
        pattern2_union = unary_union([Polygon(poly) for poly in self.pattern2_polys])
        
        # Calculate intersection
        if pattern1_union.intersects(pattern2_union):
            intersection = pattern1_union.intersection(pattern2_union)
            return intersection.area
        return 0.0
        
    def flip_x(self):
        """Flip the visualization horizontally around the center of all polygons"""
        if self.scene.items():
            # Calculate the center of all polygons
            all_points = []
            for item in self.scene.items():
                if isinstance(item, QGraphicsPolygonItem):
                    polygon = item.polygon()
                    for i in range(polygon.size()):
                        all_points.append(polygon.at(i))
            
            if not all_points:
                return
                
            # Calculate center
            center_x = sum(point.x() for point in all_points) / len(all_points)
            center_y = sum(point.y() for point in all_points) / len(all_points)
            
            # Store text items and their associated polygons
            text_items = []
            for item in self.scene.items():
                if isinstance(item, QGraphicsTextItem):
                    text_items.append(item)
            
            # Flip each polygon around the center
            for item in self.scene.items():
                if isinstance(item, QGraphicsPolygonItem):
                    polygon = item.polygon()
                    flipped_polygon = QPolygonF()
                    for i in range(polygon.size()):
                        point = polygon.at(i)
                        # Flip around center: new_x = center_x - (point.x() - center_x) = 2*center_x - point.x()
                        new_x = 2 * center_x - point.x()
                        new_y = point.y()
                        flipped_polygon.append(QPointF(new_x, new_y))
                    item.setPolygon(flipped_polygon)
            
            # Remove old text items
            for text_item in text_items:
                self.scene.removeItem(text_item)
            
            # Recalculate and add text items at new polygon centers
            self.recalculate_text_positions()
            
            # Reset view transform
            self.view.resetTransform()
            if self.scene.items():
                self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            
    def flip_y(self):
        """Flip the visualization vertically around the center of all polygons"""
        if self.scene.items():
            # Calculate the center of all polygons
            all_points = []
            for item in self.scene.items():
                if isinstance(item, QGraphicsPolygonItem):
                    polygon = item.polygon()
                    for i in range(polygon.size()):
                        all_points.append(polygon.at(i))
            
            if not all_points:
                return
                
            # Calculate center
            center_x = sum(point.x() for point in all_points) / len(all_points)
            center_y = sum(point.y() for point in all_points) / len(all_points)
            
            # Store text items and their associated polygons
            text_items = []
            for item in self.scene.items():
                if isinstance(item, QGraphicsTextItem):
                    text_items.append(item)
            
            # Flip each polygon around the center
            for item in self.scene.items():
                if isinstance(item, QGraphicsPolygonItem):
                    polygon = item.polygon()
                    flipped_polygon = QPolygonF()
                    for i in range(polygon.size()):
                        point = polygon.at(i)
                        # Flip around center: new_y = center_y - (point.y() - center_y) = 2*center_y - point.y()
                        new_x = point.x()
                        new_y = 2 * center_y - point.y()
                        flipped_polygon.append(QPointF(new_x, new_y))
                    item.setPolygon(flipped_polygon)
            
            # Remove old text items
            for text_item in text_items:
                self.scene.removeItem(text_item)
            
            # Recalculate and add text items at new polygon centers
            self.recalculate_text_positions()
            
            # Reset view transform
            self.view.resetTransform()
            if self.scene.items():
                self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
                
    def recalculate_text_positions(self):
        """Recalculate text positions based on current polygon centroids"""
        # Find all polygons and their associated text labels
        polygon_text_map = {}
        
        # First pass: collect all text items and their labels
        for item in self.scene.items():
            if isinstance(item, QGraphicsTextItem):
                text = item.toPlainText()
                # Extract pattern and number from text (e.g., "PA-1", "PB-3")
                if "-" in text:
                    pattern_part, number_part = text.split("-", 1)
                    try:
                        number = int(number_part)
                        if pattern_part == "PA":
                            pattern = "A"
                            index = number - 1
                        elif pattern_part == "PB":
                            pattern = "B"
                            index = number - 1
                        else:
                            continue
                        polygon_text_map[(pattern, index)] = text
                    except ValueError:
                        continue
        
        # Second pass: find polygons and add text at their centroids
        pattern_a_count = 0
        pattern_b_count = 0
        
        for item in self.scene.items():
            if isinstance(item, QGraphicsPolygonItem):
                polygon = item.polygon()
                if polygon.size() < 3:
                    continue
                
                # Calculate centroid
                x_coords = [polygon.at(i).x() for i in range(polygon.size())]
                y_coords = [polygon.at(i).y() for i in range(polygon.size())]
                centroid_x = sum(x_coords) / len(x_coords)
                centroid_y = sum(y_coords) / len(y_coords)
                
                # Determine pattern based on pen style (solid = Pattern A, dashed = Pattern B)
                pen = item.pen()
                if pen.style() == Qt.SolidLine:
                    pattern = "A"
                    pattern_a_count += 1
                    index = pattern_a_count - 1
                    prefix = "PA"
                    text_color = QColor(0, 0, 128)  # Deep navy
                else:  # Qt.DashLine
                    pattern = "B"
                    pattern_b_count += 1
                    index = pattern_b_count - 1
                    prefix = "PB"
                    text_color = QColor(0, 0, 128)  # Deep navy
                
                # Create text item at new centroid
                text_item = QGraphicsTextItem(f"{prefix}-{index + 1}")
                text_item.setDefaultTextColor(text_color)
                
                # Set font
                font = QFont()
                font.setBold(True)
                font.setPointSize(10)
                text_item.setFont(font)
                
                # Position text at centroid
                text_item.setPos(centroid_x - text_item.boundingRect().width() / 2,
                                centroid_y - text_item.boundingRect().height() / 2)
                
                text_item.setZValue(1000)  # Ensure text is on top
                self.scene.addItem(text_item)
        
    def update_visualization(self):
        """Update the visualization with both patterns and overlap coloring"""
        self.scene.clear()

        # Pattern A
        if self.pattern1_polys:
            poly_info = []
            for i, poly in enumerate(self.pattern1_polys):
                shapely_poly = Polygon(poly)
                area = shapely_poly.area
                is_rect = len(poly) == 4
                poly_info.append((not is_rect, area, i, poly))  # not is_rect: complex first (True), then area
            poly_info.sort()

            print("Pattern A drawing order (bottom to top):")
            for order, (is_complex, area, i, poly) in enumerate(reversed(poly_info)):
                print(f"{order+1}: {'Complex' if is_complex else 'Rectangle'} PA-{i+1} Area={area:.3f}")

            for is_complex, area, i, poly in reversed(poly_info):
                qpoints = [QPointF(x, y) for x, y in poly]
                item = QGraphicsPolygonItem(QPolygonF(qpoints))
                depth = self.pattern1_overlap_depth.get(i, 1)
                color = self.get_color_by_depth(depth)
                
                # Use faded color for overlapped lines
                if depth > 1:
                    pen = QPen(QColor(128, 128, 128), 1.0)  # Faded gray for overlapped lines
                else:
                    pen = QPen(QColor(0, 0, 0), 1.0)  # Solid black for non-overlapped lines
                    
                brush = QBrush(color)
                item.setPen(pen)
                item.setBrush(brush)
                self.scene.addItem(item)
                self.add_polygon_label(i + 1, poly, "PA", QColor(0, 0, 0))

        # Pattern B (same logic)
        if self.pattern2_polys:
            poly_info = []
            for i, poly in enumerate(self.pattern2_polys):
                shapely_poly = Polygon(poly)
                area = shapely_poly.area
                is_rect = len(poly) == 4
                poly_info.append((not is_rect, area, i, poly))
            poly_info.sort()

            print("Pattern B drawing order (bottom to top):")
            for order, (is_complex, area, i, poly) in enumerate(reversed(poly_info)):
                print(f"{order+1}: {'Complex' if is_complex else 'Rectangle'} PB-{i+1} Area={area:.3f}")

            for is_complex, area, i, poly in reversed(poly_info):
                qpoints = [QPointF(x, y) for x, y in poly]
                item = QGraphicsPolygonItem(QPolygonF(qpoints))
                depth = self.pattern2_overlap_depth.get(i, 1)
                color = self.get_color_by_depth(depth)
                
                # Use faded color for overlapped lines
                if depth > 1:
                    pen = QPen(QColor(128, 128, 128), 1.0, Qt.DashLine)  # Faded gray dashed for overlapped lines
                else:
                    pen = QPen(QColor(0, 0, 0), 1.0, Qt.DashLine)  # Solid black dashed for non-overlapped lines
                    
                brush = QBrush(color)
                item.setPen(pen)
                item.setBrush(brush)
                self.scene.addItem(item)
                self.add_polygon_label(i + 1, poly, "PB", QColor(128, 0, 128))  # Purple for PB

        if self.scene.items():
            self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            
    def add_polygon_label(self, polygon_number, poly_coords, pattern_prefix, text_color):
        """Add a numbered label to a polygon"""
        # Calculate centroid of the polygon
        if len(poly_coords) < 3:
            return
            
        # Simple centroid calculation
        x_coords = [p[0] for p in poly_coords]
        y_coords = [p[1] for p in poly_coords]
        centroid_x = sum(x_coords) / len(x_coords)
        centroid_y = sum(y_coords) / len(y_coords)
        
        # Create text item
        text_item = QGraphicsTextItem(f"{pattern_prefix}-{polygon_number}")
        text_item.setDefaultTextColor(QColor(0, 0, 128))  # Deep navy color
        
        # Set font
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        text_item.setFont(font)
        
        # Position text at centroid
        text_item.setPos(centroid_x - text_item.boundingRect().width() / 2,
                        centroid_y - text_item.boundingRect().height() / 2)
        
        # Add background for better visibility
        text_item.setZValue(1000)  # Ensure text is on top
        
        self.scene.addItem(text_item)
            
    def update_comparison_table(self):
        """Update the detailed comparison table"""
        self.comparison_table.setRowCount(0)
        
        # Calculate RDL widths
        rdl_width1 = self.pattern1_width if self.pattern1_width > 0 else self.calculate_rdl_width(self.pattern1_polys)
        rdl_width2 = self.pattern2_width if self.pattern2_width > 0 else self.calculate_rdl_width(self.pattern2_polys)
        
        # Calculate difference length based on area
        diff_length1 = self.calculate_difference_length(self.pattern1_total_area, rdl_width1) if rdl_width1 > 0 else 0
        diff_length2 = self.calculate_difference_length(self.pattern2_total_area, rdl_width2) if rdl_width2 > 0 else 0
        
        # Define metrics to compare
        metrics = [
            ("Number of Polygons", len(self.pattern1_polys), len(self.pattern2_polys)),
            ("Total Individual Area (um²)", sum(self.pattern1_individual_areas), sum(self.pattern2_individual_areas)),
            ("Non-Overlapping Area (um²)", self.pattern1_total_area, self.pattern2_total_area),
            ("RDL Width (um)", rdl_width1, rdl_width2),
            ("Difference Length (um)", diff_length1, diff_length2),
            ("Area Efficiency (%)", 
             (self.pattern1_total_area / sum(self.pattern1_individual_areas) * 100) if self.pattern1_individual_areas else 0,
             (self.pattern2_total_area / sum(self.pattern2_individual_areas) * 100) if self.pattern2_individual_areas else 0),
            ("Max Overlap Depth", max(self.pattern1_overlap_depth.values()) if self.pattern1_overlap_depth else 0,
             max(self.pattern2_overlap_depth.values()) if self.pattern2_overlap_depth else 0),
            ("Overlapping Polygons", 
             sum(1 for depth in self.pattern1_overlap_depth.values() if depth > 1),
             sum(1 for depth in self.pattern2_overlap_depth.values() if depth > 1)),
            ("Total Overlap Area (um²)", 
             sum(self.pattern1_individual_areas) - self.pattern1_total_area,
             sum(self.pattern2_individual_areas) - self.pattern2_total_area),
            ("Pattern Overlap Area (um²)", self.pattern_overlap, self.pattern_overlap),
            ("Combined Total Area (um²)", self.combined_total_area, self.combined_total_area)
        ]
        
        self.comparison_table.setRowCount(len(metrics))
        
        for row, (metric, val1, val2) in enumerate(metrics):
            # Metric name
            self.comparison_table.setItem(row, 0, QTableWidgetItem(metric))
            
            # Pattern A value
            val1_str = f"{val1:.3f}" if isinstance(val1, float) else str(val1)
            self.comparison_table.setItem(row, 1, QTableWidgetItem(val1_str))
            
            # Pattern B value
            val2_str = f"{val2:.3f}" if isinstance(val2, float) else str(val2)
            self.comparison_table.setItem(row, 2, QTableWidgetItem(val2_str))
            
            # Difference
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                diff = val1 - val2
                diff_str = f"{diff:.3f}" if isinstance(diff, float) else str(diff)
                diff_item = QTableWidgetItem(diff_str)
                
                # Color code the difference
                if diff > 0:
                    diff_item.setBackground(QColor(200, 255, 200))  # Light green
                elif diff < 0:
                    diff_item.setBackground(QColor(255, 200, 200))  # Light red
                    
                self.comparison_table.setItem(row, 3, diff_item)
            else:
                self.comparison_table.setItem(row, 3, QTableWidgetItem("N/A"))
                
            # Overlap info
            if "Overlap" in metric:
                overlap_info = f"Patterns overlap by {self.pattern_overlap:.3f} units²"
            elif "Depth" in metric:
                overlap_info = "Higher depth = more overlapping polygons"
            elif "RDL Width" in metric:
                overlap_info = "User-provided width of the RDL pattern"
            elif "Difference Length" in metric:
                overlap_info = "Length = Area / Width"
            else:
                overlap_info = ""
            self.comparison_table.setItem(row, 4, QTableWidgetItem(overlap_info))
            
            # Notes
            notes = ""
            if "Efficiency" in metric:
                notes = "Higher % = less overlap waste"
            elif "Combined" in metric:
                notes = "Total area when both patterns are used together"
            elif "RDL Width" in metric:
                notes = "User-provided width of the RDL pattern"
            elif "Difference Length" in metric:
                notes = "Calculated as Area / Width"
            self.comparison_table.setItem(row, 5, QTableWidgetItem(notes))
            
        # Resize columns to content
        self.comparison_table.resizeColumnsToContents()
        
        # Update polygon details table
        self.update_polygon_details_table()
        
        # Update calculation details
        self.update_calculation_details()
        
    def calculate_rdl_width(self, polygons):
        """Calculate the RDL width based on polygon dimensions"""
        if not polygons:
            return 0.0
            
        if not SHAPELY_AVAILABLE:
            return 0.0
            
        try:
            # Create Shapely polygons
            shapely_polys = [Polygon(poly) for poly in polygons]
            
            # Get the union of all polygons
            merged = unary_union(shapely_polys)
            
            # Get bounding box
            minx, miny, maxx, maxy = merged.bounds
            
            # Calculate width (horizontal span)
            width = maxx - minx
            
            return width
            
        except Exception as e:
            print(f"Error calculating RDL width: {e}")
            return 0.0
            
    def calculate_difference_length(self, area, width):
        """Calculate difference length based on area and width"""
        if width <= 0:
            return 0.0
            
        # Length = Area / Width
        length = area / width
        return length
        
    def update_polygon_details_table(self):
        """Update the individual polygon details table"""
        self.polygon_table.setRowCount(0)

        all_polygons = []

        # Calculate total net area for net ratio
        total_net_area_p1 = sum(
            area - self.pattern1_overlap_areas.get(i, 0.0)
            for i, area in enumerate(self.pattern1_individual_areas)
        )
        total_net_area_p2 = sum(
            area - self.pattern2_overlap_areas.get(i, 0.0)
            for i, area in enumerate(self.pattern2_individual_areas)
        )

        # Add Pattern 1 polygons
        for i, (area, depth, overlaps, overlap_area, formula) in enumerate(zip(
            self.pattern1_individual_areas,
            [self.pattern1_overlap_depth.get(i, 1) for i in range(len(self.pattern1_polys))],
            [self.pattern1_overlap_details.get(i, []) for i in range(len(self.pattern1_polys))],
            [self.pattern1_overlap_areas.get(i, 0.0) for i in range(len(self.pattern1_polys))],
            self.pattern1_formulas
        )):
            net_area = area - overlap_area
            total_pattern_area = sum(self.pattern1_individual_areas)
            raw_ratio = (area / total_pattern_area * 100) if total_pattern_area > 0 else 0
            net_ratio = (net_area / total_net_area_p1 * 100) if total_net_area_p1 > 0 else 0
            all_polygons.append({
                'pattern': 'Pattern A',
                'index': i + 1,
                'area': area,
                'depth': depth,
                'overlaps': overlaps,
                'overlap_area': overlap_area,
                'net_area': net_area,
                'raw_ratio': raw_ratio,
                'net_ratio': net_ratio,
                'efficiency': (net_area / self.pattern1_total_area * 100) if self.pattern1_total_area > 0 else 0,
                'status': 'Overlapping' if depth > 1 else 'Clean',
                'formula': formula
            })

        # Add Pattern 2 polygons
        for i, (area, depth, overlaps, overlap_area, formula) in enumerate(zip(
            self.pattern2_individual_areas,
            [self.pattern2_overlap_depth.get(i, 1) for i in range(len(self.pattern2_polys))],
            [self.pattern2_overlap_details.get(i, []) for i in range(len(self.pattern2_polys))],
            [self.pattern2_overlap_areas.get(i, 0.0) for i in range(len(self.pattern2_polys))],
            self.pattern2_formulas
        )):
            net_area = area - overlap_area
            total_pattern_area = sum(self.pattern2_individual_areas)
            raw_ratio = (area / total_pattern_area * 100) if total_pattern_area > 0 else 0
            net_ratio = (net_area / total_net_area_p2 * 100) if total_net_area_p2 > 0 else 0
            all_polygons.append({
                'pattern': 'Pattern B',
                'index': i + 1,
                'area': area,
                'depth': depth,
                'overlaps': overlaps,
                'overlap_area': overlap_area,
                'net_area': net_area,
                'raw_ratio': raw_ratio,
                'net_ratio': net_ratio,
                'efficiency': (net_area / self.pattern2_total_area * 100) if self.pattern2_total_area > 0 else 0,
                'status': 'Overlapping' if depth > 1 else 'Clean',
                'formula': formula
            })

        # Update table columns: add Net Ratio %
        self.polygon_table.setColumnCount(11)
        self.polygon_table.setHorizontalHeaderLabels([
            "Pattern", "Polygon #", "Individual Area (um²)", "Overlap Depth", "Overlaps With",
            "Overlap Area (um²)", "Net Area (um²)", "Raw Ratio %", "Net Ratio %", "Efficiency %", "Status"
        ])
        self.polygon_table.setRowCount(len(all_polygons))

        for row, poly_info in enumerate(all_polygons):
            self.polygon_table.setItem(row, 0, QTableWidgetItem(poly_info['pattern']))
            self.polygon_table.setItem(row, 1, QTableWidgetItem(str(poly_info['index'])))
            area_item = QTableWidgetItem(f"{poly_info['area']:.3f}")
            self.polygon_table.setItem(row, 2, area_item)
            depth_item = QTableWidgetItem(str(poly_info['depth']))
            if poly_info['depth'] > 1:
                depth_item.setBackground(self.get_color_by_depth(poly_info['depth']))
            self.polygon_table.setItem(row, 3, depth_item)
            overlaps_str = ""
            if poly_info['overlaps']:
                if poly_info['pattern'] == 'Pattern A':
                    overlaps_str = ", ".join([f"PA-{i+1}" for i in poly_info['overlaps']])
                else:
                    overlaps_str = ", ".join([f"PB-{i+1}" for i in poly_info['overlaps']])
            else:
                overlaps_str = "None"
            self.polygon_table.setItem(row, 4, QTableWidgetItem(overlaps_str))
            overlap_area_item = QTableWidgetItem(f"{poly_info['overlap_area']:.3f}")
            if poly_info['overlap_area'] > 0:
                overlap_area_item.setBackground(QColor(255, 200, 200))
            self.polygon_table.setItem(row, 5, overlap_area_item)
            net_area_item = QTableWidgetItem(f"{poly_info['net_area']:.3f}")
            self.polygon_table.setItem(row, 6, net_area_item)
            raw_ratio_item = QTableWidgetItem(f"{poly_info['raw_ratio']:.1f}%")
            self.polygon_table.setItem(row, 7, raw_ratio_item)
            net_ratio_item = QTableWidgetItem(f"{poly_info['net_ratio']:.1f}%")
            self.polygon_table.setItem(row, 8, net_ratio_item)
            efficiency_item = QTableWidgetItem(f"{poly_info['efficiency']:.1f}%")
            if poly_info['efficiency'] < 50:
                efficiency_item.setBackground(QColor(255, 200, 200))
            elif poly_info['efficiency'] > 80:
                efficiency_item.setBackground(QColor(200, 255, 200))
            self.polygon_table.setItem(row, 9, efficiency_item)
            status_item = QTableWidgetItem(poly_info['status'])
            if poly_info['status'] == 'Overlapping':
                status_item.setBackground(QColor(255, 200, 200))
            else:
                status_item.setBackground(QColor(200, 255, 200))
            self.polygon_table.setItem(row, 10, status_item)

        self.polygon_table.resizeColumnsToContents()
        
    def update_calculation_details(self):
        """Update the calculation details text area"""
        details = []
        details.append("=== DETAILED AREA CALCULATION BREAKDOWN (Units: um²) ===\n")
        details.append("IMPORTANT: Smart overlap calculation prevents double-counting.")
        details.append("Larger rectangles keep their full area, smaller rectangles and complex polygons lose overlap areas.\n")
        
        # Calculate RDL widths
        rdl_width1 = self.pattern1_width if self.pattern1_width > 0 else self.calculate_rdl_width(self.pattern1_polys)
        rdl_width2 = self.pattern2_width if self.pattern2_width > 0 else self.calculate_rdl_width(self.pattern2_polys)
        
        # Calculate difference lengths
        diff_length1 = self.calculate_difference_length(self.pattern1_total_area, rdl_width1) if rdl_width1 > 0 else 0
        diff_length2 = self.calculate_difference_length(self.pattern2_total_area, rdl_width2) if rdl_width2 > 0 else 0
        
        # Pattern A calculations
        if self.pattern1_polys:
            details.append("PATTERN A CALCULATIONS:")
            details.append(f"Total Individual Areas: {sum(self.pattern1_individual_areas):.3f} um²")
            details.append(f"Non-Overlapping Area: {self.pattern1_total_area:.3f} um²")
            details.append(f"Total Overlap Area: {sum(self.pattern1_individual_areas) - self.pattern1_total_area:.3f} um²")
            details.append(f"Area Efficiency: {(self.pattern1_total_area / sum(self.pattern1_individual_areas) * 100):.1f}%")
            details.append(f"RDL Width: {rdl_width1:.3f} um")
            details.append(f"Difference Length: {diff_length1:.3f} um (Area/Width)")
            details.append("")
            
            # Individual polygon breakdown with formulas
            details.append("Individual Polygon Breakdown:")
            for i, (area, formula) in enumerate(zip(self.pattern1_individual_areas, self.pattern1_formulas)):
                overlap_area = self.pattern1_overlap_areas.get(i, 0.0)
                net_area = area - overlap_area
                total_pattern_area = sum(self.pattern1_individual_areas)
                ratio = (area / total_pattern_area * 100) if total_pattern_area > 0 else 0
                details.append(f"  PA-{i+1}: {formula}")
                details.append(f"    Overlap Area: {overlap_area:.3f} um²")
                details.append(f"    Net Area: {net_area:.3f} um²")
                details.append(f"    Ratio: {ratio:.1f}% of total pattern area")
                details.append("")
            details.append("")
        
        # Pattern B calculations
        if self.pattern2_polys:
            details.append("PATTERN B CALCULATIONS:")
            details.append(f"Total Individual Areas: {sum(self.pattern2_individual_areas):.3f} um²")
            details.append(f"Non-Overlapping Area: {self.pattern2_total_area:.3f} um²")
            details.append(f"Total Overlap Area: {sum(self.pattern2_individual_areas) - self.pattern2_total_area:.3f} um²")
            details.append(f"Area Efficiency: {(self.pattern2_total_area / sum(self.pattern2_individual_areas) * 100):.1f}%")
            details.append(f"RDL Width: {rdl_width2:.3f} um")
            details.append(f"Difference Length: {diff_length2:.3f} um (Area/Width)")
            details.append("")
            
            # Individual polygon breakdown with formulas
            details.append("Individual Polygon Breakdown:")
            for i, (area, formula) in enumerate(zip(self.pattern2_individual_areas, self.pattern2_formulas)):
                overlap_area = self.pattern2_overlap_areas.get(i, 0.0)
                net_area = area - overlap_area
                total_pattern_area = sum(self.pattern2_individual_areas)
                ratio = (area / total_pattern_area * 100) if total_pattern_area > 0 else 0
                details.append(f"  PB-{i+1}: {formula}")
                details.append(f"    Overlap Area: {overlap_area:.3f} um²")
                details.append(f"    Net Area: {net_area:.3f} um²")
                details.append(f"    Ratio: {ratio:.1f}% of total pattern area")
                details.append("")
            details.append("")
        
        # Pattern comparison with percentage differences
        if self.pattern1_polys and self.pattern2_polys:
            details.append("PATTERN COMPARISON:")
            p1_efficiency = (self.pattern1_total_area / sum(self.pattern1_individual_areas) * 100) if self.pattern1_individual_areas else 0
            p2_efficiency = (self.pattern2_total_area / sum(self.pattern2_individual_areas) * 100) if self.pattern2_individual_areas else 0
            efficiency_diff = p1_efficiency - p2_efficiency
            
            p1_total = sum(self.pattern1_individual_areas)
            p2_total = sum(self.pattern2_individual_areas)
            total_diff = p1_total - p2_total
            total_diff_percent = (total_diff / p2_total * 100) if p2_total > 0 else 0
            
            # RDL width comparison
            width_diff = rdl_width1 - rdl_width2
            width_diff_percent = (width_diff / rdl_width2 * 100) if rdl_width2 > 0 else 0
            
            # Difference length comparison
            length_diff = diff_length1 - diff_length2
            length_diff_percent = (length_diff / diff_length2 * 100) if diff_length2 > 0 else 0
            
            details.append(f"Pattern A Efficiency: {p1_efficiency:.1f}%")
            details.append(f"Pattern B Efficiency: {p2_efficiency:.1f}%")
            details.append(f"Efficiency Difference: {efficiency_diff:+.1f}% ({'Pattern A better' if efficiency_diff > 0 else 'Pattern B better' if efficiency_diff < 0 else 'Equal'})")
            details.append("")
            details.append(f"Pattern A Total Area: {p1_total:.3f} um²")
            details.append(f"Pattern B Total Area: {p2_total:.3f} um²")
            details.append(f"Total Area Difference: {total_diff:+.3f} um² ({total_diff_percent:+.1f}%)")
            details.append("")
            details.append(f"Pattern A RDL Width: {rdl_width1:.3f} um")
            details.append(f"Pattern B RDL Width: {rdl_width2:.3f} um")
            details.append(f"RDL Width Difference: {width_diff:+.3f} um ({width_diff_percent:+.1f}%)")
            details.append("")
            details.append(f"Pattern A Difference Length: {diff_length1:.3f} um")
            details.append(f"Pattern B Difference Length: {diff_length2:.3f} um")
            details.append(f"Difference Length: {length_diff:+.3f} um ({length_diff_percent:+.1f}%)")
            details.append("")
            
            details.append("OVERLAP CALCULATION METHOD:")
            details.append("- Individual areas calculated using Shoelace formula for accuracy")
            details.append("- Triangles: A = 1/2 |x1y2 + x2y3 + x3y1 - x1y3 - x2y1 - x3y2|")
            details.append("- Rectangles: A = width × height")
            details.append("- Complex polygons: A = 1/2 |Shoelace formula|")
            details.append("- Overlaps detected using Polygon.intersects() and Polygon.intersection()")
            details.append("- Non-overlapping area calculated using unary_union()")
            details.append("- Smart overlap: Larger rectangles keep full area, others lose overlap")
            details.append("- Net area = Individual area - Overlap area (smart calculation)")
            details.append("- Efficiency = (Non-overlapping area / Total individual area) × 100%")
            details.append("- Ratio = (Individual area / Total pattern area) × 100%")
            details.append("- RDL Width = User-provided width (not calculated automatically)")
            details.append("- Difference Length = Non-overlapping Area / RDL Width")
            details.append("- Note: PA-4 (largest rectangle) keeps full area, others may lose overlap")
        
        self.calc_details.setPlainText("\n".join(details))
        
    def clear_all(self):
        """Clear all inputs and results"""
        self.pattern1_input.clear()
        self.pattern2_input.clear()
        self.pattern1_width_input.clear()
        self.pattern2_width_input.clear()
        self.scene.clear()
        self.comparison_table.setRowCount(0)
        self.polygon_table.setRowCount(0)
        self.calc_details.clear()
        self.pattern1_polys = []
        self.pattern2_polys = []
        self.overlap_data = {}
        self.pattern1_width = 0.0
        self.pattern2_width = 0.0

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OptimizedPolyAnalyzer()
    window.show()
    sys.exit(app.exec_())
