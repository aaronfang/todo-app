import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
import json
import tempfile
from pathlib import Path
import sys
sys.path.append('../')
from todo_app.todo_app import TodoApp
from todo_app.edge_hide import EdgeHideController

class TestTodoApp(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        data_dir = Path(self.temp_dir.name)
        self.file_patchers = [
            patch.object(TodoApp, 'get_tasks_file', return_value=data_dir / 'tasks.json'),
            patch.object(TodoApp, 'get_notes_file', return_value=data_dir / 'notes.json'),
            patch.object(TodoApp, 'get_config_file', return_value=data_dir / 'config.json'),
            patch.object(TodoApp, 'get_templates_file', return_value=data_dir / 'templates.json'),
        ]
        for patcher in self.file_patchers:
            patcher.start()
        self.root = tk.Tk()
        self.app = TodoApp(self.root)

    def tearDown(self):
        self.root.destroy()
        for patcher in reversed(self.file_patchers):
            patcher.stop()
        self.temp_dir.cleanup()

    @patch('todo_app.todo_app.Path.read_text')
    def test_load_tasks(self, mock_read_text):
        mock_tasks = [
            {"name": "Task 1", "done": False, "cancelled": False, "urgent": False, "separator": False},
            {"name": "Task 2", "done": True, "cancelled": False, "urgent": True, "separator": False},
            {"name": "───────", "separator": True, "title": False}
        ]
        mock_read_text.return_value = json.dumps(mock_tasks)
        
        tasks = self.app.load_tasks()
        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[0]['name'], "Task 1")
        self.assertFalse(tasks[0]['done'])
        self.assertTrue(tasks[1]['done'])
        self.assertTrue(tasks[1]['urgent'])
        self.assertTrue(tasks[2]['separator'])

    def test_load_templates_from_json(self):
        templates_file = TodoApp.get_templates_file()
        templates_file.write_text(json.dumps([
            {"template_id": "custom", "name": "自定义模板", "subtasks": ["步骤 A", "步骤 B"]}
        ]), encoding='utf-8')

        templates = self.app.load_templates()

        self.assertEqual(templates[0]['name'], "自定义模板")
        self.assertEqual(templates[0]['subtasks'], ["步骤 A", "步骤 B"])

    @patch('todo_app.todo_app.Path.write_text')
    def test_save_tasks(self, mock_write_text):
        self.app.tasks = [
            {"name": "Task 1", "done": False, "cancelled": False, "urgent": False, "separator": False},
            {"name": "Task 2", "done": True, "cancelled": False, "urgent": True, "separator": False},
            {"name": "───────", "separator": True, "title": False}
        ]
        self.app.save_tasks()
        mock_write_text.assert_called_once()
        saved_data = json.loads(mock_write_text.call_args[0][0])
        self.assertEqual(len(saved_data), 3)
        self.assertEqual(saved_data[0]['name'], "Task 1")
        self.assertFalse(saved_data[0]['done'])
        self.assertTrue(saved_data[1]['urgent'])
        self.assertTrue(saved_data[2]['separator'])

    @patch('todo_app.todo_app.messagebox.showinfo')
    @patch('todo_app.todo_app.filedialog.askopenfilename')
    def test_import_templates_merges_json(self, mock_open, mock_info):
        source = Path(self.temp_dir.name) / 'import.json'
        source.write_text(json.dumps([
            {"name": "外部模板", "subtasks": ["外部步骤"]}
        ]), encoding='utf-8')
        mock_open.return_value = str(source)

        self.app.import_templates()

        imported = next(template for template in self.app.templates if template['name'] == "外部模板")
        self.assertEqual(imported['subtasks'], ["外部步骤"])
        mock_info.assert_called_once()

    @patch('todo_app.todo_app.messagebox.showinfo')
    @patch('todo_app.todo_app.filedialog.asksaveasfilename')
    def test_export_templates_writes_json(self, mock_save, mock_info):
        target = Path(self.temp_dir.name) / 'export.json'
        mock_save.return_value = str(target)
        self.app.templates = [{"template_id": "x", "name": "导出模板", "subtasks": ["步骤"]}]

        self.app.export_templates()

        exported = json.loads(target.read_text(encoding='utf-8'))
        self.assertEqual(exported[0]['name'], "导出模板")
        mock_info.assert_called_once()

    def test_toggle_dark_mode(self):
        initial_mode = self.app.is_dark_mode
        self.app.toggle_dark_mode()
        self.assertNotEqual(initial_mode, self.app.is_dark_mode)

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS window behavior')
    def test_macos_window_is_resizable(self):
        self.root.update()
        self.assertEqual(self.root.resizable(), (1, 1))
        self.root.geometry('720x480')
        self.root.update()
        self.assertEqual((self.root.winfo_width(), self.root.winfo_height()), (720, 480))

    def test_edge_hide_selects_screen_with_largest_window_overlap(self):
        screens = [(0, 0, 2056, 1329), (-586, -1440, 2854, 0)]
        selected = EdgeHideController.select_screen_for_window(
            screens, -500, -1000, 500, 400
        )
        self.assertEqual(selected, screens[1])

    def test_edge_hide_uses_selected_screen_edges(self):
        external_screen = (-586, -1440, 2854, 0)
        self.assertEqual(
            EdgeHideController.hidden_x('left', external_screen, 400), -978
        )
        self.assertEqual(
            EdgeHideController.hidden_x('right', external_screen, 400), 2846
        )

    def test_add_task(self):
        self.app.entry = MagicMock()
        self.app.entry.get.return_value = "New Task"
        self.app.add_task()
        self.assertEqual(len(self.app.tasks), 1)
        self.assertEqual(self.app.tasks[0]['name'], "New Task")
        self.assertFalse(self.app.tasks[0]['done'])

    def test_add_so_character_task_does_not_apply_template(self):
        self.app.entry = MagicMock()
        self.app.entry.get.return_value = "SO｜易嘉易｜新角色制作"
        with patch.object(self.app, 'populate_listbox_without_width_change'), patch.object(self.app, 'save_tasks'):
            self.app.add_task()

        self.assertEqual(len(self.app.tasks), 1)
        self.assertEqual(self.app.tasks[0]['name'], "SO｜易嘉易｜新角色制作")
        self.assertFalse(self.app.tasks[0].get('is_subtask', False))

    def test_apply_template_to_selected_main_task(self):
        parent = {
            "name": "主任务",
            "done": False,
            "cancelled": False,
            "urgent": False,
            "separator": False,
            "task_id": "parent-id",
        }
        self.app.tasks = [parent]
        self.app.display_tasks = [parent]
        self.app.listbox = MagicMock()
        self.app.listbox.curselection.return_value = [0]
        template = {"name": "测试模板", "subtasks": ["步骤一", "步骤二"]}

        with patch.object(self.app, 'populate_listbox_without_width_change'), patch.object(self.app, 'save_tasks'), patch.object(self.app, 'update_buttons_state'), patch.object(self.app, 'update_title'):
            self.app.apply_template_to_selected_task(template)

        self.assertEqual([task['name'] for task in self.app.tasks], ["主任务", "步骤一", "步骤二"])
        self.assertTrue(all(task['is_subtask'] for task in self.app.tasks[1:]))
        self.assertTrue(all(task['parent_task_id'] == "parent-id" for task in self.app.tasks[1:]))

    @patch('todo_app.todo_app.TodoApp.populate_listbox')
    @patch('todo_app.todo_app.TodoApp.save_tasks')
    def test_remove_selected_tasks(self, mock_save, mock_populate):
        self.app.tasks = [
            {"name": "Task 1", "done": False, "cancelled": False, "urgent": False, "separator": False},
            {"name": "Task 2", "done": False, "cancelled": False, "urgent": False, "separator": False}
        ]
        self.app.display_tasks = self.app.tasks
        self.app.listbox = MagicMock()
        self.app.listbox.curselection.return_value = [0]
        self.app.remove_selected_tasks()
        self.assertEqual(len(self.app.tasks), 1)
        self.assertEqual(self.app.tasks[0]['name'], "Task 2")

    @patch('todo_app.todo_app.TodoApp.populate_listbox')
    @patch('todo_app.todo_app.TodoApp.save_tasks')
    def test_mark_selected_tasks_done(self, mock_save, mock_populate):
        self.app.tasks = [
            {"name": "Task 1", "done": False, "cancelled": False, "urgent": False, "separator": False},
            {"name": "Task 2", "done": False, "cancelled": False, "urgent": False, "separator": False}
        ]
        self.app.display_tasks = self.app.tasks
        self.app.listbox = MagicMock()
        self.app.listbox.curselection.return_value = [0]
        self.app.mark_selected_tasks_done()
        self.assertTrue(self.app.tasks[0]['done'])
        self.assertFalse(self.app.tasks[1]['done'])

if __name__ == "__main__":
    unittest.main()
