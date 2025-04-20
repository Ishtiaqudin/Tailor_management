with open('main.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Fix indentation issues
fixes = [
    # Fix for export_data
    ('filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Data", "tmms_export.json", "JSON Files (*.json)", options=options)\n        if not filename:\n        return', 
     'filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Data", "tmms_export.json", "JSON Files (*.json)", options=options)\n        if not filename:\n            return'),
    
    # Fix for import_data
    ('filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import Data", "", "JSON Files (*.json)", options=options)\n        if not filename:\n        return', 
     'filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import Data", "", "JSON Files (*.json)", options=options)\n        if not filename:\n            return'),
    
    # Fix for get_next_naap_number
    ('# Format as YYYY-NNNN (e.g., 2023-0001)\n                return f"{current_year}-{next_number:04d}"', 
     '# Format as YYYY-NNNN (e.g., 2023-0001)\n            return f"{current_year}-{next_number:04d}"'),
    
    # Fix for load_customers double else
    ('else:\n            else:', 'else:'),
    
    # Fix for LoginDialog.handle_login return
    ('self.error_label.setText("Username and password are required.")\n                            return',
     'self.error_label.setText("Username and password are required.")\n            return')
]

for old, new in fixes:
    content = content.replace(old, new)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed indentation issues in main.py') 