import math
from typing import Dict, List, Union, Tuple, Any

import pygame
from pygame._sdl2 import Renderer, Texture

from pygame_gui_sdl2.core.interfaces import IUIManagerInterface
from pygame_gui_sdl2.core.colour_gradient import ColourGradient
from pygame_gui_sdl2.core.drawable_shapes.drawable_shape import DrawableShape
from pygame_gui_sdl2.core.utility import basic_render
from pygame_gui_sdl2.core.ui_texture import TextureLayer


class RectDrawableShape(DrawableShape):
    """
    A rectangle shape for UI elements has theming options for a border, a shadow, colour
    gradients and text.

    :param containing_rect: The layout rectangle that surrounds and controls the size of this shape.
    :param theming_parameters: Various styling parameters that control the final look of the shape.
    :param states: The different UI states the shape can be in. Shapes have different surfaces
                   for each state.
    :param manager: The UI manager.

    """

    def __init__(self,
                 renderer: Renderer,
                 containing_rect: pygame.Rect,
                 theming_parameters: Dict[str, Any],
                 states: List[str],
                 manager: IUIManagerInterface):
        super().__init__(renderer, containing_rect, theming_parameters, states, manager)

        self.has_been_resized = False

        self.full_rebuild_on_size_change()

    def full_rebuild_on_size_change(self):
        """
        Completely rebuilds the rectangle shape from it's dimensions and parameters.

        Everything needs rebuilding if we change the size of the containing rectangle.

        """
        # clamping border and shadow widths so we can't form impossible negative sized surfaces
        super().full_rebuild_on_size_change()

        self.base_texture = None

        if self.shadow_width > min(math.floor(self.containing_rect.width / 2),
                                   math.floor(self.containing_rect.height / 2)):
            self.shadow_width = min(math.floor(self.containing_rect.width / 2),
                                    math.floor(self.containing_rect.height / 2))

        self.shadow_width = max(self.shadow_width, 0)

        if self.border_width > min(math.floor((self.containing_rect.width -
                                               (self.shadow_width * 2)) / 2),
                                   math.floor((self.containing_rect.height -
                                               (self.shadow_width * 2)) / 2)):
            self.border_width = min(math.floor((self.containing_rect.width -
                                                (self.shadow_width * 2)) / 2),
                                    math.floor((self.containing_rect.height -
                                                (self.shadow_width * 2)) / 2))

        self.border_width = max(self.border_width, 0)

        if self.shadow_width > 0:
            self.click_area_shape = pygame.Rect((self.containing_rect.x + self.shadow_width,
                                                 self.containing_rect.y + self.shadow_width),
                                                (self.containing_rect.width -
                                                 (2 * self.shadow_width),
                                                 self.containing_rect.height -
                                                 (2 * self.shadow_width)))
            shadow = self.ui_manager.get_shadow(self.containing_rect.size,
                                                shadow_width=self.shadow_width,
                                                corner_radius=self.shadow_width)
            if shadow is not None:
                self.base_texture = shadow

        else:
            self.click_area_shape = self.containing_rect.copy()

        if self.base_texture is None:
            self.base_texture = TextureLayer(self.renderer, size=self.containing_rect.size, target=True)

        self.border_rect = pygame.Rect((self.shadow_width,
                                        self.shadow_width),
                                       (self.click_area_shape.width, self.click_area_shape.height))

        self.background_rect = pygame.Rect((self.border_width + self.shadow_width,
                                            self.border_width + self.shadow_width),
                                           (self.click_area_shape.width - (2 * self.border_width),
                                            self.click_area_shape.height - (2 * self.border_width)))
        if 'disabled' in self.states and self.active_state == self.states['disabled']:
            self.redraw_all_states(force_full_redraw=True)
        else:
            self.redraw_all_states()

    def collide_point(self, point: Union[pygame.math.Vector2,
                                         Tuple[int, int],
                                         Tuple[float, float]]) -> bool:
        """
        Tests if a point is colliding with our Drawable shape's 'click area' hot spot.

        :param point: The point to test.

        :return: True if we are colliding.

        """
        return bool(self.click_area_shape.collidepoint(int(point[0]), int(point[1])))

    def set_dimensions(self, dimensions: Union[pygame.math.Vector2,
                                               Tuple[int, int],
                                               Tuple[float, float]]):
        """
        Changes the size of the rectangle shape. Relatively expensive to do.

        :param dimensions: The new dimensions.

        """
        if (dimensions[0] == self.containing_rect.width and
                dimensions[1] == self.containing_rect.height):
            return False
        self.containing_rect.width = int(dimensions[0])
        self.containing_rect.height = int(dimensions[1])
        self.click_area_shape.width = int(dimensions[0]) - (2 * self.shadow_width)
        self.click_area_shape.height = int(dimensions[1]) - (2 * self.shadow_width)

        self.has_been_resized = True

        self.full_rebuild_on_size_change()

        return True

    def set_position(self, point: Union[pygame.math.Vector2,
                                        Tuple[int, int],
                                        Tuple[float, float]]):
        """
        Move the shape. Only really impacts the position of the 'click_area' hot spot.

        :param point: The new position to move it to.

        """
        self.containing_rect.x = int(point[0])
        self.containing_rect.y = int(point[1])
        self.click_area_shape.x = int(point[0]) + self.shadow_width
        self.click_area_shape.y = int(point[1]) + self.shadow_width

    def redraw_state(self, state_str: str, add_text: bool = True):
        """
        Redraws the shape's surface for a given UI state.

        :param add_text:
        :param state_str: The ID string of the state to rebuild.

        """
        border_colour_state_str = state_str + '_border'
        bg_colour_state_str = state_str + '_bg'
        text_colour_state_str = state_str + '_text'
        text_shadow_colour_state_str = state_str + '_text_shadow'
        image_state_str = state_str + '_image'

        found_shape = None
        shape_id = None
        if 'filled_bar' not in self.theming and 'filled_bar_width_percentage' not in self.theming:
            shape_id = self.shape_cache.build_cache_id('rectangle', self.containing_rect.size,
                                                       self.shadow_width,
                                                       self.border_width,
                                                       self.theming[border_colour_state_str],
                                                       self.theming[bg_colour_state_str])

            found_shape = self.shape_cache.find_texture_in_cache(shape_id)
            # found_shape = None
        
        # self.states[state_str].texture.clear_all()
        
        if found_shape is not None:
            self.states[state_str].texture = found_shape.copy()
        else:
            # self.states[state_str].texture.clear_background()
            self.states[state_str].texture = self.base_texture.copy()

            if self.border_width > 0:

                if isinstance(self.theming[border_colour_state_str], ColourGradient):
                    border_shape_surface = pygame.surface.Surface(self.border_rect.size,
                                                                  flags=pygame.SRCALPHA, depth=32)
                    border_shape_surface.fill(pygame.Color('#FFFFFFFF'))
                    border_shape_texture = Texture.from_surface(self.renderer, surface=border_shape_surface)
                    self.states[state_str].texture.render_to_background(border_shape_texture,
                                                        dest=self.border_rect)
                    # self.states[state_str].texture.render_to_background(border_shape_texture,
                    #                                     dest=self.border_rect)
                    self.theming[border_colour_state_str].apply_gradient_to_texture(self.renderer,
                        border_shape_texture)
                    basic_render(self.states[state_str].texture.background_texture_layer,
                               border_shape_texture, self.border_rect)
                else:
                    self.states[state_str].texture.fill_to_background(self.theming[border_colour_state_str],
                                                        self.border_rect)

            if isinstance(self.theming[bg_colour_state_str], ColourGradient):
                background_shape_surface = pygame.surface.Surface(self.background_rect.size,
                                                                  flags=pygame.SRCALPHA, depth=32)
                background_shape_surface.fill(pygame.Color('#FFFFFFFF'))
                background_shape_texture = Texture.from_surface(self.renderer, surface=background_shape_surface)
                self.states[state_str].texture.render_to_background(background_shape_texture,
                                                    dest=self.background_rect)
                self.theming[bg_colour_state_str].apply_gradient_to_texture(self.renderer, 
                    background_shape_texture)
                basic_render(self.states[state_str].texture.background_texture_layer,
                           background_shape_texture, self.background_rect)
            else:
                self.states[state_str].texture.fill_to_background(self.theming[bg_colour_state_str],
                                                    self.background_rect)

            if 'filled_bar' in self.theming and 'filled_bar_width_percentage' in self.theming:
                bar_rect = pygame.Rect(self.background_rect.topleft,
                                       (int(self.theming['filled_bar_width_percentage'] *
                                            self.background_rect.width),
                                        self.background_rect.height))
                if isinstance(self.theming['filled_bar'], ColourGradient):
                    bar_shape_surface = pygame.surface.Surface(bar_rect.size,
                                                               flags=pygame.SRCALPHA,
                                                               depth=32)
                    bar_shape_surface.fill(pygame.Color('#FFFFFFFF'))
                    bar_shape_texture = Texture.from_surface(self.renderer, surface=bar_shape_surface)
                    self.states[state_str].texture.render_to_background(bar_shape_texture, dest=bar_rect)
                    self.theming['filled_bar'].apply_gradient_to_texture(self.renderer, bar_shape_texture)
                    basic_render(self.states[state_str].texture.background_texture_layer,
                               bar_shape_texture, bar_rect)
                else:
                    self.states[state_str].texture.fill_to_background(self.theming['filled_bar'], bar_rect)

            if self.states[state_str].cached_background_id is not None:
                self.shape_cache.remove_user_from_cache_item(
                    self.states[state_str].cached_background_id)
            if (not self.has_been_resized
                    and ((self.containing_rect.width * self.containing_rect.height) < 40000)
                    and (shape_id is not None
                         and self.states[state_str].texture.get_real_width() <= 1024
                         and self.states[state_str].texture.get_real_height() <= 1024)):
                ready_to_cache_texture = self.states[state_str].texture.copy()
                ready_to_cache_texture.clear_all()
                ready_to_cache_texture.background_texture_layer = self.states[state_str].texture.copy_background()
                self.shape_cache.add_texture_to_cache(ready_to_cache_texture,
                                                      shape_id)
                self.states[state_str].cached_background_id = shape_id
                # print("Cached rect")

        self.finalise_images_and_text(image_state_str, state_str,
                                      text_colour_state_str,
                                      text_shadow_colour_state_str,
                                      add_text)

        self.states[state_str].has_fresh_texture = True
        self.states[state_str].generated = True
        # print("Redraw state")
