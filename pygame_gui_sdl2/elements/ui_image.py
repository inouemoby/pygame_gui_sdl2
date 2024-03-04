from typing import Union, Tuple, Dict, Optional

import pygame

from pygame_gui_sdl2.core import ObjectID, TextureLayer
from pygame_gui_sdl2.core.interfaces import IContainerLikeInterface, IUIManagerInterface
from pygame_gui_sdl2.core import UIElement
from pygame_gui_sdl2.core.utility import premul_alpha_texture


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
    default_scale_type = "scale_long"
    scale_type_list = ['original', 'stretch', 'scale_long', 'scale_short']
    
    def __init__(self, renderer,
                 relative_rect: pygame.Rect,
                 image_texture: TextureLayer,
                 manager: Optional[IUIManagerInterface] = None,
                 image_is_alpha_premultiplied: bool = False,
                 scale_type: str = "",
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

        self.original_image = None
        
        self.scale_type = scale_type
        if self.scale_type == "":
            self.scale_type = self.default_scale_type

        self.set_image(image_texture, image_is_alpha_premultiplied, scale_type)
        self.rebuild_from_changed_theme_data()

    def rebuild_from_changed_theme_data(self):
        self._check_misc_theme_data_changed(attribute_name='tool_tip_delay',
                                            default_value=1.0,
                                            casting_func=float)

    def set_dimensions(self, dimensions: Union[pygame.math.Vector2,
                                               Tuple[int, int],
                                               Tuple[float, float]],
                       clamp_to_container: bool = False,
                       scale_type: str = ""):
        """
        Set the dimensions of this image, scaling the image surface to match.

        :param dimensions: The new dimensions of the image.
        :param clamp_to_container: Whether we should clamp the dimensions to the
                                   dimensions of the container or not.

        """
        super().set_dimensions(dimensions)
        if scale_type == "":
            scale_type = self.scale_type

        if self.rect.size != self.image.get_size():
            if self.original_image is None:
                if self._pre_clipped_image is not None:
                    self.original_image = self._pre_clipped_image
                else:
                    self.original_image = self.image
                    
            if scale_type not in UIImage.scale_type_list:
                scale_type = UIImage.default_scale_type
            if scale_type == 'original':
                offset = ((self.rect.width - self.original_image.get_width()) // 2,
                        (self.rect.height - self.original_image.get_height()) // 2)
                self._set_image(self.original_image.copy().scale_to(self.rect.size), offset)
                self.scale_type = 'original'
            elif scale_type == 'stretch':
                self._set_image(self.original_image.copy().scale_to(self.rect.size))
                self.scale_type = 'stretch'
            else:
                image_ratio = self.original_image.get_width() / self.original_image.get_height()
                rect_ratio = self.rect.width / self.rect.height

                if scale_type == 'scale_long':
                    self.scale_type = 'scale_long'
                    if image_ratio > rect_ratio:
                        scale_factor = self.rect.width / self.original_image.get_width()
                    else:
                        scale_factor = self.rect.height / self.original_image.get_height()
                else:  # scale_short
                    self.scale_type = 'scale_short'
                    if image_ratio > rect_ratio:
                        scale_factor = self.rect.height / self.original_image.get_height()
                    else:
                        scale_factor = self.rect.width / self.original_image.get_width()

                new_size = (int(self.original_image.get_width() * scale_factor),
                            int(self.original_image.get_height() * scale_factor))
                offset = ((self.rect.width - new_size[0]) // 2,
                        (self.rect.height - new_size[1]) // 2)
                self._set_image(self.original_image.copy().scale_to(new_size), offset)

    def set_image(self,
                  new_image: Union[TextureLayer, None],
                  image_is_alpha_premultiplied: bool = False,
                  scale_type: str = '') -> None:
        """
        Allows users to change the image displayed on a UIImage element during run time, without recreating
        the element.

        GUI images are converted to the correct format for the GUI if the supplied image is not the dimensions
        of the UIImage element it will be scaled to fit. In this situation, an original size image is retained
        as well in case of future resizing events.

        :param new_image: the new image surface to use in the UIIamge element.
        :param image_is_alpha_premultiplied: set to True if the image is already in alpha multiplied colour format.
        """
        print("start set_image")
        image_texture = new_image.convert_alpha().copy()
        if not image_is_alpha_premultiplied:
            image_texture = premul_alpha_texture(image_texture)
        if scale_type not in UIImage.scale_type_list:
            scale_type = UIImage.default_scale_type

        self.original_image = image_texture
        if scale_type == 'original':
            self.scale_type = 'original'
            offset = ((self.rect.width - image_texture.get_width()) // 2,
                    (self.rect.height - image_texture.get_height()) // 2)
            self._set_image(image_texture, dstrect=offset)
        elif scale_type == 'stretch':
            self.scale_type = 'stretch'
            self._set_image(image_texture.copy().scale_to(self.rect.size))
        else:
            image_ratio = image_texture.get_width() / image_texture.get_height()
            rect_ratio = self.rect.width / self.rect.height

            if scale_type == 'scale_long':
                self.scale_type = 'scale_long'
                if image_ratio > rect_ratio:
                    scale_factor = self.rect.width / image_texture.get_width()
                else:
                    scale_factor = self.rect.height / image_texture.get_height()
            else:  # scale_short
                self.scale_type = 'scale_short'
                if image_ratio > rect_ratio:
                    scale_factor = self.rect.height / image_texture.get_height()
                else:
                    scale_factor = self.rect.width / image_texture.get_width()

            new_size = (int(image_texture.get_width() * scale_factor),
                        int(image_texture.get_height() * scale_factor))
            offset = ((self.rect.width - new_size[0]) // 2,
                    (self.rect.height - new_size[1]) // 2)
            self._set_image(image_texture.copy().scale_to(new_size), dstrect=offset)
