from typing import Union, Tuple, Dict, Optional

import pygame
from pygame._sdl2 import Texture

from pygame_gui_sdl2.core import ObjectID, TextureLayer
from pygame_gui_sdl2.core.interfaces import IContainerLikeInterface, IUIManagerInterface
from pygame_gui_sdl2.core import UIElement
# from pygame_gui_sdl2.core.utility import premul_alpha_texture

from pygame_gui_sdl2._constants import *

class UIImage(UIElement):
    """
    Displays a pygame surface as a UI element, intended for an image but it can serve
    other purposes.

    :param relative_rect: The rectangle that contains, positions and scales the image relative to
                          it's container.
    :param image_surface: A pygame surface to display.
    :param manager: The UIManager that manages this element. If not provided or set to None,
                    it will try to use the first UIManager that was created by your application.
    :param container: The container that this element is within. If not provided or set to None
                      will be the root window's container.
    :param parent_element: The element this element 'belongs to' in the theming hierarchy.
    :param object_id: A custom defined ID for fine tuning of theming.
    :param anchors: A dictionary describing what this element's relative_rect is relative to.
    :param visible: Whether the element is visible by default. Warning - container visibility
                    may override this.
    """
    default_scale_type = SCALE_EMBED
    
    def __init__(self, renderer,
                 relative_rect: pygame.Rect,
                 image_texture: Texture,
                 manager: Optional[IUIManagerInterface] = None,
                 image_is_alpha_premultiplied: bool = False,
                 scale_type: int = SCALE_EMBED,
                 container: Optional[IContainerLikeInterface] = None,
                 parent_element: Optional[UIElement] = None,
                 object_id: Optional[Union[ObjectID, str]] = None,
                 anchors: Optional[Dict[str, Union[str, UIElement]]] = None,
                 visible: int = 1):

        super().__init__(renderer, relative_rect, manager, container,
                         starting_height=1,
                         layer_thickness=1,
                         anchors=anchors,
                         visible=visible,
                         parent_element=parent_element,
                         object_id=object_id,
                         element_id=['image'])

        self.image_texture_layer = TextureLayer(self.renderer, size=relative_rect.size)
        self.original_image = self.image_texture_layer.copy_texture(image_texture)
        
        self.scale_type = scale_type
        if self.scale_type == "":
            self.scale_type = self.default_scale_type

        self.set_image(image_texture, scale_type)
        self.rebuild_from_changed_theme_data()

    def rebuild_from_changed_theme_data(self):
        self._check_misc_theme_data_changed(attribute_name='tool_tip_delay',
                                            default_value=1.0,
                                            casting_func=float)

    def set_dimensions(self, dimensions: Union[pygame.math.Vector2,
                                               Tuple[int, int],
                                               Tuple[float, float]],
                       clamp_to_container: bool = False,
                       scale_type: int = SCALE_EMBED):
        """
        Set the dimensions of this image, scaling the image surface to match.

        :param dimensions: The new dimensions of the image.
        :param clamp_to_container: Whether we should clamp the dimensions to the
                                   dimensions of the container or not.

        """
        super().set_dimensions(dimensions)
        # if scale_type == "":
        #     scale_type = self.scale_type

        if self.rect.size != self.image.get_real_size():
            self.image_texture_layer.rebuild_father_texture(self.rect.size)
            # if self.original_image is None:
            #     if self._pre_clipped_image is not None:
            #         self.original_image = self._pre_clipped_image
            #     else:
            #         self.original_image = self.image
                    
            # if scale_type not in UIImage.scale_type_list:
            #     scale_type = UIImage.default_scale_type
            self.set_image(self.original_image, scale_type)

    def set_image(self, new_image: Union[Texture, None],
                        scale_type: int = SCALE_EMBED) -> None:
        """
        Allows users to change the image displayed on a UIImage element during run time, without recreating
        the element.

        GUI images are converted to the correct format for the GUI if the supplied image is not the dimensions
        of the UIImage element it will be scaled to fit. In this situation, an original size image is retained
        as well in case of future resizing events.

        :param new_image: the new image surface to use in the UIIamge element.
        :param image_is_alpha_premultiplied: set to True if the image is already in alpha multiplied colour format.
        """
        # new_background_texture.fill('#00000000')
        # if self.background_colour is not None and self.background_colour != '#00000000':
        # if self.background_colour is not None:
        #     new_background_texture.fill(self.background_colour)
            # print(f'set layout background to {self.background_colour}')
        
        if new_image is not None and new_image.get_rect().size != (0, 0):
            # if scale_type not in UIImage.scale_type_list:
            #     scale_type = UIImage.default_scale_type

            if scale_type == ORIGINAL:
                self.scale_type = ORIGINAL
                self.image_texture_layer.set_image_texture(new_image, ORIGINAL)
                # self._set_image(new_background_texture)
            elif scale_type == FILL:
                self.scale_type = FILL
                self.image_texture_layer.set_image_texture(new_image, FILL)
                # self._set_image(new_background_texture)
            else:
                if scale_type == SCALE_EMBED:
                    self.scale_type = SCALE_EMBED
                    self.image_texture_layer.set_image_texture(new_image, SCALE_EMBED)
                else:  # scale_short
                    self.scale_type = SCALE_SURROUND
                    self.image_texture_layer.set_image_texture(new_image, SCALE_SURROUND)

                # self._set_image(new_background_texture)
        
        self._set_image(self.image_texture_layer)
