from abc import ABCMeta, abstractmethod
from typing import Tuple
from pygame import Surface, Color, Rect
from pygame_gui_sdl2.core.ui_texture import TextureLayer


class IGUIFontInterface(metaclass=ABCMeta):
    """
    A font interface so we can easily switch between pygame.freetype.Font and pygame.Font.
    """

    @abstractmethod
    def render_premul(self, text: str, text_color: Color) -> TextureLayer:
        """
        Draws text to a surface ready for premultiplied alpha-blending
        """

    def render_premul_to(self, text: str, text_colour: Color, texture_size: Tuple[int, int], texture_position: Tuple[int, int]) -> TextureLayer:
        """


        :param text:
        :param text_colour:
        :param surf_size:
        :param surf_position:
        :return:
        """

    @abstractmethod
    def get_rect(self, text: str) -> Rect:
        """
        Not sure if we want this.
        :return:
        """

    @abstractmethod
    def get_metrics(self, text: str):
        """

        :param text:
        :return:
        """

    @abstractmethod
    def get_point_size(self):
        """

        """

    @abstractmethod
    def get_padding_height(self):
        """

        :return:
        """

    @property
    @abstractmethod
    def underline(self) -> bool:
        """

        :return:
        """

    @underline.setter
    @abstractmethod
    def underline(self, value: bool):
        """

        :param value:
        :return:
        """

    @property
    @abstractmethod
    def underline_adjustment(self) -> float:
        """

        :return:
        """

    @underline_adjustment.setter
    @abstractmethod
    def underline_adjustment(self, value: float):
        """

        :param value:
        :return:
        """

