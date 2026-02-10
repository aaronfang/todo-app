![app_icon](https://github.com/user-attachments/assets/9f082ded-572f-435e-b237-f62349d6e2e8)

[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)](#) [![Windows](https://custom-icon-badges.demolab.com/badge/Windows-0078D6?logo=windows11&logoColor=white)](#) [![macOS](https://img.shields.io/badge/macOS-000000?logo=apple&logoColor=white)](#) [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-darkred.svg)](https://www.gnu.org/licenses/gpl-3.0)

# Todo App for Windows & macOS

A feature-rich to-do GUI desktop app for Windows and macOS using python Tkinter and JSON local storage.

Free and open-source alternative to Microsoft To Do with advanced task management features.

![screenshot](https://github.com/user-attachments/assets/e89ff5e7-f8d8-4229-ae4e-32b1c81136bd)

## ✨ Features

### Core Features
- **Simple and intuitive interface** - Clean, distraction-free design
- **Dark mode** - Easy on the eyes with Ctrl+R toggle
- **Cross-platform compatibility** - Windows & macOS with native look and feel
- **Own your data** - Local JSON storage, no cloud required
- **Lightweight and fast** - No third-party dependencies
- **Free open-source software** - GPL v3 licensed

### Advanced Task Management
- **✅ Subtasks** - Add unlimited subtasks to any task (Ctrl+S)
  - Smart completion: main task auto-completes when all subtasks are done
  - Visual hierarchy with indentation
- **📅 Deadlines** - Set due dates with smart reminders
  - Overdue warning: ⚠️ Overdue X days
  - Due today alert: ⚠️ Due today
  - Upcoming reminder: ⏰ X days left
- **🔥 Urgent Tasks** - Mark important tasks (Ctrl+U)
  - Red highlight for urgent items
  - Counter in window title
- **❌ Cancelled Tasks** - Mark tasks as cancelled (Ctrl+J)
  - Gray out cancelled items
  - Separate from completed tasks
- **🎨 Custom Colors** - Set background colors for tasks
  - 12 preset colors for dark/light modes
  - Manual color code input support

### Organization & Productivity
- **📂 Sections** - Group tasks with separators
  - Type `---` for a line separator
  - Type `---Project Name` for labeled sections
- **✔️ Completed Tasks Area** - Separate collapsible section
  - One-click to expand/collapse per section
  - Shows completion count
  - Maintains task hierarchy
- **🔠 Font Size Control** - Adjust text size (Ctrl+Plus/Minus/0)
  - Range: 8-24pt
  - Per-user preference saved
- **📊 Progress Tracking** - Real-time statistics
  - Task counter: "To-Do (X/Y)"
  - Urgent task counter: "[X urgent]"
  - "All done!" celebration message

### User Experience
- **🖱️ Drag & Drop** - Reorder tasks by dragging
- **⌨️ Keyboard Shortcuts** - Full keyboard navigation
- **🎯 Multi-select** - Ctrl+Click, Shift+Click, Ctrl+A
- **📐 Smart Window Sizing** - Auto-adjusts to content
- **🎭 Alternating Row Colors** - Better visual separation
- **🔗 Right-click Context Menu** - Quick access to all actions

## Installation

### Download Portable .EXE for Windows 10/11: [🔗 To-Do_Portable_1.0.0.zip](https://github.com/jltk/todo-app/releases/download/1.0.0/To-Do_Portable_1.0.0.zip)

or [visit the release page](https://github.com/jltk/todo-app/releases). 

### Build from source (Windows & macOS)

To run this application, you need Python 3.9 or higher.

1. Clone the repository:

```bash
$ git clone https://github.com/jltk/todo-app.git
```

2. Navigate to the project directory:

```bash
$ cd todo-app
```

3. Install dependencies:

```bash
$ python -r requirements.txt
```

4. Run the application:

```bash
$ cd todo_app
$ python todo_app.py
```

## Shortcuts

| KEYS | DESCRIPTION |
| ---- | ----------- |
| **Ctrl+D** | Mark tasks as done |
| **Ctrl+U** | Mark tasks as urgent |
| **Ctrl+J** | Mark tasks as cancelled |
| **Ctrl+Del** | Delete tasks |
| **Ctrl+E** | Edit task |
| **Ctrl+R** | Toggle dark mode |
| **Ctrl+H** | About window |

| MARKUP | DESCRIPTION |
| ---- | ----------- |
| ```---``` | Adds seperator |
| ```---title here``` | Adds a seperator with title |

## macOS Compatibility

This version includes full macOS compatibility:

- **Right-click menu**: Fixed context menu activation using Button-2 and Ctrl+Click
- **Native fonts**: Uses SF Pro Text (13pt) on macOS for better readability on Retina displays
- **Optimized layout**: Improved button sizing and input field proportions
- **Native colors**: macOS-specific color scheme that matches system appearance
- **Better UI scaling**: Proper padding and spacing for macOS interface guidelines
- **Task icons**: Uses proper checkbox symbols (☐ ☑ ☒) instead of colored blocks on macOS
- **Keyboard shortcuts**: Full Command key support for all operations

## What's New in v1.0.0

This enhanced fork adds powerful task management features:

### 🎯 Major Features
- **Subtask System** - Create hierarchical task structures with unlimited nesting
- **Deadline Management** - Set due dates with intelligent overdue/upcoming reminders
- **Completed Tasks Section** - Collapsible area for finished tasks, organized by sections
- **Custom Task Colors** - Personalize tasks with 12 preset colors or custom hex codes
- **Cancelled Task Status** - Distinguish between completed and cancelled work

### 💪 Enhancements
- **Font Size Control** - Adjust text size from 8-24pt for better readability
- **Progress Statistics** - Real-time counters for pending, urgent, and completed tasks
- **Drag & Drop Reordering** - Intuitive task management with mouse
- **Smart Auto-Complete** - Main tasks automatically complete when all subtasks are done
- **Alternating Row Colors** - Improved visual task separation
- **Multi-Selection** - Ctrl/Shift click for bulk operations

### 🐛 Fixes & Polish
- Improved window sizing algorithm
- Better cross-platform font rendering
- Enhanced dark mode colors
- Optimized JSON data structure
- Task ID system for reliable parent-child relationships

## Contribute

Star and fork the repo and contribute improvements and fixes to the project.

## License

This project is licensed under the GPL license, [read the LICENSE file for details](https://github.com/jltk/todo-app/blob/main/LICENSE).
