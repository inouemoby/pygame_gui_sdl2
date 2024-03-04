from pygame._sdl2 import Texture, Renderer
from pygame import Rect, Surface, Color, draw, SRCALPHA

from typing import Tuple, List, Union
from copy import copy
from warnings import warn
from collections import deque
import numpy as np

class TextureLayer:
    def __init__(self, renderer: Renderer, size: Tuple[int, int] = None, texture: Texture = None, surface: Surface= None, maxlen: int=15):
        if renderer is None:
            raise ValueError("renderer cannot be None")
        
        self.blend_mode = 1
        if not size is None:
            if size[0] <= 0 or size[1] <= 0:
                self.father_texture = Texture(renderer=renderer, size=(1,1))
                self.father_texture.alpha = 0
            else:
                self.father_texture = Texture(renderer=renderer, size=size)
        elif not surface is None:
            if surface.get_size()[0] <= 0 or surface.get_size()[1] <= 0:
                self.father_texture = Texture(renderer=renderer, size=(1,1))
                self.father_texture.alpha = 0
            else:
                self.father_texture = Texture.from_surface(renderer, surface)
        else:
            self.father_texture = texture
            
        if self.father_texture is not None:
            self.father_srcrect = self.father_texture.get_rect().copy()
            self.father_dstrect = self.father_texture.get_rect().copy()
            self.father_texture.blend_mode = self.blend_mode
        else:
            warn("A TextureLayer's father_texture got a NoneType")
            self.father_srcrect = Rect(0,0,0,0)
            self.father_dstrect = Rect(0,0,0,0)
        self.father_angle = 0
        self.father_flip_x = False
        self.father_flip_y = False
        self.father_color = Color(255, 255, 255, 255)
        self.renderer = renderer
        self.parent_texture_layer = None
        self.sub_rect: Rect = None
        self.texture_list_maxlen = maxlen
        self.texture_list = deque(maxlen=self.texture_list_maxlen)
        # self.texture_list = []
        
    def blit(self, texture, dest: Union[Tuple, Rect] = None, area: Rect = None, special_flags=0):
        self.extend(texture, dest=dest, area=area)
        
    def append(self, texture: Texture, srcrect: Rect=None, dstrect: Rect=None, dest: Union[Tuple, Rect] = None, area: Rect = None, angle=0, flip_x=False, flip_y=False, can_override=True, can_clean=False, special_flags=0):
        if texture is None:
            return
        if srcrect is None:
            srcrect = texture.get_rect().copy()
        else: 
            srcrect = srcrect.copy()
        if area is not None:
            srcrect = area.copy()
        if dstrect is None:
            dstrect = srcrect.copy()
        else:
            dstrect = dstrect.copy()
        if dest is not None:
            if isinstance(dest, Rect):
                dstrect.left += dest.left
                dstrect.top += dest.top
            else:
                dstrect.left += dest[0]
                dstrect.top += dest[1]
                
        if self.father_texture is not None:
            
            srcrect, dstrect= self.clip_to_father(srcrect, dstrect)
            texture.blend_mode = self.blend_mode
            texture_data = {
                "texture" : texture,
                "srcrect" : srcrect,
                "dstrect" : dstrect,
                "angle" : angle,
                "flip_x" : flip_x,
                "flip_y" : flip_y,
                "color" : Color(255, 255, 255, 255),
                "can_override" : can_override,
                "can_clean" : can_clean,
            }
            if self.check_if_empty(texture_data):
                return
            if self.check_if_override(texture_data):
                self.refresh(texture_data["texture"])
                return
            self.texture_list.append(texture_data)
        else:
            self.father_texture = texture
            self.father_srcrect = srcrect.copy()
            self.father_dstrect = dstrect.copy()
            self.father_angle = angle
            self.father_flip_x = flip_x
            self.father_flip_y = flip_y
            self.father_color = Color(255, 255, 255, 255)
        
    def extend(self, texture_layer, srcrect: Rect=None, dstrect: Rect=None, dest: Union[Tuple, Rect] = None, area: Rect = None, angle=0, flip_x=False, flip_y=False, can_override=False, can_clean=False):
        if isinstance(texture_layer, TextureLayer):
            texture_layer = texture_layer.copy()
            if srcrect is None:
                srcrect = texture_layer.father_dstrect.copy()
            else:
                srcrect = srcrect.copy()
            if area is not None:
                srcrect = area.copy()
            if dstrect is None:
                dstrect = srcrect.copy()
            else: 
                dstrect = dstrect.copy()
            if dest is not None:
                if isinstance(dest, Rect):
                    dstrect.left += dest.left
                    dstrect.top += dest.top
                else:
                    dstrect.left += dest[0]
                    dstrect.top += dest[1]
            oldfather_texture_data = {
                "texture" : texture_layer.father_texture,
                "srcrect" : texture_layer.father_srcrect,
                "dstrect" : texture_layer.father_dstrect,
                "angle" : texture_layer.father_angle,
                "flip_x" : texture_layer.father_flip_x,
                "flip_y" : texture_layer.father_flip_y,
                "color" : texture_layer.father_color,
                "can_override" : can_override,
                "can_clean" : can_clean
            }
            if self.check_if_empty(oldfather_texture_data):
                pass
            else:
                new_oldfather_texture_data = self.blend_to_father(oldfather_texture_data, srcrect, dstrect, angle, flip_x, flip_y)
                if self.check_if_override(new_oldfather_texture_data):
                    self.refresh(new_oldfather_texture_data["texture"])
                if not self.check_if_empty(new_oldfather_texture_data):
                    self.texture_list.append(new_oldfather_texture_data)
            for texture_data in texture_layer.texture_list:
                if self.check_if_empty(texture_data):
                    continue
                new_texture_data = self.blend_to_father(texture_data, srcrect, dstrect, angle, flip_x, flip_y)
                if self.check_if_empty(new_texture_data):
                    continue
                if self.check_if_override(new_texture_data):
                    self.refresh(new_texture_data["texture"])
                else:
                    self.texture_list.append(new_texture_data)
        elif isinstance(texture_layer, Texture):
            self.append(texture_layer, srcrect, dstrect, dest, area, angle, flip_x, flip_y, can_override, can_clean)
            
        elif isinstance(texture_layer, Surface):
            texture = Texture.from_surface(self.father_texture.renderer, texture_layer)
            self.append(texture, srcrect, dstrect, dest, area, angle, flip_x, flip_y, can_override, can_clean)
        elif isinstance(texture_layer, list[TextureLayer]):
            for texture_data in texture_layer:
                self.extend(texture_data, srcrect, dstrect, dest, area, angle, flip_x, flip_y, can_override, can_clean)
            
    def blend_to_father(self, texture_data: dict, adjust_srcrect: Rect=None, adjust_dstrect: Union[Tuple, Rect] = None, adjust_angle=0, adjust_flip_x=False, adjust_flip_y=False):
        new_texture_data = {}
        texture_data["texture"].blend_mode = self.blend_mode 
        if self.father_texture is None:
            new_srcrect, new_dstrect = self.clip_and_adjust_a_newfather(texture_data["srcrect"], texture_data["dstrect"], adjust_srcrect, adjust_dstrect)
            new_texture_data["texture"] = texture_data["texture"]
            new_texture_data["srcrect"] = new_srcrect
            new_texture_data["dstrect"] = new_dstrect
            new_texture_data["angle"] = texture_data["angle"] + adjust_angle
            new_texture_data["flip_x"] = texture_data["flip_x"] ^ adjust_flip_x
            new_texture_data["flip_y"] = texture_data["flip_y"] ^ adjust_flip_y
            new_texture_data["color"] = Color(texture_data["color"].r, texture_data["color"].g, texture_data["color"].b, texture_data["color"].a)
            new_texture_data["can_override"] = texture_data["can_override"]
            new_texture_data["can_clean"] = texture_data["can_clean"]
            self.append(**new_texture_data)
            return None
        else:
            new_srcrect, new_dstrect = self.clip_and_adjust_from_oldfather_to_newfather(texture_data["srcrect"], texture_data["dstrect"], adjust_srcrect, adjust_dstrect)
            new_texture_data["texture"] = texture_data["texture"]
            new_texture_data["srcrect"] = new_srcrect
            new_texture_data["dstrect"] = new_dstrect
            new_texture_data["angle"] = texture_data["angle"] + adjust_angle
            new_texture_data["flip_x"] = texture_data["flip_x"] ^ adjust_flip_x
            new_texture_data["flip_y"] = texture_data["flip_y"] ^ adjust_flip_y
            new_texture_data["color"] = Color(texture_data["color"].r, texture_data["color"].g, texture_data["color"].b, texture_data["color"].a)
            new_texture_data["can_override"] = texture_data["can_override"]
            new_texture_data["can_clean"] = texture_data["can_clean"]
            self.calculate_rotate(new_texture_data, adjust_angle)
            return new_texture_data
    
    
    def clip_to_father(self, srcrect: Rect, dstrect: Rect):
        rect1 = srcrect
        rect2 = dstrect
        
        if rect2.width <=0 or rect2.height <=0:
            preserved_rect1 = Rect(rect1.left, rect1.top, 0, 0)
            rect2_clip_result = Rect(rect2.left, rect2.top, 0, 0)
        else:
            rect2_clip_result = rect2.clip(self.father_dstrect)
            preserved_rect1 = Rect(rect1.left + int((rect2_clip_result.left - rect2.left) * rect1.width / rect2.width),
                                rect1.top + int((rect2_clip_result.top - rect2.top) * rect1.height / rect2.height),
                                int(rect2_clip_result.width * rect1.width / rect2.width),
                                int(rect2_clip_result.height * rect1.height / rect2.height))
        
        return preserved_rect1, rect2_clip_result
    
    def clip_and_adjust_from_oldfather_to_newfather(self, oldfather_srcrect: Rect, oldfather_dstrect: Rect, oldtonew_srcrect: Rect, oldtonew_dstrect: Rect):
        rect1 = oldfather_srcrect
        rect2 = oldfather_dstrect
        rect3 = oldtonew_srcrect
        rect4 = oldtonew_dstrect
        
        rect3, rect4 = self.clip_to_father(rect3, rect4)
        if rect3.width <= 0 or rect3.height <= 0:
            newfather_srcrect = Rect(rect1.left, rect1.top, 0, 0)
            newfather_dstrect = Rect(rect2.left, rect2.top, 0, 0)
        else:
        
            
            rect2_clip_result = rect2.clip(rect3)

            preserved_relative_rect2 = Rect(rect2_clip_result.left - rect2.left,
                                rect2_clip_result.top - rect2.top,
                                rect2_clip_result.width,
                                rect2_clip_result.height)
            
            preserved_percent_width = rect2_clip_result.width / rect2.width
            preserved_percent_height = rect2_clip_result.height / rect2.height

            preserved_width = int(rect1.width * preserved_percent_width)
            preserved_height = int(rect1.height * preserved_percent_height)
            preserved_rect1 = Rect(rect1.left + int(preserved_relative_rect2.left * rect1.width / rect2.width),
                                rect1.top + int(preserved_relative_rect2.top * rect1.height / rect2.height),
                                preserved_width,
                                preserved_height)

            rect5 = Rect(int((rect2_clip_result.left - rect3.left) * rect4.width / rect3.width) + rect4.left,
                                int((rect2_clip_result.top - rect3.top)  * rect4.height / rect3.height) + rect4.top,
                                int(rect2_clip_result.width * rect4.width / rect3.width),
                                int(rect2_clip_result.height * rect4.height / rect3.height))
            
            newfather_srcrect = preserved_rect1
            newfather_dstrect = rect5

        return newfather_srcrect, newfather_dstrect
    
    def clip_and_adjust_a_newfather(self, old_srcrect: Rect, old_dstrect: Rect, adjust_srcrect: Rect, adjust_dstrect: Rect):
        rect1 = old_srcrect
        rect2 = old_dstrect
        rect3 = adjust_srcrect
        rect4 = adjust_dstrect
        
        
        rect2_clip_result = rect2.clip(rect3)
        if rect3.width <= 0 or rect3.height <= 0:
            newfather_srcrect = Rect(rect1.left, rect1.top, 0, 0)
            newfather_dstrect = Rect(rect2.left, rect2.top, 0, 0)
        else:
            
            preserved_relative_rect2 = Rect(rect2_clip_result.left - rect2.left,
                                rect2_clip_result.top - rect2.top,
                                rect2_clip_result.width,
                                rect2_clip_result.height)
            
            preserved_percent_width = rect2_clip_result.width / rect2.width
            preserved_percent_height = rect2_clip_result.height / rect2.height

            preserved_width = int(rect1.width * preserved_percent_width)
            preserved_height = int(rect1.height * preserved_percent_height)
            preserved_rect1 = Rect(rect1.left + int(preserved_relative_rect2.left * rect1.width / rect2.width),
                                rect1.top + int(preserved_relative_rect2.top * rect1.height / rect2.height),
                                preserved_width,
                                preserved_height)

            rect5 = Rect(int((rect2_clip_result.left - rect3.left) * rect4.width / rect3.width) + rect4.left,
                                int((rect2_clip_result.top - rect3.top)  * rect4.height / rect3.height) + rect4.top,
                                int(rect2_clip_result.width * rect4.width / rect3.width),
                                int(rect2_clip_result.height * rect4.height / rect3.height))
            
            newfather_srcrect = preserved_rect1
            newfather_dstrect = rect5

        return newfather_srcrect, newfather_dstrect
    
    def clip_to_target(self, srcrect: Rect, dstrect: Rect, target_rect: Rect):
        rect1 = srcrect
        rect2 = dstrect
        if rect2.width <=0 or rect2.height <=0:
            preserved_rect1 = Rect(rect1.left, rect1.top, 0, 0)
            rect2_clip_result = Rect(rect2.left, rect2.top, 0, 0)
        else:
            rect2_clip_result = rect2.clip(target_rect)
            preserved_rect1 = Rect(rect1.left + int((rect2_clip_result.left - rect2.left) * rect1.width / rect2.width),
                                rect1.top + int((rect2_clip_result.top - rect2.top) * rect1.height / rect2.height),
                                int(rect2_clip_result.width * rect1.width / rect2.width),
                                int(rect2_clip_result.height * rect1.height / rect2.height))
        
        return preserved_rect1, rect2_clip_result
    
    def clip_and_adjust_from_father_to_renderer(self, father_srcrect: Rect, father_dstrect: Rect, torenderer_srcrect: Rect, torenderer_dstrect: Rect):
        rect1 = father_srcrect
        rect2 = father_dstrect
        rect3 = torenderer_srcrect
        rect4 = torenderer_dstrect
        
        if rect2.width <=0 or rect2.height <=0:
            return Rect(rect1.left, rect1.top, 0, 0), Rect(rect2.left, rect2.top, 0, 0)
        
        rect2_clip_result = rect2.clip(rect3)
        # rect3, rect4 = self.clip_to_target(rect3, rect4, Rect((0, 0),self.father_texture.renderer.logical_size))
        if rect3.width <= 0 or rect3.height <= 0:
            renderer_srcrect = Rect(rect1.left, rect1.top, 0, 0)
            renderer_dstrect = Rect(rect2.left, rect2.top, 0, 0)
        else:
            preserved_relative_rect2 = Rect(rect2_clip_result.left - rect2.left,
                                rect2_clip_result.top - rect2.top,
                                rect2_clip_result.width,
                                rect2_clip_result.height)
            
            preserved_percent_width = rect2_clip_result.width / rect2.width
            preserved_percent_height = rect2_clip_result.height / rect2.height

            preserved_width = int(rect1.width * preserved_percent_width)
            preserved_height = int(rect1.height * preserved_percent_height)
            preserved_rect1 = Rect(rect1.left + int(preserved_relative_rect2.left * rect1.width / rect2.width),
                                rect1.top + int(preserved_relative_rect2.top * rect1.height / rect2.height),
                                preserved_width,
                                preserved_height)

            rect5 = Rect(int((rect2_clip_result.left - rect3.left) * rect4.width / rect3.width) + rect4.left,
                                int((rect2_clip_result.top - rect3.top)  * rect4.height / rect3.height) + rect4.top,
                                int(rect2_clip_result.width * rect4.width / rect3.width),
                                int(rect2_clip_result.height * rect4.height / rect3.height))
            
            renderer_srcrect = preserved_rect1
            renderer_dstrect = rect5

        return renderer_srcrect, renderer_dstrect
    
    def adjust_texture_data_to_draw(self, texture_data: dict, adjust_srcrect: Rect=None, adjust_dstrect: Union[Tuple, Rect] = None, adjust_angle=0, adjust_flip_x=False, adjust_flip_y=False) -> dict:
        new_texture_data = {}
        new_srcrect, new_dstrect = self.clip_and_adjust_from_father_to_renderer(texture_data["srcrect"], texture_data["dstrect"], adjust_srcrect, adjust_dstrect)
        
        new_texture_data["texture"] = texture_data["texture"]
        new_texture_data["srcrect"] = new_srcrect
        new_texture_data["dstrect"] = new_dstrect
        new_texture_data["angle"] = texture_data["angle"] + adjust_angle
        new_texture_data["flip_x"] = texture_data["flip_x"] ^ adjust_flip_x
        new_texture_data["flip_y"] = texture_data["flip_y"] ^ adjust_flip_y
        self.calculate_rotate(new_texture_data, adjust_angle)
        return new_texture_data
    
    def check_if_empty(self, texture_data):
        if texture_data is None:
            return True
        elif texture_data["srcrect"].width <= 1 or texture_data["srcrect"].height <= 1:
            return True
        elif texture_data["dstrect"].width <= 1 or texture_data["dstrect"].height <= 1:
            return True
        else:
            return False
        
    def check_if_override(self, texture_data: dict):
        if texture_data["can_override"]:
            if texture_data["dstrect"].contains(self.father_dstrect) or texture_data["dstrect"] == self.father_dstrect:
                if texture_data["color"].a == 255:
                    return True
        
        return False
    
    def copy(self):
        new_texture_layer = TextureLayer(self.renderer, size=self.father_dstrect.size)
        new_texture_layer.father_texture = self.father_texture
        new_texture_layer.father_srcrect = self.father_srcrect.copy()
        new_texture_layer.father_dstrect = self.father_dstrect.copy()
        new_texture_layer.father_angle = self.father_angle
        new_texture_layer.father_flip_x = self.father_flip_x
        new_texture_layer.father_flip_y = self.father_flip_y
        new_texture_layer.father_color = Color(self.father_color.r, self.father_color.g, self.father_color.b, self.father_color.a)
        new_texture_layer.parent_texture_layer = self.parent_texture_layer
        new_texture_layer.sub_rect = copy(self.sub_rect)
        new_texture_layer.renderer = self.renderer
        new_texture_layer.texture_list_maxlen = self.texture_list_maxlen
        new_texture_layer.texture_list = deque(maxlen=self.texture_list_maxlen)
        new_texture_layer.blend_mode = self.blend_mode
        for texture_data in self.texture_list:
            new_texture_data = {}
            new_texture_data["texture"] = texture_data["texture"]
            new_texture_data["srcrect"] = texture_data["srcrect"].copy()
            new_texture_data["dstrect"] = texture_data["dstrect"].copy()
            new_texture_data["angle"] = texture_data["angle"] 
            new_texture_data["flip_x"] = texture_data["flip_x"] 
            new_texture_data["flip_y"] = texture_data["flip_y"]
            new_texture_data["color"] = Color(texture_data["color"].r, texture_data["color"].g, texture_data["color"].b, texture_data["color"].a)
            new_texture_data["can_override"] = texture_data["can_override"]
            new_texture_data["can_clean"] = texture_data["can_clean"]
            new_texture_layer.texture_list.append(new_texture_data)
        return new_texture_layer
    
    def draw(self, srcrect: Rect=None, dstrect: Rect=None, dest: Union[Tuple, Rect] = None, area: Rect = None, angle=0, flip_x=False, flip_y=False):
        if srcrect is None:
            srcrect = self.father_dstrect.copy()
        else:
            srcrect = srcrect.copy()
        if area is not None:
            srcrect = area.copy()
        if dstrect is None:
            dstrect = srcrect.copy()
        else:
            dstrect = dstrect.copy()
        if dest is not None:
            if isinstance(dest, Rect):
                dstrect.left += dest.left
                dstrect.top += dest.top
            else:
                dstrect.left += dest[0]
                dstrect.top += dest[1]
        father_texture_data = {
            "texture" : self.father_texture,
            "srcrect" : self.father_srcrect,
            "dstrect" : self.father_dstrect,
            "angle" : self.father_angle,
            "flip_x" : self.father_flip_x,
            "flip_y" : self.father_flip_y,
        }
        new_father_texture_data = self.adjust_texture_data_to_draw(father_texture_data, srcrect, dstrect, angle, flip_x, flip_y)
        if self.check_if_empty(new_father_texture_data):
            pass
        else:
            new_father_texture_data.pop("texture")
            self.father_texture.color = self.father_color
            self.father_texture.alpha = self.father_color.a
            self.father_texture.draw(**new_father_texture_data)
            self.father_texture.color = Color(255,255,255,255)
            self.father_texture.alpha = 255
        # print(f"father_texture {self.father_texture} draw in {drawed_dstrect}")
        for texture_data in self.texture_list:
            new_texture_data = self.adjust_texture_data_to_draw(texture_data, srcrect, dstrect, angle, flip_x, flip_y)
            if self.check_if_empty(new_texture_data):
                continue
            else:
                texture = new_texture_data.pop("texture")
                texture.color = texture_data["color"]
                texture.alpha = texture_data["color"].a
                texture.draw(**new_texture_data)
                texture.color = Color(255,255,255,255)
                texture.alpha = 255
                # print(f"new_texture draw")
    
    def scale_by(self, scale: Tuple[float, float]):
        scale_x = scale[0]
        scale_y = scale[1]
        self.father_dstrect.left = self.father_dstrect.left * scale_x
        self.father_dstrect.top = self.father_dstrect.top * scale_y
        self.father_dstrect.width = self.father_dstrect.width * scale_x
        self.father_dstrect.height = self.father_dstrect.height * scale_y
        for texture_data in self.texture_list:
            texture_data["dstrect"].left = texture_data["dstrect"].left * scale_x
            texture_data["dstrect"].top = texture_data["dstrect"].top * scale_y
            texture_data["dstrect"].width = texture_data["dstrect"].width * scale_x
            texture_data["dstrect"].height = texture_data["dstrect"].height * scale_y
        return self
    
    def scale_to(self, size: Tuple[int, int]):
        scale_x = size[0] / self.father_dstrect.width
        scale_y = size[1] / self.father_dstrect.height
        self.father_dstrect.left = self.father_dstrect.left * scale_x
        self.father_dstrect.top = self.father_dstrect.top * scale_y
        self.father_dstrect.width = self.father_dstrect.width * scale_x
        self.father_dstrect.height = self.father_dstrect.height * scale_y
        for texture_data in self.texture_list:
            texture_data["dstrect"].left = texture_data["dstrect"].left * scale_x
            texture_data["dstrect"].top = texture_data["dstrect"].top * scale_y
            texture_data["dstrect"].width = texture_data["dstrect"].width * scale_x
            texture_data["dstrect"].height = texture_data["dstrect"].height * scale_y
        return self
    
    def calculate_rotate(self, texture_data: dict, angle):
        """Rotate a point around another point."""
        x = texture_data["dstrect"].centerx
        y = texture_data["dstrect"].centery
        center_x = self.father_dstrect.centerx
        center_y = self.father_dstrect.centery
        angle_rad = np.radians(angle)
        
        new_x = center_x + (x - center_x) * np.cos(angle_rad) - (y - center_y) * np.sin(angle_rad)
        new_y = center_y + (x - center_x) * np.sin(angle_rad) + (y - center_y) * np.cos(angle_rad)
        
        texture_data["dstrect"].centerx = new_x
        texture_data["dstrect"].centery = new_y
        
        return (new_x, new_y)
        
        
    def rotate(self, angle: float):
        self.father_angle += angle
        for texture_data in self.texture_list:
            self.calculate_rotate(texture_data, angle)
        return self
    
    def flip(self, flip_x=False, flip_y=False):
        self.father_flip_x = self.father_flip_x ^ flip_x
        self.father_flip_y = self.father_flip_y ^ flip_y
        for texture_data in self.texture_list:
            texture_data["flip_x"] = texture_data["flip_x"] ^ flip_x
            texture_data["flip_y"] = texture_data["flip_y"] ^ flip_y
        return self
    
    def fill(self, color, rect: Rect=None, special_flags=0):
        color = self.transfer_colortype_to_color(color)
        color_surface = Surface(self.father_dstrect.size, flags=SRCALPHA, depth=32)
        color_surface.fill(Color(color.r, color.g, color.b), rect=rect, special_flags=special_flags)
        if color.a >= 255 or color.a <= 0:
            if rect is None or rect == self.father_dstrect:
                self.refresh(color_surface)
                self.product_alpha(color.a)
                return self
        self.extend(color_surface)
        self.product_alpha(color.a)
        return self
    
    def clip(self, rect: Rect):
        self.father_srcrect, self.father_dstrect = self.clip_to_target(self.father_srcrect, self.father_dstrect, rect)
        for texture_data in self.texture_list:
            texture_data["srcrect"], texture_data["dstrect"] = self.clip_to_target(texture_data["srcrect"], texture_data["dstrect"], rect)
        return self
    
    def clean(self):
        new_texture_list = deque(maxlen=self.texture_list_maxlen)
        for texture_data in self.texture_list:
            if not texture_data["can_clean"]:
                new_texture_list.append(texture_data)
        self.texture_list = new_texture_list
    
    def subtexture(self, rect: Rect):
        subtexture = TextureLayer(self.renderer, texture=self.father_texture)
        sub_father_srcrect, sub_father_dstrect = self.clip_to_target(self.father_srcrect, self.father_dstrect, rect)
        subtexture.father_srcrect = sub_father_srcrect
        subtexture.father_dstrect = sub_father_dstrect
        subtexture.father_color = Color(self.father_color.r, self.father_color.g, self.father_color.b, self.father_color.a)
        subtexture.texture_list_maxlen = self.texture_list_maxlen
        subtexture.blend_mode = self.blend_mode
        for texture_data in self.texture_list:
            sub_texture_srcrect, sub_texture_dstrect = self.clip_to_target(texture_data["srcrect"], texture_data["dstrect"], rect)
            sub_texture_data = texture_data
            sub_texture_data["srcrect"] = sub_texture_srcrect
            sub_texture_data["dstrect"] = sub_texture_dstrect
        subtexture.parent_texture_layer = self
        subtexture.sub_rect = rect
        subtexture.renderer = self.renderer
        return subtexture
    
    def get_parent(self):
        return self.parent_texture_layer
    
    def get_offset(self):
        if self.sub_rect is None:
            return (0, 0)
        else:
            return self.sub_rect.topleft
    
    def get_list_number(self):
        return len(self.texture_list)
    
    def get_alpha(self):
        return self.father_color.a
    
    def set_alpha(self, alpha: int):
        self.father_color.a = alpha
        for texture_data in self.texture_list:
            texture_data["color"].a = alpha
    
    def product_alpha(self, alpha: int):
        convert_alpha = alpha / 255
        convert_alpha = min(max(convert_alpha, 0), 1)
        convert_father_alpha = self.father_color.a / 255
        self.father_color.a = int(min(max(convert_father_alpha * convert_alpha * 255, 0), 255))
        for texture_data in self.texture_list:
            convert_texture_alpha = texture_data["color"].a / 255
            texture_data["color"].a = int(min(max(convert_texture_alpha * convert_alpha * 255, 0), 255))
    
    def get_color(self):
        return Color(self.father_color.r, self.father_color.g, self.father_color.b, self.father_color.a)
    
    def set_color(self, color):
        color = self.transfer_colortype_to_color(color)
        self.father_color = color
        for texture_data in self.texture_list:
            texture_data["color"] = color
            
            
    def product_color(self, color):
        color = self.transfer_colortype_to_color(color)
        father_product_color = self.product_two_color(self.father_color, color)
        self.father_color = father_product_color
        for texture_data in self.texture_list:
            texture_product_color = self.product_two_color(texture_data["color"], color)
            texture_data["color"] = texture_product_color
        
    def get_blend_mode(self):
        return self.blend_mode
    
    def set_blend_mode(self, blend_mode: int):
        self.blend_mode = blend_mode
        self.father_texture.blend_mode = blend_mode
        for texture_data in self.texture_list:
            texture_data["texture"].blend_mode = blend_mode
    
    def refresh(self, surface: Union[Surface, Texture]):
        if isinstance(surface, Surface):
            self.father_texture = Texture.from_surface(self.renderer, surface)
        else:
            self.father_texture = surface
        self.father_srcrect = self.father_texture.get_rect().copy()
        # self.father_dstrect = self.father_texture.get_rect()
        self.texture_list.clear()
        
    def draw_rect(self, color: Color, rect: Rect=None, width : int=0):
        fresh_surface = Surface(self.father_dstrect.size, flags=SRCALPHA, depth=32)
        fresh_surface.fill(Color(0,0,0,0))
        draw.rect(fresh_surface, color, rect, width)
        self.extend(fresh_surface, can_override=False)
    
    def draw_line(self, color: Color, start_pos: tuple, end_pos: tuple, width : int=1):
        fresh_surface = Surface(self.father_dstrect.size, flags=SRCALPHA, depth=32)
        fresh_surface.fill(Color(0,0,0,0))
        draw.line(fresh_surface, color, start_pos, end_pos, width)
        self.extend(fresh_surface, can_override=False)
        
    def draw_circle(self, color: Color, center: tuple, radius : int=1, width : int=0):
        fresh_surface = Surface(self.father_dstrect.size, flags=SRCALPHA, depth=32)
        fresh_surface.fill(Color(0,0,0,0))
        draw.circle(fresh_surface, color, center, radius, width)
        self.extend(fresh_surface, can_override=False)
        
    def draw_ellipse(self, color: Color, bounding_rect: Rect, width : int=0):
        fresh_surface = Surface(self.father_dstrect.size, flags=SRCALPHA, depth=32)
        fresh_surface.fill(Color(0,0,0,0))
        draw.ellipse(fresh_surface, color, bounding_rect, width)
        self.extend(fresh_surface, can_override=False)
        
    def convert_alpha(self):
        return self
    
    def get_rect(self):
        return self.father_dstrect.copy()
        
    def get_size(self):
        return self.father_dstrect.size
    
    def get_width(self):
        return self.father_dstrect.width
    
    def get_height(self):
        return self.father_dstrect.height
    
    @staticmethod    
    def convert_color_to_float(color: Color):
        convert_color = (color.r / 255, color.g / 255, color.b / 255, color.a / 255)
        return convert_color
    
    @staticmethod
    def convert_float_to_color(color: tuple):
        r = min(max(int(color[0] * 255), 0), 255)
        g = min(max(int(color[1] * 255), 0), 255)
        b = min(max(int(color[2] * 255), 0), 255)
        a = min(max(int(color[3] * 255), 0), 255)
        convert_color = Color(r, g, b, a)
        return convert_color
    
    @staticmethod
    def product_two_color(color1: Color, color2: Color):
        convert_color1 = TextureLayer.convert_color_to_float(color1)
        convert_color2 = TextureLayer.convert_color_to_float(color2)
        product_color = (convert_color1[0] * convert_color2[0], convert_color1[1] * convert_color2[1], convert_color1[2] * convert_color2[2], convert_color1[3] * convert_color2[3])
        return TextureLayer.convert_float_to_color(product_color)
    
    @staticmethod
    def transfer_colortype_to_color(color):
        if isinstance(color, tuple):
            return Color(*color)
        elif isinstance(color, str):
            return Color(color)
        else:
            return Color(color.r, color.g, color.b, color.a)
    