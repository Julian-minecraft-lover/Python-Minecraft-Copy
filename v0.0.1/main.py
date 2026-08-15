from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import os
from PIL import Image

app = Ursina(borderless=False, fullscreen=False, title='平坦世界')

# 增加环境光，让颜色显示正常
scene.ambient_light = color.rgb(200, 200, 200)

# 纹理路径映射（请确保文件存在）
TEXTURE_PATHS = {
    'grass':   'textures/grass_block.png',
    'dirt':    'textures/dirt.png',
    'stone':   'textures/stone.png',
    'bedrock': 'textures/bedrock.png'
}

def load_or_create_texture(block_type):
    """加载纹理，若不存在则生成纯色纹理"""
    path = TEXTURE_PATHS.get(block_type)
    if path and os.path.exists(path):
        # 加载并处理纹理（对于草方块，乘以绿色系数）
        img = Image.open(path).convert('RGBA')
        if block_type == 'grass':
            # 乘以 (142,185,113) 归一化
            r, g, b = 142/255, 185/255, 113/255
            data = list(img.getdata())
            new_data = [(int(p[0]*r), int(p[1]*g), int(p[2]*b), p[3]) for p in data]
            img.putdata(new_data)
        return Texture(img)
    else:
        # 生成纯色纹理
        if block_type == 'grass':
            color = (142, 185, 113)
        elif block_type == 'dirt':
            color = (120, 80, 30)
        elif block_type == 'stone':
            color = (150, 150, 150)
        elif block_type == 'bedrock':
            color = (40, 40, 40)
        else:
            color = (255, 255, 255)
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
            color=color.white  # 白色，纹理自带颜色
        )

RADIUS = 10
for x in range(-RADIUS, RADIUS + 1):
    for z in range(-RADIUS, RADIUS + 1):
        Voxel((x, -3, z), 'bedrock')
        Voxel((x, -2, z), 'stone')
        Voxel((x, -1, z), 'dirt')
        Voxel((x,  0, z), 'grass')

player = FirstPersonController()
player.position = (0, 0.5, 0)

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