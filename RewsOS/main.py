import tkinter as tk
from datetime import datetime
from PIL import Image, ImageDraw, ImageTk, ImageFilter
import math


class RewsOS:
    BOOT_TIME_MS = 5500

    # ---- панель задач ----
    TASKBAR_W = 620
    TASKBAR_H = 56
    TASKBAR_RADIUS = 20

    BTN_SIZE = 40
    BTN_RADIUS = 10

    # ---- меню ----
    MENU_W = 420
    MENU_H = 320
    MENU_RADIUS = 18
    MENU_BG = "#f3f3f3"

    # ---- анимация меню ----
    MENU_ANIM_MS   = 220
    MENU_ANIM_FPS  = 60
    MENU_ANIM_EASE = 3.0

    # ---- кнопки в меню ----
    ITEM_W = 380
    ITEM_H = 46
    ITEM_RADIUS = 12
    ITEM_BG       = "#3a5fa8"
    ITEM_BG_HOVER = "#4a73c4"
    ITEM_FG       = "#ffffff"

    SS = 4

    # ---- цвета UI ----
    BG_DESKTOP      = "#1e1e2e"
    TASKBAR_BG      = "#ffffff"
    START_BTN_BG    = "#0078d4"
    START_BTN_HOVER = "#1a86e0"
    WIN_ICON_COLOR  = "#ffffff"

    # ---- обои ----
    WALLPAPER_SCALE  = 0.5
    WALLPAPER_PETALS = 7

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RewsOS v0.1")
        self.root.configure(bg="black")
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.shutdown())

        self.clock_job = None
        self.start_menu = None
        self.menu_anim_job = None

        self.wallpaper_pil = None
        self.wallpaper_ref = None

        self.taskbar_image_ref = None
        self.start_btn_img_normal = None
        self.start_btn_img_hover  = None

        self.item_images = {}
        self.menu_bg_img = None
        self.menu_items_widgets = []

        # терминал
        self.term_win = None
        self.term_output = None
        self.term_entry = None

        self.show_boot_screen()

    # =========================================================
    #   ОБОИ
    # =========================================================
    def generate_wallpaper_pil(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        W = int(sw * self.WALLPAPER_SCALE)
        H = int(sh * self.WALLPAPER_SCALE)

        img = Image.new("RGB", (W, H), (10, 15, 40))
        pixels = img.load()
        cx, cy = W / 2, H / 2
        max_r = math.hypot(W, H) / 2
        petals = self.WALLPAPER_PETALS

        for y in range(H):
            dy = y - cy
            for x in range(W):
                dx = x - cx
                r = math.hypot(dx, dy) or 1
                ang = math.atan2(dy, dx)
                bloom = (math.cos(petals * ang) + 1) / 2
                falloff = max(0.0, 1.0 - r / max_r)
                t = bloom * falloff
                R = int(10 + 40 * t)
                G = int(30 + 130 * t)
                B = int(70 + 185 * t)
                glow = max(0.0, 1.0 - r / (max_r * 0.35))
                R = min(255, R + int(30 * glow))
                B = min(255, B + int(30 * glow))
                pixels[x, y] = (R, G, B)

        img = img.filter(ImageFilter.GaussianBlur(radius=3))
        return img.resize((sw, sh), Image.LANCZOS)

    # =========================================================
    #   Скруглённая фигура на куске обоев
    # =========================================================
    def rounded_on_wallpaper(self, x, y, w, h, radius, fill):
        wall = self.wallpaper_pil.convert("RGBA")
        region = wall.crop((x, y, x + w, y + h)).copy()

        W, H = w * self.SS, h * self.SS
        R = max(1, int(radius * self.SS))
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, W - 1, H - 1), radius=R, fill=255,
        )
        mask = mask.resize((w, h), Image.LANCZOS)

        layer = Image.new("RGBA", (w, h), fill)
        layer.putalpha(mask)
        region.alpha_composite(layer)
        return ImageTk.PhotoImage(region)

    def make_start_button(self, fill):
        W = H = self.BTN_SIZE * self.SS
        R = self.BTN_RADIUS * self.SS
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((0, 0, W - 1, H - 1), radius=R, fill=fill)

        gap  = 3 * self.SS
        side = 10 * self.SS
        total = side * 2 + gap
        x0 = (W - total) // 2
        y0 = (H - total) // 2
        rad = 2 * self.SS
        for (x, y) in [
            (x0, y0),
            (x0 + side + gap, y0),
            (x0, y0 + side + gap),
            (x0 + side + gap, y0 + side + gap),
        ]:
            draw.rounded_rectangle(
                (x, y, x + side, y + side),
                radius=rad, fill=self.WIN_ICON_COLOR,
            )
        img = img.resize((self.BTN_SIZE, self.BTN_SIZE), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def make_rounded_rgba(self, w, h, radius, fill):
        W, H = w * self.SS, h * self.SS
        R = radius * self.SS
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(img).rounded_rectangle(
            (0, 0, W - 1, H - 1), radius=R, fill=fill,
        )
        img = img.resize((w, h), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    # =========================================================
    #   ЗАГРУЗКА
    # =========================================================
    def show_boot_screen(self):
        self.boot_label = tk.Label(
            self.root, text="RewsOS v0.1\nBooting...",
            fg="white", bg="black",
            font=("Consolas", 28), justify="center",
        )
        self.boot_label.place(relx=0.5, rely=0.5, anchor="center")
        self.root.after(self.BOOT_TIME_MS, self.show_desktop)

    # =========================================================
    #   РАБОЧИЙ СТОЛ
    # =========================================================
    def show_desktop(self):
        self.boot_label.destroy()

        self.wallpaper_pil = self.generate_wallpaper_pil()
        self.wallpaper_ref = ImageTk.PhotoImage(self.wallpaper_pil)
        tk.Label(self.root, image=self.wallpaper_ref, bd=0).place(
            x=0, y=0, relwidth=1, relheight=1)

        self.build_taskbar()
        self.build_clock()

    # =========================================================
    #   ПАНЕЛЬ ЗАДАЧ
    # =========================================================
    def build_taskbar(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        self.tb_x = (sw - self.TASKBAR_W) // 2
        self.tb_y = sh - self.TASKBAR_H - 14

        img = self.rounded_on_wallpaper(
            self.tb_x, self.tb_y,
            self.TASKBAR_W, self.TASKBAR_H,
            self.TASKBAR_RADIUS, self.TASKBAR_BG,
        )
        self.taskbar_image_ref = img

        self.taskbar_frame = tk.Frame(
            self.root, bg=self.BG_DESKTOP,
            width=self.TASKBAR_W, height=self.TASKBAR_H,
        )
        self.taskbar_frame.place(x=self.tb_x, y=self.tb_y,
                                 width=self.TASKBAR_W, height=self.TASKBAR_H)

        tk.Label(self.taskbar_frame, image=img, bd=0).place(
            x=0, y=0, relwidth=1, relheight=1)

        self.start_btn_img_normal = self.make_start_button(self.START_BTN_BG)
        self.start_btn_img_hover  = self.make_start_button(self.START_BTN_HOVER)

        self.start_btn = tk.Label(
            self.taskbar_frame,
            image=self.start_btn_img_normal,
            bg=self.TASKBAR_BG, bd=0, cursor="hand2",
        )
        self.start_btn.place(relx=0.5, rely=0.5, anchor="center")

        self.start_btn.bind("<Button-1>", lambda e: self.toggle_start_menu())
        self.start_btn.bind("<Enter>", self.on_start_enter)
        self.start_btn.bind("<Leave>", self.on_start_leave)

        self.btn_screen_x = self.tb_x + self.TASKBAR_W // 2
        self.btn_screen_y = self.tb_y + self.TASKBAR_H // 2

    def on_start_enter(self, _):
        self.start_btn.config(image=self.start_btn_img_hover)

    def on_start_leave(self, _):
        self.start_btn.config(image=self.start_btn_img_normal)

    # =========================================================
    #   АНИМАЦИЯ МЕНЮ
    # =========================================================
    def ease_out(self, t):
        return 1 - (1 - t) ** self.MENU_ANIM_EASE

    def toggle_start_menu(self):
        if self.start_menu is not None:
            self.animate_close_menu()
        else:
            self.animate_open_menu()

    def animate_open_menu(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        self.menu_final_x = (sw - self.MENU_W) // 2
        self.menu_final_y = (sh - self.MENU_H) // 2

        self.menu_start_x = self.btn_screen_x - self.MENU_W // 2
        self.menu_start_y = self.btn_screen_y

        self.start_menu = tk.Frame(self.root, bg=self.BG_DESKTOP)
        self.start_menu.place(x=self.menu_start_x, y=self.menu_start_y,
                              width=self.MENU_W, height=1)

        self.menu_bg_label = tk.Label(self.start_menu, bd=0, bg=self.BG_DESKTOP)
        self.menu_bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.menu_title = tk.Label(
            self.start_menu, text="Меню RewsOS",
            bg=self.MENU_BG, fg="#202020",
            font=("Segoe UI", 14, "bold"),
        )
        self.menu_title.place(relx=0.5, y=16, anchor="n")

        items = ["Терминал", "Файлы", "Настройки", "Выключение"]
        start_y = 70
        step = self.ITEM_H + 12
        self.item_images.clear()
        self.menu_items_widgets.clear()
        for i, name in enumerate(items):
            self.create_menu_item(name, start_y + i * step)

        self.menu_title.place_forget()
        for w in self.menu_items_widgets:
            w.place_forget()

        total_frames = max(1, int(self.MENU_ANIM_MS / 1000 * self.MENU_ANIM_FPS))
        self.menu_anim_frame = 0
        self.menu_anim_total = total_frames
        self.menu_anim_step_open()

    def menu_anim_step_open(self):
        f = self.menu_anim_frame
        total = self.menu_anim_total
        t = f / total
        e = self.ease_out(t)

        cur_h = max(1, int(self.MENU_H * e))
        cur_y = int(self.menu_start_y + (self.menu_final_y - self.menu_start_y) * e)
        cur_x = int(self.menu_start_x + (self.menu_final_x - self.menu_start_x) * e)

        cur_radius = int(self.MENU_RADIUS * min(1.0, e))
        cur_radius = max(4, cur_radius)
        cur_radius = min(cur_radius, max(1, cur_h // 2))

        self.start_menu.place(x=cur_x, y=cur_y,
                              width=self.MENU_W, height=cur_h)

        img = self.rounded_on_wallpaper(
            cur_x, cur_y, self.MENU_W, cur_h,
            cur_radius, self.MENU_BG,
        )
        self.menu_bg_img = img
        self.menu_bg_label.config(image=img)
        self.menu_bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        if f >= total:
            final_img = self.rounded_on_wallpaper(
                self.menu_final_x, self.menu_final_y,
                self.MENU_W, self.MENU_H,
                self.MENU_RADIUS, self.MENU_BG,
            )
            self.menu_bg_img = final_img
            self.menu_bg_label.config(image=final_img)
            self.menu_bg_label.place(x=0, y=0, relwidth=1, relheight=1)

            self.start_menu.place(
                x=self.menu_final_x, y=self.menu_final_y,
                width=self.MENU_W, height=self.MENU_H,
            )

            self.menu_title.place(relx=0.5, y=16, anchor="n")
            for w in self.menu_items_widgets:
                info = getattr(w, "_place_info", None)
                if info:
                    w.place(**info)

            self.menu_anim_job = None
            return

        self.menu_anim_frame += 1
        self.menu_anim_job = self.root.after(
            int(1000 / self.MENU_ANIM_FPS), self.menu_anim_step_open
        )

    def animate_close_menu(self):
        if self.start_menu is None:
            return

        if self.menu_anim_job:
            self.root.after_cancel(self.menu_anim_job)
            self.menu_anim_job = None

        self.menu_title.place_forget()
        for w in self.menu_items_widgets:
            w.place_forget()

        total_frames = max(1, int(self.MENU_ANIM_MS / 1000 * self.MENU_ANIM_FPS))
        self.menu_anim_frame = 0
        self.menu_anim_total = total_frames
        self.menu_anim_step_close()

    def menu_anim_step_close(self):
        f = self.menu_anim_frame
        total = self.menu_anim_total
        t = f / total
        e = self.ease_out(t)

        cur_h = max(1, int(self.MENU_H * (1 - e)))
        cur_y = int(self.menu_final_y + (self.menu_start_y - self.menu_final_y) * e)
        cur_x = int(self.menu_final_x + (self.menu_start_x - self.menu_final_x) * e)

        cur_radius = int(self.MENU_RADIUS * (1 - e))
        cur_radius = max(1, cur_radius)
        cur_radius = min(cur_radius, max(1, cur_h // 2))

        self.start_menu.place(x=cur_x, y=cur_y,
                              width=self.MENU_W, height=cur_h)

        img = self.rounded_on_wallpaper(
            cur_x, cur_y, self.MENU_W, cur_h,
            cur_radius, self.MENU_BG,
        )
        self.menu_bg_img = img
        self.menu_bg_label.config(image=img)

        if f >= total:
            self.start_menu.destroy()
            self.start_menu = None
            self.item_images.clear()
            self.menu_items_widgets.clear()
            self.menu_anim_job = None
            return

        self.menu_anim_frame += 1
        self.menu_anim_job = self.root.after(
            int(1000 / self.MENU_ANIM_FPS), self.menu_anim_step_close
        )

    # =========================================================
    #   ПУНКТЫ МЕНЮ
    # =========================================================
    def create_menu_item(self, name, y):
        img_n = self.make_rounded_rgba(
            self.ITEM_W, self.ITEM_H, self.ITEM_RADIUS, self.ITEM_BG)
        img_h = self.make_rounded_rgba(
            self.ITEM_W, self.ITEM_H, self.ITEM_RADIUS, self.ITEM_BG_HOVER)
        self.item_images[name] = (img_n, img_h)

        lbl = tk.Label(
            self.start_menu,
            text=name, image=img_n, compound="center",
            fg=self.ITEM_FG, bg=self.MENU_BG,
            font=("Segoe UI", 11, "bold"),
            bd=0, cursor="hand2",
        )
        place_kwargs = dict(relx=0.5, y=y, anchor="n",
                            width=self.ITEM_W, height=self.ITEM_H)
        lbl.place(**place_kwargs)
        lbl._place_info = place_kwargs

        lbl.bind("<Button-1>", lambda e, n=name: self.menu_action(n))
        lbl.bind("<Enter>",    lambda e, n=name: lbl.config(image=self.item_images[n][1]))
        lbl.bind("<Leave>",    lambda e, n=name: lbl.config(image=self.item_images[n][0]))

        self.menu_items_widgets.append(lbl)

    def menu_action(self, name):
        print(f"[RewsOS] Выбрано: {name}")
        if name == "Выключение":
            self.shutdown()
        elif name == "Терминал":
            self.animate_close_menu()
            self.root.after(260, self.open_terminal)
        # "Файлы" и "Настройки" пока игнорируем

    # =========================================================
    #   ТЕРМИНАЛ
    # =========================================================
    def open_terminal(self):
        if self.term_win is not None:
            try:
                self.term_win.lift()
                self.term_entry.focus_set()
                return
            except tk.TclError:
                self.term_win = None

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = 720, 460
        x = (sw - w) // 2
        y = (sh - h) // 2

        self.term_win = tk.Toplevel(self.root)
        self.term_win.title("Терминал — RewsOS")
        self.term_win.configure(bg="#0c0c0c")
        self.term_win.geometry(f"{w}x{h}+{x}+{y}")
        self.term_win.resizable(False, False)
        self.term_win.transient(self.root)
        self.term_win.protocol("WM_DELETE_WINDOW", self.close_terminal)

        # верхняя панель с заголовком и крестиком
        title_bar = tk.Frame(self.term_win, bg="#1a1a1a", height=32)
        title_bar.pack(fill="x", side="top")
        title_bar.pack_propagate(False)

        tk.Label(
            title_bar, text="Терминал — RewsOS",
            bg="#1a1a1a", fg="#e0e0e0",
            font=("Segoe UI", 10),
        ).pack(side="left", padx=10)

        close_btn = tk.Label(
            title_bar, text="✕",
            bg="#1a1a1a", fg="#e0e0e0",
            font=("Segoe UI", 10, "bold"),
            cursor="hand2", padx=10,
        )
        close_btn.pack(side="right", fill="y")
        close_btn.bind("<Button-1>", lambda e: self.close_terminal())
        close_btn.bind("<Enter>", lambda e: close_btn.config(bg="#c42b1c", fg="white"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg="#1a1a1a", fg="#e0e0e0"))

        # область вывода
        self.term_output = tk.Text(
            self.term_win,
            bg="#0c0c0c", fg="#e0e0e0",
            font=("Consolas", 11),
            bd=0, highlightthickness=0,
            wrap="word", insertbackground="#e0e0e0",
            state="disabled",
        )
        self.term_output.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        # строка ввода
        input_frame = tk.Frame(self.term_win, bg="#0c0c0c")
        input_frame.pack(fill="x", padx=8, pady=8)

        tk.Label(
            input_frame, text="RewsOS>",
            bg="#0c0c0c", fg="#4ec9b0",
            font=("Consolas", 11, "bold"),
        ).pack(side="left")

        self.term_entry = tk.Entry(
            input_frame,
            bg="#0c0c0c", fg="#e0e0e0",
            insertbackground="#e0e0e0",
            font=("Consolas", 11),
            bd=0, highlightthickness=0,
        )
        self.term_entry.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.term_entry.bind("<Return>", self.term_execute)
        self.term_entry.bind("<Escape>", lambda e: self.close_terminal())

        self.term_entry.focus_set()

        self.term_print("RewsOS Terminal v0.1")
        self.term_print("Введите 'help' для списка команд.")
        self.term_print("")

    def close_terminal(self):
        if self.term_win is not None:
            try:
                self.term_win.destroy()
            except tk.TclError:
                pass
            self.term_win = None

    def term_print(self, text):
        self.term_output.config(state="normal")
        self.term_output.insert("end", text + "\n")
        self.term_output.see("end")
        self.term_output.config(state="disabled")

    def term_execute(self, event=None):
        cmd_line = self.term_entry.get().strip()
        self.term_entry.delete(0, "end")

        self.term_print(f"RewsOS> {cmd_line}")
        if not cmd_line:
            return

        parts = cmd_line.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == "help":
            self.term_print("Доступные команды:")
            self.term_print("  help           — этот список")
            self.term_print("  echo <текст>   — вывести текст")
            self.term_print("  cls / clear    — очистить экран")
            self.term_print("  ver            — версия системы")
            self.term_print("  time           — текущее время")
            self.term_print("  date           — текущая дата")
            self.term_print("  whoami         — текущий пользователь")
            self.term_print("  dir / ls       — список файлов (заглушка)")
            self.term_print("  exit / quit    — закрыть терминал")

        elif cmd == "echo":
            self.term_print(" ".join(args))

        elif cmd in ("cls", "clear"):
            self.term_output.config(state="normal")
            self.term_output.delete("1.0", "end")
            self.term_output.config(state="disabled")

        elif cmd == "ver":
            self.term_print("RewsOS v0.1 (Terminal build)")

        elif cmd == "time":
            self.term_print(datetime.now().strftime("%H:%M:%S"))

        elif cmd == "date":
            self.term_print(datetime.now().strftime("%d.%m.%Y"))

        elif cmd == "whoami":
            self.term_print("user")

        elif cmd in ("dir", "ls"):
            self.term_print("Файловая система пока не подключена.")

        elif cmd in ("exit", "quit"):
            self.close_terminal()
            return

        else:
            self.term_print(f"'{cmd}' не является внутренней командой.")
            self.term_print("Введите 'help' для списка команд.")

        self.term_print("")

    # =========================================================
    #   ЧАСЫ
    # =========================================================
    def build_clock(self):
        self.clock_label = tk.Label(
            self.root, text="",
            fg="white", bg="#0a0e20",
            font=("Consolas", 12),
        )
        self.clock_label.place(relx=0.99, rely=0.02, anchor="ne")
        self.update_clock()

    def update_clock(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=now)
        self.clock_job = self.root.after(1000, self.update_clock)

    # =========================================================
    #   ВЫХОД
    # =========================================================
    def shutdown(self):
        if self.clock_job:
            self.root.after_cancel(self.clock_job)
        if self.menu_anim_job:
            self.root.after_cancel(self.menu_anim_job)
        self.close_terminal()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    RewsOS().run()