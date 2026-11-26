import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
import json
import tempfile
from datetime import datetime
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


def make_main_task(name, task_id, **extra):
    task = {
        "name": name,
        "done": False,
        "cancelled": False,
        "urgent": False,
        "separator": False,
        "is_subtask": False,
        "parent_task_id": None,
        "task_id": task_id,
    }
    task.update(extra)
    return task


def make_subtask(name, task_id, parent_id, **extra):
    task = {
        "name": name,
        "done": False,
        "cancelled": False,
        "urgent": False,
        "separator": False,
        "is_subtask": True,
        "parent_task_id": parent_id,
        "task_id": task_id,
    }
    task.update(extra)
    return task


class TestSubtaskCollapse(unittest.TestCase):
    """子任务列表折叠"""

    def setUp(self):
        self.app = TodoApp.__new__(TodoApp)
        self.app.tasks = [
            make_main_task("父任务A", "a"),
            make_subtask("A-1", "a1", "a"),
            make_subtask("A-2", "a2", "a"),
            make_main_task("父任务B", "b"),
            make_subtask("B-1", "b1", "b"),
        ]
        self.app.collapsed_sections = set()
        self.app.collapsed_subtask_sections = set()
        self.app.collapsed_task_ids = set()

    def names(self):
        return [task['name'] for task in self.app.organize_tasks_by_sections()
                if 'name' in task]

    def test_expanded_by_default(self):
        self.assertEqual(self.names(), ["父任务A", "A-1", "A-2", "父任务B", "B-1"])

    def test_collapsed_hides_only_that_parents_subtasks(self):
        self.app.collapsed_task_ids = {"a"}
        self.assertEqual(self.names(), ["父任务A", "父任务B", "B-1"])

    def test_collapsed_parent_shows_hidden_count(self):
        parent = self.app.tasks[0]
        self.assertEqual(self.app.get_subtask_collapse_indicator(parent), "")
        self.app.collapsed_task_ids = {"a"}
        self.assertEqual(self.app.get_subtask_collapse_indicator(parent), "  ▶ 2个子任务")
        self.assertIn("▶ 2个子任务", self.app.format_task_display_text(parent))

    def test_main_task_without_subtasks_gets_no_indicator(self):
        self.app.collapsed_task_ids = {"b"}
        self.app.tasks[3]['task_id'] = 'b'
        self.app.tasks.pop()  # 移除 B-1，使 B 没有子任务
        self.assertEqual(self.app.get_subtask_collapse_indicator(self.app.tasks[3]), "")

    def test_collapse_preserves_completed_section(self):
        self.app.tasks[0]['done'] = True
        self.app.collapsed_task_ids = {"a"}
        result = self.app.organize_tasks_by_sections()
        names = [task['name'] for task in result if 'name' in task]
        self.assertNotIn("A-1", names)
        self.assertNotIn("A-2", names)
        self.assertIn("父任务A", names)

    def test_is_subtask_collapsed_ignores_other_parents(self):
        self.app.collapsed_task_ids = {"a"}
        self.assertTrue(self.app.is_subtask_collapsed(self.app.tasks[1]))
        self.assertFalse(self.app.is_subtask_collapsed(self.app.tasks[4]))

    def test_fold_persists_to_config(self):
        self.app.collapsed_subtask_sections = set()
        self.app.collapsed_sections = set()
        self.app.is_dark_mode = False
        self.app.font_size = 10
        self.app.edge_hide_enabled = False
        self.app.edge_hide = MagicMock()
        self.app.edge_hide.geometry_for_save.return_value = "400x300"
        saved = {}

        class FakePath:
            parent = Path('.')

            def mkdir(self, **kwargs):
                pass

            def write_text(self, text, encoding=None):
                saved['text'] = text

        self.app.get_config_file = lambda: FakePath()
        self.app.collapsed_task_ids = {"a"}
        self.app.save_config()

        config = json.loads(saved['text'])
        self.assertEqual(config['collapsed_task_ids'], ["a"])

    def test_save_config_drops_deleted_task_ids(self):
        seen = {}

        class FakePath:
            parent = Path('.')

            def mkdir(self, **kwargs):
                pass

            def write_text(self, text, encoding=None):
                seen['text'] = text

        self.app.is_dark_mode = False
        self.app.font_size = 10
        self.app.edge_hide_enabled = False
        self.app.edge_hide = MagicMock()
        self.app.edge_hide.geometry_for_save.return_value = "400x300"
        self.app.get_config_file = lambda: FakePath()
        self.app.collapsed_task_ids = {"a", "已删除的id"}
        self.app.save_config()

        self.assertEqual(json.loads(seen['text'])['collapsed_task_ids'], ["a"])


class TestTaskDates(unittest.TestCase):
    """开始/暂停/结束日期记录"""

    def setUp(self):
        self.app = TodoApp.__new__(TodoApp)
        self.app.tasks = [make_main_task("任务", "t1")]
        self.app.display_tasks = self.app.tasks
        self.app.collapsed_task_ids = set()
        self.app.collapsed_sections = set()
        self.app.collapsed_subtask_sections = set()
        self.app.listbox = MagicMock()
        self.app.listbox.curselection.return_value = [0]
        self.app.saved = 0
        self.app.save_tasks = lambda: None
        self.app.save_config = lambda: None
        self.app.populate_listbox_without_width_change = lambda: None
        self.app.update_title = lambda: None
        self.app.update_buttons_state = lambda event=None: None

    def test_legacy_task_has_no_date_indicator(self):
        self.assertEqual(self.app.get_task_dates_indicator(self.app.tasks[0]), "")
        self.assertNotIn("始", self.app.format_task_display_text(self.app.tasks[0]))

    def test_record_start_today(self):
        self.app.record_task_date('start')
        self.assertEqual(len(self.app.tasks[0]['start_date']), 10)
        self.assertIn("始", self.app.format_task_display_text(self.app.tasks[0]))

    def test_pause_and_resume_keeps_pause_date(self):
        self.app.record_task_date('pause')
        task = self.app.tasks[0]
        self.assertTrue(task['paused'])
        self.assertTrue(task['pause_date'])
        self.assertIn("⏸停", self.app.get_task_dates_indicator(task))

        self.app.record_task_date('pause')
        self.assertFalse(task['paused'])
        self.assertTrue(task['pause_date'])  # 历史保留
        self.assertIn("停", self.app.get_task_dates_indicator(task))
        self.assertNotIn("⏸", self.app.get_task_dates_indicator(task))

    def test_record_end_today_clears_pause(self):
        self.app.record_task_date('pause')
        self.app.record_task_date('end')
        self.assertFalse(self.app.tasks[0].get('paused', False))
        self.assertTrue(self.app.tasks[0]['end_date'])

    def test_completing_task_fills_end_date_when_started(self):
        task = self.app.tasks[0]
        task['start_date'] = '2026-11-01'
        self.app.mark_selected_tasks_done()
        self.assertEqual(task['end_date'], datetime.now().strftime('%Y-%m-%d'))
        self.assertEqual(task['completed_time'][:10], task['end_date'])
        # 完成时间与结束日期相同，不重复显示
        self.assertNotIn("结", self.app.get_task_dates_indicator(task))

    def test_completing_legacy_task_keeps_history_untouched(self):
        task = self.app.tasks[0]
        self.app.mark_selected_tasks_done()
        self.assertTrue(task['done'])
        self.assertNotIn('end_date', task)
        self.assertNotIn('start_date', task)
        self.assertNotIn('pause_date', task)

    def test_uncompleting_clears_auto_end_date(self):
        task = self.app.tasks[0]
        task['start_date'] = '2026-11-01'
        self.app.mark_selected_tasks_done()
        self.assertIn('end_date', task)
        self.app.mark_selected_tasks_done()
        self.assertFalse(task['done'])
        self.assertNotIn('end_date', task)
        self.assertIn('start_date', task)

    def test_serialize_task_omits_empty_date_fields(self):
        data = TodoApp.serialize_task(self.app.tasks[0])
        self.assertNotIn('start_date', data)
        self.assertNotIn('pause_date', data)
        self.assertNotIn('end_date', data)
        self.assertNotIn('paused', data)

    def test_serialize_task_keeps_date_fields_when_set(self):
        task = self.app.tasks[0]
        task['start_date'] = '2026-11-01'
        task['pause_date'] = '2026-11-05'
        task['end_date'] = '2026-11-10'
        task['paused'] = True
        data = TodoApp.serialize_task(task)
        self.assertEqual(data['start_date'], '2026-11-01')
        self.assertEqual(data['pause_date'], '2026-11-05')
        self.assertEqual(data['end_date'], '2026-11-10')
        self.assertTrue(data['paused'])

    def test_format_short_date(self):
        year = datetime.now().year
        self.assertEqual(TodoApp.format_short_date(f"{year}-03-07"), "03-07")
        self.assertEqual(TodoApp.format_short_date("2020-03-07"), "2020-03-07")
        self.assertEqual(TodoApp.format_short_date(""), "")


class TestCopySubtasks(unittest.TestCase):
    """复制子任务到其他任务"""

    def setUp(self):
        self.app = TodoApp.__new__(TodoApp)
        self.app.tasks = [
            make_main_task("源任务", "src"),
            make_subtask("S-1", "s1", "src"),
            make_subtask("S-2", "s2", "src", done=True),
            make_subtask("S-3", "s3", "src", cancelled=True),
            make_main_task("目标任务", "dst"),
            make_main_task("空任务", "empty"),
        ]
        self.app.collapsed_task_ids = set()
        self.app.display_tasks = []
        self.app.listbox = MagicMock()

    def test_copy_all_subtasks_appends_after_target(self):
        source, target = self.app.tasks[0], self.app.tasks[4]
        created = self.app.clone_subtasks_to_target(source, target)
        self.assertEqual(len(created), 3)
        self.assertEqual([t['name'] for t in self.app.tasks[5:8]], ["S-1", "S-2", "S-3"])
        self.assertTrue(all(t['parent_task_id'] == 'dst' for t in created))
        self.assertTrue(all(t['is_subtask'] for t in created))
        self.assertTrue(all(not t['done'] and not t['cancelled'] for t in created))
        self.assertEqual(len({t['task_id'] for t in created}), 3)
        # 源任务的子任务保持不变
        self.assertEqual(self.app.collect_copyable_subtask_names(source), ["S-1", "S-2", "S-3"])

    def test_copy_only_active_subtasks(self):
        source, target = self.app.tasks[0], self.app.tasks[4]
        created = self.app.clone_subtasks_to_target(source, target, only_active=True)
        self.assertEqual([t['name'] for t in created], ["S-1"])

    def test_copy_inserts_after_existing_subtasks_of_target(self):
        self.app.tasks.insert(5, make_subtask("D-1", "d1", "dst"))
        source, target = self.app.tasks[0], self.app.tasks[4]
        self.app.clone_subtasks_to_target(source, target)
        names = [t['name'] for t in self.app.tasks]
        self.assertEqual(names, ["源任务", "S-1", "S-2", "S-3", "目标任务", "D-1", "S-1", "S-2", "S-3", "空任务"])

    def test_copy_does_not_touch_other_tasks(self):
        before = [dict(t) for t in self.app.tasks]
        source, target = self.app.tasks[0], self.app.tasks[4]
        self.app.clone_subtasks_to_target(source, target)
        self.assertEqual(self.app.tasks[0], before[0])
        self.assertEqual(self.app.tasks[4], before[4])

    def test_copy_expands_collapsed_target(self):
        self.app.collapsed_task_ids = {"dst"}
        source, target = self.app.tasks[0], self.app.tasks[4]
        self.app.clone_subtasks_to_target(source, target)
        self.assertNotIn("dst", self.app.collapsed_task_ids)

    def test_copy_with_no_subtasks_returns_empty(self):
        created = self.app.clone_subtasks_to_target(self.app.tasks[4], self.app.tasks[0])
        self.assertEqual(created, [])

    def test_copy_target_without_task_id_gets_one(self):
        source, target = self.app.tasks[0], self.app.tasks[4]
        target['task_id'] = None
        created = self.app.clone_subtasks_to_target(source, target)
        self.assertTrue(target['task_id'])
        self.assertTrue(all(t['parent_task_id'] == target['task_id'] for t in created))

    def test_selected_real_tasks_skips_headers_and_separators(self):
        header = {'completed_header': True, 'section_id': 0, 'done_count': 1}
        separator = {'name': '────', 'separator': True, 'title': False}
        self.app.tasks.append(separator)
        self.app.display_tasks = [self.app.tasks[0], header, separator]
        self.app.listbox.curselection.return_value = [0, 1, 2]
        self.assertEqual(self.app.get_selected_real_tasks(), [self.app.tasks[0]])

if __name__ == "__main__":
    unittest.main()
