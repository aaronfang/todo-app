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
        self.tasks = self.load_tasks()  # 真实的任务数据（不包含 completed_header）
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

    # Setup methods

    def setup_ui(self):
        self.root.title("To-Do")
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
        self.listbox = tk.Listbox(self.main_frame, selectmode=tk.EXTENDED, bd=0, highlightthickness=0,
                                  activestyle='none', font=('Microsoft YaHei UI', 10), height=10)
        self.listbox.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=(8, 5))
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def create_input_frame(self):
        self.input_frame = tk.Frame(self.main_frame)
        self.input_frame.grid(row=1, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 5))
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry = tk.Text(self.input_frame, height=1, wrap='none', bd=0, font=('Microsoft YaHei UI', 10), insertbackground='black')
        self.entry.grid(row=0, column=0, sticky="ew")

        self.setup_entry_bindings()

    def setup_entry_bindings(self):
        self.entry.bind('<FocusIn>', self.on_entry_focus_in)
        self.entry.bind('<FocusOut>', self.on_entry_focus_out)
        self.entry.bind('<Button-1>', self.on_entry_click)

    def create_buttons(self):
        button_style = {'width': 3, 'padding': (0, 0)}
        buttons = [
            ("➕", self.add_task),
            ("➖", self.remove_selected_tasks),
            ("✔", self.mark_selected_tasks_done)
        ]
        self.buttons = {}
        for col, (text, command) in enumerate(buttons, start=1):
            button = ttk.Button(self.input_frame, text=text, command=command, style='TButton', **button_style)
            button.grid(row=0, column=col, padx=(5, 0))
            self.buttons[text] = button

    def setup_bindings(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind_all('<Control-r>', self.toggle_dark_mode)
        self.root.bind_all('<Control-h>', self.show_about_dialog)

        self.listbox.bind('<Control-u>', self.toggle_urgent_task)
        self.listbox.bind('<Control-d>', self.mark_selected_tasks_done)
        self.listbox.bind('<Control-j>', self.mark_selected_tasks_cancelled)

        self.listbox.bind('<Delete>', self.remove_selected_tasks)
        self.listbox.bind('<Control-e>', self.edit_task_shortcut)
        self.listbox.bind('<Control-a>', self.select_all_or_text)

        self.listbox.bind('<<ListboxSelect>>', self.update_buttons_state)
        self.listbox.bind('<Double-1>', self.on_double_click)
        # <Button-1> 由 start_drag 处理
        self.listbox.bind('<Button-3>', self.show_context_menu)
        self.listbox.bind('<Control-Button-1>', self.on_ctrl_click)
        self.listbox.bind('<Shift-Button-1>', self.on_shift_click)

        self.entry.bind('<Return>', self.add_task)
        self.entry.bind('<KeyRelease>', self.update_buttons_state)

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Edit Task", command=self.edit_task_shortcut)
        self.context_menu.add_command(label="Set Deadline", command=self.set_deadline_shortcut)
        self.context_menu.add_command(label="Un/Mark as Done", command=self.mark_selected_tasks_done)
        self.context_menu.add_command(label="Un/Mark as Urgent", command=self.toggle_urgent_task)
        self.context_menu.add_command(label="Un/Mark as Cancelled", command=self.mark_selected_tasks_cancelled)
        self.context_menu.add_command(label="Remove Task/s", command=self.remove_selected_tasks)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Add Separator", command=self.add_separator_below)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Toggle Dark Mode", command=self.toggle_dark_mode)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="About", command=self.show_about_dialog)

        self.separator_context_menu = tk.Menu(self.root, tearoff=0)
        self.separator_context_menu.add_command(label="Edit Separator", command=self.edit_task)
        self.separator_context_menu.add_command(label="Add Separator Title", command=self.add_separator_title)
        self.separator_context_menu.add_command(label="Remove Separator", command=self.remove_selected_tasks)

        self.separator_context_menu.add_separator()
        self.separator_context_menu.add_command(label="Add Separator", command=self.add_separator_below)
        self.separator_context_menu.add_separator()
        self.separator_context_menu.add_command(label="Toggle Dark Mode", command=self.toggle_dark_mode)
        self.separator_context_menu.add_separator()
        self.separator_context_menu.add_command(label="About", command=self.show_about_dialog)




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
            self.populate_listbox()
            self.save_tasks()
            self.entry.delete("1.0", tk.END)
            self.update_buttons_state()
            self.update_title()
            self.entry.focus_set()

    def remove_selected_tasks(self, event=None):
        selected_indices = list(self.listbox.curselection())
        for index in reversed(selected_indices):
            # 跳过折叠标题，不允许删除
            if self.display_tasks[index].get('completed_header', False):
                continue
            # 从 display_tasks 中获取任务信息
            task_to_remove = self.display_tasks[index]
            # 从真实的 tasks 列表中删除
            if task_to_remove in self.tasks:
                self.tasks.remove(task_to_remove)
        self.populate_listbox()
        self.save_tasks()
        self.update_buttons_state()
        self.update_title()

    def mark_selected_tasks_done(self, event=None):
        selected_indices = self.listbox.curselection()
        for index in selected_indices:
            display_task = self.display_tasks[index]
            # 跳过分割线和折叠标题
            if display_task.get('separator', False) or display_task.get('completed_header', False):
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
        self.populate_listbox()
        self.save_tasks()
        self.update_buttons_state()
        self.update_title()

    def mark_selected_tasks_cancelled(self, event=None):
        selected_indices = self.listbox.curselection()
        for index in selected_indices:
            display_task = self.display_tasks[index]
            # 跳过分割线和折叠标题
            if display_task.get('separator', False) or display_task.get('completed_header', False):
                continue
            # 修改真实任务
            if display_task in self.tasks:
                task = display_task
                task['cancelled'] = not task.get('cancelled', False)
                if task['cancelled']:
                    task['urgent'] = False
        self.populate_listbox()
        self.save_tasks()
        self.update_buttons_state()
        self.update_title()


    def toggle_urgent_task(self, event=None):
        selected_indices = self.listbox.curselection()
        for index in selected_indices:
            display_task = self.display_tasks[index]
            # 跳过分割线和折叠标题
            if display_task.get('separator', False) or display_task.get('completed_header', False):
                continue
            # 修改真实任务
            if display_task in self.tasks:
                task = display_task
                task['urgent'] = not task.get('urgent', False)
        self.populate_listbox()
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

                self.populate_listbox()
                self.save_tasks()
                self.update_buttons_state()
                edit_window.destroy()

            def on_cancel():
                edit_window.destroy()

            text_entry.bind("<Return>", on_save)

            button_frame = tk.Frame(frame)
            button_frame.pack(fill="x", pady=(10, 0))

            save_button = ttk.Button(button_frame, text="Save", command=on_save)
            save_button.pack(side="left", padx=0)

            cancel_button = ttk.Button(button_frame, text="Cancel", command=on_cancel)
            cancel_button.pack(side="left", padx=5)

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
                    self.populate_listbox()
                    self.save_tasks()
                    self.update_buttons_state()
                edit_window.destroy()

            def on_cancel():
                edit_window.destroy()

            text_entry.bind("<Return>", on_save)

            button_frame = tk.Frame(frame)
            button_frame.pack(fill="x", pady=(10, 0))

            save_button = ttk.Button(button_frame, text="Save", command=on_save)
            save_button.pack(side="left", padx=0)

            cancel_button = ttk.Button(button_frame, text="Cancel", command=on_cancel)
            cancel_button.pack(side="left", padx=5)

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
                    self.populate_listbox()
                    self.save_tasks()
                    self.update_buttons_state()
                edit_window.destroy()

            def on_cancel():
                edit_window.destroy()

            text_entry.bind("<Return>", on_save)

            button_frame = tk.Frame(frame)
            button_frame.pack(fill="x", pady=(10, 0))

            save_button = ttk.Button(button_frame, text="Save", command=on_save)
            save_button.pack(side="left", padx=0)

            cancel_button = ttk.Button(button_frame, text="Cancel", command=on_cancel)
            cancel_button.pack(side="left", padx=5)

            edit_window.protocol("WM_DELETE_WINDOW", on_cancel)
            self.center_window_over_window(edit_window)

    def add_separator_below(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            return

        index = selected_indices[0]
        separator = {'name': '─' * 40, 'separator': True, 'title': False}
        self.tasks.insert(index + 1, separator)

        self.populate_listbox()
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
                deadline_indicator = self.get_deadline_indicator(task)
                if task.get('cancelled', False):
                    display_text = f"✖ {task['name']}{deadline_indicator}" 
                    self.listbox.insert(tk.END, display_text)
                    self.listbox.itemconfig(index, {'bg': '', 'fg': '#a9a9a9'})
                elif task.get('done', False):
                    completed_time = task.get('completed_time', '')
                    time_str = f" [{completed_time}]" if completed_time else ""
                    # 使用删除线样式
                    display_text = f"✔ {self.add_strikethrough(task['name'])}{time_str}"
                    self.listbox.insert(tk.END, display_text)
                    self.listbox.itemconfig(index, {'bg': colors['done_bg'], 'fg': colors['done_fg']})
                else:
                    display_text = f"⬜ {task['name']}{deadline_indicator}"
                    self.listbox.insert(tk.END, display_text)
        
        # display_tasks 用于显示和事件处理（包含 completed_header）
        # tasks 保持为真实任务数据（不包含 completed_header，用于保存）
        self.display_tasks = organized_tasks
        self.update_listbox_task_backgrounds()
        self.adjust_window_size()
        self.update_title()
    
    def organize_tasks_by_sections(self):
        """将任务按分割线分组，完成的任务移到每个分组的底部，添加折叠功能"""
        result = []
        current_section_active = []
        current_section_done = []
        section_id = 0
        
        for task in self.tasks:
            # 跳过已经是折叠标题的任务
            if task.get('completed_header', False):
                continue
                
            if task.get('separator', False):
                # 遇到分割线，先输出当前section的活跃任务
                result.extend(current_section_active)
                
                # 如果有已完成任务，添加折叠标题
                if current_section_done:
                    # 按完成时间排序已完成任务
                    current_section_done.sort(key=lambda t: t.get('completed_time', ''))
                    
                    # 添加"已完成"折叠标题
                    completed_header = {
                        'completed_header': True,
                        'section_id': section_id,
                        'done_count': len(current_section_done)
                    }
                    result.append(completed_header)
                    
                    # 如果该分组未折叠，则显示已完成任务
                    if section_id not in self.collapsed_sections:
                        result.extend(current_section_done)
                
                result.append(task)
                current_section_active = []
                current_section_done = []
                section_id += 1
            else:
                if task.get('done', False):
                    current_section_done.append(task)
                else:
                    current_section_active.append(task)
        
        # 处理最后一个section
        result.extend(current_section_active)
        if current_section_done:
            current_section_done.sort(key=lambda t: t.get('completed_time', ''))
            completed_header = {
                'completed_header': True,
                'section_id': section_id,
                'done_count': len(current_section_done)
            }
            result.append(completed_header)
            if section_id not in self.collapsed_sections:
                result.extend(current_section_done)
        
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
        style.configure('TButton', background=bg, foreground=fg, padding=5)
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
                self.listbox.itemconfig(index, {'bg': colors['done_bg'], 'fg': colors['done_fg']})
            elif task.get('urgent', False):
                self.listbox.itemconfig(index, {'bg': colors['urgent_bg'], 'fg': 'white'})
            else:
                self.listbox.itemconfig(index, {'bg': colors['listbox_bg'], 'fg': colors['fg']})

    def adjust_window_size(self):
        num_tasks = len(self.display_tasks)
        new_height = max(100, min(800, 100 + (num_tasks * 18)))
        
        # 计算最长任务的宽度
        max_width = 300  # 最小宽度
        max_allowed_width = 1000  # 最大宽度
        
        # 创建临时字体对象来测量文本宽度
        import tkinter.font as tkfont
        font = tkfont.Font(family='Microsoft YaHei UI', size=10)
        
        for task in self.display_tasks:
            # 获取显示文本
            if task.get('separator', False):
                display_text = task['name']
            elif task.get('completed_header', False):
                section_id = task.get('section_id', 0)
                done_count = task.get('done_count', 0)
                is_collapsed = section_id in self.collapsed_sections
                arrow = '▶' if is_collapsed else '▼'
                display_text = f"  {arrow} 已完成 ({done_count})"
            else:
                deadline_indicator = self.get_deadline_indicator(task)
                if task.get('cancelled', False):
                    display_text = f"✖ {task['name']}{deadline_indicator}"
                elif task.get('done', False):
                    completed_time = task.get('completed_time', '')
                    time_str = f" [{completed_time}]" if completed_time else ""
                    display_text = f"✔ {self.add_strikethrough(task['name'])}{time_str}"
                else:
                    display_text = f"⬜ {task['name']}{deadline_indicator}"
            
            # 测量文本宽度（加上边距和滚动条等）
            text_width = font.measure(display_text) + 80  # 加上padding和边距
            max_width = max(max_width, text_width)
        
        # 限制在最大宽度内
        final_width = min(max_width, max_allowed_width)
        
        self.root.geometry(f"{final_width}x{new_height}")

    def update_title(self):
        total_tasks = sum(1 for task in self.tasks if not task.get('separator', False) and not task.get('cancelled', False))
        done_tasks = sum(task.get('done', False) for task in self.tasks if not task.get('separator', False) and not task.get('cancelled', False))
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
        if index < len(self.display_tasks) and self.display_tasks[index].get('separator', False):
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
        
        # 重新渲染列表
        self.populate_listbox()
        self.save_config()

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
        if self.drag_start_index < len(self.display_tasks) and self.display_tasks[self.drag_start_index].get('completed_header', False):
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
                
                self.populate_listbox()
                self.save_tasks()
                self.update_buttons_state()
        self.drag_start_index = None

    def reorder_tasks(self, start_index, end_index):
        """Move the task from start_index to end_index in the tasks list."""
        task = self.tasks.pop(start_index)
        self.tasks.insert(end_index, task)
        self.populate_listbox()
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
            for task in tasks:
                if task.get('separator', False):
                    task['title'] = task.get('title', False)
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
                            'was_urgent': task.get('was_urgent', False)}
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
            'select_bg': '#555555' if self.is_dark_mode else '#d3d3d3',
            'done_bg': '#d3d3d3' if self.is_dark_mode else '#d3d3d3',
            'done_fg': '#808080' if self.is_dark_mode else '#808080',
            'urgent_bg': '#de3f4d' if self.is_dark_mode else '#de3f4d',
            'separator_fg': '#cccccc',
            'completed_header_fg': '#888888' if self.is_dark_mode else '#666666'
        }

    @staticmethod
    def get_system_font():
        return ('Microsoft YaHei UI', 10)

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
            "To-Do App 0.2.2\n\n"
            "© 2024 Jens Lettkemann <jltk@pm.me>\n\n"
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
            if len(selected_indices) == 1 and index < len(self.display_tasks) and self.display_tasks[selected_indices[0]].get('completed_header', False):
                return
            
            if len(selected_indices) == 1 and index < len(self.display_tasks) and self.display_tasks[selected_indices[0]].get('separator', False):
                if self.display_tasks[selected_indices[0]].get('title', False):
                    self.separator_context_menu.entryconfig("Edit Separator", state='normal')
                    self.separator_context_menu.entryconfig("Add Separator Title", state='disabled')
                else:
                    self.separator_context_menu.entryconfig("Edit Separator", state='disabled')
                    self.separator_context_menu.entryconfig("Add Separator Title", state='normal')

                self.separator_context_menu.tk_popup(event.x_root, event.y_root)
            else:
                only_separators_selected = all(idx < len(self.display_tasks) and self.display_tasks[idx].get('separator', False) for idx in selected_indices)
                self.context_menu.entryconfig("Un/Mark as Done", state='disabled' if only_separators_selected else 'normal')
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
            
            label = tk.Label(frame, text="选择截止日期:", font=('Microsoft YaHei UI', 10))
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
            cal = Calendar(frame, 
                          selectmode='day',
                          year=initial_date.year,
                          month=initial_date.month,
                          day=initial_date.day,
                          date_pattern='yyyy-mm-dd',
                          font=('Microsoft YaHei UI', 9),
                          headersforeground='white',
                          normalforeground='black',
                          selectforeground='white',
                          weekendforeground='red',
                          othermonthforeground='gray',
                          othermonthweforeground='gray')
            cal.pack(pady=(0, 10))
            
            # 显示当前截止日期
            if current_deadline:
                current_label = tk.Label(frame, text=f"当前截止日期: {current_deadline}", 
                                        font=('Microsoft YaHei UI', 9), fg='gray')
                current_label.pack(pady=(0, 5))
            
            button_frame = tk.Frame(frame)
            button_frame.pack(fill="x", pady=(5, 0))
            
            def on_save():
                selected_date = cal.get_date()
                current_task['deadline'] = selected_date
                self.populate_listbox()
                self.save_tasks()
                deadline_window.destroy()
            
            def on_clear():
                # 清除deadline
                current_task.pop('deadline', None)
                self.populate_listbox()
                self.save_tasks()
                deadline_window.destroy()
            
            def on_cancel():
                deadline_window.destroy()
            
            save_button = ttk.Button(button_frame, text="确定", command=on_save)
            save_button.pack(side="left", padx=(0, 5))
            
            clear_button = ttk.Button(button_frame, text="清除", command=on_clear)
            clear_button.pack(side="left", padx=(0, 5))
            
            cancel_button = ttk.Button(button_frame, text="取消", command=on_cancel)
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
            
            label = tk.Label(frame, text="截止日期 (YYYY-MM-DD):", font=('Microsoft YaHei UI', 10))
            label.pack(pady=(0, 10))
            
            date_entry = tk.Entry(frame, font=('Microsoft YaHei UI', 10))
            date_entry.insert(0, current_deadline)
            date_entry.pack(fill="x", pady=(0, 10))
            date_entry.focus_set()
            
            hint_label = tk.Label(frame, text="留空以清除截止日期", font=('Microsoft YaHei UI', 8), fg='gray')
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
                
                self.populate_listbox()
                self.save_tasks()
                deadline_window.destroy()
            
            def on_cancel():
                deadline_window.destroy()
            
            date_entry.bind("<Return>", on_save)
            
            button_frame = tk.Frame(frame)
            button_frame.pack(fill="x")
            
            save_button = ttk.Button(button_frame, text="保存", command=on_save)
            save_button.pack(side="left", padx=(0, 5))
            
            cancel_button = ttk.Button(button_frame, text="取消", command=on_cancel)
            cancel_button.pack(side="left")
            
            deadline_window.protocol("WM_DELETE_WINDOW", on_cancel)
            self.center_window_over_window(deadline_window)

def main():
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
