
# Launcher script for Tailor Master
import os
import sys
import traceback

def handle_exception(exc_type, exc_value, exc_traceback):
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Write to error log
    with open("error.log", "a", encoding="utf-8") as logf:
        logf.write(error_msg + "\n")
    
    # Show error dialog
    try:
        from PyQt5 import QtWidgets
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Critical)
        msgBox.setWindowTitle("Application Error")
        msgBox.setText(f"An unexpected error occurred: {exc_value}")
        msgBox.setDetailedText(error_msg)
        msgBox.exec_()
    except:
        print(f"CRITICAL ERROR: {error_msg}")
    
    sys.exit(1)

# Set up exception handler
sys.excepthook = handle_exception

# Ensure resources directory is found
if getattr(sys, 'frozen', False):
    # Running as a frozen executable
    base_path = os.path.dirname(sys.executable)
    resources_path = os.path.join(base_path, 'resources')
    if not os.path.exists(resources_path):
        # Create resources directory if it doesn't exist
        try:
            os.makedirs(resources_path, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create resources directory: {e}")
    
    # Add paths to system path
    if base_path not in sys.path:
        sys.path.insert(0, base_path)

# Import and run main application
try:
    import main
    from PyQt5 import QtWidgets
    
    # Initialize database
    if hasattr(main, 'init_db'):
        main.init_db()
    
    # Start application
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Tailor Master")
    
    window = main.MainWindow()
    window.show()
    
    sys.exit(app.exec_())
except Exception as e:
    handle_exception(type(e), e, e.__traceback__)
