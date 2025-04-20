import sys
import os
import platform
import hashlib # Add hashlib import for login check
from PyQt5 import QtWidgets, QtGui, QtCore
import qtmodern.styles
import qtmodern.windows
from database import init_db, get_db_connection # Import get_db_connection

# Debug flag
DEBUG_MODE = False

# Function to enable debug mode
def enable_debug_mode():
    global DEBUG_MODE
    DEBUG_MODE = True
    print("Debug mode enabled")

# Debug print function
def debug_print(*args, **kwargs):
    if DEBUG_MODE:
        print("[DEBUG]", *args, **kwargs)

# Get the resources path, works in both frozen and non-frozen environments
def get_resource_path(relative_path):
    """Get the path to a resource file, works both when frozen and in dev mode"""
    import sys, os
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    elif getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    resource_path = os.path.join(base_path, relative_path)
    return resource_path

# Get the database path
def get_db_path():
    """Get path to the database file"""
    if getattr(sys, 'frozen', False):
        # Running as a frozen executable
        base_path = os.path.dirname(sys.executable)
    else:
        # Running in a normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    db_path = os.path.join(base_path, "tmms.db")
    debug_print(f"Database path: {db_path}")
    return db_path

# Check Python version
REQUIRED_PYTHON = (3, 6)
if sys.version_info < REQUIRED_PYTHON:
    sys.stderr.write(f"Error: TMMS requires Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]} or higher\n")
    sys.stderr.write(f"Current Python version: {sys.version_info.major}.{sys.version_info.minor}\n")
    sys.exit(1)

class MainWindow(QtWidgets.QMainWindow):
    def closeEvent(self, event):
        if hasattr(self, 'timer'):
            self.timer.stop()
        if hasattr(self, 'scheduled_backup_timer'):
            self.scheduled_backup_timer.stop()
        QtWidgets.QApplication.quit()
        event.accept()
    def __init__(self, logged_in_user="Guest"): # Accept username, default to Guest
        print("    DEBUG: Entering MainWindow.__init__")
        super().__init__()
        print("    DEBUG: super().__init__() called.")
        self.logged_in_user = logged_in_user # Store the username
        self.last_backup_time = None
        self.setWindowTitle("Tailor Master")
        self.resize(1280, 720)
        print("    DEBUG: Basic window properties set.")
        # Set window icon
        print("    DEBUG: Getting icon path...")
        icon_path = get_resource_path("resources/app_logo.png")
        print(f"    DEBUG: Icon path: {icon_path}")
        if os.path.exists(icon_path):
            print("    DEBUG: Setting window icon...")
            self.setWindowIcon(QtGui.QIcon(icon_path) if os.path.exists(icon_path) else QtGui.QIcon())
        print("    DEBUG: Window icon set (or skipped).")
        
        # Initialize UI - Choose one of the UI styles:
        # Option 1: Modern UI with sidebar
        print("    DEBUG: Calling init_modern_ui...")
        self.init_modern_ui()
        print("    DEBUG: init_modern_ui returned.")
        
        # Option 2: Tab-based UI
        # self.init_ui()
        print("    DEBUG: Exiting MainWindow.__init__")
        
    def init_modern_ui(self):
        print("        DEBUG: Entering init_modern_ui...")
        # --- Main Layout ---
        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Top Bar ---
        top_bar = QtWidgets.QWidget()
        top_bar.setStyleSheet("background: #eebc1d; color: #000000; border-bottom: 2px solid #ddd;")
        top_bar.setFixedHeight(60)
        top_layout = QtWidgets.QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 8, 16, 8)
        
        # Logo
        logo_label = QtWidgets.QLabel()
        icon_path = get_resource_path("resources/app_logo.png")
        logo_pixmap = QtGui.QPixmap(icon_path)
        if logo_pixmap.isNull():
            # fallback: create a placeholder pixmap
            logo_pixmap = QtGui.QPixmap(64, 64)
            logo_pixmap.fill(QtGui.QColor(200, 200, 200))  # light gray
        logo_label.setPixmap(logo_pixmap.scaled(40, 40, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        top_layout.addWidget(logo_label)
        
        # Software Name (English only)
        title_label = QtWidgets.QLabel("<b>Tailor Master</b>")
        title_label.setStyleSheet("font-size: 22px; margin-left: 12px;")
        top_layout.addWidget(title_label)
        
        # Spacer
        top_layout.addStretch()
        
        # Date & Time
        self.datetime_label = QtWidgets.QLabel()
        self.datetime_label.setStyleSheet("font-size: 14px;")
        self.datetime_label.setFixedWidth(250) # Increased width to accommodate day name
        self.datetime_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        top_layout.addWidget(self.datetime_label)
        
        # Timer for updating time
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)
        self.update_datetime()
        
        # User (optional)
        user_label = QtWidgets.QLabel(f"ðŸ'¤ {self.logged_in_user}") # Display logged-in user
        user_label.setStyleSheet("font-size: 14px; margin-left: 16px;")
        top_layout.addWidget(user_label)
        main_layout.addWidget(top_bar)
        print("        DEBUG: Top bar created.")
        
        # --- Main Body Split ---
        body_split = QtWidgets.QHBoxLayout()
        body_split.setContentsMargins(0, 0, 0, 0)
        body_split.setSpacing(0)
        
        # --- Left Sidebar ---
        print("        DEBUG: Calling init_sidebar...")
        sidebar = self.init_sidebar()
        body_split.addWidget(sidebar)
        print("        DEBUG: Sidebar created and added.")
        
        # --- Center Panel ---
        center_panel = QtWidgets.QFrame()
        center_panel.setStyleSheet("background: #f5f5f5; border-right: 1px solid #ddd;")
        center_layout = QtWidgets.QVBoxLayout(center_panel)
        center_layout.setContentsMargins(15, 15, 15, 15)
        center_layout.setSpacing(10)
        center_layout.setAlignment(QtCore.Qt.AlignTop)
        
        # Content stacked widget to switch between different screens
        self.content_stack = QtWidgets.QStackedWidget()
        
        print("        DEBUG: Initializing screens...")
        # Initialize all screens
        print("        DEBUG: Calling init_dashboard_screen...")
        self.init_dashboard_screen()
        print("        DEBUG: Returned from init_dashboard_screen.")
        print("        DEBUG: Calling init_customer_screen...")
        self.init_customer_screen()
        print("        DEBUG: Returned from init_customer_screen.")
        print("        DEBUG: Calling init_measurement_screen...")
        self.init_measurement_screen()
        print("        DEBUG: Returned from init_measurement_screen.")
        print("        DEBUG: Calling init_history_screen...")
        self.init_history_screen()
        print("        DEBUG: Returned from init_history_screen.")
        print("        DEBUG: Calling init_settings_screen...")
        self.init_settings_screen()
        print("        DEBUG: Calling init_orders_screen...")
        self.init_orders_screen() # Initialize the new screen
        print("        DEBUG: Screens initialized.")
        
        # Initialize Finance Screen 
        print("        DEBUG: Calling init_finance_screen...")
        self.init_finance_screen()
        
        # Initialize Admin Panel Screen
        print("        DEBUG: Calling init_admin_panel_screen...")
        self.init_admin_panel_screen()
        print("        DEBUG: Exiting init_admin_panel_screen.")
        
        # Call initial dashboard update after all screens are initialized
        self.update_dashboard_stats()
        
        center_layout.addWidget(self.content_stack)
        body_split.addWidget(center_panel, 2)
        print("        DEBUG: Center panel created and added.")
        
        # --- Right Panel ---
        right_panel = QtWidgets.QFrame()
        right_panel.setStyleSheet("background: #ffffff;")
        right_panel.setFixedWidth(240)
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 15, 10, 15)
        right_layout.setSpacing(12)
        right_layout.setAlignment(QtCore.Qt.AlignTop)
        # Quick Add Button
        quick_add_btn = QtWidgets.QPushButton("Quick Add Measurement")
        # Reduced font-size from 18px to make text fit better
        quick_add_btn.setStyleSheet("background: #eebc1d; color: #000000; font-size: 15px; padding: 16px; border-radius: 8px; font-weight: bold;")
        quick_add_btn.clicked.connect(self.show_add_measurement)
        right_layout.addWidget(quick_add_btn)
        # Reminders/Notes
        reminders = QtWidgets.QLabel("<b>Reminders:</b><br>2 Deliveries Due Today<br>1 Order Pending")
        reminders.setStyleSheet("margin-top: 20px; font-size: 16px;")
        right_layout.addWidget(reminders)
        # Notes
        notes = QtWidgets.QTextEdit()
        notes.setPlaceholderText("Add notes here...")
        notes.setStyleSheet("margin-top: 16px; font-size: 16px; border: 1px solid #eebc1d; border-radius: 6px;")
        right_layout.addWidget(notes)
        right_layout.addStretch()
        body_split.addWidget(right_panel)
        main_layout.addLayout(body_split, 1)
        print("        DEBUG: Right panel created and added.")
        
        # --- Bottom Bar ---
        bottom_bar = QtWidgets.QWidget()
        bottom_bar.setStyleSheet("background: #eebc1d; color: #000000; border-top: 2px solid #ddd;")
        bottom_bar.setFixedHeight(40)
        bottom_layout = QtWidgets.QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(16, 4, 16, 4)
        bottom_layout.addWidget(QtWidgets.QLabel("Total Measurements: 250"))
        bottom_layout.addStretch()
        status_label = QtWidgets.QLabel("Status: Offline | Local Database")
        bottom_layout.addWidget(status_label)
        dev_label = QtWidgets.QLabel("Developer: Codeium AI")
        bottom_layout.addWidget(dev_label)
        main_layout.addWidget(bottom_bar)
        print("        DEBUG: Bottom bar created.")
        
        print("        DEBUG: Setting central widget...")
        self.setCentralWidget(central_widget)
        print("        DEBUG: Exiting init_modern_ui.")

    def init_sidebar(self):
        # Sidebar container
        sidebar = QtWidgets.QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("""
            #sidebar {
                background-color: #fcda77;
                border-right: 1px solid #e0e0e0;
            }
        """)
        
        # Logo section
        logo_layout = QtWidgets.QHBoxLayout()
        logo_layout.setContentsMargins(16, 24, 16, 24)
        logo_layout.setSpacing(10)
        
        logo_icon = QtWidgets.QLabel("ðŸ§µ")
        logo_icon.setStyleSheet("font-size: 24px;")
        logo_layout.addWidget(logo_icon)
        
        logo_text = QtWidgets.QLabel("TMMS")
        logo_text.setStyleSheet("font-size: 20px; font-weight: bold; color: #333333;")
        logo_layout.addWidget(logo_text)
        
        # Navigation menu
        
        # Menu items with icons and corresponding methods
        menu_items = [
         ("[D]", "Dashboard", self.show_dashboard, True),
         ("[C]", "Customers", self.show_customers, False),
         ("[M]", "Measurements", self.show_add_measurement, False), # Measurement entry screen
         ("[H]", "History", self.show_history, False), # Added History navigation item
         ("[O]", "Orders", self.show_orders, False), # Placeholder
         ("[I]", "Inventory", self.show_dashboard, False), # Placeholder, link to dashboard for now
         ("[F]", "Finance", self.show_finance, False), # Placeholder, link to dashboard for now
         ("[S]", "Settings", self.show_settings, False),
         ("[A]", "Admin Panel", self.show_admin_panel, False) # Added Admin Panel navigation
        ]
        
        self.nav_buttons = {} # Use a dict for easier lookup: {button_text: button_widget}
        for icon, text, method, is_active in menu_items:
            btn = QtWidgets.QPushButton(f" {icon}  {text}")
            btn.setCheckable(True)
            btn.setChecked(is_active)
            
            # Connect button click to its specific method AND the styling method
            btn.clicked.connect(method)
            btn.clicked.connect(lambda checked, b=btn: self.activate_nav_button(b))
            
            self.nav_buttons[text] = btn # Store button by text
            
            # Apply initial style after adding to layout
            self._style_nav_button(btn, is_active)
            
        # Add spacer at the bottom
        
        # User profile section
        profile_layout = QtWidgets.QHBoxLayout()
        profile_layout.setContentsMargins(16, 16, 16, 16)
        profile_layout.setSpacing(10)
        profile_icon = QtWidgets.QLabel("[U]")
        profile_icon.setStyleSheet("font-size: 20px;")
        profile_layout.addWidget(profile_icon)
        
        profile_text = QtWidgets.QLabel(self.logged_in_user) # Display logged-in user
        profile_text.setStyleSheet("font-size: 14px; color: #333333;")
        profile_layout.addWidget(profile_text)
        profile_layout.addStretch()
        
        # Master layout for sidebar
        sidebar_layout = QtWidgets.QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        sidebar_layout.addLayout(logo_layout)
        sidebar_layout.addLayout(profile_layout)
        
        return sidebar

    def activate_nav_button(self, clicked_button):
        """Handles styling and check state when a nav button is clicked."""
        for btn in self.nav_buttons.values():
            is_active = (btn == clicked_button)
            self._style_nav_button(btn, is_active)
            btn.setChecked(is_active) # Ensure only the clicked one is checked

    def _style_nav_button(self, button, is_active):
        """Applies the correct style to a navigation button based on its state."""
        if is_active:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #eebc1d;
                    border: none;
                    border-radius: 8px;
                    color: #ffffff;
                    font-weight: bold;
                    text-align: left;
                    padding: 12px 16px;
                    font-size: 15px;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 8px;
                    color: #333333;
                    text-align: left;
                    padding: 12px 16px;
                    font-size: 15px;
                }
                QPushButton:hover {
                    background-color: rgba(238, 188, 29, 0.3);
                }
            """)

        search_layout.setSpacing(8)
        
        search_icon = QtWidgets.QLabel("[Search]")
        search_layout.addWidget(search_icon)
        
        search_input = QtWidgets.QLineEdit()
        search_input.setPlaceholderText("Search...")
        search_input.setStyleSheet("""
            border: none;
            background: transparent;
            font-size: 14px;
        """)
        search_layout.addWidget(search_input)
        
        header_layout.addStretch()
        header_layout.addWidget(search_container)
        
        # User actions area
        actions_layout = QtWidgets.QHBoxLayout()
        actions_layout.setSpacing(16)
        
        # Notification icon
        notif_btn = QtWidgets.QPushButton("[N]")
        notif_btn.setStyleSheet("""
            font-size: 18px;
            background: transparent;
            border: none;
            padding: 8px;
        """)
        actions_layout.addWidget(notif_btn)
        
        # Settings icon
        settings_btn = QtWidgets.QPushButton("[S]")
        settings_btn.setStyleSheet("""
            font-size: 18px;
            background: transparent;
            border: none;
            padding: 8px;
        """)
        actions_layout.addWidget(settings_btn)
        
        header_layout.addLayout(actions_layout)
        
        # Ensure vertical alignment in the header
        header_layout.setAlignment(QtCore.Qt.AlignVCenter)
        
        # Add header to dashboard
        dashboard_layout.addWidget(header)
        print("            DEBUG: Dashboard header created.")
        
        # Content area
        content_area = QtWidgets.QWidget()
        content_area.setObjectName("content_area")
        content_area.setStyleSheet("""
            #content_area {
                background-color: #f5f5f5;
            }
        """)
        
        content_layout = QtWidgets.QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Dashboard cards layout (rename to avoid collision)
        cards_layout = QtWidgets.QGridLayout()
        cards_layout.setSpacing(20)
        
        # Card 1: Total Customers - Cleared Value
        self.customers_card = self.create_stat_card("Total Customers", "[C] 0", "#3498db")
        cards_layout.addWidget(self.customers_card, 0, 0)
        
        # Card 2: Total Orders - Cleared Value
        self.orders_card = self.create_stat_card("Total Orders", "[O] 0", "#2ecc71")
        cards_layout.addWidget(self.orders_card, 0, 1)
        
        # Card 3: Pending Delivery - Cleared Value
        self.pending_card = self.create_stat_card("Pending Delivery", "[P] 0", "#e74c3c")
        cards_layout.addWidget(self.pending_card, 0, 2)
        
        # Card 4: Revenue This Month - Cleared Value
        self.revenue_card = self.create_stat_card("Revenue This Month", "[R] AED 0", "#9b59b6")
        cards_layout.addWidget(self.revenue_card, 0, 3)
        
        content_layout.addLayout(cards_layout) # Add the renamed cards layout
        
        # Add spacing between cards and middle section
        content_layout.addSpacing(20)
        
        # Create middle section with two columns
        middle_section = QtWidgets.QHBoxLayout()
        
        # Orders section - left
        orders_widget = QtWidgets.QWidget()
        orders_widget.setObjectName("orders_widget")
        orders_widget.setStyleSheet("""
            #orders_widget {
                background-color: #ffffff;
                border-radius: 8px;
            }
            QTableWidget {
                border: none;
                background-color: #ffffff;
            }
            QTableWidget::item {
                padding: 10px 5px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px 5px;
                border: none;
                font-weight: bold;
                color: #2c3e50;
                text-align: left; /* Align header text left */
            }
        """)
        
        orders_layout = QtWidgets.QVBoxLayout(orders_widget)
        
        # Header with title and view all button
        orders_header = QtWidgets.QHBoxLayout()
        orders_title = QtWidgets.QLabel("Recent Orders")
        orders_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        orders_header.addWidget(orders_title)
        
        orders_header.addItem(QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        
        view_all_btn = QtWidgets.QPushButton("View All")
        view_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                border-radius: 4px;
                padding: 5px 10px;
                color: #2c3e50;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d0d3d4;
            }
        """)
        orders_header.addWidget(view_all_btn)
        
        orders_layout.addLayout(orders_header)
        
        # Orders table
        self.dash_orders_table = QtWidgets.QTableWidget()
        self.dash_orders_table.setColumnCount(4)
        self.dash_orders_table.setHorizontalHeaderLabels(["Customer", "Service", "Amount", "Status"])
        self.dash_orders_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.dash_orders_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.dash_orders_table.setShowGrid(False)
        self.dash_orders_table.verticalHeader().setVisible(False)
        # Allow columns to resize, stretch last one
        self.dash_orders_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents) # Resize based on content initially
        self.dash_orders_table.horizontalHeader().setStretchLastSection(True)
        # Set minimum section size to prevent excessive squeezing
        self.dash_orders_table.horizontalHeader().setMinimumSectionSize(80)
        
        # Clear sample data - Set row count to 0
        self.dash_orders_table.setRowCount(0)
        
        orders_layout.addWidget(self.dash_orders_table)
        
        # Activity feed - right
        activity_widget = QtWidgets.QWidget()
        activity_widget.setObjectName("activity_widget")
        activity_widget.setStyleSheet("""
            #activity_widget {
                background-color: #ffffff;
                border-radius: 8px;
            }
        """)
        
        activity_layout = QtWidgets.QVBoxLayout(activity_widget)
        activity_layout.setSpacing(10)
        
        activity_title = QtWidgets.QLabel("Activity Feed")
        activity_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        activity_layout.addWidget(activity_title)
        
        # Activities list (Use a scroll area for potentially long lists)
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none; background-color: transparent;") # Remove scroll area border
        activity_list_widget = QtWidgets.QWidget() # Widget to hold the list layout
        activity_list_layout = QtWidgets.QVBoxLayout(activity_list_widget)
        activity_list_layout.setContentsMargins(0, 5, 0, 5)
        activity_list_layout.setSpacing(8)
        
        # Removed sample activity data loop
        
        activity_list_layout.addStretch(1) # Push items to the top
        scroll_area.setWidget(activity_list_widget) # Set the list widget inside scroll area
        activity_layout.addWidget(scroll_area) # Add scroll area to the main activity layout
        
        # Add widgets to middle section
        middle_section.addWidget(orders_widget, 2) # Give orders widget more space
        middle_section.addWidget(activity_widget, 1) # Give activity widget less space
        
        content_layout.addLayout(middle_section)
        
        # Add stretch to push everything to the top
        content_layout.addStretch(1)
        
        # Add content area to main layout (the original QVBoxLayout)
        dashboard_layout.addWidget(content_area) 
        print("            DEBUG: Dashboard content area added to layout.")
        
        # Initialize data
        self.update_datetime()
        
        # Add the dashboard to the content stack
        print("            DEBUG: Adding dashboard widget to stack...")
        self.content_stack.addWidget(dashboard)
        print("            DEBUG: Exiting init_dashboard_screen.")

    def create_stat_card(self, title, value, color):
        card = QtWidgets.QWidget()
        card.setObjectName("stat_card")
        card.setStyleSheet(f"""
            #stat_card {{
                background-color: #ffffff;
                border-radius: 8px;
                border-left: 5px solid {color};
            }}
        """)
        
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        
        value_label = QtWidgets.QLabel(value)
        value_label.setObjectName("stat_value_label") # Correctly set
        value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        return card
        
    def update_datetime(self):
        from datetime import datetime
        now = datetime.now()
        if hasattr(self, 'datetime_label') and self.datetime_label:
            # This format string includes the day name (%A)
            self.datetime_label.setText(now.strftime('%A, %B %d, %Y | %H:%M:%S'))

    def init_customer_screen(self):
        customer_screen = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(customer_screen)
        
        # --- Form Fields ---
        form_layout = QtWidgets.QFormLayout()
        self.name_input = QtWidgets.QLineEdit()
        self.mobile_input = QtWidgets.QLineEdit()
        self.address_input = QtWidgets.QLineEdit()
        self.date_input = QtWidgets.QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QtCore.QDate.currentDate())
        
        form_layout.addRow("Full Name:", self.name_input)
        form_layout.addRow("Mobile Number:", self.mobile_input)
        form_layout.addRow("Address:", self.address_input)
        form_layout.addRow("Date of Entry:", self.date_input)
        layout.addLayout(form_layout)
        
        # --- Save Button ---
        self.save_btn = QtWidgets.QPushButton("Save Customer")
        self.save_btn.clicked.connect(self.save_customer)
        layout.addWidget(self.save_btn)
        
        # --- Search Bar ---
        search_layout = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search by name or mobile number...")
        self.search_btn = QtWidgets.QPushButton("Search")
        self.search_btn.clicked.connect(self.search_customers)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)
        
        # --- Customer Table ---
        self.customer_table = QtWidgets.QTableWidget()
        self.customer_table.setColumnCount(5)
        self.customer_table.setHorizontalHeaderLabels(["ID", "Naap Number", "Full Name", "Mobile Number", "Date of Entry"])
        self.customer_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.customer_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.customer_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.customer_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.customer_table)
        
        # Make the customer table columns resize correctly
        self.customer_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch) # Name
        self.customer_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch) # Mobile
        self.customer_table.resizeColumnsToContents()
        
        self.content_stack.addWidget(customer_screen)

    def init_measurement_screen(self):
        print("            DEBUG: Entering init_measurement_screen...")
        measurement_screen = QtWidgets.QWidget()

        # Main layout for the measurement screen widget itself
        screen_layout = QtWidgets.QVBoxLayout(measurement_screen)
        screen_layout.setContentsMargins(0, 0, 0, 0) # No margins for the outer layout

        # Scroll Area setup
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }") # Style scroll area

        # Container widget and layout for scrollable content
        scroll_content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(scroll_content_widget) # This holds the form groups
        content_layout.setContentsMargins(15, 15, 15, 15) # Add margins *inside* scroll area
        content_layout.setSpacing(15) # Add overall spacing *inside* scroll area
        content_layout.setAlignment(QtCore.Qt.AlignTop) # Align content to top

        # --- Customer Selection ---
        customer_group = QtWidgets.QGroupBox("Customer")
        customer_layout = QtWidgets.QHBoxLayout(customer_group)
        customer_layout.setContentsMargins(10, 10, 10, 10)
        self.measure_customer_combo = QtWidgets.QComboBox()
        customer_layout.addWidget(QtWidgets.QLabel("Select Customer:"))
        customer_layout.addWidget(self.measure_customer_combo)
        content_layout.addWidget(customer_group) # Add to scroll layout
        self.refresh_measurement_customers()

        # --- Dress Type Selection ---
        self.dress_type_combo = QtWidgets.QComboBox()
        self.dress_types = ["Shalwar Kameez", "Kurta", "Pant Shirt", "Waistcoat", "Jacket"]
        self.dress_type_combo.addItems(self.dress_types)
        self.dress_type_combo.currentIndexChanged.connect(self.update_measurement_fields)
        content_layout.addWidget(QtWidgets.QLabel("Dress Type:")) # Add to scroll layout
        content_layout.addWidget(self.dress_type_combo) # Add to scroll layout

        # Initialize the measurement input fields and combos
        self.init_measurement_fields() # Creates self.measure_inputs etc.

        # --- GroupBox for Shalwar Kameez / Kurta Measurements ---
        self.sk_measurements_group = QtWidgets.QGroupBox("Core Measurements")
        sk_measurements_layout = QtWidgets.QGridLayout()
        sk_measurements_layout.setSpacing(10)
        sk_measurements_layout.setContentsMargins(10, 15, 10, 10)
        sk_measurements_layout.setColumnStretch(1, 1) # Allow field column (1) to stretch
        self.sk_measurements_group.setLayout(sk_measurements_layout)
        # Removed setSizePolicy Maximum
        content_layout.addWidget(self.sk_measurements_group) # Add to scroll layout

        # --- GroupBox for Shalwar Kameez / Kurta Style ---
        self.sk_style_group = QtWidgets.QGroupBox("Style Details")
        sk_style_layout = QtWidgets.QGridLayout()
        sk_style_layout.setSpacing(10)
        sk_style_layout.setContentsMargins(10, 15, 10, 10)
        sk_style_layout.setColumnStretch(1, 1)
        self.sk_style_group.setLayout(sk_style_layout)
        # Removed setSizePolicy Maximum
        content_layout.addWidget(self.sk_style_group) # Add to scroll layout

        # --- Placeholder for other dress types ---
        self._init_measurement_placeholder()
        content_layout.addWidget(self.placeholder_widget) # Add to scroll layout

        # --- Fabric & Delivery GroupBox ---
        fabric_delivery_group = QtWidgets.QGroupBox("Fabric & Delivery")
        fabric_delivery_outer_layout = QtWidgets.QVBoxLayout()
        fabric_delivery_outer_layout.setContentsMargins(10, 15, 10, 10)
        fabric_delivery_outer_layout.setSpacing(10)

        # Fabric Type Row
        fabric_layout = QtWidgets.QHBoxLayout()
        fabric_label = QtWidgets.QLabel("Fabric Type:")
        self.fabric_type_combo = QtWidgets.QComboBox()
        self.fabric_type_combo.addItems(["Cotton", "Wash & Wear", "Boski", "Latha", "Karandi", "Other"])
        self.fabric_type_combo.setEditable(True)
        self.fabric_type_combo.lineEdit().setPlaceholderText("Select or type fabric type")
        fabric_layout.addWidget(fabric_label)
        fabric_layout.addWidget(self.fabric_type_combo, 1)
        fabric_delivery_outer_layout.addLayout(fabric_layout)

        # Urgent/Expected Date Row
        urgent_layout = QtWidgets.QHBoxLayout()
        urgent_layout.setSpacing(10)
        self.urgent_checkbox = QtWidgets.QCheckBox("Urgent Delivery")
        urgent_layout.addWidget(self.urgent_checkbox)
        urgent_layout.addStretch(1)
        self.expected_delivery_input = QtWidgets.QDateEdit()
        self.expected_delivery_input.setCalendarPopup(True)
        self.expected_delivery_input.setDate(QtCore.QDate.currentDate())
        self.expected_delivery_input.setEnabled(False)
        urgent_layout.addWidget(QtWidgets.QLabel("Expected Delivery Date:"))
        urgent_layout.addWidget(self.expected_delivery_input)
        fabric_delivery_outer_layout.addLayout(urgent_layout)

        fabric_delivery_group.setLayout(fabric_delivery_outer_layout)
        # Removed setSizePolicy Maximum
        content_layout.addWidget(fabric_delivery_group) # Add to scroll layout

        # Connect checkbox signal *after* date input exists
        self.urgent_checkbox.stateChanged.connect(self.toggle_expected_delivery)

        # --- Tailor Instructions GroupBox ---
        instructions_group = QtWidgets.QGroupBox("Tailor Instructions")
        instructions_layout = QtWidgets.QVBoxLayout(instructions_group)
        instructions_layout.setContentsMargins(10, 10, 10, 10)
        self.instructions_input = QtWidgets.QTextEdit()
        self.instructions_input.setPlaceholderText("Special notes for tailor (e.g., Use double stitch, Add inner lining)")
        self.instructions_input.setMinimumHeight(60)
        instructions_layout.addWidget(self.instructions_input)
        # Instructions group should naturally size, but allow text edit to expand if needed
        instructions_group.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        content_layout.addWidget(instructions_group) # Add to scroll layout

        # --- Save Button ---
        self.save_measurement_btn = QtWidgets.QPushButton("Save Measurement")
        self.save_measurement_btn.clicked.connect(self.save_measurement)
        content_layout.addWidget(self.save_measurement_btn) # Add to scroll layout
        
        # Add stretch inside the scrollable area if needed, though AlignTop might be enough
        # content_layout.addStretch(1) 
        
        # Set the container widget for the scroll area
        scroll_area.setWidget(scroll_content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        screen_layout.addWidget(scroll_area)

        self.content_stack.addWidget(measurement_screen)
        self.update_measurement_fields() # Initial call to show correct fields

    def toggle_expected_delivery(self):
        # Ensure date input exists before enabling/disabling
        if hasattr(self, 'expected_delivery_input'):
            self.expected_delivery_input.setEnabled(self.urgent_checkbox.isChecked())

    def refresh_measurement_customers(self):
        from database import DB_PATH
        import sqlite3
        self.measure_customer_combo.clear()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, naap_number, full_name, mobile_number FROM customers ORDER BY full_name ASC")
        customers = c.fetchall()
        for cid, naap, name, mobile in customers:
            self.measure_customer_combo.addItem(f"{naap} - {name} ({mobile})", cid)
        conn.close()

    def init_measurement_fields(self):
        # Define all possible fields for Shalwar Kameez/Kurta
        self.measure_inputs = {}
        labels = [
            ("Length (Lambai)", "length"),
            ("Width (Chorai)", "width"),
            ("Chest (Chati)", "chest"),
            ("Waist (Tera)", "waist"),
            ("Sleeve (Bazo)", "sleeve"),
            ("Neck (Gala)", "neck"),
            ("Shalwar (Waist)", "shalwar_waist"),
            ("Pancha (Ankle width)", "pancha"),
        ]
        
        # Stylesheet without max-width
        input_stylesheet = """
            QLineEdit {
                font-size: 14px;
                padding: 4px 6px;
                min-height: 26px;
                max-height: 30px;
            }
        """
        combo_stylesheet = """
            QComboBox {
                font-size: 14px;
                padding: 4px 6px;
                min-height: 26px;
                max-height: 30px;
            }
            QComboBox::drop-down {
                min-width: 20px;
            }
        """
        
        for label, key in labels:
            self.measure_inputs[key] = QtWidgets.QLineEdit()
            self.measure_inputs[key].setPlaceholderText("inches")
            self.measure_inputs[key].setStyleSheet(input_stylesheet)
            # Optional: Set specific validators like QDoubleValidator if needed
            # self.measure_inputs[key].setValidator(QtGui.QDoubleValidator(0.0, 100.0, 2))
        
        self.collar_type_combo = QtWidgets.QComboBox()
        self.collar_type_combo.addItems(["Ban collar", "2 Piece collar", "Other"])
        self.collar_type_combo.setStyleSheet(combo_stylesheet)
        self.stitch_type_combo = QtWidgets.QComboBox()
        self.stitch_type_combo.addItems(["Single", "Double", "Designer"])
        self.stitch_type_combo.setStyleSheet(combo_stylesheet)

    def update_measurement_fields(self):
        # Get the layouts for the SK groups
        sk_measurements_layout = self.sk_measurements_group.layout()
        sk_style_layout = self.sk_style_group.layout()

        # Clear previous fields from the specific group layouts
        if sk_measurements_layout is not None:
            while sk_measurements_layout.count():
                item = sk_measurements_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
            else:
                    clear_grid_layout(item.layout()) # Recursively clear nested layouts if any
        
        dress_type = self.dress_type_combo.currentText()

        if dress_type in ["Shalwar Kameez", "Kurta"]:
            # Ensure layouts exist before adding rows
            if not isinstance(sk_measurements_layout, QtWidgets.QGridLayout) or \
               not isinstance(sk_style_layout, QtWidgets.QGridLayout):
                print("ERROR: Measurement/Style layout is not QGridLayout in update_measurement_fields")    
                return # Avoid crash
            
            # Populate and show SK groups
            row_index = 0
            sk_measurements_layout.addWidget(QtWidgets.QLabel("Length (Lambai):"), row_index, 0)
            sk_measurements_layout.addWidget(self.measure_inputs["length"], row_index, 1)
            row_index += 1
            sk_measurements_layout.addWidget(QtWidgets.QLabel("Width (Chorai):"), row_index, 0)
            sk_measurements_layout.addWidget(self.measure_inputs["width"], row_index, 1)
            row_index += 1
            sk_measurements_layout.addWidget(QtWidgets.QLabel("Chest (Chati):"), row_index, 0)
            sk_measurements_layout.addWidget(self.measure_inputs["chest"], row_index, 1)
            row_index += 1
            sk_measurements_layout.addWidget(QtWidgets.QLabel("Waist (Tera):"), row_index, 0)
            sk_measurements_layout.addWidget(self.measure_inputs["waist"], row_index, 1)
            row_index += 1
            sk_measurements_layout.addWidget(QtWidgets.QLabel("Sleeve (Bazo):"), row_index, 0)
            sk_measurements_layout.addWidget(self.measure_inputs["sleeve"], row_index, 1)
            row_index += 1
            sk_measurements_layout.addWidget(QtWidgets.QLabel("Neck (Gala):"), row_index, 0)
            sk_measurements_layout.addWidget(self.measure_inputs["neck"], row_index, 1)
            row_index += 1
            sk_measurements_layout.addWidget(QtWidgets.QLabel("Shalwar (Waist):"), row_index, 0)
            sk_measurements_layout.addWidget(self.measure_inputs["shalwar_waist"], row_index, 1)
            row_index += 1
            sk_measurements_layout.addWidget(QtWidgets.QLabel("Pancha (Ankle width):"), row_index, 0)
            sk_measurements_layout.addWidget(self.measure_inputs["pancha"], row_index, 1)

            row_index = 0 # Reset for style layout
            sk_style_layout.addWidget(QtWidgets.QLabel("Collar Type:"), row_index, 0)
            sk_style_layout.addWidget(self.collar_type_combo, row_index, 1)
            row_index += 1
            sk_style_layout.addWidget(QtWidgets.QLabel("Stitch Type:"), row_index, 0)
            sk_style_layout.addWidget(self.stitch_type_combo, row_index, 1)

            self.sk_measurements_group.setVisible(True)
            self.sk_style_group.setVisible(True)
            self.placeholder_widget.setVisible(False)
        else:
            # Hide SK groups and show placeholder
            self.sk_measurements_group.setVisible(False)
            self.sk_style_group.setVisible(False)
            self.placeholder_widget.setVisible(True)

    def save_measurement(self):
        from database import DB_PATH
        expected_delivery_date = self.expected_delivery_input.date().toString("yyyy-MM-dd") if urgent_delivery else None
        # Gather measurements
        if dress_type in ["Shalwar Kameez", "Kurta"]:
            measurements = {k: self.measure_inputs[k].text().strip() for k in self.measure_inputs}
        else:
            measurements = {}
        measurements_json = json.dumps(measurements)
        date_created = QtCore.QDate.currentDate().toString("yyyy-MM-dd")
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO measurements (customer_id, dress_type, measurements, collar_type, stitch_type, fabric_type, tailor_instructions, urgent_delivery, expected_delivery_date, date_created) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (customer_id, dress_type, measurements_json, collar_type, stitch_type, fabric_type, tailor_instructions, urgent_delivery, expected_delivery_date, date_created))
            conn.commit()
            conn.close()
            QtWidgets.QMessageBox.information(self, "Success", "Measurement saved successfully.")
            # Clear fields
            for key in self.measure_inputs:
                self.measure_inputs[key].clear()
            self.instructions_input.clear()
            self.fabric_type_combo.setCurrentIndex(0)
            self.urgent_checkbox.setChecked(False)
            self.expected_delivery_input.setDate(QtCore.QDate.currentDate())
            self.update_dashboard_stats() # Update dashboard after saving measurement
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save measurement:\n{e}")

    def init_history_screen(self):
        history_screen = QtWidgets.QWidget() # Create the main widget for this screen
        layout = QtWidgets.QVBoxLayout(history_screen) # Set layout on the screen widget
        
        # --- Search Bar ---
        search_layout = QtWidgets.QHBoxLayout()
        self.history_search_input = QtWidgets.QLineEdit()
        self.history_search_input.setPlaceholderText("Search by name, mobile, or date (YYYY-MM-DD)...")
        self.history_search_btn = QtWidgets.QPushButton("Search")
        self.history_search_btn.clicked.connect(self.search_history)
        search_layout.addWidget(self.history_search_input)
        search_layout.addWidget(self.history_search_btn)
        layout.addLayout(search_layout)
        # --- History Table ---
        self.history_table = QtWidgets.QTableWidget()
        # Updated columns for unified view: Type, ID (Meas/Order), Naap, Customer, Details (Dress/Price), Date, Status
        self.history_table.setColumnCount(7) 
        self.history_table.setHorizontalHeaderLabels(["Type", "ID", "Naap", "Customer", "Details", "Date", "Status"])
        self.history_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.history_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.history_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.history_table)
        # --- Edit Button ---
        self.edit_measurement_btn = QtWidgets.QPushButton("Edit Selected Measurement")
        self.edit_measurement_btn.clicked.connect(self.edit_selected_measurement)
        layout.addWidget(self.edit_measurement_btn)
        # --- Buttons Row ---
        buttons_layout = QtWidgets.QHBoxLayout()
        self.view_details_btn = QtWidgets.QPushButton("View Details")
        self.view_details_btn.clicked.connect(self.show_measurement_details)
        buttons_layout.addWidget(self.view_details_btn)
        self.print_btn = QtWidgets.QPushButton("Print")
        self.print_btn.clicked.connect(self.print_measurement)
        buttons_layout.addWidget(self.print_btn)
        self.export_pdf_btn = QtWidgets.QPushButton("Export PDF")
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        buttons_layout.addWidget(self.export_pdf_btn)
        self.export_excel_btn = QtWidgets.QPushButton("Export Excel")
        self.export_excel_btn.clicked.connect(self.export_excel)
        buttons_layout.addWidget(self.export_excel_btn)
        layout.addLayout(buttons_layout)
        
        # Add the created screen widget to the stack
        self.content_stack.addWidget(history_screen)
        
        # Load initial data - deferred to show_history()
        # self.load_history()

    def load_history(self, search_term=None):
        from database import DB_PATH
        import sqlite3, json
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if search_term:
            c.execute("""
                SELECT m.id, c.naap_number, c.full_name, c.mobile_number, m.dress_type, m.measurements, m.date_created
                FROM measurements m
                JOIN customers c ON m.customer_id = c.id
                WHERE c.full_name LIKE ? OR c.mobile_number LIKE ? OR c.naap_number LIKE ? OR m.date_created LIKE ?
                ORDER BY m.date_created DESC, m.id DESC
            """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        else:
            c.execute("""
                SELECT m.id, c.naap_number, c.full_name, c.mobile_number, m.dress_type, m.measurements, m.date_created
                FROM measurements m
                JOIN customers c ON m.customer_id = c.id
                ORDER BY m.date_created DESC, m.id DESC
            """)
        rows = c.fetchall()
        conn.close()
        self.history_table.setRowCount(len(rows))
        for row_idx, (mid, naap, name, mobile, dress_type, measurements_json, date_created) in enumerate(rows):
            summary = self.get_measurement_summary(measurements_json)
            for col_idx, value in enumerate([mid, naap, f"{name} ({mobile})", dress_type, date_created, summary]):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.history_table.setItem(row_idx, col_idx, item)

    def get_measurement_summary(self, measurements_json):
        import json
        try:
            m = json.loads(measurements_json)
            # Show a few key fields as summary
            summary = ", ".join([f"Lambai: {m.get('length','')}", f"Chati: {m.get('chest','')}", f"Bazo: {m.get('sleeve','')}"])
            return summary
        except Exception:
            return "-"

    def show_measurement_details(self):
        import json # Import json module
        selected = self.history_table.currentRow()
        if selected == -1:
            QtWidgets.QMessageBox.information(self, "No Selection", "Select a record to view details.")
            return
        details_dict = self.get_measurement_details(mid) # Get dictionary
        if details_dict:
            # Format the dictionary into a string for display
            details_str = f"Naap Number: {details_dict['naap_number']}\nDress Type: {details_dict['dress_type']}\nDate: {details_dict['date_created']}\n"
            details_str += f"Customer: {details_dict['customer_name']} ({details_dict['customer_mobile']})\n" # Add customer name/mobile
            details_str += f"Collar Type: {details_dict['collar_type'] or 'N/A'}\nStitch Type: {details_dict['stitch_type'] or 'N/A'}\nFabric Type: {details_dict['fabric_type'] or 'N/A'}\n"
            details_str += f"Urgent Delivery: {'Yes' if details_dict['urgent_delivery'] else 'No'}\n"
            if details_dict['urgent_delivery']:
                details_str += f"Expected Delivery Date: {details_dict['expected_delivery_date']}\n"
            details_str += f"\nTailor Instructions:\n{details_dict['tailor_instructions'] or 'None'}\n"
            details_str += "\nMeasurements:\n"
            measurements = json.loads(details_dict['measurements'])
            for k, v in measurements.items():
                details_str += f"  {k.replace('_', ' ').title()}: {v}\n"
            QtWidgets.QMessageBox.information(self, "Measurement Details", details_str)
        else:
            QtWidgets.QMessageBox.warning(self, "Not Found", "Measurement record not found.")

    def get_measurement_details(self, mid):
        from database import DB_PATH
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        # Use row factory for easy dict conversion
        conn.row_factory = sqlite3.Row 
        c = conn.cursor()
        try:
            c.execute("""
                SELECT m.*, c.naap_number, c.full_name as customer_name, c.mobile_number as customer_mobile
                FROM measurements m 
                JOIN customers c ON m.customer_id = c.id 
                WHERE m.id = ?
            """, (mid,))
            row = c.fetchone()
            if row:
                # Convert row object to dictionary
                return dict(row)
            else:
                return None
        except Exception as e:
            print(f"Error getting measurement details: {e}")
            return None
        finally:
            conn.close()

    def edit_selected_measurement(self):
        import json # Import json module
        selected = self.history_table.currentRow()
        if selected == -1:
            QtWidgets.QMessageBox.information(self, "No Selection", "Select a measurement to edit.")
            return
        mid = self.history_table.item(selected, 0).text()
        # Fetch full details as dict
        details_dict = self.get_measurement_details(mid)
        if not details_dict:
             QtWidgets.QMessageBox.warning(self, "Error", "Could not retrieve full details for editing.")
             return

        # Switch to the measurement screen
        self.show_add_measurement()

        # Populate fields using correct variable names and data from dict
        customer_id = details_dict['customer_id']
        dress_type = details_dict['dress_type']
        measurements_json = details_dict['measurements']
        collar_type = details_dict['collar_type']
        stitch_type = details_dict['stitch_type']
        fabric_type = details_dict['fabric_type']
        tailor_instructions = details_dict['tailor_instructions']
        urgent_delivery = details_dict['urgent_delivery']
        expected_delivery_date = details_dict['expected_delivery_date']

        # Set fields on the measurement screen (self.content_stack index 2)
        idx = self.measure_customer_combo.findData(customer_id)
        if idx >= 0:
            self.measure_customer_combo.setCurrentIndex(idx)
            
        self.dress_type_combo.setCurrentText(dress_type)
        self.update_measurement_fields() # Ensure correct fields are visible

        measurements = json.loads(measurements_json)
        for k, field_widget in self.measure_inputs.items(): # Use correct dict: measure_inputs
            field_widget.setText(measurements.get(k, ""))
            
        # Check if collar/stitch combos exist before setting (they depend on dress type)
        if dress_type in ["Shalwar Kameez", "Kurta"]:
             if hasattr(self, 'collar_type_combo') and collar_type:
                 self.collar_type_combo.setCurrentText(collar_type)
             if hasattr(self, 'stitch_type_combo') and stitch_type:
                 self.stitch_type_combo.setCurrentText(stitch_type)

        if fabric_type:
            self.fabric_type_combo.setCurrentText(fabric_type)
            
        self.instructions_input.setPlainText(tailor_instructions or "")
        self.urgent_checkbox.setChecked(bool(urgent_delivery))
        
        # Update date input state based on checkbox AFTER setting the check state
        self.toggle_expected_delivery() 
        
        if urgent_delivery and expected_delivery_date:
            from PyQt5.QtCore import QDate
            self.expected_delivery_input.setDate(QDate.fromString(expected_delivery_date, "yyyy-MM-dd"))
        else:
            self.expected_delivery_input.setDate(QtCore.QDate.currentDate())
            
        # Store the ID of the measurement being edited to use in save_measurement
        # This requires modifying save_measurement to handle updates
        self.editing_measurement_id = mid 
        self.save_measurement_btn.setText("Update Measurement") # Change button text

    def print_measurement(self):
        import json # Import json module
        selected = self.history_table.currentRow()
        if selected == -1:
            QtWidgets.QMessageBox.information(self, "No Selection", "Select a record to print.")
            return
        mid = self.history_table.item(selected, 0).text()
        # Reuse the formatted string generation logic from show_measurement_details
        details_dict = self.get_measurement_details(mid)
        if details_dict:
            details_str = f"Naap Number: {details_dict['naap_number']}\nDress Type: {details_dict['dress_type']}\nDate: {details_dict['date_created']}\n"
            details_str += f"Customer: {details_dict['customer_name']} ({details_dict['customer_mobile']})\n" # Add customer name/mobile
            details_str += f"Collar Type: {details_dict['collar_type'] or 'N/A'}\nStitch Type: {details_dict['stitch_type'] or 'N/A'}\nFabric Type: {details_dict['fabric_type'] or 'N/A'}\n"
            details_str += f"Urgent Delivery: {'Yes' if details_dict['urgent_delivery'] else 'No'}\n"
            if details_dict['urgent_delivery']:
                details_str += f"Expected Delivery Date: {details_dict['expected_delivery_date']}\n"
            details_str += f"\nTailor Instructions:\n{details_dict['tailor_instructions'] or 'None'}\n"
            details_str += "\nMeasurements:\n"
            try: # Added try-except for safety during revert
                measurements = json.loads(details_dict['measurements'])
                for k, v in measurements.items():
                    details_str += f"  {k.replace('_', ' ').title()}: {v}\n"
            except json.JSONDecodeError:
                details_str += "  Error decoding measurements.\n"
        else:
            QtWidgets.QMessageBox.warning(self, "Not Found", "Measurement record not found.")
            return
            
        # Import QPrintDialog from the correct module
        from PyQt5.QtPrintSupport import QPrintDialog
        dialog = QPrintDialog()
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            printer = dialog.printer()
            doc = QtGui.QTextDocument() # Use QtGui for rich text

            # Build slightly more structured HTML with bold labels
            html_lines = []
            html_lines.append("<h1>Measurement Details</h1>")
            html_lines.append(f"<b>Naap Number:</b> {details_dict.get('naap_number', 'N/A')}<br>")
            html_lines.append(f"<b>Customer:</b> {details_dict.get('customer_name', 'N/A')} ({details_dict.get('customer_mobile', 'N/A')})<br>")
            html_lines.append(f"<b>Order Date:</b> {details_dict.get('date_created', 'N/A')}<br>")
            html_lines.append(f"<b>Dress Type:</b> {details_dict.get('dress_type', 'N/A')}<br><br>") # Add extra break

            html_lines.append(f"<b>Collar Type:</b> {details_dict.get('collar_type', 'N/A') or 'N/A'}<br>")
            html_lines.append(f"<b>Stitch Type:</b> {details_dict.get('stitch_type', 'N/A') or 'N/A'}<br>")
            html_lines.append(f"<b>Fabric Type:</b> {details_dict.get('fabric_type', 'N/A') or 'N/A'}<br>")
            html_lines.append(f"<b>Urgent:</b> {'Yes' if details_dict.get('urgent_delivery') else 'No'}<br>")
            if details_dict.get('urgent_delivery'):
                 html_lines.append(f"<b>Delivery Date:</b> {details_dict.get('expected_delivery_date', 'N/A')}<br>")
            html_lines.append("<br>") # Add extra break

            html_lines.append("<b><u>Measurements (inches):</u></b><br>")
            try:
                if measurements:
                    for k, v in measurements.items():
                        label = k.replace('_', ' ').title()
                        html_lines.append(f"&nbsp;&nbsp;<b>{label}:</b> {v}<br>")
                else:
                    html_lines.append("&nbsp;&nbsp;No measurements recorded.<br>")
            except json.JSONDecodeError:
                html_lines.append("&nbsp;&nbsp;Invalid measurement data.<br>")
            html_lines.append("<br>") # Add extra break

            instructions = details_dict.get('tailor_instructions')
            if instructions:
                html_lines.append("<b><u>Tailor Instructions:</u></b><br>")
                # Replace newlines in instructions with <br>, escape HTML
                instructions_safe = instructions.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
                html_lines.append(f"{instructions_safe}<br>")

            html_content = "".join(html_lines)

            doc.setHtml(html_content)
            # Optional: Set page size if needed
            # from PyQt5.QtCore import QSizeF, QMarginsF

    def export_pdf(self):
        """
        Export the selected measurement record as a PDF with improved error handling and formatting.
        Adds logo if available (PNG only), checks for missing fields, and gives user feedback.
        """
        from fpdf import FPDF
        import json, os
        from PyQt5 import QtWidgets, QtCore
        
        selected = self.history_table.currentRow()
        if selected == -1:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a measurement to export.")
            return
        
        mid = self.history_table.item(selected, 0).text()
        details_dict = self.get_measurement_details(mid)
        
        if not details_dict:
            QtWidgets.QMessageBox.critical(self, "Error", "Could not retrieve measurement details.")
            return
        
        # Extract and validate data from dictionary
        def safe_get(key, default="N/A"):
            val = details_dict.get(key)
            return val if val not in (None, "") else default
    
        naap_number = safe_get('naap_number')
        customer_name = safe_get('customer_name')
        date = safe_get('date_created')
        dress_type = safe_get('dress_type')
        measurements_json = safe_get('measurements', '{}')
        tailor_instructions = safe_get('tailor_instructions', "")
        collar_type = safe_get('collar_type')
        stitch_type = safe_get('stitch_type')
        fabric_type = safe_get('fabric_type')
        urgent = "Yes" if details_dict.get('urgent_delivery') else "No"
        delivery_date = details_dict.get('expected_delivery_date') if details_dict.get('urgent_delivery') else "N/A"
        
        # Ask for file location
        default_filename = f"TM_Measurement_{naap_number}_{customer_name.replace(' ', '_')}.pdf"
        filepath, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save PDF", default_filename, "PDF Files (*.pdf)")
        if not filepath:
            return  # User cancelled

        try:
            pdf = FPDF()
            pdf.add_page()

            # Try to add app logo if PNG exists (ICO not supported by FPDF)
            logo_path = os.path.join(os.path.dirname(__file__), "resources", "app_logo.png")
            if os.path.exists(logo_path):
                try:
                    pdf.image(logo_path, x=10, y=8, w=20)
                    pdf.ln(15)
                except Exception as e:
                    pass
                    print(f"Could not add logo to PDF: {e}")

            # Title
            pdf.set_font("Arial", 'B', size=16)
            pdf.cell(0, 10, "Tailor Master Measurement Sheet", ln=True, align='C')
            pdf.ln(5)

            # Customer Info Table
            pdf.set_font("Arial", 'B', size=12)
            pdf.cell(40, 8, "Naap Number:", border=1)
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 8, str(naap_number), border=1, ln=True)

            pdf.set_font("Arial", 'B', size=12)
            pdf.cell(40, 8, "Customer:", border=1)
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 8, customer_name, border=1, ln=True)

            pdf.set_font("Arial", 'B', size=12)
            pdf.cell(40, 8, "Date:", border=1)
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 8, date, border=1, ln=True)

            pdf.set_font("Arial", 'B', size=12)
            pdf.cell(40, 8, "Dress Type:", border=1)
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 8, dress_type, border=1, ln=True)

            pdf.ln(5)

            # Other Details Table
            pdf.set_font("Arial", 'B', size=12)
            pdf.cell(40, 8, "Collar Type:", border=1)
            pdf.set_font("Arial", size=12)
            pdf.cell(55, 8, collar_type, border=1)
            pdf.set_font("Arial", 'B', size=12)
            pdf.cell(40, 8, "Stitch Type:", border=1)
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 8, stitch_type, border=1, ln=True)

            pdf.set_font("Arial", 'B', size=12)
            pdf.cell(40, 8, "Fabric Type:", border=1)
            pdf.set_font("Arial", size=12)
            pdf.cell(55, 8, fabric_type, border=1)
            pdf.set_font("Arial", 'B', size=12)
            pdf.cell(40, 8, "Urgent:", border=1)
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 8, urgent, border=1, ln=True)

            if details_dict.get('urgent_delivery'):
                pdf.set_font("Arial", 'B', size=12)
                pdf.cell(40, 8, "Delivery Date:", border=1)
                pdf.set_font("Arial", size=12)
                pdf.cell(0, 8, delivery_date, border=1, ln=True)

            pdf.ln(10)

            # Measurements Section
            pdf.set_font("Arial", 'B', size=14)
            pdf.cell(0, 10, "Measurements", ln=True, align='C')
            pdf.ln(2)

            # Output measurement values in two columns
            pdf.set_font("Arial", size=12)
            try:
                measurements = json.loads(measurements_json)
            except Exception as e:
                measurements = {}
                print(f"Could not parse measurements JSON: {e}")
            col_width = pdf.w / 2 - pdf.l_margin - pdf.r_margin - 2
            keys = list(measurements.keys())
            for i in range(0, len(keys), 2):
                key1 = keys[i]
                val1 = measurements[key1]
                formatted_key1 = key1.replace('_', ' ').title()
                pdf.cell(col_width, 8, f"{formatted_key1}: {val1}", border=1, align='L')
                if i + 1 < len(keys):
                    key2 = keys[i+1]
                    val2 = measurements[key2]
                    formatted_key2 = key2.replace('_', ' ').title()
                    pdf.cell(col_width, 8, f"{formatted_key2}: {val2}", border=1, align='L', ln=True)
                else:
                    pdf.ln(8)

            # Add notes if available
            if tailor_instructions:
                pdf.ln(10)
                pdf.set_font("Arial", 'B', size=14)
                pdf.cell(0, 10, "Tailor Instructions:", ln=True)
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 8, tailor_instructions, border=1)

            # Output to file
            pdf.output(filepath)

            # Open the file and notify user
            QtWidgets.QMessageBox.information(self, "Success", f"PDF exported successfully to:\n{filepath}")
            try:
                import platform
                if platform.system() == "Windows":
                    os.startfile(filepath)
                elif platform.system() == "Darwin":
                    import subprocess
                    subprocess.call(('open', filepath))
                elif platform.system() == "Linux":
                    import subprocess
                    subprocess.call(('xdg-open', filepath))
            except Exception as e:
                print(f"Could not open PDF automatically: {e}")

        except ImportError:
            QtWidgets.QMessageBox.critical(self, "Missing Library", "The 'fpdf' library is required to export PDFs. Please install it (`pip install fpdf`).")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export Error", f"Failed to export PDF:\n{str(e)}")

    def export_excel(self):
        from database import DB_PATH
        import sqlite3, pandas as pd
        import os # Import os for platform check
        import subprocess # Import subprocess for Linux/macOS open

        # Ask user for filename first
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Excel File", "tmms_export.xlsx", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if not filename:
                return # User cancelled

        try:
            conn = sqlite3.connect(DB_PATH)
            # Fetch data using JOIN to get customer info and decode JSON measurements
            query = """
                SELECT 
                    m.id AS MeasurementID, 
                    c.naap_number AS NaapNumber, 
                    c.full_name AS CustomerName, 
                    c.mobile_number AS MobileNumber, 
                    m.dress_type AS DressType, 
                    m.measurements AS MeasurementsJSON, 
                    m.collar_type AS CollarType,
                    m.stitch_type AS StitchType,
                    m.fabric_type AS FabricType,
                    m.tailor_instructions AS Instructions,
                    m.urgent_delivery AS UrgentDelivery,
                    m.expected_delivery_date AS DeliveryDate,
                    m.date_created AS DateCreated
                FROM measurements m
                JOIN customers c ON m.customer_id = c.id
                ORDER BY m.date_created DESC, m.id DESC
            """
            
            # Use pandas to read directly from SQL query
            df = pd.read_sql_query(query, conn)
            conn.close()

            if df.empty:
                QtWidgets.QMessageBox.information(self, "No Data", "No measurement records found in the database to export.")
                return

            # Process the JSON measurements column
            def parse_measurements(json_str):
                try:
                    return json.loads(json_str)
                except (json.JSONDecodeError, TypeError):
                    return {} # Return empty dict on error
            measurements_parsed = df['MeasurementsJSON'].apply(parse_measurements)
            
            # Expand the measurements dictionary into separate columns
            measurements_df = pd.json_normalize(measurements_parsed).add_prefix('Meas_')
            
            # Combine the expanded measurements with the original dataframe (dropping the JSON column)
            df_final = pd.concat([df.drop(columns=['MeasurementsJSON']), measurements_df], axis=1)

            # Reorder columns for better readability (optional)
            core_cols = ['MeasurementID', 'NaapNumber', 'CustomerName', 'MobileNumber', 'DressType', 'DateCreated']
            detail_cols = ['CollarType', 'StitchType', 'FabricType', 'Instructions', 'UrgentDelivery', 'DeliveryDate']
            meas_cols = [col for col in df_final.columns if col.startswith('Meas_')]
            final_col_order = core_cols + detail_cols + meas_cols
             # Ensure all expected columns exist before reordering
            final_col_order = [col for col in final_col_order if col in df_final.columns]
            df_final = df_final[final_col_order]


            # Export to Excel
            df_final.to_excel(filename, index=False)
            QtWidgets.QMessageBox.information(self, "Export Complete", f"Data exported successfully to:\n{filename}")
            
            # Try to open the file
            try:
                if platform.system() == "Windows":
                    os.startfile(filename)
                elif platform.system() == "Darwin": # macOS
                    subprocess.call(('open', filename))
                else: # Linux
                    subprocess.call(('xdg-open', filename))
            except Exception as e:
                pass

        except ImportError:
            QtWidgets.QMessageBox.critical(self, "Missing Library", "The 'pandas' library is required for Excel export. Please install it (`pip install pandas openpyxl`).")
        except sqlite3.Error as e:
             QtWidgets.QMessageBox.critical(self, "Database Error", f"Failed to read data from database:\n{str(e)}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export Error", f"Failed to export Excel file:\n{str(e)}")

    def init_settings_screen(self):
        settings_screen = QtWidgets.QWidget() # Create the main widget
        layout = QtWidgets.QVBoxLayout(settings_screen) # Set layout on the widget
        layout.setAlignment(QtCore.Qt.AlignTop) # Align groups to top
        
        # GroupBox for Backup/Restore
        backup_group = QtWidgets.QGroupBox("Backup & Restore")
        backup_layout = QtWidgets.QVBoxLayout(backup_group)

        # --- Backup Button ---
        self.backup_btn = QtWidgets.QPushButton("Backup Database Now")
        self.backup_btn.clicked.connect(self.backup_database)
        backup_layout.addWidget(self.backup_btn)
        # --- Restore Button ---
        self.restore_btn = QtWidgets.QPushButton("Restore Database from Backup")
        self.restore_btn.clicked.connect(self.restore_database)
        backup_layout.addWidget(self.restore_btn)
        # --- Last Backup Label ---
        self.last_backup_label = QtWidgets.QLabel("Last auto-backup: Never") # Initialize text
        self.last_backup_label.setStyleSheet("color: #555; font-style: italic; margin-top: 5px;")
        backup_layout.addWidget(self.last_backup_label)
        # --- Info Label ---
        backup_info = QtWidgets.QLabel("Backup creates a safe copy. Restore overwrites current data with a selected backup.")
        backup_info.setWordWrap(True)
        backup_layout.addWidget(backup_info)
        
        layout.addWidget(backup_group)

        # GroupBox for Import/Export
        data_group = QtWidgets.QGroupBox("Data Import & Export")
        data_layout = QtWidgets.QVBoxLayout(data_group)
        
        # --- Export Data Button ---
        self.export_data_btn = QtWidgets.QPushButton("Export All Data (JSON)")
        self.export_data_btn.clicked.connect(self.export_data)
        data_layout.addWidget(self.export_data_btn)
        # --- Import Data Button ---
        self.import_data_btn = QtWidgets.QPushButton("Import Data (JSON)")
        self.import_data_btn.clicked.connect(self.import_data)
        data_layout.addWidget(self.import_data_btn)
        # --- Info Label ---
        data_info = QtWidgets.QLabel("Export saves all customers and measurements to a JSON file. Import loads data from a JSON file (can replace or merge).")
        data_info.setWordWrap(True)
        data_layout.addWidget(data_info)

        layout.addWidget(data_group)

        layout.addStretch(1) # Push groups to the top
        
        # Add the screen widget to the content stack
        self.content_stack.addWidget(settings_screen)
        
        # Update backup label initially
        self.update_last_backup_label()

    def backup_database(self):
        from database import DB_PATH
        from datetime import datetime
        import os
        import shutil
        
        try:
            # Create backup directory if it doesn't exist
            backup_dir = os.path.join(os.path.dirname(__file__), "backups")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Create backup with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"tmms_backup_{timestamp}.db")
            
            # Copy the database file
            shutil.copy2(DB_PATH, backup_path)
            
            # Update last backup time
            self.last_backup_time = datetime.now()
            self.update_last_backup_label()
            
            QtWidgets.QMessageBox.information(self, "Backup Complete", f"Database backed up to:\n{backup_path}")
            return
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Backup Failed", f"Error during backup:\n{str(e)}")
            return

    def restore_database(self):
        from database import DB_PATH
        import os
        import shutil
        
        # First create a backup of current database
        self.backup_database()
        
        # Select backup file
        backup_dir = os.path.join(os.path.dirname(__file__), "backups")
        if not os.path.exists(backup_dir):
            QtWidgets.QMessageBox.warning(self, "No Backups", "No backup directory found.")
            return
        
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Backup File", backup_dir, "SQLite Database (*.db)")
        
        if not filepath:
                return False
        
        try:
            # Confirm restore
            confirm = QtWidgets.QMessageBox.question(
                self, "Confirm Restore", 
                "This will overwrite the current database with the selected backup.\nAre you sure you want to continue?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if confirm == QtWidgets.QMessageBox.Yes:
                # Copy backup to main database file
                shutil.copy2(filepath, DB_PATH)
                
                QtWidgets.QMessageBox.information(self, "Restore Complete", 
                    "Database has been restored from backup.\nRestart the application to see changes.")
                return True
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Restore Failed", f"Error during restore:\n{str(e)}")
        return False

    def automatic_backup(self):
        import os, shutil, datetime
        from database import DB_PATH
        backup_dir = os.path.join(os.path.dirname(DB_PATH), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"tmms_autobackup_{timestamp}.db")
        try:
            shutil.copy2(DB_PATH, backup_path)
            self.last_backup_time = datetime.datetime.now()
            self.update_last_backup_label()
        except Exception as e:
            print(f"Auto-backup failed: {e}")

    def update_last_backup_label(self):
        # Safer check: ensure attribute exists and is a QLabel instance
        if (
            hasattr(self, 'last_backup_label') 
            and isinstance(self.last_backup_label, QtWidgets.QLabel)
        ):
            # Check if the widget is still valid (hasn't been deleted)
            try:
                # Accessing parent() might still raise RuntimeError if deleted,
                # but checking type first reduces AttributeError risk.
                # A simple check for None might suffice if it's guaranteed to be set to None on deletion.
                if self.last_backup_label.parent() is None and self.last_backup_label.window() is None:
                    # Widget seems to be deleted or not yet fully constructed
                    return
            except RuntimeError:
                # Widget has been deleted
                return

            if self.last_backup_time:
                self.last_backup_label.setText(f"Last auto-backup: {self.last_backup_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                # Check for existing backup files to provide a better initial message
                backup_dir = os.path.join(os.path.dirname(get_db_path()), "backups")
                if os.path.exists(backup_dir) and any(f.endswith(".db") for f in os.listdir(backup_dir)):
                    self.last_backup_label.setText("Last auto-backup: Unknown (backup files exist)")
                else:
                    self.last_backup_label.setText("Last auto-backup: Never")

    def export_data(self):
        from database import DB_PATH
        import sqlite3, json
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Data", "tmms_export.json", "JSON Files (*.json)", options=options)
        if not filename:
            return
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT * FROM customers")
            customers = [dict(zip([d[0] for d in c.description], row)) for row in c.fetchall()]
            c.execute("SELECT * FROM measurements")
            measurements = [dict(zip([d[0] for d in c.description], row)) for row in c.fetchall()]
            conn.close()
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({"customers": customers, "measurements": measurements}, f, indent=2)
            QtWidgets.QMessageBox.information(self, "Export Complete", f"Data exported to:\n{filename}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export Failed", f"Error during export:\n{e}")

    def import_data(self):
        from database import DB_PATH
        import sqlite3, json
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import Data", "", "JSON Files (*.json)", options=options)
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            customers = data.get("customers", [])
            measurements = data.get("measurements", [])
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Import Failed", f"Could not read file:\n{e}")
            return
        # Ask user: Replace or Merge
        choice = QtWidgets.QMessageBox.question(self, "Import Mode", "Replace all existing data with import? (Yes = Replace, No = Merge)", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            if choice == QtWidgets.QMessageBox.Yes:
                c.execute("DELETE FROM measurements")
                c.execute("DELETE FROM customers")
            # Insert customers
            for cust in customers:
                # Avoid duplicate mobile numbers in merge
                c.execute("SELECT id FROM customers WHERE mobile_number = ?", (cust["mobile_number"],))
                exists = c.fetchone()
                if exists and choice == QtWidgets.QMessageBox.No:
                    continue
                c.execute("INSERT INTO customers (id, naap_number, full_name, mobile_number, address, date_of_entry) VALUES (?, ?, ?, ?, ?, ?)",
                          (cust["id"], cust["naap_number"], cust["full_name"], cust["mobile_number"], cust.get("address", ""), cust["date_of_entry"]))
            # Insert measurements
            for meas in measurements:
                # Avoid duplicate by id in merge
                c.execute("SELECT id FROM measurements WHERE id = ?", (meas["id"],))
                exists = c.fetchone()
                if exists and choice == QtWidgets.QMessageBox.No:
                    continue
                c.execute("INSERT INTO measurements (id, customer_id, dress_type, measurements, collar_type, stitch_type, fabric_type, tailor_instructions, urgent_delivery, expected_delivery_date, date_created) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          (meas["id"], meas["customer_id"], meas["dress_type"], meas["measurements"], meas.get("collar_type"), meas.get("stitch_type"), meas.get("fabric_type"), meas.get("tailor_instructions"), meas.get("urgent_delivery"), meas.get("expected_delivery_date"), meas["date_created"]))
            conn.commit()
            conn.close()
            QtWidgets.QMessageBox.information(self, "Import Complete", "Data import finished.")
            self.refresh_measurement_customers()
            self.load_customers()
            self.load_history()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Import Failed", f"Error during import:\n{e}")

    def get_next_naap_number(self):
        """Generates the next sequential Naap Number based on the current year."""
        from database import DB_PATH
        import sqlite3
        from datetime import datetime
 
        current_year = datetime.now().year
        next_number = 1
 
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Check if the counter for the current year exists
            c.execute("SELECT last_number FROM counters WHERE year = ?", (current_year,))
            result = c.fetchone()
            
            if result:
                last_number = result[0]
                next_number = last_number + 1
                # Update the counter
                c.execute("UPDATE counters SET last_number = ? WHERE year = ?", (next_number, current_year))
            else:
                # Insert a new counter for the year
                c.execute("INSERT INTO counters (year, last_number) VALUES (?, ?)", (current_year, next_number))
            
            conn.commit()
            conn.close()
            
            # Format as YYYY-NNNN (e.g., 2023-0001)
            return f"{current_year}-{next_number:04d}"
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Database Error", f"Failed to generate Naap Number: {e}")
            return
 
    def save_customer(self):
        """Saves the customer details entered in the form to the database."""
        from database import DB_PATH
        import sqlite3
 
        name = self.name_input.text().strip()
        mobile = self.mobile_input.text().strip()
        address = self.address_input.text().strip()
        date_of_entry = self.date_input.date().toString("yyyy-MM-dd")
 
        if not name or not mobile:
            QtWidgets.QMessageBox.warning(self, "Missing Information", "Full Name and Mobile Number are required.")
            return
 
        naap_number = self.get_next_naap_number()
        if not naap_number:
                return # Error message already shown by get_next_naap_number
 
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO customers (naap_number, full_name, mobile_number, address, date_of_entry) VALUES (?, ?, ?, ?, ?)",
                      (naap_number, name, mobile, address, date_of_entry))
            conn.commit()
            conn.close()
 
            QtWidgets.QMessageBox.information(self, "Success", f"Customer '{name}' saved successfully with Naap Number: {naap_number}.")
             
            # Clear fields
            self.name_input.clear()
            self.mobile_input.clear()
            self.address_input.clear()
            self.date_input.setDate(QtCore.QDate.currentDate())
             
            # Refresh customer list in table and measurement dropdown
            self.load_customers()
            self.refresh_measurement_customers()
             
        except sqlite3.IntegrityError: # Handles UNIQUE constraint violation for naap_number (shouldn't happen with proper counter)
            QtWidgets.QMessageBox.critical(self, "Error", "Failed to save customer. Generated Naap Number might already exist (contact support).")
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Database Error", f"Failed to save customer: {e}")
             
    def load_customers(self, search_term=None):
        """Loads customers into the table, optionally filtering by search term."""
        from database import DB_PATH
        import sqlite3
 
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            if search_term:
                # Search by name, mobile, or naap number
                # Search by name, mobile, or naap number
                term = f"%{search_term}%"
                c.execute("""
                    FROM customers 
                    WHERE full_name LIKE ? OR mobile_number LIKE ? OR naap_number LIKE ?
                    ORDER BY full_name ASC
                """, (term, term, term))
            else:
                c.execute("SELECT id, naap_number, full_name, mobile_number, date_of_entry FROM customers ORDER BY full_name ASC")
            rows = c.fetchall()
            conn.close()
 
            self.customer_table.setRowCount(len(rows))
            for row_idx, (cid, naap, name, mobile, date_entry) in enumerate(rows):
                self.customer_table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(cid)))
                self.customer_table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(naap))
                self.customer_table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(name))
                self.customer_table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(mobile))
                self.customer_table.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(date_entry))
             
            self.customer_table.resizeColumnsToContents() # Adjust column widths
            self.customer_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch) # Name
            self.customer_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch) # Mobile
                 
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Database Error", f"Failed to load customers: {e}")
             
    def search_customers(self):
        """Filters the customer table based on the search input field."""
        search_term = self.search_input.text().strip()
        self.load_customers(search_term)

    # Initialize placeholder for non-SK measurement types
    def _init_measurement_placeholder(self):
        self.placeholder_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.placeholder_widget)
        label = QtWidgets.QLabel("Measurement fields for this dress type will be added soon.")
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(label)
        self.placeholder_widget.setVisible(False) # Initially hidden

    def init_orders_screen(self):
        """Initializes the screen for managing Orders."""
        print("            DEBUG: Entering init_orders_screen...")
        orders_screen = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout(orders_screen) # Main layout: Form on left, Table on right
        main_layout.setSpacing(15)

        # --- Left Side: Order Creation Form ---
        form_widget = QtWidgets.QWidget()
        form_layout = QtWidgets.QVBoxLayout(form_widget)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setAlignment(QtCore.Qt.AlignTop)

        form_group = QtWidgets.QGroupBox("Create New Order")
        form_grid_layout = QtWidgets.QFormLayout(form_group)
        form_grid_layout.setSpacing(10)

        # Customer Selection
        self.order_customer_combo = QtWidgets.QComboBox()
        form_grid_layout.addRow("Customer:", self.order_customer_combo)

        # Optional Measurement Link (Populate based on selected customer later)
        self.order_measurement_combo = QtWidgets.QComboBox()
        self.order_measurement_combo.addItem("None", None) # Option for no specific measurement
        form_grid_layout.addRow("Measurement (Optional):", self.order_measurement_combo)

        # Dates
        self.order_due_date_input = QtWidgets.QDateEdit()
        self.order_due_date_input.setCalendarPopup(True)
        self.order_due_date_input.setDate(QtCore.QDate.currentDate().addDays(7)) # Default to 1 week later
        form_grid_layout.addRow("Due Date:", self.order_due_date_input)

        # Price & Payment
        price_layout = QtWidgets.QHBoxLayout()
        self.order_price_input = QtWidgets.QDoubleSpinBox() # Use DoubleSpinBox for currency
        self.order_price_input.setPrefix("AED ")
        self.order_price_input.setRange(0, 100000) # Set a reasonable range
        self.order_price_input.setDecimals(2)
        self.order_paid_input = QtWidgets.QDoubleSpinBox()
        self.order_paid_input.setPrefix("AED ")
        self.order_paid_input.setRange(0, 100000)
        self.order_paid_input.setDecimals(2)
        price_layout.addWidget(QtWidgets.QLabel("Price:"))
        price_layout.addWidget(self.order_price_input)
        price_layout.addWidget(QtWidgets.QLabel("Paid:"))
        price_layout.addWidget(self.order_paid_input)
        form_grid_layout.addRow(price_layout)

        # Notes
        self.order_notes_input = QtWidgets.QTextEdit()
        self.order_notes_input.setPlaceholderText("Enter any order-specific notes...")
        self.order_notes_input.setFixedHeight(80) # Make notes slightly taller
        form_grid_layout.addRow("Notes:", self.order_notes_input)

        # Save Button
        self.save_order_btn = QtWidgets.QPushButton("Save Order")
        # self.save_order_btn.clicked.connect(self.save_order) # Connect this later
        form_grid_layout.addRow("", self.save_order_btn)

        form_layout.addWidget(form_group)
        form_layout.addStretch(1)

        # --- Right Side: Orders Table ---
        table_widget = QtWidgets.QWidget()
        table_layout = QtWidgets.QVBoxLayout(table_widget)
        table_layout.setContentsMargins(10, 10, 10, 10)

        table_header_layout = QtWidgets.QHBoxLayout()
        table_header_layout.addWidget(QtWidgets.QLabel("<b>Pending Orders</b>")) # Title
        table_header_layout.addStretch()
        # Add search/filter later if needed

        table_layout.addLayout(table_header_layout)

        self.orders_table = QtWidgets.QTableWidget()
        self.orders_table.setColumnCount(7) # ID, Customer, Price, Paid, Due Date, Status, Payment Status
        self.orders_table.setHorizontalHeaderLabels(["ID", "Customer", "Price", "Paid", "Due Date", "Status", "Payment"]) # Shortened labels
        self.orders_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.orders_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.orders_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.orders_table.verticalHeader().setVisible(False)
        self.orders_table.horizontalHeader().setStretchLastSection(True)
        # Adjust column widths (make Customer wider)
        self.orders_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.orders_table.resizeColumnsToContents()

        table_layout.addWidget(self.orders_table)

        # Buttons for table actions (e.g., Mark Complete, View Details)
        table_actions_layout = QtWidgets.QHBoxLayout()
        self.order_view_details_btn = QtWidgets.QPushButton("View Details")
        self.order_view_details_btn.clicked.connect(self.view_selected_order_details)
        self.order_update_status_btn = QtWidgets.QPushButton("Update Status")
        self.order_update_status_btn.clicked.connect(self.update_selected_order_status)
        table_actions_layout.addWidget(self.order_view_details_btn)
        table_actions_layout.addWidget(self.order_update_status_btn)
        table_actions_layout.addStretch()
        table_layout.addLayout(table_actions_layout)

        # Add left and right widgets to main layout
        main_layout.addWidget(form_widget, 1) # Give form less space
        main_layout.addWidget(table_widget, 2) # Give table more space

        # Add the orders screen widget to the stack
        self.content_stack.addWidget(orders_screen)

        # Populate customer dropdown initially
        self.refresh_order_customers() # Need to create this helper function

        # Connect customer combo signal to populate measurements
        self.order_customer_combo.currentIndexChanged.connect(self.refresh_order_measurements)

        # Load initial orders
        # self.load_orders() # Need to create this function

        print("            DEBUG: Exiting init_orders_screen.")

    def refresh_order_customers(self):
        """Refreshes the customer dropdown in the orders screen."""
        from database import DB_PATH
        import sqlite3
        print("            DEBUG: Refreshing order customers...")
        try:
            if hasattr(self, 'order_customer_combo'):
                self.order_customer_combo.clear()
                self.order_customer_combo.addItem("Select Customer...", None) # Placeholder
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT id, naap_number, full_name FROM customers ORDER BY full_name ASC")
                customers = c.fetchall()
                conn.close()
                for cid, naap, name in customers:
                    display_text = f"{naap} - {name}"
                    self.order_customer_combo.addItem(display_text, cid) # Store customer ID as data
            else:
                print("ERROR: order_customer_combo not found during refresh.")
        except sqlite3.Error as e:
            print(f"ERROR: Database error refreshing order customers: {e}")
        except Exception as e:
            print(f"ERROR: Unexpected error refreshing order customers: {e}")

    # Placeholder for refreshing measurements based on selected customer
    def refresh_order_measurements(self):
        """Refreshes the measurement dropdown based on the selected customer."""
        print("            DEBUG: Entering refresh_order_measurements...")
        from database import DB_PATH, get_db_connection
        import sqlite3

        try:
            if not hasattr(self, 'order_customer_combo') or not hasattr(self, 'order_measurement_combo'):
                print("ERROR: Customer or Measurement combo box not found.")
                return

            self.order_measurement_combo.clear()
            self.order_measurement_combo.addItem("None (General Order)", None) # Default option

            customer_idx = self.order_customer_combo.currentIndex()
            customer_id = self.order_customer_combo.itemData(customer_idx) if customer_idx > 0 else None

            if customer_id is not None:
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, dress_type, date_created FROM measurements WHERE customer_id = ? ORDER BY date_created DESC", (customer_id,))
                    measurements = c.fetchall()
                
                if measurements:
                    for mid, dress_type, date_created in measurements:
                        display_text = f"ID: {mid} - {dress_type} ({date_created})"
                        self.order_measurement_combo.addItem(display_text, mid) # Store measurement ID
                else:
                    # Keep the "None" option if no measurements found
                    pass
            else:
                # Keep the "None" option if no customer selected
                pass

        except sqlite3.Error as e:
            print(f"ERROR: Database error refreshing order measurements: {e}")
            QtWidgets.QMessageBox.warning(self, "DB Error", "Could not load measurements for the selected customer.")
        except Exception as e:
            print(f"ERROR: Unexpected error refreshing order measurements: {e}")

    # --- Order Table Action Handlers ---
    def get_selected_order_id(self):
        """Helper function to get the ID of the selected order in the table."""
        if not hasattr(self, 'orders_table'): 
            return None
        selected_row = self.orders_table.currentRow()
        if selected_row < 0:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select an order from the table first.")
            return
        try:
            order_id_item = self.orders_table.item(selected_row, 0) # ID is in the first column
            return int(order_id_item.text())
        except (AttributeError, ValueError, TypeError) as e:
            print(f"ERROR: Could not get order ID from table row {selected_row}: {e}")
            QtWidgets.QMessageBox.warning(self, "Error", "Could not determine the selected order ID.")
            return

    def view_selected_order_details(self):
        """Fetches and displays full details for the selected order."""
        print("            DEBUG: Entering view_selected_order_details...")
        order_id = self.get_selected_order_id()
        if order_id is None: return

        from database import get_db_connection
        import sqlite3

        try:
            with get_db_connection() as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("""
                    SELECT o.*, c.full_name AS customer_name, c.mobile_number AS customer_mobile
                    FROM orders o
                    JOIN customers c ON o.customer_id = c.id
                    WHERE o.id = ?
                """, (order_id,))
                order_details = c.fetchone()

            if not order_details:
                QtWidgets.QMessageBox.warning(self, "Not Found", f"Order ID {order_id} not found in the database.")
                return

            # Format details for display
            details_str = f"--- Order #{order_details['id']} Details ---\
"
            details_str += f"Customer: {order_details['customer_name']} ({order_details['customer_mobile']})\
"
            details_str += f"Order Date: {order_details['order_date']}\
"
            details_str += f"Due Date: {order_details['due_date']}\
"
            details_str += f"Associated Measurement ID: {order_details['measurement_id'] if order_details['measurement_id'] else 'N/A'}\
"
            details_str += f"Price: AED {order_details['price']:.2f}\
"
            details_str += f"Amount Paid: AED {order_details['amount_paid']:.2f}\
"
            details_str += f"Payment Status: {order_details['payment_status']}\
"
            details_str += f"Order Status: {order_details['order_status']}\
"
            details_str += f"\nNotes:\n{order_details['notes'] if order_details['notes'] else 'None'}"

            QtWidgets.QMessageBox.information(self, f"Order #{order_id} Details", details_str)

        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Database Error", f"Failed to fetch order details: {e}")
            print(f"ERROR: Database error fetching order details: {e}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"An unexpected error occurred while fetching order details: {e}")
            print(f"ERROR: Unexpected error fetching order details: {e}")

    def update_selected_order_status(self):
        """Updates the status of the selected order."""
        print("            DEBUG: Entering update_selected_order_status...")
        order_id = self.get_selected_order_id()
        if order_id is None: return

        from database import get_db_connection
        import sqlite3

        # Define possible statuses and valid transitions (optional, but good practice)
        all_statuses = ['Pending', 'In Progress', 'Ready', 'Delivered', 'Cancelled']
        # You could add logic here to get the *current* status first and only offer valid next steps

        # Use QInputDialog to get the new status from the user
        new_status, ok = QtWidgets.QInputDialog.getItem(self, 
                                                        "Update Order Status", 
                                                        f"Select new status for Order #{order_id}:", 
                                                        all_statuses, 
                                                        0, # Default selection index
                                                        False) # Non-editable dropdown

        if ok and new_status:
            print(f"            DEBUG: User selected new status '{new_status}' for order {order_id}")
            # Update the database
            try:
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("UPDATE orders SET order_status = ? WHERE id = ?", (new_status, order_id))
                    conn.commit()
                
                QtWidgets.QMessageBox.information(self, "Success", f"Order #{order_id} status updated to '{new_status}'.")
                print(f"            DEBUG: Order {order_id} status updated.")
                
                # Refresh the table to show the change (or remove the row if Delivered/Cancelled)
                self.load_orders()

            except sqlite3.Error as e:
                QtWidgets.QMessageBox.critical(self, "Database Error", f"Failed to update order status: {e}")
                print(f"ERROR: Database error updating order status: {e}")
            except Exception as e:
                pass
                QtWidgets.QMessageBox.critical(self, "Error", f"An unexpected error occurred while updating order status: {e}")
                print(f"ERROR: Unexpected error updating order status: {e}")
        else:
            print("            DEBUG: Status update cancelled by user.")

    # Placeholder for loading orders into the table
    def load_orders(self):
        """Loads pending/in-progress orders into the orders table."""
        print("            DEBUG: Entering load_orders...")
        from database import DB_PATH, get_db_connection
        import sqlite3

        try:
            if not hasattr(self, 'orders_table'):
                print("ERROR: orders_table not found during load.")
                return
            
            self.orders_table.setRowCount(0) # Clear existing rows

            with get_db_connection() as conn:
                conn.row_factory = sqlite3.Row # Use row factory for dict-like access
                c = conn.cursor()
                # Fetch orders that are not yet Delivered or Cancelled, joining with customers
                c.execute("""
                    SELECT o.id, c.full_name, o.price, o.amount_paid, o.due_date, o.order_status, o.payment_status
                    FROM orders o
                    JOIN customers c ON o.customer_id = c.id
                    WHERE o.order_status NOT IN ('Delivered', 'Cancelled')
                    ORDER BY o.due_date ASC, o.id DESC
                """)
                orders = c.fetchall()
            
            self.orders_table.setRowCount(len(orders))
            for row_idx, order in enumerate(orders):
                # Column order: ID, Customer, Price, Paid, Due Date, Status, Payment
                self.orders_table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(order['id'])))
                self.orders_table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(order['full_name']))
                self.orders_table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(f"AED {order['price']:.2f}"))
                self.orders_table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(f"AED {order['amount_paid']:.2f}"))
                self.orders_table.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(order['due_date']))
                self.orders_table.setItem(row_idx, 5, QtWidgets.QTableWidgetItem(order['order_status']))
                self.orders_table.setItem(row_idx, 6, QtWidgets.QTableWidgetItem(order['payment_status']))
                
                # Optional: Add styling based on status or due date
                # Example: Color rows based on payment status
                if order['payment_status'] == 'Paid':
                    for col_idx in range(self.orders_table.columnCount()):
                        item = self.orders_table.item(row_idx, col_idx)
                        if item: item.setBackground(QtGui.QColor("#d4efdf")) # Light green
                elif order['payment_status'] == 'Partially Paid':
                     for col_idx in range(self.orders_table.columnCount()):
                        item = self.orders_table.item(row_idx, col_idx)
                        if item: item.setBackground(QtGui.QColor("#fdebd0")) # Light orange

            self.orders_table.resizeColumnsToContents()
            self.orders_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch) # Stretch customer name
            print(f"            DEBUG: Loaded {len(orders)} orders.")

        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Database Error", f"Failed to load orders: {e}")
            print(f"ERROR: Database error loading orders: {e}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"An unexpected error occurred while loading orders: {e}")
            print(f"ERROR: Unexpected error loading orders: {e}")

    # Placeholder for saving a new order
    def save_order(self):
        # This function will be implemented later
        pass

    def init_finance_screen(self):
        """Initializes the placeholder screen for Finance."""
        print("            DEBUG: Entering init_finance_screen...")
        finance_screen = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(finance_screen)
        layout.setAlignment(QtCore.Qt.AlignCenter)

        title_label = QtWidgets.QLabel("Finance Section")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)

        placeholder_label = QtWidgets.QLabel("Functionality for managing finances (income, expenses, reports) will be implemented here.")
        placeholder_label.setStyleSheet("font-size: 16px; color: #777; margin-top: 10px;")
        placeholder_label.setWordWrap(True)
        layout.addWidget(placeholder_label)

        layout.addStretch()

        # Add the finance screen widget to the stack
        self.content_stack.addWidget(finance_screen)
        print("            DEBUG: Exiting init_finance_screen.")

    # Add the new update method here, outside init_dashboard_screen
    def update_dashboard_stats(self):
        """Queries the database and updates dashboard statistics and tables."""
        from database import DB_PATH
        import sqlite3
        from datetime import datetime
        print("        DEBUG: Updating dashboard stats...") # We see this

        conn = None # Initialize conn to None
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            # 1. Total Customers
            c.execute("SELECT COUNT(*) FROM customers")
            customer_count = c.fetchone()[0]
            # Potential Error Source 1: Finding child widget might fail if init_dashboard_screen didn't complete fully or card widget name is wrong.
            cust_value_label = self.customers_card.findChild(QtWidgets.QLabel, "stat_value_label")
            if cust_value_label:
                cust_value_label.setText(f"ðŸ' {customer_count}")

            # 2. Total Orders (using measurements for now)
            c.execute("SELECT COUNT(*) FROM measurements")
            order_count = c.fetchone()[0]
             # Potential Error Source 2: Similar to above.
            order_value_label = self.orders_card.findChild(QtWidgets.QLabel, "stat_value_label")
            if order_value_label:
                order_value_label.setText(f"Orders: {order_count}")

            # 3. Pending Delivery (Urgent & future date)
            today_str = datetime.now().strftime("%Y-%m-%d")
            c.execute("SELECT COUNT(*) FROM measurements WHERE urgent_delivery = 1 AND date(expected_delivery_date) >= date(?)", (today_str,))
            pending_count = c.fetchone()[0]
            # Potential Error Source 3: Similar to above.
            pending_value_label = self.pending_card.findChild(QtWidgets.QLabel, "stat_value_label")
            if pending_value_label:
                pending_value_label.setText(f"Pending: {pending_count}")

            # 4. Revenue (Placeholder)
            revenue_value_label = self.revenue_card.findChild(QtWidgets.QLabel, "stat_value_label")
            if revenue_value_label:
                revenue_value_label.setText("AED 0") # Keep as 0 until implemented

            # 5. Recent Orders Table
            c.execute("""
                SELECT c.full_name, m.dress_type, m.date_created
                FROM measurements m
                JOIN customers c ON m.customer_id = c.id
                ORDER BY m.id DESC
                LIMIT 5
            """)
            recent_measurements = c.fetchall()

            # Potential Error Source 4: Accessing self.dash_orders_table might fail if it wasn't created properly in init_dashboard_screen.
            self.dash_orders_table.setRowCount(0) # Clear existing rows
            self.dash_orders_table.setRowCount(len(recent_measurements))
            for row_idx, (name, dress_type, date_created) in enumerate(recent_measurements):
                self.dash_orders_table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(name))
                self.dash_orders_table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(dress_type))
                self.dash_orders_table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem("N/A")) # Amount
                self.dash_orders_table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem("N/A")) # Status
                # Optionally add coloring/styling based on date_created or future status

            print(f"        DEBUG: Dashboard stats updated: Cust={customer_count}, Orders={order_count}, Pending={pending_count}") # We DON'T see this

        except sqlite3.Error as e:
            print(f"ERROR: Failed to update dashboard stats - {e}")
        except AttributeError as e:
             print(f"ERROR: Attribute error updating dashboard stats (likely missing UI element): {e}") # This is a likely error type
        finally:
            if conn:
                conn.close()

    # --- Account Management Handlers --- 
    def handle_save_username(self):
        import sqlite3 # Import for error handling
        new_username = self.admin_new_username_input.text().strip()

        # Reset status label
        self.admin_username_status_label.setText("")
        self.admin_username_status_label.setStyleSheet("color: red; font-style: italic;") # Default to red

        # Validation
        if not new_username:
            self.admin_username_status_label.setText("New username cannot be empty.")
            return
        if new_username == self.logged_in_user:
            self.admin_username_status_label.setText("New username is the same as current.")
            return
 
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                # Check if new username already exists
                c.execute("SELECT id FROM users WHERE username = ?", (new_username,))
                existing_user = c.fetchone()
                if existing_user:
                    self.admin_username_status_label.setText("Username already taken.")
                    return
 
                # Update the username in the database
                c.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, self.logged_in_user))
                conn.commit()
 
                # Update username in the application state and UI
                old_username = self.logged_in_user
                self.logged_in_user = new_username
                self.update_displayed_username() # Call helper to update UI
 
                self.admin_username_status_label.setStyleSheet("color: green; font-style: italic;") # Green
                self.admin_username_status_label.setText("Username updated successfully.")
                self.admin_new_username_input.clear() # Clear input field
 
        except sqlite3.Error as e:
            self.admin_username_status_label.setText(f"Database error.")
            print(f"Database error changing username: {e}")
        except Exception as e:
            self.admin_username_status_label.setText(f"An unexpected error occurred.")
            print(f"Error changing username: {e}")

    def handle_save_password(self):
        import sqlite3 # Import for error handling
        # Get values from the settings screen input fields
        current_password = self.settings_current_password_input.text()
        new_password = self.settings_new_password_input.text()
        confirm_password = self.settings_confirm_password_input.text()

        # Reset status label
        self.password_status_label.setText("")
        self.password_status_label.setStyleSheet("color: red; font-style: italic;") # Default to red for errors

        # Validation
        if not current_password or not new_password or not confirm_password:
            self.password_status_label.setText("All password fields are required.")
            return
        if new_password != confirm_password:
            self.password_status_label.setText("New passwords do not match.")
            return
        if len(new_password) < 6:
            self.password_status_label.setText("Password must be at least 6 characters.")
            return

        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                # Get current stored hash for the logged-in user
                c.execute("SELECT password_hash FROM users WHERE username = ?", (self.logged_in_user,))
                result = c.fetchone()

                if not result:
                    self.password_status_label.setText("Error: Current user not found.")
                    return

                stored_hash = result[0]
                # Hash the entered current password
                current_password_hash = hashlib.sha256(current_password.encode('utf-8')).hexdigest()

                # Check if current password is correct
                if current_password_hash != stored_hash:
                    self.password_status_label.setText("Incorrect current password.")
                    return

                # Hash the new password
                new_password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()

                # Update the database
                c.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_password_hash, self.logged_in_user))
                conn.commit()

                self.password_status_label.setStyleSheet("color: green; font-style: italic;") # Green for success
                self.password_status_label.setText("Password updated successfully.")
                # Clear password fields after success
                self.settings_current_password_input.clear()
                self.settings_new_password_input.clear()
                self.settings_confirm_password_input.clear()

        except sqlite3.Error as e:
            self.password_status_label.setText(f"Database error.")
            print(f"Database error changing password: {e}")
        except Exception as e:
            self.password_status_label.setText(f"An unexpected error occurred.")
            print(f"Error changing password: {e}")

    def update_displayed_username(self):
        """Helper method to update all UI elements showing the username."""
        # Update settings screen label
        if hasattr(self, 'settings_current_username_label'):
            self.settings_current_username_label.setText(f"Current: {self.logged_in_user}")
         
        # Find and update top bar label (might need a more robust way if layout changes)
        # Assuming top_bar structure remains consistent
        try:
            top_bar = self.centralWidget().layout().itemAt(0).widget() # Get top bar widget
            top_layout = top_bar.layout()
            # Iterate backwards through top layout items to find the user label reliably
            for i in range(top_layout.count() - 1, -1, -1):
                item = top_layout.itemAt(i)
                widget = item.widget()
                if isinstance(widget, QtWidgets.QLabel) and widget.text().startswith("ðŸ'¤"):
                    widget.setText(f"ðŸ'¤ {self.logged_in_user}")
                    break # Found and updated
        except AttributeError as e:
             print(f"Error updating top bar username display: {e}")

        # Find and update sidebar profile label (might need a more robust way)
        # Assuming sidebar structure remains consistent
        try:
            # Find sidebar (assuming it's the first widget in body_split layout)
            body_split = self.centralWidget().layout().itemAt(1).layout()
            sidebar = body_split.itemAt(0).widget()
            sidebar_layout = sidebar.layout()
            profile_layout = sidebar_layout.itemAt(2).layout() # Assuming profile is 3rd layout
            # Iterate backwards through profile layout items to find the label
            for i in range(profile_layout.count() - 1, -1, -1):
                item = profile_layout.itemAt(i)
                widget = item.widget()
                # Check if it's the label (not the icon or stretch) based on presence of text
                if isinstance(widget, QtWidgets.QLabel) and not widget.text().startswith("ðŸ'¤"):
                    widget.setText(self.logged_in_user)
                    break # Found and updated
        except (AttributeError, IndexError) as e:
             print(f"Error updating sidebar username display: {e}")

    # --- Admin Panel Screen --- NEW SCREEN INIT
    def init_admin_panel_screen(self):
        """Initializes the screen for admin user management."""
        print("            DEBUG: Entering init_admin_panel_screen...")
        admin_screen = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(admin_screen)
        layout.setAlignment(QtCore.Qt.AlignTop)

        # --- Account Management Group --- (Moved from Settings)
        account_group = QtWidgets.QGroupBox("User Account Management")
        account_layout = QtWidgets.QVBoxLayout(account_group)

        # Username Change
        username_form_layout = QtWidgets.QFormLayout()
        # Use 'admin_' prefix for attributes related to this screen
        self.admin_current_username_label = QtWidgets.QLabel(f"Current: {self.logged_in_user}") 
        self.admin_new_username_input = QtWidgets.QLineEdit()
        self.admin_new_username_input.setPlaceholderText("Enter new username")
        self.admin_save_username_btn = QtWidgets.QPushButton("Save Username")
        self.admin_save_username_btn.clicked.connect(self.handle_save_username) # Connect to handler
        self.admin_username_status_label = QtWidgets.QLabel("")
        self.admin_username_status_label.setStyleSheet("color: green; font-style: italic;")
        username_form_layout.addRow(self.admin_current_username_label)
        username_form_layout.addRow("New Username:", self.admin_new_username_input)
        username_form_layout.addRow("", self.admin_save_username_btn)
        username_form_layout.addRow("", self.admin_username_status_label)
        account_layout.addLayout(username_form_layout)

        # Separator
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        account_layout.addWidget(separator)

        # Password Change
        password_form_layout = QtWidgets.QFormLayout()
        self.admin_current_password_input = QtWidgets.QLineEdit()
        self.admin_current_password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.admin_current_password_input.setPlaceholderText("Enter current password")
        self.admin_new_password_input = QtWidgets.QLineEdit()
        self.admin_new_password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.admin_new_password_input.setPlaceholderText("Enter new password (min 6 chars)")
        self.admin_confirm_password_input = QtWidgets.QLineEdit()
        self.admin_confirm_password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.admin_confirm_password_input.setPlaceholderText("Confirm new password")
        self.admin_save_password_btn = QtWidgets.QPushButton("Save Password")
        self.admin_save_password_btn.clicked.connect(self.handle_save_password) # Connect to handler
        self.admin_password_status_label = QtWidgets.QLabel("")
        self.admin_password_status_label.setStyleSheet("color: green; font-style: italic;")
        password_form_layout.addRow("Current Password:", self.admin_current_password_input)
        password_form_layout.addRow("New Password:", self.admin_new_password_input)
        password_form_layout.addRow("Confirm Password:", self.admin_confirm_password_input)
        password_form_layout.addRow("", self.admin_save_password_btn)
        password_form_layout.addRow("", self.admin_password_status_label)
        account_layout.addLayout(password_form_layout)
        
        layout.addWidget(account_group)
        layout.addStretch(1)

        self.content_stack.addWidget(admin_screen) # Add to stack
        print("            DEBUG: Exiting init_admin_panel_screen.")

# --- Login Dialog --- NEW CLASS
class LoginDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login - Tailor Master")
        self.setMinimumWidth(400)

        # Fetch icon path
        icon_path = get_resource_path("resources/app_logo.png") 
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        else:
            print("Warning: app_logo.png not found for login dialog icon.")

        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30) # Add padding
        main_layout.setSpacing(20) # Add spacing between elements
        self.setStyleSheet("background-color: #f8f9fa;") # Light background

        # --- Logo --- 
        logo_label = QtWidgets.QLabel()
        logo_pixmap = QtGui.QPixmap(icon_path)
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(64, 64, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
            logo_label.setAlignment(QtCore.Qt.AlignCenter)
            main_layout.addWidget(logo_label)
        
        # --- Title --- 
        title_label = QtWidgets.QLabel("Tailor Master Login")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # --- Form (Styling to be applied later) --- 
        form_layout = QtWidgets.QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(QtCore.Qt.AlignRight)
        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("Enter username") # Add placeholder
        self.username_input.setStyleSheet("""
            QLineEdit { 
                padding: 8px 12px; 
                border: 1px solid #ccc; 
                border-radius: 4px; 
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #eebc1d;
            }
        """)
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Enter password") # Add placeholder
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit { 
                padding: 8px 12px; 
                border: 1px solid #ccc; 
                border-radius: 4px; 
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #eebc1d;
            }
        """)

        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)

        main_layout.addLayout(form_layout)

        # Error Label
        self.error_label = QtWidgets.QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c; font-size: 12px; padding-top: 5px;") # Style error label
        self.error_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(self.error_label)

        # Login Button
        login_button = QtWidgets.QPushButton("Login")
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #eebc1d; 
                color: #000000;
                font-size: 14px; 
                font-weight: bold;
                padding: 10px 15px;
                border-radius: 5px;
                border: none;
                min-height: 24px; /* Ensure button has height */
            }
            QPushButton:hover {
                background-color: #dcaa0a; /* Darker shade on hover */
            }
            QPushButton:pressed {
                background-color: #c79809; /* Even darker when pressed */
            }
        """)
        login_button.clicked.connect(self.handle_login)
        main_layout.addWidget(login_button) # Add to main layout

        # Connect return key press in password field to login
        self.password_input.returnPressed.connect(self.handle_login)

        self.username = None # Reset username before login attempt

    def handle_login(self):
        entered_username = self.username_input.text().strip()
        entered_password = self.password_input.text()

        if not entered_username or not entered_password:
            self.error_label.setText("Username and password are required.")
            return

        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT password_hash FROM users WHERE username = ?", (entered_username,))
                result = c.fetchone()

                if result:
                    stored_password_hash = result[0]
                    # Hash the entered password
                    entered_password_hash = hashlib.sha256(entered_password.encode('utf-8')).hexdigest()
                    
                    # Compare hashes
                    if entered_password_hash == stored_password_hash:
                        self.username = entered_username # Store username
                        self.accept() # Close dialog successfully
                    else:
                        self.error_label.setText("Invalid username or password.")
                else:
                    self.error_label.setText("Invalid username or password.")
        except Exception as e:
            self.error_label.setText("An unexpected error occurred.")

# --- Change Password Dialog --- NEW CLASS
class ChangePasswordDialog(QtWidgets.QDialog):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username # Store the username of the user changing the password
        self.setWindowTitle(f"Change Password for {self.username}")
        self.setMinimumWidth(350)

        layout = QtWidgets.QVBoxLayout(self)
        form_layout = QtWidgets.QFormLayout()

        self.current_password_input = QtWidgets.QLineEdit()
        self.current_password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.new_password_input = QtWidgets.QLineEdit()
        self.new_password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirm_password_input = QtWidgets.QLineEdit()
        self.confirm_password_input.setEchoMode(QtWidgets.QLineEdit.Password)

        form_layout.addRow("Current Password:", self.current_password_input)
        form_layout.addRow("New Password:", self.new_password_input)
        form_layout.addRow("Confirm New Password:", self.confirm_password_input)

        layout.addLayout(form_layout)

        self.error_label = QtWidgets.QLabel("")
        self.error_label.setStyleSheet("color: red; margin-top: 5px;")
        layout.addWidget(self.error_label)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_new_password)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def save_new_password(self):
        import sqlite3 # Need sqlite3 for error handling
        current_password = self.current_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        # Validation
        if not current_password or not new_password or not confirm_password:
            self.error_label.setText("All fields are required.")
            return
        if new_password != confirm_password:
            self.error_label.setText("New passwords do not match.")
            return
        if len(new_password) < 6:
            self.error_label.setText("New password must be at least 6 characters long.") # Basic length check
            return

        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                # Get current stored hash
                c.execute("SELECT password_hash FROM users WHERE username = ?", (self.username,))
                result = c.fetchone()

                if not result:
                    self.error_label.setText("Error: User not found.") # Should not happen if logged in
                    return

                stored_hash = result[0]
                # Hash entered current password
                current_password_hash = hashlib.sha256(current_password.encode('utf-8')).hexdigest()

                # Check if current password is correct
                if current_password_hash != stored_hash:
                    self.error_label.setText("Incorrect current password.")
                    return

                # Hash the new password
                new_password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()

                # Update the database
                c.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_password_hash, self.username))
                conn.commit()

                QtWidgets.QMessageBox.information(self, "Success", "Password updated successfully.")
                self.accept() # Close dialog on success

        except sqlite3.Error as e:
            self.error_label.setText(f"Database error: {e}")
            print(f"Database error changing password: {e}")
        except Exception as e:
            self.error_label.setText(f"An unexpected error occurred: {e}")
            print(f"Error changing password: {e}")

if __name__ == "__main__":
    import traceback
    import sys, os
    from PyQt5 import QtWidgets

    def exception_hook(exctype, value, tb):
        error_msg = ''.join(traceback.format_exception(exctype, value, tb))
        with open("error.log", "a", encoding="utf-8") as logf:
            logf.write(error_msg + "\n")
        try:
            app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
            QtWidgets.QMessageBox.critical(None, "Application Error", f"An unexpected error occurred. Details have been logged to error.log.\n\n{value}")
        except Exception as e:
            print(f"Error displaying error dialog: {e}")
        sys.exit(1)

    sys.excepthook = exception_hook

    # Initialize DB (creates default admin if needed)
    print("DEBUG: Initializing DB...") # Debug print 1
    init_db()
    print("DEBUG: DB Initialized.") # Debug print 2

    # --- Login Handling --- 
    app = QtWidgets.QApplication(sys.argv)

    # Show Login Dialog
    login_dialog = LoginDialog()
    login_result = login_dialog.exec_()
    logged_in_user = login_dialog.username # Get username if login was successful

    if login_result == QtWidgets.QDialog.Accepted:
        print(f"DEBUG: Login successful for user: {logged_in_user}")
        # Proceed to main application
        # Apply custom stylesheet (ensure app instance exists)
        current_app = QtWidgets.QApplication.instance() or app
        try:
            qss_path = get_resource_path("resources/tmms.qss")
            if os.path.exists(qss_path):
                with open(qss_path, "r") as f:
                    current_app.setStyleSheet(f.read())
                print(f"Applied custom stylesheet from {qss_path}")
        except Exception as e:
            print(f"Error applying stylesheet: {e}")
        
        print("DEBUG: Creating MainWindow...") # Debug print 3
        # Pass username to MainWindow (requires modification in MainWindow.__init__)
        mw = MainWindow(logged_in_user=logged_in_user)
        print("DEBUG: MainWindow Created.") # Debug print 4
        print("DEBUG: Showing MainWindow...") # Debug print 5
        mw.show()
        print("DEBUG: MainWindow Shown.") # Debug print 6
        sys.exit(current_app.exec_())
    else:
        print("DEBUG: Login cancelled or failed. Exiting.")
        sys.exit(0)

