from typing import Optional

import pygame
from pygame._sdl2 import Renderer, Texture
from pygame.surface import Surface
from pygame.rect import Rect
from pygame.image import load

from pygame_gui_sdl2.core.text.text_layout_rect import TextLayoutRect, Padding
from pygame_gui_sdl2.core.ui_texture import TextureLayer

class ImageLayoutRect(TextLayoutRect):
    """
    Represents an image that sits in the text.
    """
    def __init__(self, renderer: Renderer, image_path, float_position, padding: Padding):
        self.renderer = renderer
        self.image_path = image_path
        self.image_text = Texture.from_surface(renderer, surface=load(image_path).convert_alpha().premul_alpha())
        self.image_text.blend_mode = 1
        self.padding = padding
        self.size_with_padding = (self.image_text.get_width() + padding.left + padding.right,
                                  self.image_text.get_height() + padding.top + padding.bottom)
        super().__init__(renderer, self.size_with_padding, float_pos=float_position)

    def finalise(self,
                 target_texture: TextureLayer,
                 target_area: Rect,
                 row_chunk_origin: int,
                 row_chunk_height: int,
                 row_bg_height: int,
                 x_scroll_offset: int = 0,
                 letter_end: Optional[int] = None):
        blit_rect = self.copy()
        blit_rect.width -= (self.padding.left + self.padding.right)
        blit_rect.height -= (self.padding.top + self.padding.bottom)
        blit_rect.left += self.padding.left
        blit_rect.top += self.padding.top
        target_texture.render_to_text(self.image_text, dest=blit_rect, area=target_area)
