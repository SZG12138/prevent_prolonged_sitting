import tkinter as tk
from tkinter import simpledialog
import threading
import os
import sys

# ---------- 配置 ----------
WORK_MINUTES = 45          # 默认/重置后的工作分钟数
SNOOZE_MINUTES = 5         # “再坐一会”的延迟分钟数

# ---------- 全局变量 ----------
current_duration = WORK_MINUTES   # 当前实际使用的计时周期（分钟）
current_timer_id = None           # 存储当前的 after 任务 ID，用于取消

# ---------- 获取资源路径 ----------
def resource_path(relative_path):
    """ 获取绝对路径，兼容开发环境和 PyInstaller 打包 """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ---------- 核心计时逻辑 ----------
def start_timer(root, minutes):
    """取消当前计时，并以指定分钟数启动新倒计时"""
    global current_timer_id, current_duration

    current_duration = minutes

    # 取消现有的定时任务
    if current_timer_id is not None:
        root.after_cancel(current_timer_id)
        current_timer_id = None

    # 设置新的定时器
    current_timer_id = root.after(
        current_duration * 60 * 1000,
        remind_window, root
    )

def reset_to_default(root):
    """重置计时器为默认的45分钟"""
    start_timer(root, WORK_MINUTES)

# ---------- 提醒窗口 ----------
def remind_window(root):
    """ 在主线程中弹出的全屏遮罩提醒 """
    top = tk.Toplevel(root)
    top.attributes('-fullscreen', True)
    top.attributes('-alpha', 0.75)
    top.attributes('-topmost', True)
    top.overrideredirect(True)
    top.configure(bg='black')

    msg = tk.Label(top, text=f"已经坐了 {current_duration} 分钟\n起来活动一下吧！",
                   font=('微软雅黑', 36, 'bold'), fg='white', bg='black')
    msg.pack(expand=True)

    btn_frame = tk.Frame(top, bg='black')
    btn_frame.pack(pady=50)

    def rest_done():
        top.destroy()
        # 起身后，重置为默认45分钟
        reset_to_default(root)

    def snooze():
        top.destroy()
        # 再坐一会儿：只延迟提醒
        global current_timer_id
        if current_timer_id is not None:
            root.after_cancel(current_timer_id)
        current_timer_id = root.after(
            SNOOZE_MINUTES * 60 * 1000,
            remind_window, root
        )

    tk.Button(btn_frame, text='我已起身', font=('微软雅黑', 20),
              command=rest_done, width=12, height=2).pack(side='left', padx=20)
    tk.Button(btn_frame, text=f'再坐{SNOOZE_MINUTES}分钟', font=('微软雅黑', 20),
              command=snooze, width=12, height=2).pack(side='left', padx=20)

    top.bind('<Escape>', lambda e: top.destroy())
    top.focus_force()

# ---------- 自定义对话框 ----------
def show_custom_dialog(root):
    """弹出输入框，让用户设定新的计时周期（分钟）"""
    try:
        minutes = simpledialog.askinteger(
            "自定义提醒",
            "请输入多少分钟后提醒（分钟）：",
            parent=root,
            minvalue=1,
            maxvalue=240
        )
        if minutes:
            start_timer(root, minutes)
    except Exception:
        pass

# ---------- 系统托盘 ----------
def create_tray(root):
    """ 创建系统托盘图标，提供精简菜单 """
    try:
        import pystray
        from PIL import Image
    except ImportError:
        print("请先安装依赖: pip install pystray pillow")
        root.destroy()
        return

    icon_path = resource_path("icon.ico")
    if not os.path.exists(icon_path):
        image = Image.new('RGB', (64, 64), color='green')
    else:
        image = Image.open(icon_path)

    # 托盘菜单：只保留三个核心功能
    menu = pystray.Menu(
        pystray.MenuItem(
            '自定义倒计时...',
            lambda: root.after_idle(show_custom_dialog, root)
        ),
        pystray.MenuItem(
            '重置计时（45分钟）',
            lambda: root.after_idle(reset_to_default, root)
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('退出', lambda: root.destroy()),
    )

    tray_icon = pystray.Icon("防久坐", image, "防久坐提醒", menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()

# ---------- 主程序 ----------
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()

    # 启动时使用默认45分钟
    start_timer(root, WORK_MINUTES)

    create_tray(root)
    root.mainloop()