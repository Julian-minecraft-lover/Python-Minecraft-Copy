from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from perlin_noise import PerlinNoise
import os
from PIL import Image

app = Ursina(borderless=False, fullscreen=False, title='Minecraft 0.0.3')
scene.ambient_light = color.rgb(200, 200, 200)

# ---------- 纹理配置 ----------
BLOCK_TEXTURES = {
    'grass': {
        'front': 'textures/grass_block_side.png',
        'back':  'textures/grass_block_side.png',
        'left':  'textures/grass_block_side.png',
        'right': 'textures/grass_block_side.png',
        'top':   'textures/grass_block_top.png',
        'bottom':'textures/dirt.png'
    },
    'dirt': {
        'front': 'textures/dirt.png',
        'back':  'textures/dirt.png',
        'left':  'textures/dirt.png',
        'right': 'textures/dirt.png',
        'top':   'textures/dirt.png',
        'bottom':'textures/dirt.png'
    },
    'stone': {
        'front': 'textures/stone.png',
        'back':  'textures/stone.png',
        'left':  'textures/stone.png',
        'right': 'textures/stone.png',
        'top':   'textures/stone.png',
        'bottom':'textures/stone.png'
    },
    'bedrock': {
        'front': 'textures/bedrock.png',
        'back':  'textures/bedrock.png',
        'left':  'textures/bedrock.png',
        'right': 'textures/bedrock.png',
        'top':   'textures/bedrock.png',
        'bottom':'textures/bedrock.png'
    }
}

DEFAULT_COLORS = {
    'grass': (145, 189, 89, 255),
    'dirt': (120, 80, 30, 255),
    'stone': (150, 150, 150, 255),
    'bedrock': (40, 40, 40, 255)
}

def load_image(path, default_color):
    if path and os.path.exists(path):
        try:
            img = Image.open(path).convert('RGBA')
            # 强制不透明
            data = list(img.getdata())
            new_data = [(r, g, b, 255) for (r, g, b, a) in data]
            img.putdata(new_data)
            return img
        except:
            pass
    return Image.new('RGBA', (16, 16), color=default_color)

def create_atlas(block_type):
    tex_dict = BLOCK_TEXTURES.get(block_type, {})
    default = DEFAULT_COLORS.get(block_type, (128,128,128,255))
    faces = ['front', 'back', 'left', 'right', 'top', 'bottom']
    images = []
    for face in faces:
        path = tex_dict.get(face)
        img = load_image(path, default)
        # 如果是草方块顶部，乘以绿色系数
        if block_type == 'grass' and face == 'top':
            r, g, b = 142/255, 185/255, 113/255
            data = list(img.getdata())
            new_data = [(int(p[0]*r), int(p[1]*g), int(p[2]*b), p[3]) for p in data]
            img.putdata(new_data)
        images.append(img)
    atlas = Image.new('RGBA', (16*6, 16))
    for i, img in enumerate(images):
        atlas.paste(img, (i*16, 0))
    return Texture(atlas)

def create_cube_mesh():
    v = [
        (-0.5, -0.5, -0.5),  # 0
        ( 0.5, -0.5, -0.5),  # 1
        ( 0.5,  0.5, -0.5),  # 2
        (-0.5,  0.5, -0.5),  # 3
        (-0.5, -0.5,  0.5),  # 4
        ( 0.5, -0.5,  0.5),  # 5
        ( 0.5,  0.5,  0.5),  # 6
        (-0.5,  0.5,  0.5),  # 7
    ]
    # 每个面的顶点索引（从外部看逆时针）
    face_indices = [
        [4,5,6,7],  # 前 (z+)
        [1,0,3,2],  # 后 (z-)
        [0,4,7,3],  # 左 (x-)
        [5,1,2,6],  # 右 (x+)
        [7,6,2,3],  # 上 (y+)
        [0,1,5,4],  # 下 (y-)
    ]
    uv_width = 1/6
    vertices = []
    uvs = []
    triangles = []
    for fi, idx_list in enumerate(face_indices):
        base = fi * 4
        for vi in idx_list:
            vertices.append(v[vi])
        u_offset = fi * uv_width
        # UV：左下(0) -> 右下(1) -> 右上(2) -> 左上(3)
        uv_list = [
            (u_offset, 0),
            (u_offset + uv_width, 0),
            (u_offset + uv_width, 1),
            (u_offset, 1)
        ]
        uvs.extend(uv_list)
        # 三角形（逆时针）
        triangles += [base, base+2, base+1, base, base+3, base+2]  # 关键修正
    return Mesh(vertices=vertices, uvs=uvs, triangles=triangles, mode='triangle')

class Voxel(Entity):
    def __init__(self, position, block_type):
        self.block_type = block_type
        atlas = create_atlas(block_type)
        mesh = create_cube_mesh()
        super().__init__(
            position=position,
            model=mesh,
            texture=atlas,
            collider='box',
            scale=1,
            color=color.white,
            # double_sided=True   # 如果仍有问题，取消注释此行强制双面渲染
        )

# ---------- 地形生成 ----------
noise = PerlinNoise(octaves=4, seed=42)
RADIUS = 10
HEIGHT_SCALE = 4
BASE_Y = -2
BEDROCK_TOP = -8
STONE_TOP = -4

def get_height(x, z):
    scale = 0.05
    return BASE_Y + noise([x * scale, z * scale]) * HEIGHT_SCALE

for x in range(-RADIUS, RADIUS + 1):
    for z in range(-RADIUS, RADIUS + 1):
        height = get_height(x, z)
        surface_y = round(height)
        for y in range(BEDROCK_TOP - 2, surface_y + 1):
            if y == surface_y:
                block = 'grass'
            elif y > STONE_TOP:
                block = 'dirt'
            elif y > BEDROCK_TOP:
                block = 'stone'
            else:
                block = 'bedrock'
            Voxel((x, y, z), block)

player = FirstPersonController()
player.position = (0, get_height(0,0) + 1, 0)

def input(key):
    if key == 'left mouse down':
        hit = raycast(camera.world_position, camera.forward, distance=5, ignore=(player,))
        if hit.hit and hasattr(hit.entity, 'block_type'):
            destroy(hit.entity)
    if key == 'right mouse down':
        hit = raycast(camera.world_position, camera.forward, distance=5, ignore=(player,))
        if hit.hit and hasattr(hit.entity, 'block_type'):
            new_pos = hit.entity.position + hit.normal
            if not any(e.position == new_pos and isinstance(e, Voxel) for e in scene.entities):
                Voxel(new_pos, 'stone')

app.run()