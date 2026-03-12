import tkinter as tk
from tkinter import ttk
from pathlib import Path
import sys
from datetime import datetime, timedelta
try:
    from tkcalendar import Calendar
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False

try:
    import pywinstyles
    PYWINSTYLES_AVAILABLE = True
except ImportError:
    PYWINSTYLES_AVAILABLE = False

class TodoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.is_dark_mode = False
        self.font_size = 13 if sys.platform == "darwin" else 10  # 默认字体大小
        self.tasks = self.load_tasks()  # 真实的任务数据（不包含 completed_header）
        
        # 确保所有任务都有task_id，并修复父子关系
        self.ensure_task_ids()
        
        self.display_tasks = []  # 用于显示的任务列表（包含 completed_header）
        self.shift_pressed = False
        self.bulk_selection_mode = False
        self.key_event_processing = False
        self.selected_indices = set()
        self.collapsed_sections = set()  # 记录哪些分组的已完成任务被折叠

        self.root.withdraw()

        # 先加载配置（包括折叠状态），再设置UI
        self.load_config()
        self.setup_ui()
        self.setup_bindings()

        self.listbox.bind('<Button-1>', self.start_drag)
        self.listbox.bind('<B1-Motion>', self.do_drag)
        self.listbox.bind('<ButtonRelease-1>', self.end_drag)

        self.drag_start_index = None

        self.root.after(10, self.show_window)

    def ensure_task_ids(self):
        """确保所有任务都有唯一的task_id"""
        import uuid
        needs_save = False
        for task in self.tasks:
            if 'task_id' not in task or not task['task_id']:
                task['task_id'] = str(uuid.uuid4())
                needs_save = True
        
        # 如果添加了新的task_id，保存一次
        if needs_save:
            self.save_tasks()

    # Setup methods

    def setup_ui(self):
        self.root.title("To-Do")
        # 根据平台设置不同的最小窗口尺寸
        if sys.platform == "darwin":  # macOS
            self.root.minsize(400, 100)  # macOS上使用更大的最小宽度
        else:  # Windows和其他系统
            self.root.minsize(300, 100)
        self.set_window_icon()

        self.create_main_frame()
        self.create_listbox()
        self.create_input_frame()
        self.create_buttons()

        self.populate_listbox()
        self.apply_theme()
        self.update_buttons_state()
        self.create_context_menu()

    def create_main_frame(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def create_listbox(self):
        # 不设置固定height，让listbox根据内容和窗口大小自适应
        self.listbox = tk.Listbox(self.main_frame, selectmode=tk.EXTENDED, bd=0, highlightthickness=0,
                                  activestyle='none', font=self.get_system_font())
        self.listbox.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=(8, 5))
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def create_input_frame(self):
        self.input_frame = tk.Frame(self.main_frame)
        self.input_frame.grid(row=1, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 5))
        
        # 根据平台调整输入框的权重分配
        if sys.platform == "darwin":  # macOS
            # 在macOS上给输入框更多空间，按钮占用较少空间
            self.input_frame.grid_columnconfigure(0, weight=10)  # 输入框权重大幅提高
            # 按钮列不设置权重，让它们保持最小尺寸
        else:  # Windows和其他系统
            self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry = tk.Text(self.input_frame, height=1, wrap='none', bd=0, font=self.get_system_font(), insertbackground='black')
        self.entry.grid(row=0, column=0, sticky="ew")

        self.setup_entry_bindings()

    def setup_entry_bindings(self):
        self.entry.bind('<FocusIn>', self.on_entry_focus_in)
        self.entry.bind('<FocusOut>', self.on_entry_focus_out)
        self.entry.bind('<Button-1>', self.on_entry_click)

    def create_buttons(self):
        # 根据平台调整按钮样式
        if sys.platform == "darwin":  # macOS
            button_style = {'width': 2, 'padding': (2, 2)}  # 增加宽度和padding
        else:  # Windows和其他系统
            button_style = {'width': 3, 'padding': (0, 0)}
            
        buttons = [
            ("➕", self.add_task),
            ("➖", self.remove_selected_tasks),
            ("✔", self.mark_selected_tasks_done)
        ]
        self.buttons = {}
        for col, (text, command) in enumerate(buttons, start=1):
            button = ttk.Button(self.input_frame, text=text, command=command, style='TButton', **button_style)
            # 在macOS上使用更大的padx，确保按钮有足够空间
            if sys.platform == "darwin":
                padx = (3, 3)  # 增加左右边距
                sticky = ""  # 不扩展
            else:
                padx = (5, 0)
                sticky = ""
            button.grid(row=0, column=col, padx=padx, sticky=sticky)
            self.buttons[text] = button

    def setup_bindings(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind_all('<Control-r>', self.toggle_dark_mode)
        self.root.bind_all('<Control-h>', self.show_about_dialog)
        
        # 字体大小调整快捷键
        self.root.bind_all('<Control-plus>', self.increase_font_size)
        self.root.bind_all('<Control-equal>', self.increase_font_size)  # 兼容不同键盘布局
        self.root.bind_all('<Control-minus>', self.decrease_font_size)
        self.root.bind_all('<Control-0>', self.reset_font_size)

        self.listbox.bind('<Control-u>', self.toggle_urgent_task)
        self.listbox.bind('<Control-d>', self.mark_selected_tasks_done)
        self.listbox.bind('<Control-j>', self.mark_selected_tasks_cancelled)
        self.listbox.bind('<Control-s>', self.add_subtask_shortcut)  # 添加子任务快捷键

        self.listbox.bind('<Delete>', self.remove_selected_tasks)
        self.listbox.bind('<Control-e>', self.edit_task_shortcut)
        self.listbox.bind('<Control-a>', self.select_all_or_text)

        self.listbox.bind('<<ListboxSelect>>', self.update_buttons_state)
        self.listbox.bind('<Double-1>', self.on_double_click)
        # <Button-1> 由 start_drag 处理
        
        # 右键菜单绑定 - macOS和Windows兼容
        if sys.platform == "darwin":  # macOS
            self.listbox.bind('<Button-2>', self.show_context_menu)  # 右键
            self.listbox.bind('<Control-Button-1>', self.show_context_menu_or_ctrl_click)  # Ctrl+左键（兼容右键菜单和多选）
        else:  # Windows和其他系统
            self.listbox.bind('<Button-3>', self.show_context_menu)
            self.listbox.bind('<Control-Button-1>', self.on_ctrl_click)
            
        self.listbox.bind('<Shift-Button-1>', self.on_shift_click)

        self.entry.bind('<Return>', self.add_task)
        self.entry.bind('<KeyRelease>', self.update_buttons_state)

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="编辑任务", command=self.edit_task_shortcut)
        self.context_menu.add_command(label="设置截止日期", command=self.set_deadline_shortcut)
        self.context_menu.add_command(label="设置背景颜色", command=self.set_task_background_color_shortcut)
        self.context_menu.add_command(label="添加子任务", command=self.add_subtask_shortcut)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="标记为完成/未完成", command=self.mark_selected_tasks_done)
        self.context_menu.add_command(label="标记为紧急/取消紧急", command=self.toggle_urgent_task)
        self.context_menu.add_command(label="标记为取消/恢复", command=self.mark_selected_tasks_cancelled)
        self.context_menu.add_command(label="删除任务", command=self.remove_selected_tasks)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="添加分隔符", command=self.add_separator_below)
        self.context_menu.add_separator()
        
        # 字体大小子菜单
        font_menu = tk.Menu(self.context_menu, tearoff=0)
        font_menu.add_command(label="增大字体 (+)", command=self.increase_font_size)
        font_menu.add_command(label="减小字体 (-)", command=self.decrease_font_size)
        font_menu.add_separator()
        font_menu.add_command(label="重置字体大小", command=self.reset_font_size)
        self.context_menu.add_cascade(label="字体大小", menu=font_menu)
        
        self.context_menu.add_command(label="切换暗色模式", command=self.toggle_dark_mode)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="关于", command=self.show_about_dialog)

        self.separator_context_menu = tk.Menu(self.root, tearoff=0)
        self.separator_context_menu.add_command(label="编辑分隔符", command=self.edit_task)
        self.separator_context_menu.add_command(label="添加分隔符标题", command=self.add_separator_title)
        self.separator_context_menu.add_command(label="删除分隔符", command=self.remove_selected_tasks)

        self.separator_context_menu.add_separator()
        self.separator_context_menu.add_command(label="添加分隔符", command=self.add_separator_below)
        self.separator_context_menu.add_separator()
        
        # 为分隔符菜单也添加字体大小选项
        separator_font_menu = tk.Menu(self.separator_context_menu, tearoff=0)
        separator_font_menu.add_command(label="增大字体 (+)", command=self.increase_font_size)
        separator_font_menu.add_command(label="减小字体 (-)", command=self.decrease_font_size)
        separator_font_menu.add_separator()
        separator_font_menu.add_command(label="重置字体大小", command=self.reset_font_size)
        self.separator_context_menu.add_cascade(label="字体大小", menu=separator_font_menu)
        
        self.separator_context_menu.add_command(label="切换暗色模式", command=self.toggle_dark_mode)
        self.separator_context_menu.add_separator()
        self.separator_context_menu.add_command(label="关于", command=self.show_about_dialog)





    def set_window_icon(self, window=None):
        from tkinter import PhotoImage
        if window is None:
            window = self.root
        icon_path = Path(__file__).parent / 'app_icon.ico'
        if icon_path.is_file():
            window.iconbitmap(icon_path)

    # Core functionality

    def add_task(self, event=None):
        task_name = self.entry.get("1.0", "end-1c").strip()
        if task_name:
            if task_name.startswith('---'):
                title_text = task_name[3:].strip()
                if title_text:
                    title_text = title_text.upper()

                    separator_line_before = '─' * 2
                    separator_line_after = '─' * 30 

                    display_text = f"{separator_line_before} {title_text} {separator_line_after}"
                    self.tasks.append({'name': display_text, 'separator': True, 'title': True})
                else:
                    self.tasks.append({'name': '─' * 40, 'separator': True, 'title': False})
            else:
                self.tasks.append({'name': task_name})
            # 添加任务时保持窗口尺寸不变
            self.populate_listbox_without_width_change()
            self.save_tasks()
            self.entry.delete("1.0", tk.END)
            self.update_buttons_state()
            self.update_title()
            self.entry.focus_set()

    def remove_selected_tasks(self, event=None):
        selected_indices = list(self.listbox.curselection())
        for index in reversed(selected_indices):
            # 跳过折叠标题，不允许删除
            if (index >= len(self.display_tasks) or 
                self.display_tasks[index].get('completed_header', False)):
                continue
            # 从 display_tasks 中获取任务信息
            task_to_remove = self.display_tasks[index]
            # 从真实的 tasks 列表中删除
            if task_to_remove in self.tasks:
                self.tasks.remove(task_to_remove)
        # 删除任务时保持窗口尺寸不变
        self.populate_listbox_without_width_change()
        self.save_tasks()
        self.update_buttons_state()
        self.update_title()

    def mark_selected_tasks_done(self, event=None):
        selected_indices = self.listbox.curselection()
        for index in selected_indices:
            display_task = self.display_tasks[index]
            # 跳过分割线和折叠标题
            if (display_task.get('separator', False) or 
                display_task.get('completed_header', False)):
                continue
            # 在真实的 tasks 列表中找到对应的任务并修改
            if display_task in self.tasks:
                task = display_task  # 引用同一个对象
                was_done = task.get('done', False)
                task['done'] = not was_done
                if task['done'] and not was_done:
                    # 标记为完成时，记录完成时间
                    task['completed_time'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                    # 如果有紧急状态，保存它以便后续恢复
                    if task.get('urgent', False):
                        task['was_urgent'] = True
                        task['urgent'] = False
                elif not task['done'] and was_done:
                    # 取消完成时，删除完成时间
                    task.pop('completed_time', None)
                    # 恢复之前的紧急状态
                    if task.get('was_urgent', False):
                        task['urgent'] = True
                        task.pop('was_urgent', None)
                    
                    # 如果是子任务被标记为未完成，则自动将其主任务也标记为未完成
                    if task.get('is_subtask', False):
                        self.auto_uncomplete_parent_task(task)
        
        # 检查是否有主任务的所有子任务都完成了，如果是则自动完成主任务
        self.auto_complete_parent_tasks()
        
        # 任务完成状态改变时不改变窗口宽度
        self.populate_listbox_without_width_change()
        self.save_tasks()
        self.update_buttons_state()
        self.update_title()

    def mark_selected_tasks_cancelled(self, event=None):
        selected_indices = self.listbox.curselection()
        for index in selected_indices:
            display_task = self.display_tasks[index]
            # 跳过分割线和折叠标题
            if (display_task.get('separator', False) or 
                display_task.get('completed_header', False)):
                continue
            # 修改真实任务
            if display_task in self.tasks:
                task = display_task
                task['cancelled'] = not task.get('cancelled', False)
                if task['cancelled']:
                    task['urgent'] = False
        # 任务取消状态改变时不改变窗口宽度
        self.populate_listbox_without_width_change()
        self.save_tasks()
        self.update_buttons_state()
        self.update_title()


    def toggle_urgent_task(self, event=None):
        selected_indices = self.listbox.curselection()
        for index in selected_indices:
            display_task = self.display_tasks[index]
            # 跳过分割线和折叠标题
            if (display_task.get('separator', False) or 
                display_task.get('completed_header', False)):
                continue
            # 修改真实任务
            if display_task in self.tasks:
                task = display_task
                task['urgent'] = not task.get('urgent', False)
        # 切换紧急状态时不改变窗口宽度
        self.populate_listbox_without_width_change()
        self.save_tasks()
        self.update_buttons_state()
        self.update_title()

    def edit_task(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            return

        index = selected_indices[0]
        current_task = self.display_tasks[index]
        
        # 不允许编辑折叠标题
        if current_task.get('completed_header', False):
            return
        
        # 找到真实任务在 self.tasks 中的位置
        if current_task not in self.tasks:
            return

        if current_task.get('separator', False):
            title_text = ''
            if current_task.get('title', False):
                title_text = current_task['name'][2:-30].strip()

            edit_window = tk.Toplevel(self.root)
            edit_window.title("Edit Separator Title")
            edit_window.geometry("200x120")
            edit_window.transient(self.root)
            edit_window.grab_set()

            self.set_window_icon(edit_window)
            self.apply_title_bar_color(edit_window)

            frame = tk.Frame(edit_window, padx=20, pady=20)
            frame.pack(fill="both", expand=True)

            text_entry = tk.Text(frame, wrap='word', height=2, width=28)
            text_entry.insert(tk.END, title_text)
            text_entry.pack(fill="both", expand=True)

            text_entry.focus_set()

            def on_save(event=None):
                new_title = text_entry.get("1.0", "end-1c").strip()

                if new_title:
                    separator_line_before = '─' * 2
                    separator_line_after = '─' * 30
                    display_text = f"{separator_line_before} {new_title.upper()} {separator_line_after}"
                    current_task['name'] = display_text
                    current_task['title'] = True
                else:
                    current_task['name'] = '─' * 40
                    current_task['title'] = False

                # 编辑任务时保持窗口尺寸不变
                self.populate_listbox_without_width_change()
                self.save_tasks()
                self.update_buttons_state()
                edit_window.destroy()

            def on_cancel():
                edit_window.destroy()

            text_entry.bind("<Return>", on_save)

            button_frame = tk.Frame(frame)
            button_frame.pack(fill="x", pady=(10, 0))

            # 根据平台调整按钮宽度，在macOS下使用更宽的按钮以避免文字裁切
            if sys.platform == "darwin":  # macOS
                button_width = 8  # macOS下使用更宽的按钮
                button_padx = 8  # 增加按钮间距
            else:  # Windows和其他系统
                button_width = 6  # 默认宽度
                button_padx = 5

            save_button = ttk.Button(button_frame, text="Save", command=on_save, width=button_width)
            save_button.pack(side="left", padx=0)

            cancel_button = ttk.Button(button_frame, text="Cancel", command=on_cancel, width=button_width)
            cancel_button.pack(side="left", padx=button_padx)

            edit_window.protocol("WM_DELETE_WINDOW", on_cancel)
            self.center_window_over_window(edit_window)

        else:
            current_task_name = current_task['name']

            edit_window = tk.Toplevel(self.root)
            edit_window.title("Edit Task")
            edit_window.geometry("200x120")
            edit_window.transient(self.root)
            edit_window.grab_set()

            self.set_window_icon(edit_window)
            self.apply_title_bar_color(edit_window)

            frame = tk.Frame(edit_window, padx=20, pady=20)
            frame.pack(fill="both", expand=True)

            text_entry = tk.Text(frame, wrap='word', height=2, width=28)
            text_entry.insert(tk.END, current_task_name)
            text_entry.pack(fill="both", expand=True)

            text_entry.focus_set()

            def on_save(event=None):
                new_name = text_entry.get("1.0", "end-1c").strip()
                if new_name:
                    current_task['name'] = new_name
                    # 编辑任务时保持窗口尺寸不变
                    self.populate_listbox_without_width_change()
                    self.save_tasks()
                    self.update_buttons_state()
                edit_window.destroy()

            def on_cancel():
                edit_window.destroy()

            text_entry.bind("<Return>", on_save)

            button_frame = tk.Frame(frame)
            button_frame.pack(fill="x", pady=(10, 0))

            # 根据平台调整按钮宽度，在macOS下使用更宽的按钮以避免文字裁切
            if sys.platform == "darwin":  # macOS
                button_width = 8  # macOS下使用更宽的按钮
                button_padx = 8  # 增加按钮间距
            else:  # Windows和其他系统
                button_width = 6  # 默认宽度
                button_padx = 5

            save_button = ttk.Button(button_frame, text="Save", command=on_save, width=button_width)
            save_button.pack(side="left", padx=0)

            cancel_button = ttk.Button(button_frame, text="Cancel", command=on_cancel, width=button_width)
            cancel_button.pack(side="left", padx=button_padx)

            edit_window.protocol("WM_DELETE_WINDOW", on_cancel)
            self.center_window_over_window(edit_window)


    def add_separator_title(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            return

        index = selected_indices[0]
        current_task = self.display_tasks[index]
        
        if current_task not in self.tasks:
            return

        if current_task.get('separator', False) and not current_task.get('title', False):
            edit_window = tk.Toplevel(self.root)
            edit_window.title("Add Separator Title")
            edit_window.geometry("200x120")
            edit_window.transient(self.root)
            edit_window.grab_set()

            self.set_window_icon(edit_window)
            self.apply_title_bar_color(edit_window)

            frame = tk.Frame(edit_window, padx=20, pady=20)
            frame.pack(fill="both", expand=True)

            text_entry = tk.Text(frame, wrap='word', height=2, width=28)
            text_entry.pack(fill="both", expand=True)

            def on_save(event=None):
                title_text = text_entry.get("1.0", "end-1c").strip().upper()
                if title_text:
                    separator_line_before = '─' * 2
                    separator_line_after = '─' * 30
                    display_text = f"{separator_line_before} {title_text} {separator_line_after}"
                    current_task['name'] = display_text
                    current_task['title'] = True
                    # 添加分隔符标题时保持窗口尺寸不变
                    self.populate_listbox_without_width_change()
                    self.save_tasks()
                    self.update_buttons_state()
                edit_window.destroy()

            def on_cancel():
                edit_window.destroy()

            text_entry.bind("<Return>", on_save)

            button_frame = tk.Frame(frame)
            button_frame.pack(fill="x", pady=(10, 0))

            # 根据平台调整按钮宽度，在macOS下使用更宽的按钮以避免文字裁切
            if sys.platform == "darwin":  # macOS
                button_width = 8  # macOS下使用更宽的按钮
                button_padx = 8  # 增加按钮间距
            else:  # Windows和其他系统
                button_width = 6  # 默认宽度
                button_padx = 5

            save_button = ttk.Button(button_frame, text="Save", command=on_save, width=button_width)
            save_button.pack(side="left", padx=0)

            cancel_button = ttk.Button(button_frame, text="Cancel", command=on_cancel, width=button_width)
            cancel_button.pack(side="left", padx=button_padx)

            edit_window.protocol("WM_DELETE_WINDOW", on_cancel)
            self.center_window_over_window(edit_window)

    def add_separator_below(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            return

        index = selected_indices[0]
        separator = {'name': '─' * 40, 'separator': True, 'title': False}
        self.tasks.insert(index + 1, separator)

        # 添加分隔符时保持窗口尺寸不变
        self.populate_listbox_without_width_change()
        self.save_tasks()
        self.update_buttons_state()

    # UI update methods

    def populate_listbox(self):
        self.listbox.delete(0, tk.END)
        colors = self.get_theme_colors()
        
        # 确保 self.tasks 不包含 completed_header（真实任务数据）
        self.tasks = [task for task in self.tasks if not task.get('completed_header', False)]
        
        # 重新组织任务列表：将完成的任务移到分割线最下部，并添加折叠标题
        # organized_tasks 包含 completed_header，用于显示
        organized_tasks = self.organize_tasks_by_sections()
        
        # 用于跟踪主任务的计数，实现交替背景色
        main_task_count = 0
        
        for index, task in enumerate(organized_tasks):
            if task.get('separator', False):
                display_text = task['name']
                self.listbox.insert(tk.END, display_text)
                self.listbox.itemconfig(index, {'bg': '', 'fg': colors['separator_fg']})
            elif task.get('completed_header', False):
                # 已完成分组的折叠/展开标题
                section_id = task.get('section_id', 0)
                is_collapsed = section_id in self.collapsed_sections
                done_count = task.get('done_count', 0)
                arrow = '▶' if is_collapsed else '▼'
                display_text = f"  {arrow} 已完成 ({done_count})"
                self.listbox.insert(tk.END, display_text)
                self.listbox.itemconfig(index, {'bg': '', 'fg': colors['completed_header_fg']})
            else:
                # 如果是主任务，增加计数
                is_main_task = not task.get('is_subtask', False)
                if is_main_task:
                    main_task_count += 1
                
                icons = self.get_task_icons()
                deadline_indicator = self.get_deadline_indicator(task)
                
                # 子任务缩进
                indent = "    " if task.get('is_subtask', False) else ""
                
                # 根据主任务计数决定背景色（奇偶交替）
                use_alt_bg = (main_task_count % 2 == 0)
                
                if task.get('cancelled', False):
                    display_text = f"{indent}{icons['cancelled']} {task['name']}{deadline_indicator}" 
                    self.listbox.insert(tk.END, display_text)
                    bg_color = colors['alt_bg'] if use_alt_bg else colors['listbox_bg']
                    self.listbox.itemconfig(index, {'bg': bg_color, 'fg': '#a9a9a9'})
                elif task.get('done', False):
                    completed_time = task.get('completed_time', '')
                    time_str = f" [{completed_time}]" if completed_time else ""
                    # 使用删除线样式
                    display_text = f"{indent}{icons['checked']} {self.add_strikethrough(task['name'])}{time_str}"
                    self.listbox.insert(tk.END, display_text)
                    bg_color = colors['alt_bg'] if use_alt_bg else colors['listbox_bg']
                    self.listbox.itemconfig(index, {'bg': bg_color, 'fg': colors['done_fg']})
                else:
                    display_text = f"{indent}{icons['unchecked']} {task['name']}{deadline_indicator}"
                    self.listbox.insert(tk.END, display_text)
                    bg_color = colors['alt_bg'] if use_alt_bg else colors['listbox_bg']
                    self.listbox.itemconfig(index, {'bg': bg_color, 'fg': colors['fg']})
        
        # display_tasks 用于显示和事件处理（包含 completed_header）
        # tasks 保持为真实任务数据（不包含 completed_header，用于保存）
        self.display_tasks = organized_tasks
        self.update_listbox_task_backgrounds()
        self.adjust_window_size()
        self.update_title()
    
    def organize_tasks_by_sections(self):
        """将任务按分割线分组，完成的任务和取消的任务移到每个分组的底部，添加折叠功能
        主任务完成时，其所有子任务跟随主任务一起移动到已完成区域"""
        result = []
        current_section_active = []
        current_section_done = []
        section_id = 0
        
        i = 0
        while i < len(self.tasks):
            task = self.tasks[i]
            
            # 跳过已经是折叠标题的任务
            if task.get('completed_header', False):
                i += 1
                continue
                
            if task.get('separator', False):
                # 遇到分割线，先输出当前section的活跃任务
                result.extend(current_section_active)
                
                # 如果有已完成任务，添加折叠标题
                if current_section_done:
                    # 按主任务的完成时间排序，但保持子任务跟随主任务
                    sorted_done_tasks = self.sort_tasks_preserve_hierarchy(current_section_done)
                    
                    # 添加"已完成"折叠标题
                    # 只计算主任务的数量，不包括子任务
                    main_tasks_done_count = sum(1 for t in sorted_done_tasks if not t.get('is_subtask', False))
                    completed_header = {
                        'completed_header': True,
                        'section_id': section_id,
                        'done_count': main_tasks_done_count
                    }
                    result.append(completed_header)
                    
                    # 如果该分组未折叠，则显示已完成任务
                    if section_id not in self.collapsed_sections:
                        result.extend(sorted_done_tasks)
                
                result.append(task)
                current_section_active = []
                current_section_done = []
                section_id += 1
                i += 1
            else:
                if task.get('is_subtask', False):
                    # 子任务应该已经在处理主任务时被处理了，这里跳过
                    i += 1
                    continue
                else:
                    # 主任务：收集主任务及其所有子任务
                    main_task = task
                    task_group = [main_task]  # 主任务和其子任务的组合
                    
                    # 查找该主任务的所有子任务（在整个任务列表中查找）
                    parent_task_id = main_task.get('task_id')
                    for other_task in self.tasks:
                        if (other_task.get('is_subtask', False) and 
                            other_task.get('parent_task_id') == parent_task_id):
                            task_group.append(other_task)
                    
                    # 根据主任务的状态决定整个任务组的分类
                    if main_task.get('done', False) or main_task.get('cancelled', False):
                        # 主任务完成/取消，整个任务组移动到已完成区域
                        current_section_done.extend(task_group)
                    else:
                        # 主任务未完成，整个任务组保持在活跃区域
                        current_section_active.extend(task_group)
                    
                    i += 1
        
        # 处理最后一个section
        result.extend(current_section_active)
        if current_section_done:
            # 按主任务的完成时间排序，但保持子任务跟随主任务
            sorted_done_tasks = self.sort_tasks_preserve_hierarchy(current_section_done)
            # 只计算主任务的数量，不包括子任务
            main_tasks_done_count = sum(1 for t in sorted_done_tasks if not t.get('is_subtask', False))
            completed_header = {
                'completed_header': True,
                'section_id': section_id,
                'done_count': main_tasks_done_count
            }
            result.append(completed_header)
            if section_id not in self.collapsed_sections:
                result.extend(sorted_done_tasks)
        
        return result
    
    def sort_tasks_preserve_hierarchy(self, tasks):
        """对任务进行排序，但保持子任务跟随主任务的层级关系"""
        # 分离主任务和子任务
        main_tasks = [t for t in tasks if not t.get('is_subtask', False)]
        subtasks = [t for t in tasks if t.get('is_subtask', False)]
        
        # 按完成时间排序主任务
        main_tasks.sort(key=lambda t: t.get('completed_time', ''))
        
        # 重新组织任务，确保子任务跟随主任务
        result = []
        for main_task in main_tasks:
            result.append(main_task)
            # 找到该主任务的所有子任务并添加到结果中
            main_task_id = main_task.get('task_id')
            main_task_subtasks = [st for st in subtasks if st.get('parent_task_id') == main_task_id]
            # 子任务也按完成时间排序
            main_task_subtasks.sort(key=lambda t: t.get('completed_time', ''))
            result.extend(main_task_subtasks)
        
        return result
    
    def add_strikethrough(self, text):
        """为文字添加删除线效果"""
        return ''.join([char + '\u0336' for char in text])
    
    def get_deadline_indicator(self, task):
        """获取deadline提示标识"""
        deadline = task.get('deadline', '')
        if not deadline or task.get('done', False):
            return ''
        
        try:
            deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
            now = datetime.now()
            days_diff = (deadline_date - now).days
            
            if days_diff < 0:
                return f' ⚠️超期{abs(days_diff)}天'
            elif days_diff == 0:
                return ' ⚠️今天到期'
            elif days_diff <= 3:
                return f' ⏰{days_diff}天后到期'
            else:
                return f' 📅{deadline}'
        except:
            return ''

    def update_buttons_state(self, event=None):
        selected_indices = self.listbox.curselection()
        has_selection = bool(selected_indices) or self.bulk_selection_mode
        
        # 过滤掉折叠标题和分割线
        valid_selections = [idx for idx in selected_indices 
                           if idx < len(self.display_tasks)
                           and not self.display_tasks[idx].get('separator', False) 
                           and not self.display_tasks[idx].get('completed_header', False)]
        
        only_separators_selected = all(idx < len(self.display_tasks) and 
                                       (self.display_tasks[idx].get('separator', False) or 
                                        self.display_tasks[idx].get('completed_header', False))
                                       for idx in selected_indices)
        all_cancelled = all(idx < len(self.display_tasks) and 
                           self.display_tasks[idx].get('cancelled', False) 
                           for idx in valid_selections) if valid_selections else False

        self.buttons["➕"]['state'] = 'normal' if self.entry.get("1.0", "end-1c").strip() else 'disabled'
        self.buttons["➖"]['state'] = 'normal' if valid_selections else 'disabled'
        self.buttons["✔"]['state'] = 'disabled' if only_separators_selected or all_cancelled or not valid_selections else 'normal'


    def update_buttons_style(self, bg, fg):
        style = ttk.Style()
        
        # 根据平台调整按钮样式
        if sys.platform == "darwin":  # macOS
            style.configure('TButton', 
                          background=bg, 
                          foreground=fg, 
                          padding=(2, 1),  # 非常紧凑的padding
                          relief='flat',
                          borderwidth=1,
                          width=1,  # 最小宽度
                          font=self.get_system_font())  # 使用系统字体
        else:  # Windows和其他系统
            style.configure('TButton', 
                          background=bg, 
                          foreground=fg, 
                          padding=5)
        
        style.map('TButton', 
                background=[('active', bg), ('disabled', '#666666' if self.is_dark_mode else '#c0c0c0')],
                foreground=[('active', fg), ('disabled', 'grey')])

    def update_listbox_task_backgrounds(self):
        colors = self.get_theme_colors()
        for index, task in enumerate(self.display_tasks):
            if task.get('separator', False):
                self.listbox.itemconfig(index, {'bg': '', 'fg': colors['separator_fg']})
            elif task.get('completed_header', False):
                self.listbox.itemconfig(index, {'bg': '', 'fg': colors['completed_header_fg']})
            elif task.get('cancelled', False):
                self.listbox.itemconfig(index, {'bg': '', 'fg': '#a9a9a9'})
            elif task.get('done', False):
                self.listbox.itemconfig(index, {'bg': '', 'fg': colors['done_fg']})
            elif task.get('urgent', False):
                # 紧急任务使用红色背景，覆盖自定义背景色
                self.listbox.itemconfig(index, {'bg': colors['urgent_bg'], 'fg': 'white'})
            else:
                # 主任务：使用自定义背景色或默认主任务背景色
                if not task.get('is_subtask', False):
                    custom_bg = task.get('custom_bg_color', '')
                    if custom_bg:
                        # 使用用户自定义的背景色
                        self.listbox.itemconfig(index, {'bg': custom_bg, 'fg': colors['fg']})
                    else:
                        # 使用默认主任务背景色
                        self.listbox.itemconfig(index, {'bg': colors['main_task_bg'], 'fg': colors['fg']})
                else:
                    # 子任务：使用普通背景色
                    self.listbox.itemconfig(index, {'bg': colors['listbox_bg'], 'fg': colors['fg']})

    def adjust_window_size(self, allow_width_change=True, allow_height_change=True):
        num_tasks = len(self.display_tasks)
        
        # 根据平台调整行高
        if sys.platform == "darwin":  # macOS
            line_height = 20  # macOS上使用更大的行高以适应13pt字体
        else:  # Windows和其他系统
            line_height = 18
        
        # 计算基础高度：包括输入框、按钮、边距等UI元素的高度
        if sys.platform == "darwin":  # macOS
            base_ui_height = 140  # macOS需要更多空间
        else:  # Windows和其他系统
            base_ui_height = 130  # 增加基础高度
        
        # 根据任务数量计算内容高度，不设置上限，完全自适应
        content_height = num_tasks * line_height
        
        # 计算总高度：基础UI高度 + 内容高度 + 额外底部边距，设置最小高度但不设置最大高度
        extra_bottom_margin = 20  # 额外的底部边距，防止裁切
        new_height = max(150, base_ui_height + content_height + extra_bottom_margin)
        
        # 获取屏幕高度，确保窗口不会超出屏幕
        screen_height = self.root.winfo_screenheight()
        # 留出一些边距给系统任务栏等
        max_screen_height = screen_height - 100
        
        # 如果计算的高度超过屏幕高度，则使用屏幕高度并启用滚动
        if new_height > max_screen_height:
            new_height = max_screen_height
        
        # 获取当前窗口尺寸
        current_geometry = self.root.geometry()
        current_width = int(current_geometry.split('x')[0]) if 'x' in current_geometry else 450
        current_height = int(current_geometry.split('x')[1].split('+')[0]) if 'x' in current_geometry else new_height
        
        # 如果不允许宽度变化，直接使用当前宽度
        if not allow_width_change:
            final_width = current_width
        else:
            # 计算最长任务的宽度 - 只计算当前显示的任务
            if sys.platform == "darwin":  # macOS
                min_width = 450  # macOS上使用更大的最小宽度
                max_allowed_width = 1200  # 更大的最大宽度
            else:  # Windows和其他系统
                min_width = 300  # 最小宽度
                max_allowed_width = 1000  # 最大宽度
            
            # 创建临时字体对象来测量文本宽度
            import tkinter.font as tkfont
            font = tkfont.Font(family=self.get_system_font()[0], size=self.get_system_font()[1])
            
            calculated_width = min_width
            
            # 重新组织任务，获取当前实际显示的任务列表
            current_display_tasks = self.organize_tasks_by_sections()
            
            for task in current_display_tasks:
                # 获取显示文本，但在宽度计算时使用原始文本避免删除线影响
                if task.get('separator', False):
                    display_text = task['name']
                elif task.get('completed_header', False):
                    section_id = task.get('section_id', 0)
                    done_count = task.get('done_count', 0)
                    is_collapsed = section_id in self.collapsed_sections
                    arrow = '▶' if is_collapsed else '▼'
                    display_text = f"  {arrow} 已完成 ({done_count})"
                else:
                    icons = self.get_task_icons()
                    deadline_indicator = self.get_deadline_indicator(task)
                    
                    # 子任务缩进
                    indent = "    " if task.get('is_subtask', False) else ""
                    
                    if task.get('cancelled', False):
                        display_text = f"{indent}{icons['cancelled']} {task['name']}{deadline_indicator}"
                    elif task.get('done', False):
                        completed_time = task.get('completed_time', '')
                        time_str = f" [{completed_time}]" if completed_time else ""
                        # 在宽度计算时使用原始文本，不使用删除线版本
                        display_text = f"{indent}{icons['checked']} {task['name']}{time_str}"
                    else:
                        display_text = f"{indent}{icons['unchecked']} {task['name']}{deadline_indicator}"
                
                # 测量文本宽度（加上边距和滚动条等）
                text_width = font.measure(display_text) + 80  # 加上padding和边距
                calculated_width = max(calculated_width, text_width)
            
            # 在macOS上为按钮预留额外空间
            if sys.platform == "darwin":
                # 为三个按钮预留额外空间，每个按钮大约需要35-40像素
                button_space = 120  # 三个按钮 + 边距
                calculated_width += button_space
            
            # 限制在最大宽度内
            calculated_width = min(calculated_width, max_allowed_width)
            
            # 改进的宽度稳定性逻辑：优先保持当前宽度，只在内容明显超出时才调整
            width_threshold = 50  # 增大阈值，让窗口更稳定
            
            # 检查当前宽度是否能容纳所有内容
            content_fits_current_width = calculated_width <= current_width + 20  # 留一些缓冲
            
            if content_fits_current_width:
                # 如果当前宽度能容纳所有内容，保持不变
                final_width = max(current_width, min_width)
            elif calculated_width > current_width + width_threshold:
                # 只有在内容明显超出当前宽度时才扩大窗口
                final_width = calculated_width
            elif calculated_width < current_width - width_threshold:
                # 只有在内容明显少于当前宽度时才缩小窗口
                final_width = max(calculated_width, min_width)
            else:
                # 其他情况保持当前宽度
                final_width = max(current_width, min_width)
        
        # 如果不允许高度变化，使用当前高度
        if not allow_height_change:
            final_height = current_height
        else:
            final_height = new_height
        
        self.root.geometry(f"{final_width}x{final_height}")

    def update_title(self):
        # 只计算主任务的数量（不包括子任务、分割线和已取消的任务）
        total_tasks = sum(1 for task in self.tasks if not task.get('separator', False) and not task.get('cancelled', False) and not task.get('is_subtask', False))
        done_tasks = sum(task.get('done', False) for task in self.tasks if not task.get('separator', False) and not task.get('cancelled', False) and not task.get('is_subtask', False))
        urgent_tasks = self.count_urgent_tasks()

        urgent_text = f"[{urgent_tasks} urgent]" if urgent_tasks > 0 else ""

        if total_tasks == 0:
            self.root.title("To-Do")
        elif done_tasks == total_tasks:
            self.root.title(f"To-Do ({done_tasks}/{total_tasks}) — All done! {urgent_text}")
        else:
            self.root.title(f"To-Do ({done_tasks}/{total_tasks}) {urgent_text}")

    def apply_theme(self):
        colors = self.get_theme_colors()
        self.root.configure(bg=colors['bg'])
        self.main_frame.configure(bg=colors['bg'])
        self.input_frame.configure(bg=colors['bg'])
        self.listbox.configure(bg=colors['listbox_bg'], fg=colors['fg'],
                               selectbackground=colors['select_bg'], selectforeground=colors['fg'])
        self.entry.configure(bg=colors['entry_bg'], fg=colors['fg'])
        self.update_buttons_style(colors['button_bg'], colors['button_fg'])
        self.update_listbox_task_backgrounds()

        self.entry.config(insertbackground=colors['caret_color'])
        self.apply_title_bar_color()
    
    def apply_title_bar_color(self, window=None):
        """设置窗口标题栏颜色以匹配主题"""
        if not PYWINSTYLES_AVAILABLE or sys.platform != 'win32':
            return
        
        if window is None:
            window = self.root
        
        try:
            if self.is_dark_mode:
                # 深色模式：使用深色标题栏
                pywinstyles.apply_style(window, 'dark')
                # 设置标题栏颜色为深色
                pywinstyles.change_header_color(window, '#15131e')
            else:
                # 浅色模式：使用浅色标题栏
                pywinstyles.apply_style(window, 'normal')
                pywinstyles.change_header_color(window, 'white')
        except Exception as e:
            # 如果设置失败，静默处理
            pass

    # Event handlers

    def on_double_click(self, event):
        """处理双击事件"""
        index = self.listbox.nearest(event.y)
        
        # 如果双击的是折叠标题，也切换折叠状态（与单击行为一致）
        if index < len(self.display_tasks) and self.display_tasks[index].get('completed_header', False):
            self.toggle_completed_section(index)
            return 'break'  # 阻止事件继续传播
        
        # 如果双击的是分割线，不做任何操作
        if (index < len(self.display_tasks) and 
            self.display_tasks[index].get('separator', False)):
            return 'break'
        
        # 否则标记为完成/未完成
        self.mark_selected_tasks_done(event)
        return 'break'
    
    def toggle_completed_section(self, index):
        """切换已完成分组的折叠/展开状态"""
        if index >= len(self.display_tasks):
            return
        
        task = self.display_tasks[index]
        if not task.get('completed_header', False):
            return
        
        section_id = task.get('section_id', 0)
        
        # 切换折叠状态
        if section_id in self.collapsed_sections:
            self.collapsed_sections.remove(section_id)
        else:
            self.collapsed_sections.add(section_id)
        
        # 清除选中状态，避免误操作
        self.listbox.selection_clear(0, tk.END)
        
        # 重新渲染列表，但不改变窗口宽度
        self.populate_listbox_without_width_change()
        self.save_config()
    
    def populate_listbox_without_width_change(self):
        """重新填充列表框但不改变窗口宽度和高度"""
        self.listbox.delete(0, tk.END)
        colors = self.get_theme_colors()
        
        # 确保 self.tasks 不包含 completed_header（真实任务数据）
        self.tasks = [task for task in self.tasks if not task.get('completed_header', False)]
        
        # 重新组织任务列表：将完成的任务移到分割线最下部，并添加折叠标题
        # organized_tasks 包含 completed_header，用于显示
        organized_tasks = self.organize_tasks_by_sections()
        
        # 用于跟踪主任务的计数，实现交替背景色
        main_task_count = 0
        
        for index, task in enumerate(organized_tasks):
            if task.get('separator', False):
                display_text = task['name']
                self.listbox.insert(tk.END, display_text)
                self.listbox.itemconfig(index, {'bg': '', 'fg': colors['separator_fg']})
            elif task.get('completed_header', False):
                # 已完成分组的折叠/展开标题
                section_id = task.get('section_id', 0)
                is_collapsed = section_id in self.collapsed_sections
                done_count = task.get('done_count', 0)
                arrow = '▶' if is_collapsed else '▼'
                display_text = f"  {arrow} 已完成 ({done_count})"
                self.listbox.insert(tk.END, display_text)
                self.listbox.itemconfig(index, {'bg': '', 'fg': colors['completed_header_fg']})
            else:
                # 如果是主任务，增加计数
                is_main_task = not task.get('is_subtask', False)
                if is_main_task:
                    main_task_count += 1
                
                icons = self.get_task_icons()
                deadline_indicator = self.get_deadline_indicator(task)
                
                # 子任务缩进
                indent = "    " if task.get('is_subtask', False) else ""
                
                # 根据主任务计数决定背景色（奇偶交替）
                use_alt_bg = (main_task_count % 2 == 0)
                
                if task.get('cancelled', False):
                    display_text = f"{indent}{icons['cancelled']} {task['name']}{deadline_indicator}" 
                    self.listbox.insert(tk.END, display_text)
                    bg_color = colors['alt_bg'] if use_alt_bg else colors['listbox_bg']
                    self.listbox.itemconfig(index, {'bg': bg_color, 'fg': '#a9a9a9'})
                elif task.get('done', False):
                    completed_time = task.get('completed_time', '')
                    time_str = f" [{completed_time}]" if completed_time else ""
                    # 使用删除线样式
                    display_text = f"{indent}{icons['checked']} {self.add_strikethrough(task['name'])}{time_str}"
                    self.listbox.insert(tk.END, display_text)
                    bg_color = colors['alt_bg'] if use_alt_bg else colors['listbox_bg']
                    self.listbox.itemconfig(index, {'bg': bg_color, 'fg': colors['done_fg']})
                else:
                    display_text = f"{indent}{icons['unchecked']} {task['name']}{deadline_indicator}"
                    self.listbox.insert(tk.END, display_text)
                    bg_color = colors['alt_bg'] if use_alt_bg else colors['listbox_bg']
                    self.listbox.itemconfig(index, {'bg': bg_color, 'fg': colors['fg']})
        
        # display_tasks 用于显示和事件处理（包含 completed_header）
        # tasks 保持为真实任务数据（不包含 completed_header，用于保存）
        self.display_tasks = organized_tasks
        
        self.update_listbox_task_backgrounds()
        # 不改变宽度和高度
        self.adjust_window_size(allow_width_change=False, allow_height_change=False)
        self.update_title()

    def show_context_menu_or_ctrl_click(self, event):
        """在macOS上处理Ctrl+Click - 区分右键菜单和多选操作"""
        # 在macOS上，长按Ctrl+Click通常用于右键菜单
        # 短按用于多选，这里我们简化处理：如果已经有选中项，则显示菜单，否则进行多选
        current_selection = self.listbox.curselection()
        if len(current_selection) > 0:
            # 已有选中项，显示右键菜单
            self.show_context_menu(event)
        else:
            # 没有选中项，执行多选操作
            self.on_ctrl_click(event)

    def on_ctrl_click(self, event):
        """Handle robust Ctrl-click to toggle selection of individual tasks."""
        index = self.listbox.nearest(event.y)
        if index in self.listbox.curselection():
            self.listbox.selection_clear(index)
        else:
            self.listbox.selection_set(index)

        self.update_buttons_state()

        return 'break'

    def on_shift_click(self, event):
        """Handle Shift-click to select a range of tasks."""
        index = self.listbox.nearest(event.y)
        cur_selection = self.listbox.curselection()
        if cur_selection:
            start_index = cur_selection[0]
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(start_index, index)
        else:
            self.listbox.selection_set(index)

    def on_entry_focus_in(self, event=None):
        colors = self.get_theme_colors()
        self.entry.configure(highlightbackground=colors['entry_border_focus'], highlightcolor=colors['entry_border_focus'], highlightthickness=1)
        self.entry.config(insertbackground=colors['caret_color_focus'])

    def on_entry_focus_out(self, event=None):
        colors = self.get_theme_colors()
        self.entry.configure(highlightbackground=colors['entry_bg'], highlightcolor=colors['entry_bg'], highlightthickness=1)
        self.entry.config(insertbackground=colors['caret_color'])

    def on_entry_click(self, event=None):
        self.listbox.selection_clear(0, tk.END)
        self.entry.focus_set()
        self.bulk_selection_mode = False
        self.update_buttons_state()

    def on_close(self):
        self.root.unbind_all('<Control-v>')
        self.root.unbind_all('<Control-u>')
        self.root.unbind_all('<Control-d>')
        self.root.unbind_all('<Delete>')
        self.root.unbind_all('<Control-e>')
        self.root.unbind_all('<Control-a>')
        self.listbox.unbind('<<ListboxSelect>>')
        self.listbox.unbind('<Double-1>')
        self.entry.unbind('<Return>')
        self.entry.unbind('<KeyRelease>')
        self.listbox.unbind('<Button-1>')
        
        # 清理右键菜单绑定 - 跨平台兼容
        if sys.platform == "darwin":  # macOS
            self.listbox.unbind('<Button-2>')
            self.listbox.unbind('<Control-Button-1>')
        else:  # Windows和其他系统
            self.listbox.unbind('<Button-3>')
            
        self.root.unbind_all('<Control-h>')

        self.save_config()
        self.root.destroy()
        self.root.quit()

    def on_shift_key_press(self, event):
        self.shift_pressed = True
        self.update_bulk_selection_mode()

    def on_shift_key_release(self, event):
        self.shift_pressed = False
        self.update_bulk_selection_mode()

    # Selection handling
    
    def handle_single_selection(self, index):
        if index in self.selected_indices:
            self.selected_indices.remove(index)
            self.listbox.selection_clear(index)
        else:
            self.selected_indices.add(index)
            self.listbox.selection_set(index)
        self.update_buttons_state()

    def handle_bulk_selection(self, index):
        if index in self.selected_indices:
            self.selected_indices.remove(index)
        else:
            self.selected_indices.add(index)
        
        self.update_listbox_selections()

    def update_bulk_selection_mode(self):
        if self.shift_pressed:
            self.bulk_selection_mode = True
        else:
            self.bulk_selection_mode = False
        self.update_buttons_state()

    def update_listbox_selections(self):
        self.listbox.selection_clear(0, tk.END)
        for idx in self.selected_indices:
            self.listbox.selection_set(idx)
        self.update_buttons_state()

    def select_all_tasks(self, event=None):
        self.selected_indices = set(range(len(self.tasks)))
        self.update_listbox_selections()

    def select_all_or_text(self, event=None):
        if self.entry.focus_get() == self.entry:
            self.entry.tag_add(tk.SEL, "1.0", tk.END)
            self.entry.mark_set(tk.INSERT, "1.0")
            self.entry.see(tk.INSERT)
        else:
            self.select_all_tasks()

    # Drag and drop functionality

    def start_drag(self, event):
        """Handle the start of the drag event."""
        self.drag_start_index = self.listbox.nearest(event.y)
        
        # 如果点击的是已完成标题，切换折叠状态而不是拖拽
        if (self.drag_start_index < len(self.display_tasks) and 
            self.display_tasks[self.drag_start_index].get('completed_header', False)):
            self.toggle_completed_section(self.drag_start_index)
            self.drag_start_index = None
            return 'break'
        
        # 如果点击的是分割线，允许拖拽但不影响其他逻辑
        # 普通任务：正常的拖拽和选择逻辑
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.drag_start_index)
        self.selected_indices = {self.drag_start_index}
        self.update_buttons_state()

    def do_drag(self, event):
        """Handle the dragging motion and visually highlight the item being dragged over."""
        drag_over_index = self.listbox.nearest(event.y)
        if drag_over_index != self.drag_start_index:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(drag_over_index)
    
    def end_drag(self, event):
        """Handle dropping the item by moving it to the new position."""
        drag_end_index = self.listbox.nearest(event.y)
        if self.drag_start_index is not None and drag_end_index != self.drag_start_index:
            # 从 display_tasks 获取被拖拽的任务
            dragged_task = self.display_tasks[self.drag_start_index]
            target_task = self.display_tasks[drag_end_index]
            
            # 在真实的 tasks 列表中重新排序
            if dragged_task in self.tasks and target_task in self.tasks:
                start_idx_in_tasks = self.tasks.index(dragged_task)
                end_idx_in_tasks = self.tasks.index(target_task)
                task = self.tasks.pop(start_idx_in_tasks)
                self.tasks.insert(end_idx_in_tasks, task)
                
                # 拖拽重排序时不改变窗口宽度
                self.populate_listbox_without_width_change()
                self.save_tasks()
                self.update_buttons_state()
        self.drag_start_index = None

    def reorder_tasks(self, start_index, end_index):
        """Move the task from start_index to end_index in the tasks list."""
        task = self.tasks.pop(start_index)
        self.tasks.insert(end_index, task)
        # 重排序时不改变窗口宽度
        self.populate_listbox_without_width_change()
        self.save_tasks()
        self.update_buttons_state()

    # File I/O and configuration

    @classmethod
    def load_tasks(cls):
        import json
        tasks_file = cls.get_tasks_file()
        tasks_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            tasks = json.loads(tasks_file.read_text(encoding='utf-8'))
            
            # 为旧数据创建task_id映射
            task_id_map = {}  # 内存地址 -> task_id 的映射
            
            for task in tasks:
                if task.get('separator', False):
                    task['title'] = task.get('title', False)
                
                # 确保每个任务都有唯一的task_id
                if 'task_id' not in task or not task['task_id']:
                    import uuid
                    task['task_id'] = str(uuid.uuid4())
                
                # 处理旧的parent_id字段（基于内存地址）
                if 'parent_id' in task and task['parent_id'] is not None:
                    # 这是旧格式的子任务，需要转换
                    old_parent_id = task['parent_id']
                    if old_parent_id in task_id_map:
                        task['parent_task_id'] = task_id_map[old_parent_id]
                    else:
                        # 找不到父任务，清除子任务标记
                        task['is_subtask'] = False
                    # 删除旧字段
                    del task['parent_id']
                
                # 为主任务建立映射（用于处理旧数据）
                if not task.get('is_subtask', False):
                    # 这可能是一个主任务，但我们无法从保存的数据中恢复内存地址映射
                    # 所以旧的子任务关系可能会丢失，这是数据格式升级的代价
                    pass
            
            return tasks
        except (json.JSONDecodeError, FileNotFoundError):
            return []


    def save_tasks(self):
        import json
        try:
            # 过滤掉 completed_header，只保存真实的任务
            tasks_to_save = [{'name': task['name'], 
                            'done': task.get('done', False), 
                            'cancelled': task.get('cancelled', False), 
                            'urgent': task.get('urgent', False), 
                            'separator': task.get('separator', False), 
                            'title': task.get('title', False),
                            'completed_time': task.get('completed_time', ''),
                            'deadline': task.get('deadline', ''),
                            'was_urgent': task.get('was_urgent', False),
                            'subtasks': task.get('subtasks', []),  # 添加子任务支持
                            'is_subtask': task.get('is_subtask', False),  # 标记是否为子任务
                            'parent_task_id': task.get('parent_task_id', None),  # 父任务的task_id
                            'task_id': task.get('task_id', None),  # 任务的唯一ID
                            'custom_bg_color': task.get('custom_bg_color', '')}  # 自定义背景色
                            for task in self.tasks if not task.get('completed_header', False)]

            self.get_tasks_file().write_text(json.dumps(tasks_to_save, indent=4), encoding='utf-8')
        except Exception as e:
            print(f"Error saving tasks: {e}")



    def load_config(self):
        import json
        config_file = self.get_config_file()
        if config_file.is_file():
            config = json.loads(config_file.read_text(encoding='utf-8'))
            self.is_dark_mode = config.get('dark_mode', False)
            # 加载字体大小，如果没有保存则使用默认值
            default_font_size = 13 if sys.platform == "darwin" else 10
            self.font_size = config.get('font_size', default_font_size)
            # 加载折叠状态，默认为空（全部展开）
            collapsed_list = config.get('collapsed_sections', [])
            self.collapsed_sections = set(collapsed_list)
            
            self.initial_geometry = config.get('geometry', '')
        else:
            self.initial_geometry = ''
            # 默认全部展开（空集合）
            self.collapsed_sections = set()
    
    def get_all_section_ids(self):
        """获取所有分组的ID"""
        section_ids = set()
        section_id = 0
        has_done = False
        
        for task in self.tasks:
            if task.get('completed_header', False):
                continue
            if task.get('separator', False):
                if has_done:
                    section_ids.add(section_id)
                section_id += 1
                has_done = False
            elif task.get('done', False):
                has_done = True
        
        # 最后一个分组
        if has_done:
            section_ids.add(section_id)
        
        return section_ids

    def save_config(self):
        import json
        try:
            config_file = self.get_config_file()
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config = {
                'geometry': self.root.geometry(),
                'dark_mode': self.is_dark_mode,
                'font_size': self.font_size,
                'collapsed_sections': list(self.collapsed_sections)
            }
            config_file.write_text(json.dumps(config, indent=4), encoding='utf-8')
        except Exception as e:
            print(f"Error saving config: {e}")

    # Utility methods

    @staticmethod
    def get_base_dir():
        return Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent

    @classmethod
    def get_tasks_file(cls):
        return cls.get_base_dir() / 'todo_app' / 'tasks.json'

    @classmethod
    def get_config_file(cls):
        return cls.get_base_dir() / 'todo_app' / 'config.json'

    def get_theme_colors(self):
        if sys.platform == "darwin":  # macOS特定颜色
            if self.is_dark_mode:
                return {
                    'bg': '#1e1e1e',  # macOS深色模式背景
                    'fg': '#ffffff',
                    'entry_bg': '#2d2d2d',  # 更柔和的输入框背景
                    'entry_border_focus': '#007aff',  # macOS蓝色
                    'caret_color': '#ffffff',
                    'caret_color_focus': '#007aff',
                    'button_bg': '#2d2d2d',
                    'button_fg': '#007aff',  # macOS系统蓝色
                    'listbox_bg': '#1e1e1e',
                    'alt_bg': '#252525',  # 交替背景色，比主背景稍亮
                    'select_bg': '#3a3a3c',  # macOS选中背景
                    'done_bg': '#d3d3d3',
                    'done_fg': '#808080',
                    'urgent_bg': '#ff3b30',  # macOS红色
                    'separator_fg': '#8e8e93',  # macOS灰色
                    'completed_header_fg': '#8e8e93',
                    'main_task_bg': '#2C3E50'  # 主任务默认背景色（暗色）
                }
            else:
                return {
                    'bg': '#ffffff',
                    'fg': '#000000',
                    'entry_bg': '#f2f2f7',  # macOS浅色输入框
                    'entry_border_focus': '#007aff',
                    'caret_color': '#000000',
                    'caret_color_focus': '#007aff',
                    'button_bg': '#f2f2f7',
                    'button_fg': '#007aff',
                    'listbox_bg': '#ffffff',
                    'alt_bg': '#f8f8f8',  # 交替背景色，比主背景稍暗
                    'select_bg': '#e5e5ea',  # macOS浅色选中
                    'done_bg': '#d3d3d3',
                    'done_fg': '#808080',
                    'urgent_bg': '#ff3b30',
                    'separator_fg': '#8e8e93',
                    'completed_header_fg': '#8e8e93',
                    'main_task_bg': '#F0E5FF'  # 主任务默认背景色（亮色）
                }
        else:  # Windows和其他系统的原有颜色
            return {
                'bg': '#15131e' if self.is_dark_mode else 'white',
                'fg': 'white' if self.is_dark_mode else 'black',
                'entry_bg': '#444444' if self.is_dark_mode else '#f0f0f0',
                'entry_border_focus': '#cccccc' if self.is_dark_mode else '#333333',
                'caret_color': 'white' if self.is_dark_mode else 'black',
                'caret_color_focus': '#cccccc' if self.is_dark_mode else '#333333',
                'button_bg': '#444444' if self.is_dark_mode else '#e0e0e0',
                'button_fg': '#00BFFF' if self.is_dark_mode else '#1E90FF',
                'listbox_bg': '#15131e' if self.is_dark_mode else 'white',
                'alt_bg': '#1a1820' if self.is_dark_mode else '#f5f5f5',  # 交替背景色
                'select_bg': '#555555' if self.is_dark_mode else '#d3d3d3',
                'done_bg': '#d3d3d3' if self.is_dark_mode else '#d3d3d3',
                'done_fg': '#808080' if self.is_dark_mode else '#808080',
                'urgent_bg': '#de3f4d' if self.is_dark_mode else '#de3f4d',
                'separator_fg': '#cccccc',
                'completed_header_fg': '#888888' if self.is_dark_mode else '#666666',
                'main_task_bg': '#2C3E50' if self.is_dark_mode else '#F0E5FF'  # 主任务默认背景色
            }

    @staticmethod
    def get_task_icons():
        """获取适合当前系统的任务图标"""
        if sys.platform == "darwin":  # macOS
            return {
                'unchecked': '☐',  # 空心方框，在macOS上显示为白色边框
                'checked': '☑',    # 带勾的方框
                'cancelled': '☒'   # 带X的方框
            }
        else:  # Windows和其他系统
            return {
                'unchecked': '⬜',  # 白色大方块
                'checked': '✔',    # 勾号
                'cancelled': '✖'   # X号
            }

    def get_system_font(self):
        """获取适合当前系统的字体，使用用户设置的字体大小"""
        if sys.platform == "darwin":  # macOS
            return ('SF Pro Text', self.font_size)
        elif sys.platform == "win32":  # Windows
            return ('Microsoft YaHei UI', self.font_size)
        else:  # Linux和其他系统
            return ('DejaVu Sans', self.font_size)

    def count_urgent_tasks(self):
        return sum(1 for task in self.tasks if task.get('urgent', False))

    # Window management

    def show_window(self):
        if self.initial_geometry:
            # 如果有保存的几何信息，使用保存的位置和大小
            self.root.geometry(self.initial_geometry)
        else:
            # 否则使用 adjust_window_size 计算的大小，并居中显示
            # adjust_window_size 已经在 populate_listbox 中被调用过了
            self.center_window()
        
        self.root.deiconify()
        
        self.root.lift()
        self.root.focus_force()
        
        if sys.platform == "win32":
            self.root.attributes('-topmost', True)
            self.root.update()
            self.root.attributes('-topmost', False)

    def center_window(self, default_size=None):
        self.root.update_idletasks()
        if default_size:
            width, height = map(int, default_size.split('x'))
        else:
            width, height = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def center_window_over_window(self, window):
        window.update_idletasks()
        
        main_window_width = self.root.winfo_width()
        main_window_height = self.root.winfo_height()
        main_window_x = self.root.winfo_x()
        main_window_y = self.root.winfo_y()

        window_width = window.winfo_reqwidth()
        window_height = window.winfo_reqheight()

        x = main_window_x + (main_window_width - window_width) // 2
        y = main_window_y + (main_window_height - window_height) // 2

        window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Miscellaneous

    def toggle_dark_mode(self, event=None):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        self.apply_title_bar_color()
    
    def increase_font_size(self, event=None):
        """增大字体大小"""
        max_font_size = 24  # 设置最大字体大小
        if self.font_size < max_font_size:
            self.font_size += 1
            self.update_font_size()
    
    def decrease_font_size(self, event=None):
        """减小字体大小"""
        min_font_size = 8  # 设置最小字体大小
        if self.font_size > min_font_size:
            self.font_size -= 1
            self.update_font_size()
    
    def reset_font_size(self, event=None):
        """重置字体大小为默认值"""
        default_size = 13 if sys.platform == "darwin" else 10
        if self.font_size != default_size:
            self.font_size = default_size
            self.update_font_size()
    
    def update_font_size(self):
        """更新所有UI元素的字体大小"""
        new_font = self.get_system_font()
        
        # 更新listbox字体
        self.listbox.configure(font=new_font)
        
        # 更新输入框字体
        self.entry.configure(font=new_font)
        
        # 更新按钮字体
        self.update_buttons_style(self.get_theme_colors()['button_bg'], self.get_theme_colors()['button_fg'])
        
        # 重新计算窗口大小，但允许宽度变化以适应新的字体大小
        self.populate_listbox()  # 这会调用 adjust_window_size()
        
        # 保存配置
        self.save_config()
        
    def show_about_dialog(self, event=None):
        from tkinter import PhotoImage
        about_window = tk.Toplevel(self.root)
        about_window.title("About")
        about_window.resizable(False, False)

        self.set_window_icon(about_window)
        self.apply_title_bar_color(about_window)

        icon_path = Path(__file__).parent / 'app_logo.png'
        if icon_path.is_file():
            app_icon = PhotoImage(file=icon_path)
            icon_label = tk.Label(about_window, image=app_icon)
            icon_label.image = app_icon 
            icon_label.pack(pady=(5, 5))

        about_text = (
            "To-Do App v1.0.0\n\n"
            "Original: © 2024 Jens Lettkemann <jltk@pm.me>\n"
            "Enhanced Fork: © 2026 Aaron\n\n"
            "This software is licensed under GPLv3+.\n"
        )
        github_link = "Source code"
        license_link = "LICENSE"

        text_frame = tk.Frame(about_window, padx=10, pady=10)
        text_frame.pack(fill="both", expand=True)

        text = tk.Label(text_frame, text=about_text, anchor="center")
        text.pack(fill="x", pady=(0, 5))

        github_label = tk.Label(text_frame, text=github_link, fg="blue", cursor="hand2")
        github_label.pack(fill="x", pady=5)
        github_label.bind("<Button-1>", lambda e: self.open_link("https://github.com/jltk/todo-app"))

        license_label = tk.Label(text_frame, text=license_link, fg="blue", cursor="hand2")
        license_label.pack(fill="x", pady=5)
        license_label.bind("<Button-1>", lambda e: self.open_link("https://github.com/jltk/todo-app/blob/main/LICENSE"))

        about_window.update_idletasks()
        min_width = max(text.winfo_width(), github_label.winfo_width(), license_label.winfo_width()) + 20
        min_height = text.winfo_height() + github_label.winfo_height() + license_label.winfo_height() + 40
        about_window.geometry(f"{min_width}x{min_height}")

        self.center_window_over_window(about_window)

    def open_link(self, url):
        import webbrowser
        webbrowser.open(url)

    def show_context_menu(self, event):
        try:
            index = self.listbox.nearest(event.y)
            current_selection = self.listbox.curselection()

            if not current_selection or len(current_selection) == 1:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(index)
            
            selected_indices = self.listbox.curselection()
            
            # 不对折叠标题显示右键菜单
            if (len(selected_indices) == 1 and index < len(self.display_tasks) and 
                self.display_tasks[selected_indices[0]].get('completed_header', False)):
                return
            
            if len(selected_indices) == 1 and index < len(self.display_tasks) and self.display_tasks[selected_indices[0]].get('separator', False):
                if self.display_tasks[selected_indices[0]].get('title', False):
                    self.separator_context_menu.entryconfig("编辑分隔符", state='normal')
                    self.separator_context_menu.entryconfig("添加分隔符标题", state='disabled')
                else:
                    self.separator_context_menu.entryconfig("编辑分隔符", state='disabled')
                    self.separator_context_menu.entryconfig("添加分隔符标题", state='normal')

                self.separator_context_menu.tk_popup(event.x_root, event.y_root)
            else:
                only_separators_selected = all(idx < len(self.display_tasks) and 
                                               self.display_tasks[idx].get('separator', False) 
                                               for idx in selected_indices)
                
                # 检查是否选中了子任务
                has_subtask_selected = any(idx < len(self.display_tasks) and 
                                         self.display_tasks[idx].get('is_subtask', False) 
                                         for idx in selected_indices)
                
                # 只有选中单个主任务时才显示"添加子任务"选项
                single_main_task_selected = (len(selected_indices) == 1 and 
                                           index < len(self.display_tasks) and 
                                           not self.display_tasks[selected_indices[0]].get('separator', False) and
                                           not self.display_tasks[selected_indices[0]].get('completed_header', False) and
                                           not self.display_tasks[selected_indices[0]].get('is_subtask', False))
                
                self.context_menu.entryconfig("标记为完成/未完成", state='disabled' if only_separators_selected else 'normal')
                self.context_menu.entryconfig("添加子任务", state='normal' if single_main_task_selected else 'disabled')
                self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    # Shortcut methods

    def remove_task_shortcut(self, event=None):
        if self.listbox.curselection():
            self.remove_selected_tasks()

    def mark_as_done_shortcut(self, event=None):
        if self.listbox.curselection():
            self.mark_selected_tasks_done()

    def edit_task_shortcut(self, event=None):
        if self.listbox.curselection():
            self.edit_task()
    
    def set_deadline_shortcut(self, event=None):
        if self.listbox.curselection():
            self.set_deadline()
    
    def set_task_background_color_shortcut(self, event=None):
        if self.listbox.curselection():
            self.set_task_background_color()
    
    def set_task_background_color(self):
        """设置主任务的自定义背景色"""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            return
        
        index = selected_indices[0]
        current_task = self.display_tasks[index]
        
        # 不允许对分割线、折叠标题和子任务设置背景色
        if (current_task.get('separator', False) or 
            current_task.get('completed_header', False) or 
            current_task.get('is_subtask', False)):
            return
        
        # 确保任务在真实列表中
        if current_task not in self.tasks:
            return
        
        current_color = current_task.get('custom_bg_color', '')
        
        # 创建颜色选择对话框
        color_window = tk.Toplevel(self.root)
        color_window.title("设置背景颜色")
        color_window.geometry("380x300")
        color_window.transient(self.root)
        color_window.grab_set()
        
        self.set_window_icon(color_window)
        self.apply_title_bar_color(color_window)
        
        frame = tk.Frame(color_window, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        # 颜色输入区域
        input_label = tk.Label(frame, text="输入颜色代码 (如 #2C3E50):", font=self.get_system_font())
        input_label.pack(pady=(0, 5))
        
        color_input_frame = tk.Frame(frame)
        color_input_frame.pack(fill="x", pady=(0, 10))
        
        color_entry = tk.Entry(color_input_frame, font=self.get_system_font(), width=15)
        color_entry.insert(0, current_color)
        color_entry.pack(side="left", padx=(0, 5))
        
        # 颜色预览框
        preview_label = tk.Label(color_input_frame, text="  预览  ", relief="solid", borderwidth=1)
        preview_label.pack(side="left")
        
        def update_preview(*args):
            """更新颜色预览"""
            color = color_entry.get().strip()
            if color:
                try:
                    # 验证颜色代码
                    preview_label.configure(bg=color)
                except:
                    # 无效颜色，显示默认
                    preview_label.configure(bg='white' if not self.is_dark_mode else '#2d2d2d')
            else:
                preview_label.configure(bg='white' if not self.is_dark_mode else '#2d2d2d')
        
        color_entry.bind('<KeyRelease>', update_preview)
        update_preview()  # 初始预览
        
        # 分隔线
        separator = ttk.Separator(frame, orient='horizontal')
        separator.pack(fill="x", pady=(5, 10))
        
        # 预设颜色标签
        preset_label = tk.Label(frame, text="或选择预设颜色:", font=self.get_system_font())
        preset_label.pack(pady=(0, 8))
        
        # 预设的颜色选项（适合暗色主题）
        if self.is_dark_mode:
            preset_colors = [
                ('#2C3E50', '深蓝灰'),
                ('#34495E', '石板灰'),
                ('#16A085', '深青绿'),
                ('#27AE60', '深绿'),
                ('#2980B9', '深蓝'),
                ('#8E44AD', '深紫'),
                ('#C0392B', '深红'),
                ('#D35400', '深橙'),
                ('#7F8C8D', '灰色'),
                ('#9B59B6', '紫色'),
                ('#E67E22', '橙色'),
                ('', '无背景')
            ]
        else:
            # 浅色主题的颜色
            preset_colors = [
                ('#FFE5E5', '浅红'),
                ('#FFF0E5', '浅橙'),
                ('#FFFFE5', '浅黄'),
                ('#E5FFE5', '浅绿'),
                ('#E5F5FF', '浅蓝'),
                ('#F0E5FF', '浅紫'),
                ('#FFE5F5', '浅粉'),
                ('#F0F0F0', '浅灰'),
                ('#E8F8F5', '淡青'),
                ('#FEF5E7', '米色'),
                ('#F4ECF7', '淡紫'),
                ('', '无背景')
            ]
        
        # 创建颜色按钮网格
        color_frame = tk.Frame(frame)
        color_frame.pack(pady=(0, 10))
        
        for i, (color, name) in enumerate(preset_colors):
            row = i // 4
            col = i % 4
            
            def make_color_button(c):
                def set_color():
                    color_entry.delete(0, tk.END)
                    color_entry.insert(0, c)
                    update_preview()
                return set_color
            
            if color:
                # 有颜色的按钮
                btn = tk.Button(color_frame, text=name, bg=color, width=8, height=1,
                              relief='raised', borderwidth=1,
                              font=(self.get_system_font()[0], self.get_system_font()[1] - 2),
                              command=make_color_button(color))
            else:
                # 无背景色按钮
                btn = tk.Button(color_frame, text=name, width=8, height=1,
                              relief='raised', borderwidth=1,
                              font=(self.get_system_font()[0], self.get_system_font()[1] - 2),
                              command=make_color_button(color))
            
            btn.grid(row=row, column=col, padx=2, pady=2)
        
        button_frame = tk.Frame(frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        def on_save():
            color = color_entry.get().strip()
            if color:
                # 验证颜色代码格式
                if not color.startswith('#'):
                    color = '#' + color
                try:
                    # 尝试使用颜色来验证
                    test_label = tk.Label(color_window, bg=color)
                    test_label.destroy()
                    current_task['custom_bg_color'] = color
                except:
                    # 无效颜色，不保存
                    pass
            else:
                current_task.pop('custom_bg_color', None)
            
            self.populate_listbox_without_width_change()
            self.save_tasks()
            color_window.destroy()
        
        def on_cancel():
            color_window.destroy()
        
        color_entry.bind("<Return>", lambda e: on_save())
        
        # 根据平台调整按钮宽度
        if sys.platform == "darwin":  # macOS
            button_width = 8
            button_padx = (0, 8)
        else:  # Windows和其他系统
            button_width = 6
            button_padx = (0, 5)
        
        save_button = ttk.Button(button_frame, text="确定", command=on_save, width=button_width)
        save_button.pack(side="left", padx=button_padx)
        
        cancel_button = ttk.Button(button_frame, text="取消", command=on_cancel, width=button_width)
        cancel_button.pack(side="left")
        
        color_window.protocol("WM_DELETE_WINDOW", on_cancel)
        self.center_window_over_window(color_window)
    
    def auto_complete_parent_tasks(self):
        """检查并自动完成所有子任务都已完成的主任务"""
        for task in self.tasks:
            # 只检查主任务
            if task.get('is_subtask', False) or task.get('separator', False):
                continue
            
            # 如果主任务已经完成，跳过
            if task.get('done', False):
                continue
            
            # 查找该主任务的所有子任务
            parent_task_id = task.get('task_id')
            if not parent_task_id:
                continue
            
            subtasks = [t for t in self.tasks 
                       if t.get('is_subtask', False) and 
                       t.get('parent_task_id') == parent_task_id]
            
            # 如果没有子任务，跳过
            if not subtasks:
                continue
            
            # 检查是否所有子任务都完成了
            all_subtasks_done = all(st.get('done', False) for st in subtasks)
            
            if all_subtasks_done:
                # 自动完成主任务
                task['done'] = True
                task['completed_time'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                # 如果有紧急状态，保存它
                if task.get('urgent', False):
                    task['was_urgent'] = True
                    task['urgent'] = False
    
    def auto_uncomplete_parent_task(self, subtask):
        """当子任务被标记为未完成时，自动将其主任务也标记为未完成"""
        if not subtask.get('is_subtask', False):
            return
        
        parent_task_id = subtask.get('parent_task_id')
        if not parent_task_id:
            return
        
        # 查找父任务
        parent_task = None
        for task in self.tasks:
            if task.get('task_id') == parent_task_id and not task.get('is_subtask', False):
                parent_task = task
                break
        
        if not parent_task:
            return
        
        # 如果父任务已完成，将其标记为未完成
        if parent_task.get('done', False):
            parent_task['done'] = False
            parent_task.pop('completed_time', None)
            # 恢复之前的紧急状态
            if parent_task.get('was_urgent', False):
                parent_task['urgent'] = True
                parent_task.pop('was_urgent', None)
    
    def set_deadline(self):
        """设置任务的截止日期"""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            return
        
        index = selected_indices[0]
        current_task = self.display_tasks[index]
        
        # 不允许对分割线和折叠标题设置deadline
        if current_task.get('separator', False) or current_task.get('completed_header', False):
            return
        
        # 确保任务在真实列表中
        if current_task not in self.tasks:
            return
        
        current_deadline = current_task.get('deadline', '')
        
        if CALENDAR_AVAILABLE:
            # 使用图形化日历选择器
            deadline_window = tk.Toplevel(self.root)
            deadline_window.title("设置截止日期")
            deadline_window.resizable(False, False)
            deadline_window.transient(self.root)
            deadline_window.grab_set()
            
            self.set_window_icon(deadline_window)
            self.apply_title_bar_color(deadline_window)
            
            frame = tk.Frame(deadline_window, padx=15, pady=15)
            frame.pack(fill="both", expand=True)
            
            label = tk.Label(frame, text="选择截止日期:", font=self.get_system_font())
            label.pack(pady=(0, 10))
            
            # 设置初始日期
            if current_deadline:
                try:
                    initial_date = datetime.strptime(current_deadline, '%Y-%m-%d')
                except:
                    initial_date = datetime.now()
            else:
                initial_date = datetime.now()
            
            # 创建日历控件
            font_family, font_size = self.get_system_font()
            cal = Calendar(frame, 
                          selectmode='day',
                          year=initial_date.year,
                          month=initial_date.month,
                          day=initial_date.day,
                          date_pattern='yyyy-mm-dd',
                          font=(font_family, font_size - 1),
                          headersforeground='white',
                          normalforeground='black',
                          selectforeground='white',
                          weekendforeground='red',
                          othermonthforeground='gray',
                          othermonthweforeground='gray')
            cal.pack(pady=(0, 10))
            
            # 显示当前截止日期
            if current_deadline:
                font_family, font_size = self.get_system_font()
                current_label = tk.Label(frame, text=f"当前截止日期: {current_deadline}", 
                                        font=(font_family, font_size - 1), fg='gray')
                current_label.pack(pady=(0, 5))
            
            button_frame = tk.Frame(frame)
            button_frame.pack(fill="x", pady=(5, 0))
            
            def on_save():
                selected_date = cal.get_date()
                current_task['deadline'] = selected_date
                # 设置截止日期时不改变窗口宽度
                self.populate_listbox_without_width_change()
                self.save_tasks()
                deadline_window.destroy()
            
            def on_clear():
                # 清除deadline
                current_task.pop('deadline', None)
                # 清除截止日期时不改变窗口宽度
                self.populate_listbox_without_width_change()
                self.save_tasks()
                deadline_window.destroy()
            
            def on_cancel():
                deadline_window.destroy()
            
            # 根据平台调整按钮宽度，在macOS下使用更宽的按钮以避免文字裁切
            if sys.platform == "darwin":  # macOS
                button_width = 8  # macOS下使用更宽的按钮
                button_padx = (0, 8)  # 增加按钮间距
            else:  # Windows和其他系统
                button_width = 6  # 默认宽度
                button_padx = (0, 5)
            
            save_button = ttk.Button(button_frame, text="确定", command=on_save, width=button_width)
            save_button.pack(side="left", padx=button_padx)
            
            clear_button = ttk.Button(button_frame, text="清除", command=on_clear, width=button_width)
            clear_button.pack(side="left", padx=button_padx)
            
            cancel_button = ttk.Button(button_frame, text="取消", command=on_cancel, width=button_width)
            cancel_button.pack(side="left")
            
            deadline_window.protocol("WM_DELETE_WINDOW", on_cancel)
            deadline_window.update_idletasks()
            self.center_window_over_window(deadline_window)
            
        else:
            # 降级方案：使用文本输入
            deadline_window = tk.Toplevel(self.root)
            deadline_window.title("设置截止日期")
            deadline_window.geometry("300x150")
            deadline_window.transient(self.root)
            deadline_window.grab_set()
            
            self.set_window_icon(deadline_window)
            self.apply_title_bar_color(deadline_window)
            
            frame = tk.Frame(deadline_window, padx=20, pady=20)
            frame.pack(fill="both", expand=True)
            
            label = tk.Label(frame, text="截止日期 (YYYY-MM-DD):", font=self.get_system_font())
            label.pack(pady=(0, 10))
            
            date_entry = tk.Entry(frame, font=self.get_system_font())
            date_entry.insert(0, current_deadline)
            date_entry.pack(fill="x", pady=(0, 10))
            date_entry.focus_set()
            
            font_family, font_size = self.get_system_font()
            hint_label = tk.Label(frame, text="留空以清除截止日期", font=(font_family, font_size - 2), fg='gray')
            hint_label.pack(pady=(0, 10))
            
            def on_save(event=None):
                deadline_str = date_entry.get().strip()
                if deadline_str:
                    try:
                        # 验证日期格式
                        datetime.strptime(deadline_str, '%Y-%m-%d')
                        current_task['deadline'] = deadline_str
                    except ValueError:
                        # 日期格式错误，不保存
                        pass
                else:
                    # 清除deadline
                    current_task.pop('deadline', None)
                
                # 设置截止日期时不改变窗口宽度
                self.populate_listbox_without_width_change()
                self.save_tasks()
                deadline_window.destroy()
            
            def on_cancel():
                deadline_window.destroy()
            
            date_entry.bind("<Return>", on_save)
            
            button_frame = tk.Frame(frame)
            button_frame.pack(fill="x")
            
            # 根据平台调整按钮宽度，在macOS下使用更宽的按钮以避免文字裁切
            if sys.platform == "darwin":  # macOS
                button_width = 8  # macOS下使用更宽的按钮
                button_padx = (0, 8)  # 增加按钮间距
            else:  # Windows和其他系统
                button_width = 6  # 默认宽度
                button_padx = (0, 5)
            
            save_button = ttk.Button(button_frame, text="保存", command=on_save, width=button_width)
            save_button.pack(side="left", padx=button_padx)
            
            cancel_button = ttk.Button(button_frame, text="取消", command=on_cancel, width=button_width)
            cancel_button.pack(side="left")
            
            deadline_window.protocol("WM_DELETE_WINDOW", on_cancel)
            self.center_window_over_window(deadline_window)

    # Subtask methods
    
    def add_subtask_shortcut(self, event=None):
        """添加子任务的快捷方法"""
        if self.listbox.curselection():
            self.add_subtask()
    
    def add_subtask(self):
        """为选中的任务添加子任务"""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            return
        
        index = selected_indices[0]
        current_task = self.display_tasks[index]
        
        # 不允许对分割线、折叠标题和子任务添加子任务
        if (current_task.get('separator', False) or 
            current_task.get('completed_header', False) or 
            current_task.get('is_subtask', False)):
            return
        
        # 确保任务在真实列表中
        if current_task not in self.tasks:
            return
        
        # 创建添加子任务的对话框
        subtask_window = tk.Toplevel(self.root)
        subtask_window.title("添加子任务")
        subtask_window.geometry("300x120")
        subtask_window.transient(self.root)
        subtask_window.grab_set()
        
        self.set_window_icon(subtask_window)
        self.apply_title_bar_color(subtask_window)
        
        frame = tk.Frame(subtask_window, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        label = tk.Label(frame, text="子任务名称:", font=self.get_system_font())
        label.pack(pady=(0, 10))
        
        subtask_entry = tk.Text(frame, wrap='word', height=2, width=35, font=self.get_system_font())
        subtask_entry.pack(fill="both", expand=True, pady=(0, 10))
        subtask_entry.focus_set()
        
        def on_save(event=None):
            subtask_name = subtask_entry.get("1.0", "end-1c").strip()
            if subtask_name:
                # 生成唯一的任务ID
                import uuid
                task_id = str(uuid.uuid4())
                
                # 确保父任务有task_id
                if 'task_id' not in current_task or not current_task['task_id']:
                    current_task['task_id'] = str(uuid.uuid4())
                
                # 创建子任务
                subtask = {
                    'name': subtask_name,
                    'is_subtask': True,
                    'parent_task_id': current_task['task_id'],  # 使用父任务的task_id
                    'task_id': task_id
                }
                
                # 找到父任务在真实列表中的位置
                parent_index = self.tasks.index(current_task)
                
                # 找到该主任务的最后一个子任务的位置
                insert_index = parent_index + 1
                parent_task_id = current_task['task_id']
                
                # 从父任务后面开始查找，找到最后一个属于该父任务的子任务
                for i in range(parent_index + 1, len(self.tasks)):
                    task = self.tasks[i]
                    # 如果遇到其他主任务或分割线，停止查找
                    if not task.get('is_subtask', False) or task.get('separator', False):
                        break
                    # 如果是当前父任务的子任务，更新插入位置
                    if task.get('parent_task_id') == parent_task_id:
                        insert_index = i + 1
                
                # 在找到的位置插入新子任务
                self.tasks.insert(insert_index, subtask)
                
                # 添加子任务时不改变窗口宽度
                self.populate_listbox_without_width_change()
                self.save_tasks()
                self.update_buttons_state()
                self.update_title()
            
            subtask_window.destroy()
        
        def on_cancel():
            subtask_window.destroy()
        
        subtask_entry.bind("<Return>", on_save)
        
        button_frame = tk.Frame(frame)
        button_frame.pack(fill="x")
        
        # 根据平台调整按钮宽度
        if sys.platform == "darwin":  # macOS
            button_width = 8
            button_padx = (0, 8)
        else:  # Windows和其他系统
            button_width = 6
            button_padx = (0, 5)
        
        save_button = ttk.Button(button_frame, text="添加", command=on_save, width=button_width)
        save_button.pack(side="left", padx=button_padx)
        
        cancel_button = ttk.Button(button_frame, text="取消", command=on_cancel, width=button_width)
        cancel_button.pack(side="left")
        
        subtask_window.protocol("WM_DELETE_WINDOW", on_cancel)
        self.center_window_over_window(subtask_window)

def main():
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
