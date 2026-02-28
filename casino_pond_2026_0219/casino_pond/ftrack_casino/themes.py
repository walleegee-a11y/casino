"""
Theme management for FastTrack

Provides light and dark mode themes with consistent styling
"""

from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QApplication


class ThemeManager:
    """Manage application themes"""

    # Light theme colors (default) - Classical professional
    LIGHT_THEME = {
        'window': '#FAFAFA',        # Light gray-white
        'window_text': '#212121',   # Almost black
        'base': '#FFFFFF',          # Pure white
        'alternate_base': '#F5F5F5',# Very light gray
        'text': '#212121',          # Almost black
        'button': '#E0E0E0',        # Medium light gray
        'button_text': '#212121',   # Almost black
        'bright_text': '#D32F2F',   # Deep red
        'highlight': '#5B9BD5',     # Classic blue
        'highlight_text': '#FFFFFF',# White
        'disabled_text': '#9E9E9E', # Gray
        'tooltip_base': '#FFFDE7',  # Light yellow
        'tooltip_text': '#212121',  # Almost black
    }

    # Dark theme colors
    DARK_THEME = {
        'window': '#2B2B2B',
        'window_text': '#E0E0E0',
        'base': '#1E1E1E',
        'alternate_base': '#3A3A3A',
        'text': '#E0E0E0',
        'button': '#3A3A3A',
        'button_text': '#E0E0E0',
        'bright_text': '#FF6B6B',
        'highlight': '#4A4A8A',
        'highlight_text': '#FFFFFF',
        'disabled_text': '#707070',
        'tooltip_base': '#3A3A3A',
        'tooltip_text': '#E0E0E0',
    }

    # Button styles for light theme - Classical professional
    LIGHT_BUTTON_STYLES = {
        "default": {
            "background": "#F5F5F5",
            "border": "#BEBEBE",
            "hover": "#E8E8E8",
            "pressed": "#D8D8D8",
            "text": "#000000"
        },
        "action": {
            "background": "#4A90E2",
            "border": "#357ABD",
            "hover": "#5A9FF2",
            "pressed": "#3A80D2",
            "text": "#FFFFFF"
        },
        "danger": {
            "background": "#DC3545",
            "border": "#BD2130",
            "hover": "#E04555",
            "pressed": "#CC2535",
            "text": "#FFFFFF"
        },
        "gray": {
            "background": "#E0E0E0",
            "border": "#BEBEBE",
            "hover": "#D0D0D0",
            "pressed": "#C0C0C0",
            "text": "#000000"
        },
        "blue": {
            "background": "#5B9BD5",
            "border": "#4A7FB5",
            "hover": "#6BABE5",
            "pressed": "#4B8BC5",
            "text": "#FFFFFF"
        }
    }

    # Button styles for dark theme - Classical professional
    DARK_BUTTON_STYLES = {
        "default": {
            "background": "#424242",
            "border": "#616161",
            "hover": "#525252",
            "pressed": "#323232",
            "text": "#E0E0E0"
        },
        "action": {
            "background": "#1976D2",
            "border": "#0D47A1",
            "hover": "#2196F3",
            "pressed": "#0D5CB8",
            "text": "#FFFFFF"
        },
        "danger": {
            "background": "#C62828",
            "border": "#B71C1C",
            "hover": "#D32F2F",
            "pressed": "#A82020",
            "text": "#FFFFFF"
        },
        "gray": {
            "background": "#525252",
            "border": "#757575",
            "hover": "#616161",
            "pressed": "#424242",
            "text": "#E0E0E0"
        },
        "blue": {
            "background": "#1976D2",
            "border": "#0D47A1",
            "hover": "#2196F3",
            "pressed": "#0D5CB8",
            "text": "#FFFFFF"
        }
    }

    @staticmethod
    def apply_light_theme(app: QApplication):
        """Apply light theme to the application"""
        palette = QPalette()

        # Set colors from light theme
        palette.setColor(QPalette.Window, QColor(ThemeManager.LIGHT_THEME['window']))
        palette.setColor(QPalette.WindowText, QColor(ThemeManager.LIGHT_THEME['window_text']))
        palette.setColor(QPalette.Base, QColor(ThemeManager.LIGHT_THEME['base']))
        palette.setColor(QPalette.AlternateBase, QColor(ThemeManager.LIGHT_THEME['alternate_base']))
        palette.setColor(QPalette.Text, QColor(ThemeManager.LIGHT_THEME['text']))
        palette.setColor(QPalette.Button, QColor(ThemeManager.LIGHT_THEME['button']))
        palette.setColor(QPalette.ButtonText, QColor(ThemeManager.LIGHT_THEME['button_text']))
        palette.setColor(QPalette.BrightText, QColor(ThemeManager.LIGHT_THEME['bright_text']))
        palette.setColor(QPalette.Highlight, QColor(ThemeManager.LIGHT_THEME['highlight']))
        palette.setColor(QPalette.HighlightedText, QColor(ThemeManager.LIGHT_THEME['highlight_text']))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(ThemeManager.LIGHT_THEME['disabled_text']))
        palette.setColor(QPalette.ToolTipBase, QColor(ThemeManager.LIGHT_THEME['tooltip_base']))
        palette.setColor(QPalette.ToolTipText, QColor(ThemeManager.LIGHT_THEME['tooltip_text']))

        app.setPalette(palette)

    @staticmethod
    def apply_dark_theme(app: QApplication):
        """Apply dark theme to the application"""
        palette = QPalette()

        # Set colors from dark theme
        palette.setColor(QPalette.Window, QColor(ThemeManager.DARK_THEME['window']))
        palette.setColor(QPalette.WindowText, QColor(ThemeManager.DARK_THEME['window_text']))
        palette.setColor(QPalette.Base, QColor(ThemeManager.DARK_THEME['base']))
        palette.setColor(QPalette.AlternateBase, QColor(ThemeManager.DARK_THEME['alternate_base']))
        palette.setColor(QPalette.Text, QColor(ThemeManager.DARK_THEME['text']))
        palette.setColor(QPalette.Button, QColor(ThemeManager.DARK_THEME['button']))
        palette.setColor(QPalette.ButtonText, QColor(ThemeManager.DARK_THEME['button_text']))
        palette.setColor(QPalette.BrightText, QColor(ThemeManager.DARK_THEME['bright_text']))
        palette.setColor(QPalette.Highlight, QColor(ThemeManager.DARK_THEME['highlight']))
        palette.setColor(QPalette.HighlightedText, QColor(ThemeManager.DARK_THEME['highlight_text']))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(ThemeManager.DARK_THEME['disabled_text']))
        palette.setColor(QPalette.ToolTipBase, QColor(ThemeManager.DARK_THEME['tooltip_base']))
        palette.setColor(QPalette.ToolTipText, QColor(ThemeManager.DARK_THEME['tooltip_text']))

        app.setPalette(palette)

    @staticmethod
    def get_button_styles(theme='light'):
        """Get button styles for the specified theme"""
        if theme == 'dark':
            return ThemeManager.DARK_BUTTON_STYLES
        return ThemeManager.LIGHT_BUTTON_STYLES

    @staticmethod
    def style_button(button, style_type="default", theme='light'):
        """Apply themed button styling"""
        styles = ThemeManager.get_button_styles(theme)
        style = styles[style_type]

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {style['background']};
                border: 1px solid {style['border']};
                border-radius: 2px;
                padding: 4px 8px;
                color: {style['text']};
                font-family: Terminus;
                font-size: 8pt;
            }}
            QPushButton:hover {{
                background-color: {style['hover']};
            }}
            QPushButton:pressed {{
                background-color: {style['pressed']};
            }}
            QPushButton:disabled {{
                background-color: #4A4A4A;
                border: 1px solid #5A5A5A;
                color: #707070;
            }}
        """)

    @staticmethod
    def get_table_style(theme='light'):
        """Get table styling for the specified theme"""
        if theme == 'dark':
            return """
                QTableWidget {
                    background-color: #1E1E1E;
                    color: #E0E0E0;
                    font-family: Terminus;
                    font-size: 8pt;
                    gridline-color: #424242;
                }
                QHeaderView::section {
                    background-color: #424242;
                    color: #E0E0E0;
                    padding: 4px;
                    border: 1px solid #616161;
                    font-family: Terminus;
                    font-size: 8pt;
                }
                QTableWidget::item {
                    padding: 4px;
                }
                QTableWidget::item:selected {
                    background-color: #1976D2;
                    color: #FFFFFF;
                }
            """
        return """
            QTableWidget {
                background-color: #FFFFFF;
                color: #212121;
                font-family: Terminus;
                font-size: 8pt;
                gridline-color: #E0E0E0;
            }
            QHeaderView::section {
                background-color: #E0E0E0;
                color: #212121;
                padding: 4px;
                border: 1px solid #BEBEBE;
                font-family: Terminus;
                font-size: 8pt;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #5B9BD5;
                color: #FFFFFF;
            }
        """

