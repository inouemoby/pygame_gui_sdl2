from typing import Union, Any

import pygame
from pygame._sdl2 import Texture, Renderer

from pygame_gui_sdl2.core.interfaces.colour_gradient_interface import IColourGradientInterface
from pygame_gui_sdl2.core.utility import basic_render


class ColourGradient(IColourGradientInterface):
    """
    Creates a small surface containing a smooth gradient between two or three colours.

    :param angle_direction: Angle direction of the gradient in degrees.
    :param colour_1: The first colour of the gradient.
    :param colour_2: The second colour of the gradient.
    :param colour_3: An optional third colour for the gradient.
    """
    def __init__(self, angle_direction: int,
                 colour_1: pygame.Color,
                 colour_2: pygame.Color,
                 colour_3: Union[pygame.Color, None] = None):

        self.angle_direction = angle_direction
        self.colour_1 = colour_1
        self.colour_2 = colour_2
        self.colour_3 = colour_3

        if self.colour_3 is None:
            pixel_width = 2
            colour_pixels_surf = pygame.surface.Surface((pixel_width, 1),
                                                        flags=pygame.SRCALPHA, depth=32)
            colour_pixels_surf.fill(self.colour_1, pygame.Rect((0, 0), (1, 1)))
            colour_pixels_surf.fill(self.colour_2, pygame.Rect((1, 0), (1, 1)))
        else:
            pixel_width = 3
            colour_pixels_surf = pygame.surface.Surface((pixel_width, 1),
                                                        flags=pygame.SRCALPHA, depth=32)
            colour_pixels_surf.fill(self.colour_1, pygame.Rect((0, 0), (1, 1)))
            colour_pixels_surf.fill(self.colour_2, pygame.Rect((1, 0), (1, 1)))
            colour_pixels_surf.fill(self.colour_3, pygame.Rect((2, 0), (1, 1)))

        self.gradient_surface = pygame.transform.rotozoom(colour_pixels_surf, 0, 30)

    def __eq__(self, other: Any) -> bool:
        """
        Checks if this gradient is equal to another when compared with the == symbol.

        :return: True if they have the same colours and direction.
        """
        if not isinstance(other, ColourGradient):
            return False
        return (self.colour_1 == other.colour_1 and
                self.colour_2 == other.colour_2 and
                self.colour_3 == other.colour_3 and
                self.angle_direction == other.angle_direction)

    def __str__(self) -> str:
        """
        Creates a string representation of this gradient.

        :return: The string representation.
        """
        result = (str(self.angle_direction) + '_' +
                  str(self.colour_1.r) + '_' + str(self.colour_1.g) + '_' +
                  str(self.colour_1.b) + '_' + str(self.colour_1.a) + '_' +
                  str(self.colour_2.r) + '_' + str(self.colour_2.g) + '_' +
                  str(self.colour_2.b) + '_' + str(self.colour_2.a))
        if self.colour_3 is not None:
            result += ('_' + str(self.colour_3.r) + '_' + str(self.colour_3.g) +
                       '_' + str(self.colour_3.b) + '_' + str(self.colour_3.a))

        return result

    def apply_gradient_to_texture(self, renderer: Renderer, input_texture: Texture,
                                  rect: Union[pygame.Rect, None] = None):
        """
        Applies this gradient to a specified input surface using blending multiplication.
        As a result this method works best when the input surface is a mostly white, stencil shape
        type surface.

        :param input_surface:
        :param rect: The rectangle on the surface to apply the gradient to. If None, applies to the
                     whole surface.
        """
        # scale the gradient up to the right size
        input_texture_size = input_texture.get_rect().size
        # inverse_rotated_input = input_texture.copy().rotate(-self.angle_direction)
        # gradient_size = inverse_rotated_input.get_rect().size
        gradient_size = input_texture_size
        gradient_surf = pygame.surface.Surface(gradient_size, flags=pygame.SRCALPHA, depth=32)

        pygame.transform.scale(self.gradient_surface, gradient_size, gradient_surf)
        gradient_surf = pygame.transform.rotate(gradient_surf, self.angle_direction)
        gradient_texture = Texture.from_surface(renderer, gradient_surf)
        gradient_texture.blend_mode = 1

        renderer.target = input_texture
        input_texture.blend_mode = 1
        if rect is not None:
            gradient_texture.draw(dstrect=rect)
        else:
            gradient_placement_rect = gradient_surf.get_rect()
            gradient_placement_rect.center = (int(input_texture_size[0] / 2),
                                              int(input_texture_size[1] / 2))

            gradient_texture.draw(dstrect=pygame.Rect(gradient_placement_rect.topleft, gradient_texture.get_rect().size))
        renderer.target = None