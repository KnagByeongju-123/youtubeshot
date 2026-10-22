"""썸네일 편집기 — DreamArt Thumbnail Studio(github.com/KnagByeongju-123/thumbnail, MIT) 화면을 이 프로그램에 맞춘 것.

  썸네일_편집기.bat 에 콘텐츠 폴더(또는 <제목>_썸네일_편집.json)를 끌어다 놓으면
  프로그램이 고른 썸네일이 배경·오린 사진·문구·강조색까지 그대로 열림 → 드래그·휠로 다듬고
  '💾 유튜브 썸네일로 저장' = <제목>_썸네일_유튜브.jpg 를 바로 바꿈 (예전 것은 _썸네일_유튜브_이전.jpg 로 한 번 남김)
  '🎬 첫 5초에서 캡처' = 완성 영상의 처음 장면을 열어 원하는 부분만 잘라 넣기 (규칙: 썸네일 = 영상 첫 5초의 약속)
"""
from __future__ import annotations

from pathlib import Path
import glob
import json
import os
import re
import shutil
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageTk

import 썸네일_엔진 as TE
from 썸네일_엔진 import (ARRANGEMENTS, DESIGN_PRESETS, FRAMES, OVERLAYS, PRESETS, SHAPES, STICKERS,
                     TAG_POSITIONS, THEMES, TITLE_STYLES, PhotoLayer, RenderOptions,
                     arrange_layers, load_image, make_sticker, render_with_bounds, save_thumbnail)
from 썸네일_영상캡처 import VideoCaptureDialog

try:                                   # AI 누끼(rembg) - 프로그램과 같은 모델 (models\rembg)
    import 썸네일_합성
    TE.CUTOUT = 썸네일_합성.cutout
except Exception:
    pass

ROOT_DIR = Path(__file__).resolve().parent
VIDEO_FILTER = [("동영상 파일", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v"), ("모든 파일", "*.*")]
IMAGE_FILTER = [("이미지", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("모든 파일", "*.*")]

# 다크 UI 색상
BG = "#17191f"
FIELD = "#252932"
BORDER = "#363b47"
TEXT = "#e9ebf1"
MUTED = "#8d95a7"
ACCENT = "#f5c542"
ACCENT_DARK = "#d6a51c"
PREVIEW_BG = "#0d1018"


class ThumbnailMakerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("썸네일 편집기 (DreamArt 썸네일 스튜디오 기반)")
        self.meta: dict = {}            # 프로그램에서 불러온 정보: base, video, out, opening, title
        self.state_path: str = ""
        self.root.geometry("1380x900")
        self.root.minsize(1080, 700)
        self.root.configure(background=BG)

        self.background: Image.Image | None = None
        self.layers: list[PhotoLayer] = []
        self.selected: int | None = None
        self.auto_arrange = True        # 직접 옮기기 전까지는 사진 추가 시 자동 정렬
        self.capture_dialog: VideoCaptureDialog | None = None
        self.preview_photo = None
        self.preview_image: Image.Image | None = None
        self.preview_bounds: list = []
        self.preview_geom = (0, 0, 1.0)  # (x 오프셋, y 오프셋, 화면배율)
        self.preview_job = None
        self.drag = None
        self._syncing = False
        self.status_var = tk.StringVar(value="사진을 추가하거나 동영상에서 장면을 캡처하세요.  (Ctrl+V 로 복사한 이미지 붙여넣기)")

        # 전체 옵션
        self.preset_var = tk.StringVar(value="YouTube HD 1280×720")
        self.arrange_var = tk.StringVar(value="좌우 대칭")
        self.design_var = tk.StringVar(value="미스터리 다큐")
        self.theme_var = tk.StringVar(value="골드")
        self.title_style_var = tk.StringVar(value="외곽선")
        self.overlay_var = tk.StringVar(value="하단 그라데이션")
        self.frame_var = tk.StringVar(value="테두리")
        self.tag_pos_var = tk.StringVar(value="제목 위")
        self.align_var = tk.StringVar(value="center")
        self.font_var = tk.DoubleVar(value=86)
        self.text_y_var = tk.DoubleVar(value=76)
        self.brightness_var = tk.DoubleVar(value=85)
        self.darkness_var = tk.DoubleVar(value=62)
        self.blur_var = tk.DoubleVar(value=0)
        self.sat_var = tk.DoubleVar(value=100)
        self.subtitle_var = tk.StringVar(value="DREAMART VIDEO HIGHLIGHT")
        self.bg_label = tk.StringVar(value="내장 배경")

        # 선택한 사진 레이어 속성
        self.lx = tk.DoubleVar(value=50)
        self.ly = tk.DoubleVar(value=45)
        self.lsize = tk.DoubleVar(value=60)
        self.lrot = tk.DoubleVar(value=0)
        self.lop = tk.DoubleVar(value=100)
        self.lshape = tk.StringVar(value="원본")
        self.loutline = tk.BooleanVar(value=False)
        self.lshadow = tk.BooleanVar(value=True)
        self.lremove = tk.BooleanVar(value=False)
        self.lai = tk.BooleanVar(value=False)
        self.lvisible = tk.BooleanVar(value=True)
        self.layer_title = tk.StringVar(value="선택된 사진 없음")

        self._style()
        self._build_ui()
        self._bind_keys()
        self.root.after(200, self.update_preview)

    # ─────────────────────────────────────────────── 스타일 / 화면 구성
    def _style(self):
        sty = ttk.Style(self.root)
        if "clam" in sty.theme_names():
            sty.theme_use("clam")
        sty.configure(".", background=BG, foreground=TEXT, fieldbackground=FIELD, bordercolor=BORDER,
                      lightcolor=BG, darkcolor=BG, troughcolor=FIELD, focuscolor=ACCENT,
                      selectbackground=ACCENT, selectforeground="#111111", insertcolor=TEXT, arrowcolor=TEXT)
        sty.configure("TButton", background=FIELD, padding=(10, 6), bordercolor=BORDER,
                      lightcolor=FIELD, darkcolor=FIELD)
        sty.map("TButton", background=[("pressed", BORDER), ("active", "#30343f")])
        sty.configure("Accent.TButton", background=ACCENT, foreground="#14161a", padding=(14, 9),
                      font=("", 10, "bold"), lightcolor=ACCENT, darkcolor=ACCENT, bordercolor=ACCENT_DARK)
        sty.map("Accent.TButton", background=[("pressed", ACCENT_DARK), ("active", "#ffd45e")],
                foreground=[("active", "#14161a")])
        sty.configure("Small.TButton", padding=(6, 4))
        sty.configure("Subhead.TLabel", font=("", 11, "bold"), foreground=ACCENT)
        sty.configure("Help.TLabel", foreground=MUTED, font=("", 9))
        sty.configure("Title.TLabel", font=("", 16, "bold"))
        sty.configure("TCombobox", fieldbackground=FIELD, background=FIELD, foreground=TEXT, arrowcolor=TEXT,
                      lightcolor=FIELD, darkcolor=FIELD)
        sty.map("TCombobox", fieldbackground=[("readonly", FIELD)], foreground=[("readonly", TEXT)],
                selectbackground=[("readonly", FIELD)], selectforeground=[("readonly", TEXT)])
        sty.configure("TEntry", fieldbackground=FIELD, lightcolor=FIELD, darkcolor=FIELD)
        for w in ("TCheckbutton", "TRadiobutton"):
            sty.configure(w, background=BG, foreground=TEXT, indicatorbackground=FIELD,
                          indicatorforeground="#14161a", upperbordercolor=BORDER, lowerbordercolor=BORDER)
            sty.map(w, indicatorbackground=[("selected", ACCENT), ("active", BORDER)],
                    background=[("active", BG)])
        sty.configure("Horizontal.TScale", background="#c9ced9", troughcolor=FIELD, bordercolor=BORDER,
                      lightcolor="#c9ced9", darkcolor="#c9ced9")
        sty.configure("Vertical.TScrollbar", background=FIELD, troughcolor=BG, arrowcolor=MUTED,
                      bordercolor=BG, lightcolor=FIELD, darkcolor=FIELD)
        sty.configure("TSeparator", background=BORDER)
        sty.configure("TPanedwindow", background=BG)
        self.root.option_add("*TCombobox*Listbox.background", FIELD)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#14161a")

    def _build_ui(self):
        toolbar = ttk.Frame(self.root, padding=(16, 12, 16, 10))
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text="DreamArt", style="Title.TLabel", foreground=ACCENT).pack(side="left")
        ttk.Label(toolbar, text="  썸네일 스튜디오", style="Title.TLabel").pack(side="left")
        ttk.Button(toolbar, text="💾 유튜브 썸네일로 저장", style="Accent.TButton",
                   command=self.save_to_program).pack(side="right", padx=(8, 0))
        ttk.Button(toolbar, text="🎬 첫 5초에서 캡처", command=lambda: self.open_video(start=0.0)).pack(side="right", padx=(8, 0))
        ttk.Button(toolbar, text="🎬 동영상 캡처", command=self.open_video).pack(side="right", padx=(8, 0))
        ttk.Button(toolbar, text="📂 영상 폴더 열기", command=self.open_folder_dialog).pack(side="right", padx=(8, 0))
        ttk.Button(toolbar, text="＋ 사진 추가 (여러 장)", command=self.add_photos).pack(side="right", padx=(8, 0))
        ttk.Button(toolbar, text="📋 붙여넣기", command=self.paste_clipboard).pack(side="right")

        body = ttk.PanedWindow(self.root, orient="horizontal")
        body.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        left = ttk.Frame(body, width=420)
        right = ttk.Frame(body)
        body.add(left, weight=0)
        body.add(right, weight=1)

        scroll = tk.Canvas(left, highlightthickness=0, width=405, background=BG)
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=scroll.yview)
        scroll.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        scroll.pack(side="left", fill="both", expand=True)
        panel = ttk.Frame(scroll, padding=(12, 4, 14, 16))
        panel_id = scroll.create_window((0, 0), window=panel, anchor="nw")
        panel.bind("<Configure>", lambda e: scroll.configure(scrollregion=scroll.bbox("all")))
        scroll.bind("<Configure>", lambda e: scroll.itemconfigure(panel_id, width=e.width))

        def wheel(ev):
            if ev.num == 4:
                scroll.yview_scroll(-2, "units")
            elif ev.num == 5:
                scroll.yview_scroll(2, "units")
            elif ev.delta:
                scroll.yview_scroll(-int(ev.delta / 120) or (-1 if ev.delta > 0 else 1), "units")

        def on_enter(_):
            for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                scroll.bind_all(seq, wheel)

        def on_leave(_):
            for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                scroll.unbind_all(seq)
        panel.bind("<Enter>", on_enter)
        panel.bind("<Leave>", on_leave)

        self._build_background(panel)
        self._build_layers(panel)
        self._build_text(panel)
        self._build_design(panel)
        self._build_output(panel)

        preview_outer = ttk.Frame(right, padding=(14, 4, 8, 10))
        preview_outer.pack(fill="both", expand=True)
        info = ttk.Frame(preview_outer)
        info.pack(fill="x", pady=(0, 8))
        ttk.Label(info, text="실시간 미리보기", font=("", 13, "bold")).pack(side="left")
        ttk.Label(info, text="   사진 클릭=선택 · 드래그=이동 · 휠=크기 · Shift+휠=회전 · Delete=삭제",
                  style="Help.TLabel").pack(side="left")
        self.dimension_label = ttk.Label(info, text="1280 × 720", style="Help.TLabel")
        self.dimension_label.pack(side="right")
        self.preview_canvas = tk.Canvas(preview_outer, background=PREVIEW_BG, highlightthickness=1,
                                        highlightbackground=BORDER, highlightcolor=ACCENT)
        self.preview_canvas.pack(fill="both", expand=True)
        c = self.preview_canvas
        c.bind("<Configure>", lambda e: self.schedule_preview(60))
        c.bind("<ButtonPress-1>", self._preview_press)
        c.bind("<B1-Motion>", self._preview_drag)
        c.bind("<ButtonRelease-1>", self._preview_release)
        c.bind("<Motion>", self._preview_hover)
        c.bind("<MouseWheel>", self._preview_wheel)
        c.bind("<Button-4>", lambda e: self._preview_wheel(e, 1))
        c.bind("<Button-5>", lambda e: self._preview_wheel(e, -1))
        c.bind("<Shift-MouseWheel>", lambda e: self._preview_wheel(e, rotate=True))
        c.bind("<Shift-Button-4>", lambda e: self._preview_wheel(e, 1, rotate=True))
        c.bind("<Shift-Button-5>", lambda e: self._preview_wheel(e, -1, rotate=True))
        c.bind("<Delete>", lambda e: self.delete_layer())
        c.bind("<BackSpace>", lambda e: self.delete_layer())
        for key, dx, dy in (("Left", -1, 0), ("Right", 1, 0), ("Up", 0, -1), ("Down", 0, 1)):
            c.bind(f"<{key}>", lambda e, dx=dx, dy=dy: self.nudge(dx * .005, dy * .005))
            c.bind(f"<Shift-{key}>", lambda e, dx=dx, dy=dy: self.nudge(dx * .03, dy * .03))

        ttk.Label(preview_outer, text="사진·영상의 저작권을 확인하세요. 제목에서 [대괄호]로 감싼 단어는 강조색으로 표시됩니다.",
                  style="Help.TLabel").pack(anchor="w", pady=(8, 6))
        export = ttk.Frame(preview_outer)
        export.pack(fill="x", pady=(2, 0))
        ttk.Button(export, text="JPEG 썸네일 저장", style="Accent.TButton",
                   command=lambda: self.export("jpg")).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(export, text="PNG 썸네일 저장", style="Accent.TButton",
                   command=lambda: self.export("png")).pack(side="left", fill="x", expand=True, padx=(5, 0))
        status = tk.Label(self.root, textvariable=self.status_var, anchor="w", padx=16, pady=6,
                          background="#101217", foreground=MUTED)
        status.pack(fill="x")

    def _build_background(self, panel):
        self._section(panel, "01  배경")
        row = ttk.Frame(panel)
        row.pack(fill="x", pady=2)
        ttk.Button(row, text="배경 이미지 열기", command=self.open_background).pack(side="left")
        ttk.Button(row, text="×", width=3, style="Small.TButton",
                   command=self.clear_background).pack(side="left", padx=(4, 8))
        ttk.Label(row, textvariable=self.bg_label, style="Help.TLabel").pack(side="left")
        self._slider(panel, "배경 밝기", self.brightness_var, 20, 150, "%", self.schedule_preview)
        self._slider(panel, "배경 흐림", self.blur_var, 0, 30, "", self.schedule_preview)
        self._slider(panel, "배경 채도 (0=흑백)", self.sat_var, 0, 200, "%", self.schedule_preview)

    def _build_layers(self, panel):
        self._section(panel, "02  사진 레이어 (개수 제한 없음)")
        ttk.Label(panel, text="목록 위쪽이 앞(위)에 보입니다. 미리보기에서 사진을 직접 끌어서 옮길 수 있어요.",
                  style="Help.TLabel", wraplength=370).pack(anchor="w", pady=(0, 6))
        listframe = ttk.Frame(panel)
        listframe.pack(fill="x")
        self.layer_list = tk.Listbox(listframe, height=7, activestyle="none", exportselection=False,
                                     background=FIELD, foreground=TEXT, selectbackground=ACCENT,
                                     selectforeground="#14161a", highlightthickness=1,
                                     highlightbackground=BORDER, highlightcolor=ACCENT, borderwidth=0,
                                     font=("", 10))
        self.layer_list.pack(side="left", fill="x", expand=True)
        self.layer_list.bind("<<ListboxSelect>>", self._on_list_select)
        side = ttk.Frame(listframe)
        side.pack(side="left", fill="y", padx=(6, 0))
        for text, cmd in (("▲ 앞으로", lambda: self.move_layer(1)), ("▼ 뒤로", lambda: self.move_layer(-1)),
                          ("복제", self.duplicate_layer), ("삭제", self.delete_layer)):
            ttk.Button(side, text=text, width=8, style="Small.TButton", command=cmd).pack(fill="x", pady=1)

        row = ttk.Frame(panel)
        row.pack(fill="x", pady=(8, 2))
        ttk.Button(row, text="＋ 사진 추가", command=self.add_photos).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="🎬 영상에서 캡처", command=self.open_video).pack(side="left", fill="x",
                                                                         expand=True, padx=(5, 0))
        ttk.Label(panel, text="강조 스티커 추가", style="Help.TLabel").pack(anchor="w", pady=(8, 2))
        srow = ttk.Frame(panel)
        srow.pack(fill="x")
        srow.columnconfigure((0, 1), weight=1)
        for i, kind in enumerate(STICKERS):
            ttk.Button(srow, text=kind, style="Small.TButton", command=lambda k=kind: self.add_sticker(k)
                       ).grid(row=i // 2, column=i % 2, sticky="ew", padx=1, pady=1)
        arow = ttk.Frame(panel)
        arow.pack(fill="x", pady=(8, 4))
        ttk.Label(arow, text="자동 배치").pack(side="left")
        ttk.Combobox(arow, textvariable=self.arrange_var, values=ARRANGEMENTS, state="readonly",
                     width=14).pack(side="left", padx=6)
        ttk.Button(arow, text="정렬하기", style="Small.TButton", command=self.arrange_now).pack(side="left")

        box = ttk.Frame(panel, padding=(0, 6, 0, 0))
        box.pack(fill="x")
        ttk.Label(box, textvariable=self.layer_title, font=("", 10, "bold")).pack(anchor="w", pady=(2, 2))
        on = self._layer_changed
        self._slider(box, "가로 위치", self.lx, -20, 120, "%", on)
        self._slider(box, "세로 위치", self.ly, -20, 120, "%", on)
        self._slider(box, "크기", self.lsize, 5, 150, "%", on)
        self._slider(box, "회전", self.lrot, -180, 180, "°", on)
        self._slider(box, "투명도", self.lop, 10, 100, "%", on)
        srow2 = ttk.Frame(box)
        srow2.pack(fill="x", pady=(6, 2))
        ttk.Label(srow2, text="모양").pack(side="left")
        shape = ttk.Combobox(srow2, textvariable=self.lshape, values=SHAPES, state="readonly", width=12)
        shape.pack(side="left", padx=6)
        shape.bind("<<ComboboxSelected>>", lambda e: on())
        checks = ttk.Frame(box)
        checks.pack(fill="x", pady=2)
        for text, var in (("테두리", self.loutline), ("그림자", self.lshadow), ("보이기", self.lvisible)):
            ttk.Checkbutton(checks, text=text, variable=var, command=on).pack(side="left", padx=(0, 10))
        ttk.Checkbutton(box, text="AI 누끼 (주인공만 정확하게 오리기)", variable=self.lai, command=on).pack(anchor="w")
        ttk.Checkbutton(box, text="단색 배경 제거 (간이 누끼)", variable=self.lremove, command=on).pack(anchor="w")

    def _build_text(self, panel):
        self._section(panel, "03  문구")
        ttk.Label(panel, text="메인 제목  —  [단어] 로 감싸면 강조색").pack(anchor="w")
        self.title_text = tk.Text(panel, height=3, width=34, font=("", 11), wrap="word", undo=True,
                                  background=FIELD, foreground=TEXT, insertbackground=TEXT,
                                  highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT,
                                  borderwidth=0, padx=6, pady=4)
        self.title_text.insert("1.0", "1,700년 잠든 [쿠샨 문자]\n해독의 반전")
        self.title_text.pack(fill="x", pady=(3, 8))
        self.title_text.bind("<KeyRelease>", lambda e: self.schedule_preview())
        ttk.Label(panel, text="태그 문구 (비우면 숨김)").pack(anchor="w")
        ttk.Entry(panel, textvariable=self.subtitle_var).pack(fill="x", pady=(3, 6))
        self.subtitle_var.trace_add("write", lambda *a: self.schedule_preview())
        self._combo(panel, "태그 위치", self.tag_pos_var, TAG_POSITIONS)
        frame = ttk.Frame(panel)
        frame.pack(fill="x", pady=(3, 4))
        ttk.Label(frame, text="정렬").pack(side="left", padx=(0, 12))
        for label, value in [("왼쪽", "left"), ("가운데", "center"), ("오른쪽", "right")]:
            ttk.Radiobutton(frame, text=label, variable=self.align_var, value=value,
                            command=self.schedule_preview).pack(side="left", padx=(0, 6))
        self._slider(panel, "제목 크기", self.font_var, 32, 175, "px", self.schedule_preview)
        self._slider(panel, "텍스트 세로 위치", self.text_y_var, 12, 92, "%", self.schedule_preview)

    def _build_design(self, panel):
        self._section(panel, "04  디자인")
        row = ttk.Frame(panel)
        row.pack(fill="x", pady=(0, 6))
        ttk.Label(row, text="원클릭 프리셋").pack(side="left")
        ttk.Combobox(row, textvariable=self.design_var, values=list(DESIGN_PRESETS), state="readonly",
                     width=13).pack(side="left", padx=6)
        ttk.Button(row, text="적용", style="Small.TButton", command=self.apply_design).pack(side="left")
        self._combo(panel, "색상 테마", self.theme_var, list(THEMES))
        self._combo(panel, "제목 효과", self.title_style_var, TITLE_STYLES)
        self._combo(panel, "글자 뒤 어둡게 (오버레이)", self.overlay_var, OVERLAYS)
        self._slider(panel, "오버레이 강도", self.darkness_var, 0, 100, "%", self.schedule_preview)
        self._combo(panel, "프레임 장식", self.frame_var, FRAMES)

    def _build_output(self, panel):
        self._section(panel, "05  출력")
        self._combo(panel, "출력 크기", self.preset_var, list(PRESETS))
        ttk.Button(panel, text="소스 코드 폴더 열기", command=self.open_source_folder).pack(fill="x", pady=(6, 0))

    def _section(self, panel, text):
        ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=(14, 10))
        ttk.Label(panel, text=text, style="Subhead.TLabel").pack(anchor="w", pady=(0, 6))

    def _combo(self, panel, text, var, values):
        ttk.Label(panel, text=text).pack(anchor="w")
        combo = ttk.Combobox(panel, textvariable=var, values=values, state="readonly")
        combo.pack(fill="x", pady=(3, 7))
        combo.bind("<<ComboboxSelected>>", lambda e: self.schedule_preview())

    def _slider(self, panel, text, var, lo, hi, unit, on_change):
        line = ttk.Frame(panel)
        line.pack(fill="x", pady=(4, 0))
        ttk.Label(line, text=text).pack(side="left")
        readout = ttk.Label(line, text="", width=7, anchor="e", style="Help.TLabel")
        readout.pack(side="right")

        def refresh(*_):
            try:
                readout.configure(text=f"{round(float(var.get()))}{unit}")
            except (tk.TclError, ValueError):
                return
            if not self._syncing:
                on_change()
        var.trace_add("write", refresh)
        readout.configure(text=f"{round(var.get())}{unit}")
        ttk.Scale(panel, from_=lo, to=hi, variable=var).pack(fill="x")

    def _bind_keys(self):
        self.root.bind_all("<Control-v>", self._paste_shortcut)
        self.root.bind_all("<Control-V>", self._paste_shortcut)
        self.root.bind_all("<Control-d>", lambda e: self.duplicate_layer() if not self._typing(e) else None)

    @staticmethod
    def _typing(event) -> bool:
        return isinstance(event.widget, (tk.Text, tk.Entry, ttk.Entry))

    # ─────────────────────────────────────────────── 배경
    def open_background(self):
        path = filedialog.askopenfilename(parent=self.root, title="배경 이미지 선택", filetypes=IMAGE_FILTER)
        if path:
            try:
                self._set_background(load_image(path), Path(path).name)
            except Exception as exc:
                messagebox.showerror("이미지 열기 실패", f"이미지를 불러오지 못했습니다.\n{exc}", parent=self.root)

    def _set_background(self, img: Image.Image, name: str):
        self.background = img.convert("RGBA")
        self.bg_label.set(name if len(name) < 26 else name[:23] + "…")
        self.status_var.set(f"배경: {img.width}×{img.height} 적용")
        self.schedule_preview()

    def clear_background(self):
        self.background = None
        self.bg_label.set("내장 배경")
        self.schedule_preview()

    # ─────────────────────────────────────────────── 레이어 관리
    def _size(self):
        return PRESETS[self.preset_var.get()]

    def _new_layer(self, img: Image.Image, name: str, kind="photo", **kw) -> PhotoLayer:
        layer = PhotoLayer(img.convert("RGBA"), name=name, kind=kind, **kw)
        if kind == "photo" and not kw:
            w, h = self._size()
            k = sum(1 for l in self.layers if l.kind == "photo")
            aspect = img.width / max(1, img.height)
            layer.height = min(.6, .55 * w / (aspect * h))
            layer.x, layer.y = min(.85, .3 + .08 * k), min(.75, .4 + .05 * k)
        return layer

    def _insert(self, layer: PhotoLayer):
        # 스티커는 맨 위, 사진은 스티커 아래 가장 위에
        if layer.kind == "sticker":
            self.layers.append(layer)
        else:
            idx = len(self.layers)
            while idx > 0 and self.layers[idx - 1].kind == "sticker":
                idx -= 1
            self.layers.insert(idx, layer)
        return self.layers.index(layer)

    def add_photos(self):
        paths = filedialog.askopenfilenames(parent=self.root, title="사진 선택 (여러 장 가능)", filetypes=IMAGE_FILTER)
        if not paths:
            return
        added, failed = 0, []
        last = None
        for p in paths:
            try:
                layer = self._new_layer(load_image(p), Path(p).name)
                layer.src = str(p)
                last = self._insert(layer)
                added += 1
            except Exception as exc:
                failed.append(f"{Path(p).name}: {exc}")
        self._after_add(last, f"사진 {added}장 추가")
        if failed:
            messagebox.showwarning("일부 사진을 열지 못했습니다", "\n".join(failed[:8]), parent=self.root)

    def _after_add(self, index, message):
        if index is None:
            return
        if self.auto_arrange:
            arrange_layers(self.layers, self.arrange_var.get(), self._size())
        self.refresh_list(select=index)
        hint = "" if self.auto_arrange else "  ('정렬하기'로 다시 자동 배치 가능)"
        self.status_var.set(message + hint)
        self.schedule_preview()

    def add_sticker(self, kind: str):
        _, accent = THEMES.get(self.theme_var.get(), THEMES["골드"])
        color = (235, 35, 35) if kind in ("빨간 원", "화살표") or sum(accent) > 690 else accent
        height = {"빨간 원": .36, "화살표": .16}.get(kind, .22)
        layer = self._new_layer(make_sticker(kind, color), kind, kind="sticker",
                                x=.5, y=.42, height=height, sticker=kind)
        idx = self._insert(layer)
        self.refresh_list(select=idx)
        self.status_var.set(f"스티커 '{kind}' 추가 — 미리보기에서 끌어서 위치를 잡으세요. (회전 슬라이더로 방향 조절)")
        self.schedule_preview()

    def arrange_now(self):
        if not any(l.kind == "photo" for l in self.layers):
            self.status_var.set("정렬할 사진이 없습니다.")
            return
        arrange_layers(self.layers, self.arrange_var.get(), self._size())
        self.auto_arrange = True
        self._sync_props()
        self.status_var.set(f"'{self.arrange_var.get()}' 방식으로 사진을 다시 배치했습니다.")
        self.schedule_preview()

    def delete_layer(self):
        if self.selected is None:
            return
        removed = self.layers.pop(self.selected)
        nxt = min(self.selected, len(self.layers) - 1) if self.layers else None
        self.refresh_list(select=nxt)
        self.status_var.set(f"'{removed.name}' 삭제")
        self.schedule_preview()

    def duplicate_layer(self):
        if self.selected is None:
            return
        twin = self.layers[self.selected].copy()
        twin.x, twin.y = min(1.1, twin.x + .04), min(1.1, twin.y + .04)
        self.layers.insert(self.selected + 1, twin)
        self.auto_arrange = False
        self.refresh_list(select=self.selected + 1)
        self.schedule_preview()

    def move_layer(self, step: int):
        i = self.selected
        if i is None:
            return
        j = i + step
        if not 0 <= j < len(self.layers):
            return
        self.layers[i], self.layers[j] = self.layers[j], self.layers[i]
        self.refresh_list(select=j)
        self.schedule_preview()

    def nudge(self, dx, dy):
        if self.selected is None:
            return "break"
        layer = self.layers[self.selected]
        layer.x += dx
        layer.y += dy
        self.auto_arrange = False
        self._sync_props()
        self.schedule_preview(30)
        return "break"

    def refresh_list(self, select: int | None = None):
        self.layer_list.delete(0, "end")
        n = len(self.layers)
        for row in range(n):
            layer = self.layers[n - 1 - row]
            eye = "●" if layer.visible else "○"
            icon = "◆" if layer.kind == "sticker" else "▣"
            self.layer_list.insert("end", f" {eye}  {icon}  {layer.name}")
            if not layer.visible:
                self.layer_list.itemconfigure(row, foreground=MUTED)
        self.select_layer(select)

    def select_layer(self, index: int | None):
        self.selected = index if index is not None and 0 <= index < len(self.layers) else None
        self.layer_list.selection_clear(0, "end")
        if self.selected is not None:
            row = len(self.layers) - 1 - self.selected
            self.layer_list.selection_set(row)
            self.layer_list.see(row)
        self._sync_props()
        self.draw_preview()

    def _on_list_select(self, _):
        sel = self.layer_list.curselection()
        if sel:
            self.select_layer(len(self.layers) - 1 - sel[0])

    def _sync_props(self):
        """선택한 레이어 값을 슬라이더에 반영 (반영 중에는 미리보기 갱신 안 함)."""
        self._syncing = True
        try:
            if self.selected is None:
                self.layer_title.set("선택된 사진 없음  —  목록이나 미리보기에서 사진을 클릭하세요")
                return
            l = self.layers[self.selected]
            self.layer_title.set(f"선택: {l.name if len(l.name) < 30 else l.name[:27] + '…'}")
            self.lx.set(round(l.x * 100, 1))
            self.ly.set(round(l.y * 100, 1))
            self.lsize.set(round(l.height * 100, 1))
            self.lrot.set(round(l.rotation, 1))
            self.lop.set(l.opacity)
            self.lshape.set(l.shape)
            self.loutline.set(l.outline)
            self.lshadow.set(l.shadow)
            self.lremove.set(l.remove_bg)
            self.lai.set(l.ai_cutout)
            self.lvisible.set(l.visible)
        finally:
            self._syncing = False

    def _layer_changed(self):
        if self._syncing or self.selected is None:
            return
        l = self.layers[self.selected]
        try:
            l.x, l.y = self.lx.get() / 100, self.ly.get() / 100
            l.height = max(.05, self.lsize.get() / 100)
            l.rotation = self.lrot.get()
            l.opacity = round(self.lop.get())
        except tk.TclError:
            return
        visible_changed = l.visible != self.lvisible.get()
        l.shape, l.outline, l.shadow = self.lshape.get(), self.loutline.get(), self.lshadow.get()
        l.remove_bg, l.visible = self.lremove.get(), self.lvisible.get()
        if l.ai_cutout != self.lai.get():
            l.ai_cutout = self.lai.get()
            l._cache.clear()
        self.auto_arrange = False
        if visible_changed:
            self.refresh_list(select=self.selected)
        self.schedule_preview(40)

    # ─────────────────────────────────────────────── 붙여넣기 / 동영상
    def _paste_shortcut(self, event):
        if self._typing(event):
            return None  # 글자 입력칸에서는 일반 붙여넣기
        self.paste_clipboard()
        return "break"

    def paste_clipboard(self):
        try:
            from PIL import ImageGrab
            data = ImageGrab.grabclipboard()
        except Exception as exc:
            self.status_var.set(f"클립보드를 읽을 수 없습니다: {exc}")
            return
        images = []
        if isinstance(data, Image.Image):
            images.append((data, "붙여넣은 이미지"))
        elif isinstance(data, list):
            for p in data:
                try:
                    images.append((load_image(p), Path(p).name))
                except Exception:
                    pass
        if not images:
            self.status_var.set("클립보드에 이미지가 없습니다. (화면 캡처 후 Ctrl+V 하거나, 탐색기에서 파일을 복사하세요)")
            return
        last = None
        for img, name in images:
            last = self._insert(self._new_layer(img, name))
        self._after_add(last, f"클립보드에서 {len(images)}장 추가")

    def open_video(self, start: float | None = None):
        if self.capture_dialog is not None and self.capture_dialog.winfo_exists():
            self.capture_dialog.lift()
            self.capture_dialog.focus_force()
            if start is not None:
                self.capture_dialog.seek(start)
            return
        vid = self.meta.get("video", "")
        if vid and Path(vid).is_file():          # 프로그램에서 연 영상이면 그 영상을 바로
            path = vid
        else:
            path = filedialog.askopenfilename(parent=self.root, title="동영상 선택", filetypes=VIDEO_FILTER,
                                              initialdir=str(Path(vid).parent) if vid else None)
        if not path:
            return
        try:
            self.capture_dialog = VideoCaptureDialog(self.root, path, self.on_video_capture, start=start or 0.0)
            self.capture_dialog.transient(self.root)
            self.capture_dialog.focus_force()
        except Exception as exc:
            messagebox.showerror("동영상 열기 실패", f"동영상을 열지 못했습니다.\n{exc}", parent=self.root)
            self.capture_dialog = None

    def on_video_capture(self, frame: Image.Image, target: str):
        name = f"영상 캡처 {frame.width}×{frame.height}"
        if target == "배경":
            self._set_background(frame, name)
            return
        if target == "선택한 사진 교체":
            if self.selected is None:
                raise ValueError("교체할 사진을 메인 창에서 먼저 선택하세요.")
            layer = self.layers[self.selected]
            layer.image, layer.name = frame.convert("RGBA"), name
            layer._cache.clear()
            self.refresh_list(select=self.selected)
            self.schedule_preview()
            return
        self._after_add(self._insert(self._new_layer(frame, name)), f"{name} 추가")

    # ─────────────────────────────────────────────── 디자인 프리셋
    def apply_design(self):
        preset = DESIGN_PRESETS.get(self.design_var.get())
        if not preset:
            return
        mapping = {"theme": self.theme_var, "title_style": self.title_style_var, "overlay": self.overlay_var,
                   "darkness": self.darkness_var, "align": self.align_var, "tag_position": self.tag_pos_var,
                   "frame": self.frame_var, "text_y": self.text_y_var, "bg_saturation": self.sat_var,
                   "bg_blur": self.blur_var}
        self._syncing = True
        try:
            for key, value in preset.items():
                mapping[key].set(value)
        finally:
            self._syncing = False
        self.status_var.set(f"디자인 프리셋 '{self.design_var.get()}' 적용")
        self.schedule_preview()

    # ─────────────────────────────────────────────── 렌더링 / 미리보기
    def _options(self, size=None) -> RenderOptions:
        return RenderOptions(
            size=size or self._size(),
            title=self.title_text.get("1.0", "end-1c"), subtitle=self.subtitle_var.get(),
            theme=self.theme_var.get(), align=self.align_var.get(),
            font_size=round(self.font_var.get()), text_y=round(self.text_y_var.get()),
            brightness=round(self.brightness_var.get()), darkness=round(self.darkness_var.get()),
            title_style=self.title_style_var.get(), overlay=self.overlay_var.get(),
            frame=self.frame_var.get(), tag_position=self.tag_pos_var.get(),
            bg_blur=round(self.blur_var.get()), bg_saturation=round(self.sat_var.get()),
            layers=self.layers,
        )

    def schedule_preview(self, delay: int = 140):
        if self.preview_job is not None:
            self.root.after_cancel(self.preview_job)
        self.preview_job = self.root.after(delay, self.update_preview)

    def _preview_size(self):
        """미리보기는 화면 크기에 맞춘 해상도로 그려서 빠르게 (저장은 원본 해상도)."""
        w, h = self._size()
        cw = max(200, self.preview_canvas.winfo_width() - 8)
        ch = max(200, self.preview_canvas.winfo_height() - 8)
        scale = min(1.0, cw / w, ch / h)
        pw, ph = max(200, round(w * scale)), max(200, round(h * scale))
        return pw, ph

    def update_preview(self):
        self.preview_job = None
        try:
            self.preview_image, self.preview_bounds = render_with_bounds(self._options(self._preview_size()),
                                                                         self.background)
            w, h = self._size()
            self.dimension_label.configure(text=f"출력 {w} × {h}")
            self.draw_preview()
        except Exception as exc:
            self.status_var.set(f"미리보기 오류: {exc}")

    def draw_preview(self):
        c = self.preview_canvas
        c.delete("all")
        if self.preview_image is None:
            return
        cw, ch = max(1, c.winfo_width()), max(1, c.winfo_height())
        im = self.preview_image
        scale = min((cw - 8) / im.width, (ch - 8) / im.height, 1.0)
        nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
        shown = im if (nw, nh) == im.size else im.resize((nw, nh), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(shown)
        ox, oy = (cw - nw) // 2, (ch - nh) // 2
        self.preview_geom = (ox, oy, scale)
        c.create_image(ox, oy, anchor="nw", image=self.preview_photo)
        if self.selected is not None and self.selected < len(self.preview_bounds):
            b = self.preview_bounds[self.selected]
            if b:
                x1, y1, x2, y2 = (ox + b[0] * scale, oy + b[1] * scale, ox + b[2] * scale, oy + b[3] * scale)
                c.create_rectangle(x1, y1, x2, y2, outline="#000000", width=3)
                c.create_rectangle(x1, y1, x2, y2, outline=ACCENT, width=2, dash=(6, 4))

    def _hit(self, event) -> tuple[int | None, float, float]:
        ox, oy, scale = self.preview_geom
        ix, iy = (event.x - ox) / scale, (event.y - oy) / scale
        for i in range(len(self.preview_bounds) - 1, -1, -1):
            b = self.preview_bounds[i]
            if b and b[0] <= ix <= b[2] and b[1] <= iy <= b[3]:
                return i, ix, iy
        return None, ix, iy

    def _preview_press(self, event):
        self.preview_canvas.focus_set()
        idx, ix, iy = self._hit(event)
        if idx is None:
            return
        if idx != self.selected:
            self.select_layer(idx)
        l = self.layers[idx]
        self.drag = (ix, iy, l.x, l.y)

    def _preview_drag(self, event):
        if not self.drag or self.selected is None or self.preview_image is None:
            return
        ox, oy, scale = self.preview_geom
        ix, iy = (event.x - ox) / scale, (event.y - oy) / scale
        sx, sy, lx, ly = self.drag
        l = self.layers[self.selected]
        l.x = lx + (ix - sx) / self.preview_image.width
        l.y = ly + (iy - sy) / self.preview_image.height
        self.auto_arrange = False
        self._sync_props()
        self.schedule_preview(15)

    def _preview_release(self, _):
        if self.drag:
            self.drag = None
            self.schedule_preview(10)

    def _preview_hover(self, event):
        idx, _, _ = self._hit(event)
        self.preview_canvas.configure(cursor="fleur" if idx is not None else "")

    def _preview_wheel(self, event, direction: int | None = None, rotate=False):
        if self.selected is None:
            return
        d = direction if direction is not None else (1 if event.delta > 0 else -1)
        l = self.layers[self.selected]
        if rotate:
            l.rotation = max(-180, min(180, l.rotation + 3 * d))
        else:
            l.height = max(.05, min(1.5, l.height * (1.06 if d > 0 else 1 / 1.06)))
        self.auto_arrange = False
        self._sync_props()
        self.schedule_preview(30)
        return "break"

    # ─────────────────────────────────────────────── 저장 / 기타
    def export(self, format_name: str):
        suffix = ".jpg" if format_name == "jpg" else ".png"
        path = filedialog.asksaveasfilename(
            parent=self.root, title="썸네일 저장", defaultextension=suffix,
            initialfile="dreamart_thumbnail" + suffix,
            filetypes=[("JPEG 이미지", "*.jpg") if format_name == "jpg" else ("PNG 이미지", "*.png")],
        )
        if not path:
            return
        try:
            image, _ = render_with_bounds(self._options(), self.background)  # 원본 해상도로 다시 그림
            save_thumbnail(image, path)
            size_kb = Path(path).stat().st_size / 1024
            self.status_var.set(f"저장 완료: {Path(path).name} ({size_kb:,.0f} KB)")
            if suffix == ".jpg" and size_kb > 2048:
                messagebox.showwarning("저장 완료 / 용량 확인", f"{path}\n\nJPEG 파일이 2 MB를 초과했습니다.", parent=self.root)
            else:
                messagebox.showinfo("저장 완료", f"{path}\n\n해상도: {image.width}×{image.height}\n파일 크기: {size_kb:,.0f} KB",
                                    parent=self.root)
        except Exception as exc:
            messagebox.showerror("저장 실패", str(exc), parent=self.root)

    def open_source_folder(self):
        try:
            if sys.platform == "win32":
                os.startfile(str(ROOT_DIR))
            else:
                import subprocess
                subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(ROOT_DIR)])
        except Exception as exc:
            messagebox.showinfo("소스 코드 위치", f"소스 코드 폴더:\n{ROOT_DIR}\n\n{exc}", parent=self.root)

    # ─────────────────────────────────────────────── 프로그램과 연결 (불러오기 / 유튜브 썸네일로 저장)
    @staticmethod
    def find_state(target: str) -> tuple[str, dict]:
        """콘텐츠 폴더·편집 json·영상·썸네일 경로 → (편집 json 경로, 상태). 편집 json 이 없는 예전 영상은 프로젝트에서 기본 상태를 만듦"""
        p = Path(target)
        if p.is_dir():
            js = [x for x in glob.glob(str(p / "*_썸네일_편집.json")) if "_쇼츠_" not in Path(x).name]
            if js:
                p = Path(js[0])
            else:
                projs = [x for x in glob.glob(str(p / "*_프로젝트.json")) if "_쇼츠_" not in Path(x).name]
                if not projs:
                    raise FileNotFoundError("이 폴더에서 영상 프로젝트(_프로젝트.json)를 못 찾았어요.")
                p = Path(projs[0][: -len("_프로젝트.json")] + "_썸네일_편집.json")
        elif p.suffix.lower() != ".json" or p.name.endswith("_프로젝트.json"):
            base = re.sub(r"(_썸네일_유튜브\.jpg|_프로젝트\.json|\.mp4)$", "", str(p))
            p = Path(base + "_썸네일_편집.json")
        if p.is_file():
            return str(p), json.loads(p.read_text(encoding="utf-8"))
        base = str(p)[: -len("_썸네일_편집.json")]           # 예전 영상: 프로젝트의 첫 사진 + 제목으로 시작
        proj = json.loads(Path(base + "_프로젝트.json").read_text(encoding="utf-8"))
        root_dir = ROOT_DIR
        photos = [m.group(1).strip() for m in re.finditer(r"\[사진:\s*([^|\]]+)", proj.get("story", ""))]
        photos = [x if os.path.isabs(x) else str(root_dir / x) for x in photos]
        opening = next((x for x in photos if Path(x).is_file()), "")
        opts = RenderOptions(title=str(proj.get("title", "")), subtitle="", **{k: v for k, v in DESIGN_PRESETS["미스터리 다큐"].items()})
        d = TE.state_dict(opts, opening, design="미스터리 다큐")
        d.update(base=base, video=base + ".mp4", out=base + "_썸네일_유튜브.jpg", opening=opening, title=proj.get("title", ""))
        return str(p), d

    def load_program_state(self, target: str):
        try:
            self.state_path, d = self.find_state(target)
            opts, bg = TE.load_state(d)
        except Exception as exc:
            messagebox.showerror("불러오기 실패", str(exc), parent=self.root)
            return
        self.meta = {k: d.get(k, "") for k in ("base", "video", "out", "opening", "title")}
        size = tuple(opts.size)
        key = next((k for k, v in PRESETS.items() if tuple(v) == size), None)
        if key is None:
            key = f"원래 크기 {size[0]}×{size[1]}"
            PRESETS[key] = size
        self._syncing = True
        try:
            self.preset_var.set(key)
            self.theme_var.set(opts.theme)
            self.title_style_var.set(opts.title_style)
            self.overlay_var.set(opts.overlay)
            self.frame_var.set(opts.frame)
            self.tag_pos_var.set(opts.tag_position)
            self.align_var.set(opts.align)
            self.font_var.set(opts.font_size)
            self.text_y_var.set(opts.text_y)
            self.brightness_var.set(opts.brightness)
            self.darkness_var.set(opts.darkness)
            self.blur_var.set(opts.bg_blur)
            self.sat_var.set(opts.bg_saturation)
            self.subtitle_var.set(opts.subtitle)
            if d.get("design") in DESIGN_PRESETS:
                self.design_var.set(d["design"])
        finally:
            self._syncing = False
        self.title_text.delete("1.0", "end")
        self.title_text.insert("1.0", opts.title)
        self.layers = list(opts.layers)
        self.auto_arrange = False
        if bg is not None:
            self._set_background(bg, Path(d.get("background", "")).name or "배경")
        self.refresh_list(select=None)
        name = Path(self.meta.get("base") or target).name
        self.root.title(f"썸네일 편집기 — {name}")
        self.status_var.set(f"불러옴: {name}  ·  다듬은 뒤 '💾 유튜브 썸네일로 저장'을 누르면 {Path(self.meta.get('out') or '').name} 가 바뀝니다")
        self.schedule_preview(50)

    def open_folder_dialog(self):
        d = filedialog.askdirectory(parent=self.root, title="영상 콘텐츠 폴더 선택 (output\\장문\\00xx_제목)",
                                    initialdir=str(ROOT_DIR / "output" / "장문"))
        if d:
            self.load_program_state(d)

    def save_to_program(self):
        out = self.meta.get("out")
        if not out:
            self.export("jpg")         # 프로그램에서 연 게 아니면 일반 저장
            return
        try:
            image, _ = render_with_bounds(self._options(), self.background)
            outp = Path(out)
            old = outp.with_name(outp.stem + "_이전.jpg")
            if outp.is_file() and not old.exists():          # 처음 바꿀 때만 원래 것을 남겨 둠
                shutil.copyfile(outp, old)
            save_thumbnail(image, outp)
            base = self.meta.get("base") or str(outp)[: -len("_썸네일_유튜브.jpg")]
            bg_path = ""
            if self.background is not None:
                bg_path = str(Path(base + "_썸네일_편집") / "배경.png")
                Path(bg_path).parent.mkdir(parents=True, exist_ok=True)
                self.background.convert("RGB").save(bg_path)
            TE.save_state(self.state_path or base + "_썸네일_편집.json", self._options(), bg_path,
                          image_dir=base + "_썸네일_편집", **self.meta,
                          design=self.design_var.get())
            kb = outp.stat().st_size / 1024
            self.status_var.set(f"저장 완료: {outp.name} ({kb:,.0f} KB) · 편집 상태도 저장 (다음에 그대로 다시 열림)")
            messagebox.showinfo("유튜브 썸네일 저장", f"{outp}\n\n{image.width}×{image.height} · {kb:,.0f} KB"
                                + (f"\n(예전 썸네일: {old.name})" if old.exists() else ""), parent=self.root)
        except Exception as exc:
            messagebox.showerror("저장 실패", str(exc), parent=self.root)

    def close(self):
        if self.capture_dialog is not None and self.capture_dialog.winfo_exists():
            self.capture_dialog.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ThumbnailMakerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    args = [a for a in sys.argv[1:] if a.strip()]
    if args:                       # 썸네일_편집기.bat 에 폴더·json 을 끌어다 놓으면 그 영상의 썸네일을 바로 엶
        root.after(300, lambda: app.load_program_state(args[0]))
    root.mainloop()


if __name__ == "__main__":
    main()
