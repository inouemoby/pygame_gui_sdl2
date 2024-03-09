from pygame._sdl2 import Texture, Renderer
from pygame import Rect, Surface, Color, draw, SRCALPHA
from pygame_gui_sdl2.core import TextureLayer

from typing import Tuple, Union
from copy import copy
from warnings import warn
from collections import deque
import numpy as np


# 渲染逻辑和原本的TextureLayer完全不一样，需要慎重对待
# 已经用原本的重塑了，这个废案

class TextTextureLayer(TextureLayer):
    def __init__(self, renderer: Renderer, size: Tuple[int, int] = None, texture: Texture = None, surface: Surface= None, maxlen: int=15):
        super().__init__(renderer, size, texture, surface, maxlen)
        # self.
    
    def set_render_texture(self):
        self.target_render_texture = Texture(self.renderer, size=self.father_dstrect.size, streaming=True, target=True, scale_quality=2)
        self.extend(self.target_render_texture, can_clean=True)
        
    # def extend_text(self, texture_layer: TextureLayer, srcrect: Rect=None, dstrect: Rect=None, dest: Union[Tuple, Rect] = None, area: Rect = None, color = Color('#FFFFFFFF')):
        