import pygame


from pygame_gui_sdl2.core.interfaces.gui_font_interface import IGUIFontInterface
from pygame.freetype import Font
from typing import Union, IO, Optional, Dict, Tuple
from os import PathLike
from pygame import Color, Surface, Rect
from pygame._sdl2 import Texture

AnyPath = Union[str, bytes, PathLike]
FileArg = Union[AnyPath, IO]


class GUIFontFreetype(IGUIFontInterface):

    def __init__(self, renderer, file: Optional[FileArg], size: Union[int, float],
                 force_style: bool = False, style: Optional[Dict[str, bool]] = None):
        self.renderer = renderer
        self.__internal_font: Font = Font(file, size, resolution=100)
        self.__internal_font.pad = True
        self.__internal_font.origin = True
        self.__internal_font.kerning = True

        self.__underline = False
        self.__underline_adjustment = 0.0

        self.point_size = size

        if style is not None:
            self.__internal_font.antialiased = style['antialiased']

            if force_style:
                self.__internal_font.strong = style['bold']
                self.__internal_font.oblique = style['italic']


    @property
    def underline(self) -> bool:
        return self.__internal_font.underline

    @underline.setter
    def underline(self, value: bool):
        self.__internal_font.underline = value

    @property
    def underline_adjustment(self) -> float:
        return self.__internal_font.underline_adjustment

    @underline_adjustment.setter
    def underline_adjustment(self, value: float):
        self.__internal_font.underline_adjustment = value

    def get_point_size(self):
        return self.point_size

    def get_rect(self, text: str) -> Rect:
        supposed_rect = self.__internal_font.get_rect(text)
        text_surface, text_rect = self.__internal_font.render(text, pygame.Color("white"))
        return pygame.Rect(supposed_rect.topleft, text_surface.get_size())

    def get_metrics(self, text: str):
        return self.__internal_font.get_metrics(text)

    def render_premul(self, text: str, text_color: Color) -> Texture:
        text_surface, text_rect = self.__internal_font.render(text, text_color)
        text_surface = text_surface.convert_alpha()
        if text_surface.get_width() > 0 and text_surface.get_height() > 0:
            text_surface = text_surface.premul_alpha()
        temp_texture = Texture.from_surface(self.renderer, surface=text_surface)
        temp_texture.blend_mode = 1
        text_texture = Texture(self.renderer, size=text_surface.get_size(), target=True, scale_quality=2)
        text_texture.blend_mode = 1
        self.renderer.target = text_texture
        self.renderer.draw_color = Color("#00000000")
        self.renderer.clear()
        temp_texture.draw()
        self.renderer.target = None
        return text_texture

    def render_premul_to(self, text: str, text_colour: Color,
                         texture_size: Tuple[int, int], texture_position: Tuple[int, int]) -> Texture:
        text_surface = pygame.Surface(texture_size, depth=32, flags=pygame.SRCALPHA)
        self.__internal_font.render_to(text_surface, texture_position, text, fgcolor=text_colour)
        if text_surface.get_width() > 0 and text_surface.get_height() > 0:
            text_surface = text_surface.premul_alpha()
        temp_texture = Texture.from_surface(self.renderer, surface=text_surface)
        temp_texture.blend_mode = 1
        text_texture = Texture(self.renderer, size=text_surface.get_size(), target=True, scale_quality=2)
        text_texture.blend_mode = 1
        self.renderer.target = text_texture
        self.renderer.draw_color = Color("#00000000")
        self.renderer.clear()
        temp_texture.draw()
        self.renderer.target = None
        return text_texture

    def get_padding_height(self):
        # 'font padding' this determines the amount of padding that
        # font.pad adds to the top of text excluding
        # any padding added to make glyphs even - this is useful
        # for 'base-line centering' when we want to center text
        # that doesn't drop below the base line (no y's, g's, p's etc)
        # but also don't want it to flicker on and off. Base-line
        # centering is the default for chunks on a single style row.

        return -self.__internal_font.get_sized_descender(self.point_size)
