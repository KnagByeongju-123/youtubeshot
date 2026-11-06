"""블록 애니 공용 부품 — 블록(복셀)으로 캐릭터를 만들고 블렌더 장면에 올림, 캐릭터 시트(앞·옆·옆·뒤) 그리기

모델 = 부위(part) 여러 개. 부위마다 '돌아가는 중심점(pivot)'과 블록 목록 {(x,y,z): 색이름} 이 있음.
부위는 부모-자식으로 이어져서(엉덩이 → 몸통 → 머리·팔), 부위를 돌리면 걷기·헤엄치기 같은 움직임이 됨.
좌표: x = 캐릭터의 오른쪽(+)·왼쪽(-), y = 뒤(+)·앞(-), z = 위. 캐릭터는 -y 쪽(앞)을 봄. 블록 한 칸 = 1.
실행 환경: .blender_venv (bpy 5.0.1), 화면 없이 xvfb-run 으로.
"""
import math

import bpy

BLOCK = 0.94          # 블록 크기(1보다 조금 작게 → 블록 사이 어두운 틈이 생겨 블록 느낌)


def hex_lin(h):
    """'#rrggbb'(화면 색) → 블렌더가 쓰는 선형 색"""
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


class Part:
    def __init__(self, name, pivot=(0, 0, 0), parent=None):
        self.name, self.pivot, self.parent = name, pivot, parent
        self.vox = {}

    def box(self, x0, x1, y0, y1, z0, z1, col):
        """x0~x1, y0~y1, z0~z1 (양끝 포함) 를 col 색 블록으로 채움"""
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.vox[(x, y, z)] = col

    def set(self, x, y, z, col):
        self.vox[(x, y, z)] = col

    def rm(self, x, y, z):
        self.vox.pop((x, y, z), None)


class Model:
    """parts: 이름 → Part. palette: 색이름 → '#rrggbb'. scale: 블록 한 칸의 실제 크기(장면 단위)"""
    def __init__(self, name, palette, scale=1.0):
        self.name, self.palette, self.scale = name, palette, scale
        self.parts = {}
        self.glow = set()      # 스스로 빛나는 색이름 (해파리·발광 물고기)

    def part(self, name, pivot=(0, 0, 0), parent=None):
        p = Part(name, pivot, parent)
        self.parts[name] = p
        return p

    def all_vox(self):
        for p in self.parts.values():
            for k, c in p.vox.items():
                yield k, c

    def bounds(self):
        ks = [k for k, _ in self.all_vox()]
        lo = [min(k[i] for k in ks) - 0.5 for i in range(3)]
        hi = [max(k[i] for k in ks) + 0.5 for i in range(3)]
        return [v * self.scale for v in lo], [v * self.scale for v in hi]


_MATS = {}


def material(key, hexcol, glow=False):
    k = (key, hexcol)
    if k in _MATS and _MATS[k].name in bpy.data.materials:
        return _MATS[k]
    m = bpy.data.materials.new(f"{key}")
    rgb = hex_lin(hexcol)
    m.diffuse_color = (*rgb, 1)
    m.roughness = 0.8
    m.metallic = 0.0
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = (*rgb, 1)
        if glow:
            b.inputs["Emission Color"].default_value = (*rgb, 1)
            b.inputs["Emission Strength"].default_value = 3.0
    _MATS[k] = m
    return m


def _cube_mesh(name, vox, palette, glow, offset):
    """블록 목록 → 메시 하나 (색마다 재질 칸). 모든 면을 남김(틈으로 옆면이 보여 블록 선이 생김)"""
    keys = sorted(set(vox.values()))
    kidx = {k: i for i, k in enumerate(keys)}
    h = BLOCK / 2
    corners = [(-h, -h, -h), (h, -h, -h), (h, h, -h), (-h, h, -h), (-h, -h, h), (h, -h, h), (h, h, h), (-h, h, h)]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    verts, faces, fmat = [], [], []
    ox, oy, oz = offset
    for (x, y, z), c in vox.items():
        # 속에 묻힌 블록도 남김: 빼면 블록 틈(특히 마디와 마디 사이)으로 뒤가 비쳐 흰 줄이 보임
        base = len(verts)
        for cx, cy, cz in corners:
            verts.append((x - ox + cx, y - oy + cy, z - oz + cz))
        for q in quads:
            faces.append(tuple(base + i for i in q))
            fmat.append(kidx[c])
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    for k in keys:
        me.materials.append(material(k, palette[k], k in glow))
    me.polygons.foreach_set("material_index", fmat)
    me.update()
    return me


def build(model, collection=None, location=(0, 0, 0)):
    """모델을 장면에 올림. 돌려주는 것: (뿌리 빈 물체, {부위이름: 부위 물체})"""
    col = collection or bpy.context.scene.collection
    root = bpy.data.objects.new(model.name, None)
    col.objects.link(root)
    root.location = location
    root.scale = (model.scale,) * 3
    objs = {}
    order, seen = [], set()

    def visit(n):
        if n in seen:
            return
        p = model.parts[n]
        if p.parent:
            visit(p.parent)
        seen.add(n)
        order.append(n)
    for n in model.parts:
        visit(n)
    for n in order:
        p = model.parts[n]
        if p.vox:
            me = _cube_mesh(f"{model.name}.{n}", p.vox, model.palette, model.glow, p.pivot)
            o = bpy.data.objects.new(f"{model.name}.{n}", me)
        else:
            o = bpy.data.objects.new(f"{model.name}.{n}", None)
        col.objects.link(o)
        if p.parent:
            pp = model.parts[p.parent].pivot
            o.parent = objs[p.parent]
            o.location = (p.pivot[0] - pp[0], p.pivot[1] - pp[1], p.pivot[2] - pp[2])
        else:
            o.parent = root
            o.location = p.pivot
        objs[n] = o
    return root, objs


# ---------------------------------------------------------------- 장면 준비
def new_scene(bg="#ffffff", w=1280, h=720, fps=24):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()
    sc = bpy.context.scene
    r = sc.render
    r.engine = "BLENDER_WORKBENCH"
    r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
    r.fps = fps
    r.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.exposure = 0.45
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "MATERIAL"
    sh.show_shadows = True
    sh.shadow_intensity = 0.35
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sh.cavity_ridge_factor = 0.6
    sh.cavity_valley_factor = 1.2
    sh.curvature_ridge_factor = 0.8
    sh.curvature_valley_factor = 1.0
    sh.show_specular_highlight = False
    sc.display.render_aa = "8"
    sc.display.light_direction = (0.45, -0.35, 0.82)
    wd = bpy.data.worlds.new("w")
    sc.world = wd
    wd.color = hex_lin(bg)
    r.image_settings.file_format = "PNG"
    return sc


def ortho_camera(sc, view, center, extent, margin=1.12):
    """view: front(앞), left(왼옆), right(오른옆), back(뒤), extent = 보이는 (가로, 세로)"""
    cam = bpy.data.cameras.new("cam")
    cam.type = "ORTHO"
    co = bpy.data.objects.new("cam", cam)
    sc.collection.objects.link(co)
    sc.camera = co
    d = 500
    cx, cy, cz = center
    pos = {"front": ((cx, cy - d, cz), (math.pi / 2, 0, 0)),
           "back": ((cx, cy + d, cz), (math.pi / 2, 0, math.pi)),
           "right": ((cx + d, cy, cz), (math.pi / 2, 0, math.pi / 2)),
           "left": ((cx - d, cy, cz), (math.pi / 2, 0, -math.pi / 2))}[view]
    co.location, co.rotation_euler = pos
    cam.clip_end = 2000
    cam.ortho_scale = max(extent) * margin
    return co


def render_views(model_fn, out_prefix, px_per_unit=40, views=("front", "right", "left", "back")):
    """모델을 네 방향에서 정사영으로 그려 PNG 4장. 돌려주는 것: 파일 목록"""
    files = []
    for v in views:
        sc = new_scene("#ffffff")
        m = model_fn()
        build(m)
        lo, hi = m.bounds()
        c = [(lo[i] + hi[i]) / 2 for i in range(3)]
        ext_w = (hi[0] - lo[0]) if v in ("front", "back") else (hi[1] - lo[1])
        ext_h = hi[2] - lo[2]
        mg = 1.12
        sc.render.resolution_x = max(64, int(ext_w * px_per_unit * mg))
        sc.render.resolution_y = max(64, int(ext_h * px_per_unit * mg))
        cam = ortho_camera(sc, v, c, (ext_w, ext_h))
        cam.data.ortho_scale = max(ext_w, ext_h) * mg
        sc.render.filepath = f"{out_prefix}_{v}.png"
        bpy.ops.render.render(write_still=True)
        files.append(sc.render.filepath)
    return files


def compose_sheet(files, out, title, labels=("앞", "옆(오른쪽)", "옆(왼쪽)", "뒤"), max_h=900):
    """네 방향 그림을 흰 바탕 한 장에 나란히 + 아래 이름표"""
    from PIL import Image, ImageDraw, ImageFont
    ims = [Image.open(f).convert("RGB") for f in files]
    H = max(i.height for i in ims)
    k = min(1.0, max_h / H)
    ims = [i.resize((max(1, int(i.width * k)), max(1, int(i.height * k))), Image.NEAREST) for i in ims]
    H = max(i.height for i in ims)
    gap, top, bot = 40, 70, 60
    W = sum(i.width for i in ims) + gap * (len(ims) + 1)
    if W > (H + top + bot) * 3.2 and len(ims) == 4:     # 긴 동물(고래·배)은 2줄로: 위 = 옆 둘, 아래 = 앞·뒤
        return _sheet_2rows(ims, out, title, labels, gap, top, bot)
    sheet = Image.new("RGB", (W, H + top + bot), "white")
    d = ImageDraw.Draw(sheet)
    try:
        ft = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", 34)
        fl = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", 24)
    except OSError:
        ft = fl = ImageFont.load_default()
    d.text((gap, 18), title, fill=(30, 30, 30), font=ft)
    x = gap
    for im, lb in zip(ims, labels):
        sheet.paste(im, (x, top + (H - im.height)))
        d.text((x + im.width // 2, top + H + 14), lb, fill=(90, 90, 90), font=fl, anchor="ma")
        x += im.width + gap
    sheet.save(out, quality=95)
    return out


def _sheet_2rows(ims, out, title, labels, gap, top, bot):
    from PIL import Image, ImageDraw, ImageFont
    f, r, l, b = ims
    rows = [[(r, labels[1]), (l, labels[2])], [(f, labels[0]), (b, labels[3])]]
    rw = [sum(i.width for i, _ in row) + gap * 3 for row in rows]
    rh = [max(i.height for i, _ in row) for row in rows]
    W, H = max(rw), top + sum(h + bot for h in rh)
    sheet = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(sheet)
    ft = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", 34)
    fl = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", 24)
    d.text((gap, 18), title, fill=(30, 30, 30), font=ft)
    y = top
    for row, h in zip(rows, rh):
        x = gap
        for im, lb in row:
            sheet.paste(im, (x, y + h - im.height))
            d.text((x + im.width // 2, y + h + 14), lb, fill=(90, 90, 90), font=fl, anchor="ma")
            x += im.width + gap
        y += h + bot
    sheet.save(out, quality=95)
    return out
