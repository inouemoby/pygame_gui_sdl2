from typing import Optional, Tuple

from pygame_gui_sdl2.core.interfaces.gui_font_interface import IGUIFontInterface
from pygame.color import Color
from pygame._sdl2 import Renderer


from pygame_gui_sdl2.core.text.text_line_chunk import TextLineChunkFTFont


class HyperlinkTextChunk(TextLineChunkFTFont):
    """
    Represents a hyperlink to the layout system..

    """
    def __init__(self, 
                 renderer: Renderer,
                 href: str,
                 text: str,
                 font: IGUIFontInterface,
                 underlined: bool,
                 colour: Color,
                 bg_colour: Color,
                 hover_colour: Color,
                 active_colour: Color,
                 hover_underline: bool,
                 text_shadow_data: Optional[Tuple[int, int, int]] = None,
                 effect_id: Optional[str] = None):
        super().__init__(renderer, text, font, underlined, colour, False, bg_colour,
                         text_shadow_data, effect_id=effect_id)

        self.href = href
        self.is_hovered = False

        self.normal_colour = colour
        self.hover_colour = hover_colour
        self.active_colour = active_colour

        self.normal_underline = underlined
        self.hover_underline = hover_underline

        self.last_row_origin = 0
        self.last_row_height = 0

    def on_hovered(self):
        """
        Handles hovering over this text chunk with the mouse. Used for links.

        """
        if not (self.is_active or self.is_selected):
            self.colour = self.hover_colour
            self.underlined = self.hover_underline
            self.is_hovered = True
            self.redraw()

    def on_unhovered(self):
        """
        Handles hovering over this text chunk with the mouse. Used for links.

        """
        if not (self.is_active or self.is_selected):
            self.colour = self.normal_colour
            self.underlined = self.normal_underline
            self.is_hovered = False
            self.redraw()

    def set_active(self):
        """
        Handles clicking on this text chunk with the mouse. Used for links.

        """
        self.colour = self.active_colour
        self.is_active = True
        self.redraw()

    def set_inactive(self):
        """
        Handles clicking on this text chunk with the mouse. Used for links.

        """
        self.colour = self.normal_colour
        self.is_active = False
        self.redraw()

    def _split_at(self, right_side, split_pos, target_texture,
                  target_texture_area, baseline_centred):
        right_side_chunk = HyperlinkTextChunk(self.href,
                                              right_side,
                                              self.font,
                                              self.underlined,
                                              self.colour,
                                              self.bg_colour,
                                              self.hover_colour,
                                              self.active_colour,
                                              self.hover_underline,
                                              self.text_shadow_data,
                                              self.effect_id)

        right_side_chunk.topleft = split_pos  # pylint: disable=attribute-defined-outside-init
        right_side_chunk.target_texture = target_texture
        right_side_chunk.target_texture_area = target_texture_area
        right_side_chunk.should_centre_from_baseline = baseline_centred
        return right_side_chunk
