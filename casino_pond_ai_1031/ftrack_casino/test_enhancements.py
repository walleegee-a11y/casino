#!/usr/bin/env python3.12
"""
Standalone test for FastTrack Rich Text Editor & History enhancements
Run this to see the new features without launching the full FastTrack app
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from gui import RichTextDescriptionEditor, DescriptionHistoryDialog

# Sample test data with HTML
TEST_ISSUE_DATA = {
    'id': 'TEST_001',
    'title': 'Test Issue for Rich Text Editor Demo',
    'description': 'Current description with bold text and checkboxes',
    'description_html': '''<p><b>Current Description</b></p>
<p>This is a <b>test issue</b> to demonstrate the new <i>rich text</i> editor features.</p>
<h2>Features:</h2>
<ul>
<li>WYSIWYG rich text editing</li>
<li>Interactive clickable checkboxes</li>
<li>Tables with visual editing</li>
<li>Bold, italic, underline, colors</li>
</ul>
<h2>TODO List:</h2>
<ul>
<li>☑ Implement rich text editor</li>
<li>☑ Add formatting toolbar</li>
<li>☐ Test checkbox clicking</li>
<li>☐ Test table insertion</li>
</ul>
<p>Try editing this with the rich text editor!</p>
<p><span style="color: #ff0000;">You can change text colors too!</span></p>
''',
    'description_history': [
        {
            'timestamp': '2025-11-01 10:00:00',
            'user': 'alice',
            'old_description': 'First version of the description. This was the initial text.',
            'old_description_html': '<p>First version of the description.</p><p>This was the initial text.</p>'
        },
        {
            'timestamp': '2025-11-01 12:30:00',
            'user': 'bob',
            'old_description': 'Second version. Added more details here.',
            'old_description_html': '<p><b>Second version</b>.</p><p>Added more <i>details</i> here.</p>'
        },
        {
            'timestamp': '2025-11-01 14:15:00',
            'user': 'charlie',
            'old_description': 'Third version with checkboxes',
            'old_description_html': '''<p>Third version with <b>checkboxes</b></p>
<ul>
<li>☐ Task one</li>
<li>☐ Task two</li>
</ul>'''
        },
        {
            'timestamp': '2025-11-01 16:00:00',
            'user': 'dave',
            'old_description': 'Version with table',
            'old_description_html': '''<p><b>Version with table</b></p>
<table border="1">
<tr><th>Feature</th><th>Status</th></tr>
<tr><td>Editor</td><td>Complete</td></tr>
<tr><td>Tables</td><td>Testing</td></tr>
</table>''',
            'restored_from': 'Version #2 (2025-11-01 12:30:00)'
        },
        {
            'timestamp': '2025-11-01 17:30:00',
            'user': 'scott',
            'old_description': 'Description with mixed checkboxes',
            'old_description_html': '''<p><b>Description with Tasks</b></p>
<h2>TODO List:</h2>
<ul>
<li>☐ Implement rich text editor</li>
<li>☐ Add formatting toolbar</li>
<li>☐ Add checkbox support</li>
<li>☐ Test checkbox rendering</li>
</ul>
<p>This version has all tasks <span style="color: #ff0000;">unchecked</span>.</p>'''
        }
    ]
}


class TestWindow(QWidget):
    """Simple test window with buttons to launch new dialogs"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FastTrack Enhancement Test")
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        # Test rich text editor button
        btn_editor = QPushButton("[TEST] Rich Text Editor")
        btn_editor.setMinimumHeight(50)
        btn_editor.clicked.connect(self.test_rich_text_editor)
        layout.addWidget(btn_editor)

        # Test history dialog button
        btn_history = QPushButton("[TEST] History Dialog with HTML")
        btn_history.setMinimumHeight(50)
        btn_history.clicked.connect(self.test_history_dialog)
        layout.addWidget(btn_history)

        # Info label
        from PyQt5.QtWidgets import QLabel
        info = QLabel(
            "Click the buttons above to test the new features:\n\n"
            "1. Rich Text Editor:\n"
            "   - Try formatting buttons (Bold, Italic, Color)\n"
            "   - Click checkboxes to toggle them\n"
            "   - Insert a table\n\n"
            "2. History Dialog:\n"
            "   - View HTML-rendered versions\n"
            "   - Compare diffs\n"
            "   - Try searching and restoring versions"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.setLayout(layout)

    def test_rich_text_editor(self):
        """Test the rich text description editor"""
        current_desc = TEST_ISSUE_DATA.get('description_html', TEST_ISSUE_DATA['description'])

        editor = RichTextDescriptionEditor(current_desc, self)

        if editor.exec_():  # If user clicked Save
            new_desc = editor.get_description()
            new_html = editor.get_description_html()
            print("[OK] Rich Text Editor test completed!")
            print(f"Plain text ({len(new_desc)} chars):")
            print(new_desc[:200] + "..." if len(new_desc) > 200 else new_desc)
            print(f"\nHTML ({len(new_html)} chars):")
            print(new_html[:300] + "..." if len(new_html) > 300 else new_html)
        else:
            print("[CANCELLED] Editor cancelled")

    def test_history_dialog(self):
        """Test the history dialog with visual diff"""
        # Create a temporary YAML file path (won't actually save in test mode)
        import tempfile
        temp_path = os.path.join(tempfile.gettempdir(), "test_issue.yaml")

        history_dlg = DescriptionHistoryDialog(TEST_ISSUE_DATA, temp_path, self)
        history_dlg.exec_()

        print("[OK] History dialog test completed!")
        print(f"Viewed {len(TEST_ISSUE_DATA['description_history'])} historical versions")


def main():
    """Run the test application"""
    app = QApplication(sys.argv)

    # Set app font
    from PyQt5.QtGui import QFont
    app.setFont(QFont("Terminus", 8))

    print("=" * 60)
    print("FastTrack Rich Text Editor & History Enhancement Test")
    print("=" * 60)
    print()
    print("This test demonstrates the new features:")
    print("  [WYSIWYG]   Rich text editor (no markdown syntax!)")
    print("  [CHECKBOX]  Interactive clickable checkboxes")
    print("  [TABLES]    Visual table editing")
    print("  [FORMAT]    Bold, Italic, Colors, Font sizes")
    print("  [DIFF]      Visual diff with color coding")
    print("  [RESTORE]   Version restoration")
    print("  [SEARCH]    Search & filter")
    print("  [EXPORT]    HTML export")
    print()
    print("Click the buttons in the window to test each feature!")
    print("=" * 60)
    print()

    window = TestWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
