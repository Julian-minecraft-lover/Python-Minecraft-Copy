from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from perlin_noise import PerlinNoise
import os
from PIL import Image

app = Ursina(borderless=False, fullscreen=False, title='起伏地形')
scene.ambient_light = color.rgb(200, 200, 200)

# ---------- 纹理 ----------
TEXTURE_PATHS = {
    'grass':   'textures/grass_block.png',
    'dirt':    'textures/dirt.png',
    'stone':   'textures/stone.png',
    'bedrock': 'textures/bedrock.png'
}

def load_or_create_texture(block_type):
    path = TEXTURE_PATHS.get(block_type)
    if path and os.path.exists(path):
        img = Image.open(path).convert('RGBA')
        if block_type == 'grass':
            r, g, b = 142/255, 185/255, 113/255
            data = list(img.getdata())
            new_data = [(int(p[0]*r), int(p[1]*g), int(p[2]*b), p[3]) for p in data]
            img.putdata(new_data)
        return Texture(img)
    else:
        color_map = {
            'grass': (142, 185, 113),
            'dirt': (120, 80, 30),
            'stone': (150, 150, 150),
            'bedrock': (40, 40, 40)
        }
        color = color_map.get(block_type, (255, 255, 255))
        img = Image.new('RGB', (16, 16), color=color)
        return Texture(img)

class Voxel(Entity):
    def __init__(self, position, block_type):
        self.block_type = block_type
        texture = load_or_create_texture(block_type)
        super().__init__(
            position=position,
            model='cube',
            texture=texture,
            collider='box',
            scale=1,
            color=color.white
        )

# ---------- 地形参数（缩小范围，提高帧率）----------
noise = PerlinNoise(octaves=4, seed=42)
RADIUS = 10                     # 从20降至10，方块数减少约4倍
HEIGHT_SCALE = 4
BASE_Y = -2
BEDROCK_TOP = -8
STONE_TOP = -4

def get_height(x, z):
    scale = 0.05
    return BASE_Y + noise([x * scale, z * scale]) * HEIGHT_SCALE

# 生成地形
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

# ---------- 玩家定位（直接计算高度，不依赖射线）----------
player = FirstPersonController()
# 计算 (0,0) 处的地表高度
start_height = get_height(0, 0) + 1   # 站在地表上方1单位
player.position = (0, start_height, 0)

# ---------- 交互 ----------
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
                Voxel(new_pos, 'grass')

app.run()