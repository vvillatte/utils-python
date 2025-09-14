import tkinter as tk
import ctypes
# import json
from .config_loader import load_config

class CrosshairOverlay:
    def __init__(self):
        self.config = load_config()
        self.style = self.config['styles'][self.config['default']]
        self.color = self.style.get('color', 'red')
        self.thickness = self.style.get('thickness', 2)
        self.elements = self.style.get('elements', [])
        self.canvas_size = self._infer_canvas_size()
        self.root = None
        self.canvas = None

    def _infer_canvas_size(self):
        max_offset = 0
        for el in self.elements:
            for key in ['x1', 'x2', 'y1', 'y2']:
                val = el.get(key)
                if isinstance(val, int):
                    max_offset = max(max_offset, abs(val))
            if el['type'] == 'dot':
                max_offset = max(max_offset, el.get('radius', 2))
            if el['type'] == 'triangle':
                max_offset = max(max_offset, el.get('size', 4) * 2)
        return 2 * (max_offset + 20)  # Padding around center

    def _make_clickthrough(self):
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        extended_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, extended_style | 0x80000 | 0x20)
        ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0x00ffffff, 0, 0x1)

    def _resolve_coord(self, value, center, full):
        if value == "center":
            return center
        elif value == "full":
            return full
        elif value == 0:
            return 0
        elif isinstance(value, int):
            return center + value
        else:
            return center  # fallback

    def _draw_crosshair(self):
        s = self.canvas_size // 2
        for el in self.elements:
            t = el['type']
            if t == 'line':
                x1 = self._resolve_coord(el['x1'], s, self.canvas_size)
                y1 = self._resolve_coord(el['y1'], s, self.canvas_size)
                x2 = self._resolve_coord(el['x2'], s, self.canvas_size)
                y2 = self._resolve_coord(el['y2'], s, self.canvas_size)
                self.canvas.create_line(x1, y1, x2, y2, fill=self.color, width=self.thickness)

            elif t == 'dot':
                r = el.get('radius', 2)
                self.canvas.create_oval(s - r, s - r, s + r, s + r, fill=self.color, outline=self.color)

            elif t == 'triangle':
                ts = el.get('size', 4)
                dist = el.get('distance', 0)
                dir = el.get('direction')
                if dir == 'up':
                    points = [s, s - dist,
                              s - ts, s - dist - ts,
                              s + ts, s - dist - ts]
                elif dir == 'down':
                    points = [s, s + dist,
                              s - ts, s + dist + ts,
                              s + ts, s + dist + ts]
                elif dir == 'left':
                    points = [s - dist, s,
                              s - dist - ts, s - ts,
                              s - dist - ts, s + ts]
                elif dir == 'right':
                    points = [s + dist, s,
                              s + dist + ts, s - ts,
                              s + dist + ts, s + ts]
                else:
                    continue
                self.canvas.create_polygon(points, fill=self.color, outline=self.color)

    def _setup_window(self):
        self.root = tk.Tk()
        self.root.attributes('-topmost', True)
        self.root.attributes('-transparentcolor', 'white')
        self.root.configure(bg='white')  # Window background
        self.root.overrideredirect(True)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        s = self.canvas_size // 2
        x = screen_width // 2 - s
        y = screen_height // 2 - s
        self.root.geometry(f"{self.canvas_size}x{self.canvas_size}+{x}+{y}")

        # Canvas background must match window background
        self.canvas = tk.Canvas(self.root, width=self.canvas_size, height=self.canvas_size,
                                bg='white', highlightthickness=0, bd=0)
        self.canvas.pack()

        self._draw_crosshair()
        self.root.update_idletasks()
        self._make_clickthrough()

    def run(self):
        self._setup_window()
        self.root.mainloop()