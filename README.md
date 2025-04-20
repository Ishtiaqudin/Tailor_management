# Tailor Master Management System

A comprehensive tailoring shop management application built with PyQt5.

## Features

- Dashboard with statistics and activity feed
- Customer management
- Measurement recording and tracking
- Order history
- PDF and Excel exports
- Database backup and restore

## Requirements

- Python 3.6 or higher
- Dependencies listed in `requirements.txt`

## Installation

1. Clone this repository or download the source code
2. Install the required dependencies:

```
pip install -r requirements.txt
```

## Running the Application

To run the application from source code:

```
python main.py
```

## Building an Executable

To build a standalone executable:

1. Make sure PyInstaller is installed:
```
pip install pyinstaller
```

2. Run the build script:
```
python build_exe.py
```

3. The executable will be created in the `dist` folder

## Updating the Executable

After making changes to the code:

1. Run the build script again:
```
python build_exe.py
```

2. The executable in the `dist` folder will be updated with your changes

## Directory Structure

- `main.py` - Main application code
- `database.py` - Database connection and initialization
- `resources/` - Application resources (icons, stylesheets)
- `backups/` - Database backup files
- `build_exe.py` - Script to build standalone executable

---

More features and UI coming soon!
