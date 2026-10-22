"""동영상 탐색, 시점 프레임 추출, GUI 마우스 부분 선택 도구."""
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import cv2
from PIL import Image, ImageTk


class VideoError(RuntimeError):
    pass


class VideoReader:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.cap = cv2.VideoCapture(self.path)
        if not self.cap.isOpened():
            raise VideoError("동영상을 열 수 없습니다. 파일 경로 또는 코덱을 확인하세요.")
        self.fps = float(self.cap.get(cv2.CAP_PROP_FPS))
        if not 0 < self.fps < 1000:
            self.fps = 30.0
        self.frame_count = max(0, int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        self.duration = max(0., (self.frame_count - 1) / self.fps) if self.frame_count else 0.
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def read_at(self, seconds: float) -> tuple[Image.Image, float]:
        if not self.cap.isOpened():
            raise VideoError("동영상이 닫혔습니다.")
        seconds = max(0., float(seconds))
        if self.frame_count:
            index = max(0, min(self.frame_count - 1, round(seconds * self.fps)))
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        else:
            self.cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000.)
        ok, bgr = self.cap.read()
        if not ok or bgr is None:
            raise VideoError("이 시간의 프레임을 읽을 수 없습니다. 다른 위치를 선택하세요.")
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        frame = Image.fromarray(rgb, "RGB")
        actual_index = self.cap.get(cv2.CAP_PROP_POS_FRAMES) - 1
        actual_second = max(0., actual_index / self.fps) if actual_index >= 0 else seconds
        return frame, actual_second

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()


def crop_frame(frame: Image.Image, coords: tuple[int, int, int, int] | None) -> Image.Image:
    if coords is None:
        return frame.copy()
    x1, y1, x2, y2 = coords
    x1, x2 = sorted((max(0, min(frame.width, x1)), max(0, min(frame.width, x2))))
    y1, y2 = sorted((max(0, min(frame.height, y1)), max(0, min(frame.height, y2))))
    if x2 - x1 < 3 or y2 - y1 < 3:
        raise ValueError("부분 캡처 영역이 너무 작습니다. 마우스로 넓게 선택하세요.")
    return frame.crop((x1, y1, x2, y2))


def to_timestamp(seconds: float) -> str:
    hrs = int(seconds) // 3600
    mins = (int(seconds) % 3600) // 60
    sec = seconds % 60
    return f"{hrs:02d}:{mins:02d}:{sec:06.3f}"


def parse_timestamp(value: str) -> float:
    try:
        parts = [float(p) for p in value.strip().split(":")]
        if not parts or len(parts) > 3 or any(p < 0 for p in parts):
            raise ValueError
        if len(parts) == 3 and (parts[1] >= 60 or parts[2] >= 60):
            raise ValueError
        if len(parts) == 2 and parts[1] >= 60:
            raise ValueError
        total = 0.0
        for p in parts:
            total = total * 60 + p
        return total
    except ValueError:
        raise ValueError("시간은 초(12.5), 분:초(01:12.5) 또는 시:분:초(00:01:12.5) 형식으로 입력하세요.")


class VideoCaptureDialog(tk.Toplevel):
    """시간 탐색 -> ROI 드래그 -> 이미지 반영/별도 저장. 여러 번 캡처 가능."""

    TARGETS = ("새 사진 레이어", "배경", "선택한 사진 교체")

    def __init__(self, parent: tk.Misc, path: str,
                 on_apply, start: float = 0.0):  # on_apply(Image, target) -> None · start = 처음 보여 줄 시점(초)
        self.reader = VideoReader(path)
        try:
            super().__init__(parent)
        except Exception:
            self.reader.close()
            raise
        self.on_apply = on_apply
        self.title("동영상 프레임 / 부분 캡처 — DreamArt")
        self.geometry("990x820")
        self.minsize(730, 670)
        self.configure(background=ttk.Style(self).lookup(".", "background") or "#f4f5f8")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.frame_image: Image.Image | None = None
        self.tk_image = None
        self.roi: tuple[int, int, int, int] | None = None
        self.start_point = None
        self.display_rect = (0, 0, 1, 1)
        self.seek_job = None
        self.in_slider_update = False
        self.position = 0.0
        self.position_var = tk.DoubleVar(value=0)
        self.target_var = tk.StringVar(value=self.TARGETS[0])
        self.clock_var = tk.StringVar(value="00:00:00.000")
        self.note_var = tk.StringVar(value="동영상 화면에서 마우스로 드래그하면 해당 부분만 캡처합니다.")
        self._build(path)
        self.after(100, lambda: self.seek(float(start or 0.0)))

    def _build(self, path: str):
        info = ttk.Frame(self, padding=(14, 12))
        info.pack(fill="x")
        ttk.Label(info, text="동영상: " + Path(path).name, font=("", 12, "bold")).pack(anchor="w")
        duration = to_timestamp(self.reader.duration) if self.reader.frame_count else "길이 확인 불가"
        ttk.Label(info, text=f"{self.reader.width}×{self.reader.height}  |  {self.reader.fps:.3g} FPS  |  {duration}  |  총 {self.reader.frame_count or '?'}프레임").pack(anchor="w", pady=(4, 0))
        outer = ttk.Frame(self, padding=(12, 0, 12, 4))
        outer.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(outer, bg="#0b1120", cursor="crosshair", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self._mouse_down)
        self.canvas.bind("<B1-Motion>", self._mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._mouse_up)
        self.canvas.bind("<Configure>", lambda event: self._draw_frame())

        times = ttk.Frame(self, padding=(16, 10))
        times.pack(fill="x")
        self.scale = ttk.Scale(times, from_=0, to=max(.1, self.reader.duration or 60),
                               variable=self.position_var, command=self._scale_moved)
        self.scale.pack(fill="x")
        line = ttk.Frame(times)
        line.pack(fill="x", pady=(8, 0))
        ttk.Button(line, text="◀ 1초", command=lambda: self.seek(self.position - 1)).pack(side="left", padx=2)
        ttk.Button(line, text="◀ 1프레임", command=lambda: self.seek(self.position - 1 / self.reader.fps)).pack(side="left", padx=2)
        ttk.Button(line, text="1프레임 ▶", command=lambda: self.seek(self.position + 1 / self.reader.fps)).pack(side="left", padx=2)
        ttk.Button(line, text="1초 ▶", command=lambda: self.seek(self.position + 1)).pack(side="left", padx=2)
        ttk.Label(line, text="시간 이동:").pack(side="left", padx=(18, 3))
        self.entry = ttk.Entry(line, textvariable=self.clock_var, width=13)
        self.entry.pack(side="left")
        self.entry.bind("<Return>", lambda e: self._jump_to_time())
        ttk.Button(line, text="이동", command=self._jump_to_time).pack(side="left", padx=3)
        ttk.Button(line, text="선택 해제", command=self._clear_roi).pack(side="right")

        actions = ttk.Frame(self, padding=(16, 6, 16, 8))
        actions.pack(fill="x")
        ttk.Label(actions, text="캡처 적용 위치").pack(side="left")
        ttk.Combobox(actions, textvariable=self.target_var, values=self.TARGETS,
                     width=15, state="readonly").pack(side="left", padx=(8, 10))
        ttk.Button(actions, text="선택 영역을 썸네일에 적용", style="Accent.TButton",
                   command=self._apply).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="부분 캡처 PNG 저장", command=self._save).pack(side="left")
        ttk.Button(actions, text="닫기", command=self.close).pack(side="right")
        ttk.Label(self, textvariable=self.note_var, padding=(16, 0, 16, 12), wraplength=900).pack(fill="x")

    def _scale_moved(self, value: str) -> None:
        if self.in_slider_update:
            return
        if self.seek_job:
            self.after_cancel(self.seek_job)
        self.seek_job = self.after(120, lambda: self.seek(float(self.position_var.get())))

    def _jump_to_time(self) -> None:
        try:
            self.seek(parse_timestamp(self.clock_var.get()))
        except ValueError as exc:
            messagebox.showwarning("시간 형식 확인", str(exc), parent=self)

    def seek(self, seconds: float) -> None:
        if self.seek_job is not None:
            self.after_cancel(self.seek_job)
            self.seek_job = None
        seconds = max(0., min(seconds, self.reader.duration)) if self.reader.frame_count else max(0., seconds)
        try:
            frame, self.position = self.reader.read_at(seconds)
        except (VideoError, cv2.error) as exc:
            self.note_var.set(str(exc))
            return
        self.frame_image = frame
        self.roi = None
        self.in_slider_update = True
        try:
            if not self.reader.frame_count and self.position > float(self.scale.cget("to")):
                self.scale.configure(to=self.position + 30)
            self.position_var.set(self.position)
        finally:
            self.in_slider_update = False
        self.clock_var.set(to_timestamp(self.position))
        self._draw_frame()
        self.note_var.set("드래그로 부분 영역 선택 / 선택하지 않으면 프레임 전체를 캡처합니다.")

    def _draw_frame(self) -> None:
        if self.frame_image is None:
            return
        cw = max(1, self.canvas.winfo_width())
        ch = max(1, self.canvas.winfo_height())
        fw, fh = self.frame_image.size
        scale = min(cw / fw, ch / fh)
        dw, dh = max(1, int(fw * scale)), max(1, int(fh * scale))
        ox, oy = (cw - dw) // 2, (ch - dh) // 2
        self.display_rect = (ox, oy, dw, dh)
        im = self.frame_image.resize((dw, dh), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(im)
        self.canvas.delete("all")
        self.canvas.create_image(ox, oy, anchor="nw", image=self.tk_image)
        self._draw_roi()

    def _canvas_to_original(self, x: int, y: int) -> tuple[int, int]:
        ox, oy, dw, dh = self.display_rect
        x = max(ox, min(ox + dw, x))
        y = max(oy, min(oy + dh, y))
        fw, fh = self.frame_image.size
        return (round((x - ox) * fw / dw), round((y - oy) * fh / dh))

    def _draw_roi(self) -> None:
        self.canvas.delete("selection")
        if self.roi is None or self.frame_image is None:
            return
        ox, oy, dw, dh = self.display_rect
        fw, fh = self.frame_image.size
        x1, y1, x2, y2 = self.roi
        sx1, sy1 = ox + x1 * dw / fw, oy + y1 * dh / fh
        sx2, sy2 = ox + x2 * dw / fw, oy + y2 * dh / fh
        self.canvas.create_rectangle(sx1, sy1, sx2, sy2, outline="#ffdb4d", width=3,
                                     dash=(8, 4), tags="selection")
        self.canvas.create_text(min(sx1, sx2) + 6, max(oy + 12, min(sy1, sy2) - 14),
                                text=f"{abs(x2-x1)}×{abs(y2-y1)}", anchor="w", fill="#ffe66d",
                                font=("", 11, "bold"), tags="selection")

    def _mouse_down(self, event) -> None:
        if self.frame_image is None:
            return
        self.start_point = self._canvas_to_original(event.x, event.y)
        self.roi = (*self.start_point, *self.start_point)
        self._draw_roi()

    def _mouse_drag(self, event) -> None:
        if self.start_point is None:
            return
        x, y = self._canvas_to_original(event.x, event.y)
        self.roi = (*self.start_point, x, y)
        self._draw_roi()

    def _mouse_up(self, event) -> None:
        if self.start_point is None:
            return
        x, y = self._canvas_to_original(event.x, event.y)
        x0, y0 = self.start_point
        self.start_point = None
        self.roi = (x0, y0, x, y) if abs(x - x0) >= 3 and abs(y - y0) >= 3 else None
        self._draw_roi()
        if self.roi:
            self.note_var.set(f"선택된 부분: {abs(x-x0)}×{abs(y-y0)}픽셀 | 적용하거나 PNG로 저장하세요.")

    def _clear_roi(self) -> None:
        self.roi = None
        self._draw_roi()
        self.note_var.set("영역을 해제했습니다. 현재 프레임 전체를 캡처할 수 있습니다.")

    def _extract(self) -> Image.Image:
        if self.frame_image is None:
            raise VideoError("아직 읽어온 프레임이 없습니다.")
        return crop_frame(self.frame_image, self.roi)

    def _apply(self) -> None:
        try:
            extracted = self._extract()
            self.on_apply(extracted, self.target_var.get())
            self.note_var.set(f"✓ {to_timestamp(self.position)} / {extracted.width}×{extracted.height} 영역을 '{self.target_var.get()}'에 적용했습니다. 다른 구간도 이어서 캡처할 수 있습니다.")
        except Exception as exc:
            messagebox.showerror("캡처 적용 오류", str(exc), parent=self)

    def _save(self) -> None:
        try:
            cropped = self._extract()
        except (ValueError, VideoError) as exc:
            messagebox.showwarning("캡처 오류", str(exc), parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".png",
            filetypes=[("PNG 이미지", "*.png")], initialfile="video_capture.png")
        if path:
            try:
                cropped.save(path, format="PNG")
                self.note_var.set(f"캡처 이미지를 저장했습니다: {path}")
            except OSError as exc:
                messagebox.showerror("저장 실패", str(exc), parent=self)

    def close(self) -> None:
        if self.seek_job is not None:
            self.after_cancel(self.seek_job)
        self.reader.close()
        self.destroy()
