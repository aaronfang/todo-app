# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-02-10

### 🎉 Major Release - Enhanced Fork

This release represents a major enhancement of the original todo-app with advanced task management features.

### ✨ Added

#### Core Features
- **Subtask System** - Create hierarchical task structures
  - Add unlimited subtasks with Ctrl+S
  - Visual indentation for clarity
  - Smart auto-completion: main task completes when all subtasks are done
  - Subtasks follow parent task when marked complete/cancelled
  - Unique UUID-based task identification system

- **Deadline Management** - Intelligent due date tracking
  - Set deadlines via right-click context menu
  - Calendar picker (tkcalendar) or text input fallback
  - Smart reminders:
    - ⚠️ Overdue X days (red warning)
    - ⚠️ Due today (orange alert)
    - ⏰ X days left (blue reminder for 1-3 days)
    - 📅 Date display for longer-term tasks
  - Completed tasks hide deadline indicators

- **Completed Tasks Section** - Organized completion tracking
  - Collapsible area with "▼ Completed (X)" header
  - Click to toggle ▶ (collapsed) / ▼ (expanded)
  - Per-section collapse state (for tasks grouped by separators)
  - Collapse state persists in config.json
  - Shows completion timestamp for each task
  - Maintains parent-child task relationships

- **Custom Task Colors** - Visual task categorization
  - Set background colors via right-click menu
  - 12 preset colors optimized for dark/light modes
  - Manual hex color input (#RRGGBB format)
  - Real-time color preview
  - Clear color option to reset
  - Only available for main tasks (not subtasks)

- **Cancelled Task Status** - Distinguish incomplete work
  - Mark tasks as cancelled with Ctrl+J
  - Gray color (#a9a9a9) with special icon (☒ / ✖)
  - Cancelled tasks move to completed section
  - Preserves task history without cluttering active list

#### UI Enhancements
- **Font Size Control**
  - Adjust with Ctrl+Plus, Ctrl+Minus, Ctrl+0 (reset)
  - Range: 8-24pt
  - Available in right-click context menu
  - Preference saved per user

- **Progress Statistics**
  - Window title shows: "To-Do (X/Y)" for pending tasks
  - Urgent task counter: "[X urgent]"
  - "All done!" message when complete
  - Only counts main tasks (excludes subtasks and separators)

- **Alternating Row Colors**
  - Improves visual task separation
  - Main tasks use alternating backgrounds
  - Subtasks maintain consistent background

- **Smart Window Sizing**
  - Auto-adjusts to content
  - Width stability mechanism to prevent constant resizing
  - Respects screen boundaries (max height: screen - 100px)
  - Platform-specific minimum sizes (Windows: 300x100, macOS: 400x100)

- **Drag & Drop Reordering**
  - Click and drag tasks to reorder
  - Works with main tasks, subtasks, and separators
  - Maintains window width during reorder

#### Keyboard & Mouse Improvements
- **New Shortcuts**
  - Ctrl+S: Add subtask
  - Ctrl+J: Mark as cancelled
  - Ctrl+Plus/=: Increase font size
  - Ctrl+Minus: Decrease font size
  - Ctrl+0: Reset font size
  - Ctrl+A: Select all tasks

- **Multi-Selection**
  - Ctrl+Click: Toggle individual selection
  - Shift+Click: Range selection
  - macOS compatibility for Ctrl-click vs right-click

- **Right-Click Context Menu**
  - Add Subtask
  - Set Deadline
  - Set Background Color
  - Increase/Decrease Font Size
  - Edit Task
  - All task state toggles

#### Data Management
- **Enhanced Data Structure**
  - UUID-based task identification
  - Parent-child relationship tracking via `parent_task_id`
  - Subtask flag: `is_subtask`
  - Background color storage: `bg_color`
  - Deadline storage: `deadline` (ISO format)
  - Completion timestamp: `completed_at`

- **Configuration Persistence**
  - Font size preference
  - Collapse states per section
  - Window geometry
  - Dark mode setting

- **Auto-Migration**
  - Automatically adds task_id to existing tasks
  - Handles legacy parent_id field

### 🔧 Fixed
- Window sizing algorithm for better content fitting
- macOS right-click menu activation
- Multi-selection conflicts with context menu on macOS
- Task counter accuracy (excludes subtasks and separators)
- Parent task auto-completion logic
- Collapsed section state persistence

### 🎨 Improved
- Dark mode color scheme for better contrast
- Font rendering on macOS Retina displays
- Button sizing and padding for both platforms
- Listbox item spacing and alignment
- JSON data structure organization
- Code modularity and maintainability

### 📝 Documentation
- Comprehensive README with all features
- Updated keyboard shortcuts table
- Added mouse controls reference
- Version history in About dialog
- This CHANGELOG file

### 🔗 Dependencies
- **Optional**: `tkcalendar` for calendar picker (graceful fallback to text input)
- **Optional**: `pywinstyles` for Windows title bar theming

---

## [0.3.0] - 2024

### Added (Original Release by Jens Lettkemann)
- Basic task management (add, edit, delete)
- Mark tasks as done/undone
- Urgent task marking (Ctrl+U)
- Dark mode toggle (Ctrl+R)
- Task separators with titles (`---` or `---Title`)
- Cross-platform support (Windows & macOS)
- Local JSON storage
- Native UI styling per platform
- Portable Windows executable

### Features (Original)
- Simple Tkinter GUI
- No external dependencies
- Keyboard shortcuts
- Context menu
- Auto-saving
- Window geometry persistence
- GPL v3 license

---

## Attribution

**Original Author**: Jens Lettkemann (jltk@pm.me)  
**Enhanced Fork**: Aaron (2026)  
**License**: GNU General Public License v3.0

This enhanced version builds upon the excellent foundation of the original todo-app, adding advanced task management features while maintaining the simplicity and privacy-first approach.
