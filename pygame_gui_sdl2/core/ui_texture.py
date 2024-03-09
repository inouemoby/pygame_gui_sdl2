from pygame._sdl2 import Texture, Renderer
from pygame import Rect, Surface, Color, draw, SRCALPHA

from typing import Tuple, List, Union
from copy import copy
from warnings import warn
from collections import deque
import numpy as np

from pygame_gui_sdl2._constants import *


# 似乎可以用renderer提前设置target一个texture把两个texture合并，后续优化可以尝试这个思路

class TextureLayer:
    
    default_scale_type = SCALE_EMBED
    
    def __init__(self, renderer: Renderer, size: Tuple[int, int] , maxlen: int=6, target=False):
        if renderer is None:
            raise ValueError("renderer cannot be None")
        self.renderer = renderer
        self.empty_texture = Texture(self.renderer, size=(1,1), target=True, scale_quality=0)
        self.blend_mode = 1
        self.renderer.draw_blend_mode = self.blend_mode
        if size[0] <= 0 or size[1] <= 0:
            self.father_texture = self.empty_texture
            # self.father_texture.alpha = 0
        else:
            self.father_texture = Texture(renderer=renderer, size=size, target=True, scale_quality=2)
            
        self.father_texture.blend_mode = self.blend_mode

        self.father_texture_data = {
            "srcrect" : self.father_texture.get_rect().copy(),
            "dstrect" : self.father_texture.get_rect().copy(),
            "angle" : 0,
            "flip_x" : False,
            "flip_y" : False
        }
        self.father_color = Color(255, 255, 255, 255)
        self.renderer = renderer
        # self.parent_texture_layer = None
        # self.sub_rect: Rect = None
        self.effect_texture_list_maxlen = maxlen
        self.effect_texture_list = deque(maxlen=self.effect_texture_list_maxlen) # 转变思路，用来储存
        
        self.target = target
        self.clear_color = Color('#00000000')
        
        
        self.image_texture_layer = self.empty_texture # 一个layer只能显示一张图片纹理，不如说为什么要显示那么多不同的纹理在一个单元上
        self.image_texture_layer_data = {
            "srcrect" : self.image_texture_layer.get_rect().copy(),
            "dstrect" : self.image_texture_layer.get_rect().copy(),
            "angle" : 0,
            "flip_x" : False,
            "flip_y" : False,
            "color" : Color("#FFFFFFFF")
        }
        # self.image_texture_layer.blend_mode = self.blend_mode
        self.effect_texture_layer = Texture(self.renderer, size=self.father_texture.get_rect().size, target=True, scale_quality=2)
        # self.effect_texture_layer.blend_mode = self.blend_mode
        
        self.render_list = []
        if target:
            self.background_texture_layer = Texture(self.renderer, size=self.father_texture.get_rect().size, target=True, scale_quality=2)
            self.text_shadow_texture_layer = Texture(self.renderer, size=self.father_texture.get_rect().size, target=True, scale_quality=2)
            self.text_texture_layer = Texture(self.renderer, size=self.father_texture.get_rect().size, target=True, scale_quality=2)
            self.top_texture_layer = Texture(self.renderer, size=self.father_texture.get_rect().size, target=True, scale_quality=2)

            # self.background_texture_layer.blend_mode = self.blend_mode
            # self.text_shadow_texture_layer.blend_mode = self.blend_mode
            # self.text_texture_layer.blend_mode = self.blend_mode
            # self.top_texture_layer.blend_mode = self.blend_mode
            
            self.render_list.append(self.background_texture_layer)
            self.render_list.append(self.image_texture_layer)
            self.render_list.append(self.text_shadow_texture_layer)
            self.render_list.append(self.text_texture_layer)
            self.render_list.append(self.top_texture_layer)
        else:
            self.render_list.append(self.image_texture_layer)
        self.render_list.append(self.effect_texture_layer)
        
        _color_surface = Surface((1, 1))
        _color_surface.fill('#FFFFFFFF')
        self._color_texture = Texture.from_surface(self.renderer, _color_surface)
        self._color_texture.color = Color(255, 255, 255)
        self._color_texture.alpha = 255
        self._color_texture.blend_mode = self.blend_mode
        self.set_blend_mode(self.blend_mode)
        self.clear_all()
        # self._color_texture.blend_mode = self.blend_mode
        # self.texture_list = []
        # print("init TextureLayer")
        
    def render_to_background(self, target_texture: Union[Texture, Surface], srcrect: Rect=None, dstrect: Rect=None, dest: Union[Tuple, Rect] = None, area: Rect = None, angle=0, flip_x=False, flip_y=False, color = Color('#FFFFFFFF')):
        if self.target:
            if isinstance(target_texture, Surface):
                target_texture = Texture.from_surface(self.renderer, target_texture)
            
            if isinstance(target_texture, Texture):
                self.background_texture_layer = self.render_to_target(target_texture, self.background_texture_layer, srcrect, dstrect, dest, area, angle, flip_x, flip_y, color)
                # print("render_to_background")
            else:
                raise ValueError("target_texture should be a Texture or a Surface")
        else:
            raise ValueError("This TextureLayer is not a target")
    
    def render_to_text_shadow(self, target_texture: Union[Texture, Surface], srcrect: Rect=None, dstrect: Rect=None, dest: Union[Tuple, Rect] = None, area: Rect = None, angle=0, flip_x=False, flip_y=False, color = Color('#FFFFFFFF')):
        if self.target:
            if isinstance(target_texture, Surface):
                target_texture = Texture.from_surface(self.renderer, target_texture)
            
            if isinstance(target_texture, Texture):
                self.text_shadow_texture_layer = self.render_to_target(target_texture, self.text_shadow_texture_layer, srcrect, dstrect, dest, area, angle, flip_x, flip_y, color)
                
            else:
                raise ValueError("target_texture should be a Texture or a Surface")
        else:
            raise ValueError("This TextureLayer is not a target")
        
    def render_to_text(self, target_texture: Union[Texture, Surface], srcrect: Rect=None, dstrect: Rect=None, dest: Union[Tuple, Rect] = None, area: Rect = None, angle=0, flip_x=False, flip_y=False, color = Color('#FFFFFFFF')):
        if self.target:
            if isinstance(target_texture, Surface):
                target_texture = Texture.from_surface(self.renderer, target_texture)
            
            if isinstance(target_texture, Texture):
                self.text_texture_layer = self.render_to_target(target_texture, self.text_texture_layer, srcrect, dstrect, dest, area, angle, flip_x, flip_y, color)
            else:
                raise ValueError("target_texture should be a Texture or a Surface")
        else:
            raise ValueError("This TextureLayer is not a target")
        
    def render_to_top(self, target_texture: Union[Texture, Surface], srcrect: Rect=None, dstrect: Rect=None, dest: Union[Tuple, Rect] = None, area: Rect = None, angle=0, flip_x=False, flip_y=False, color = Color('#FFFFFFFF')):
        if self.target:
            if isinstance(target_texture, Surface):
                target_texture = Texture.from_surface(self.renderer, target_texture)
            
            if isinstance(target_texture, Texture):
                self.top_texture_layer = self.render_to_target(target_texture, self.top_texture_layer, srcrect, dstrect, dest, area, angle, flip_x, flip_y, color)
                
            else:
                raise ValueError("target_texture should be a Texture or a Surface")
        else:
            raise ValueError("This TextureLayer is not a target")
    
    def render_to_father(self, target_texture: Texture, srcrect: Rect=None, dstrect: Rect=None, dest: Union[Tuple, Rect] = None, area: Rect = None, angle=0, flip_x=False, flip_y=False, color = Color('#FFFFFFFF')):

        self.father_texture = self.render_to_target(target_texture, self.father_texture, srcrect, dstrect, dest, area, angle, flip_x, flip_y, color)
    
    
    def render_to_target(self, target_texture: Texture, dest_texture: Texture = None, srcrect: Rect=None, dstrect: Rect=None, dest: Union[Tuple, Rect] = None, area: Rect = None, angle=0, flip_x=False, flip_y=False, color = Color('#FFFFFFFF')):
        target_texture.blend_mode = self.blend_mode
        # target_texture = self.copy_texture(target_texture)
        if srcrect is None:
            srcrect = target_texture.get_rect().copy()
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
        
        if dest_texture is not None:
            dest_texture_rect = dest_texture.get_rect()
            srcrect, dstrect = self.clip_to_target(srcrect, dstrect, dest_texture_rect)
            new_dest_texture = Texture(self.renderer, size=dest_texture_rect.size, target=True, scale_quality=2)
            self.renderer.target = new_dest_texture
            self.renderer.draw_color = self.clear_color.rgba
            self.renderer.clear()
            dest_texture.blend_mode = self.blend_mode
            new_dest_texture.blend_mode = self.blend_mode
            if color.a != 255:
                dest_texture.alpha = 255
                top_rect = Rect(0, 0, dest_texture_rect.width, dstrect.top)
                bottom_rect = Rect(0, dstrect.bottom, dest_texture_rect.width, dest_texture_rect.height - dstrect.bottom)
                left_rect = Rect(0, dstrect.top, dstrect.left, dstrect.height)
                right_rect = Rect(dstrect.right, dstrect.top, dest_texture_rect.width - dstrect.right, dstrect.height)
                dest_texture.draw(srcrect=top_rect, dstrect=top_rect)
                dest_texture.draw(srcrect=bottom_rect, dstrect=bottom_rect)
                dest_texture.draw(srcrect=left_rect, dstrect=left_rect)
                dest_texture.draw(srcrect=right_rect, dstrect=right_rect)
                dest_texture.alpha = color.a
                dest_texture.draw(srcrect=dstrect, dstrect=dstrect)
            else:
                dest_texture.alpha = 255
                dest_texture.draw()
            dest_texture.alpha = 255
        else:
            self.renderer.target = None
            
        new_dstrect, new_srcrect = self.clip_to_target(dstrect, srcrect, target_texture.get_rect())
        
        target_texture_color = Color(target_texture.color.rgb)
        target_texture_color.a = target_texture.alpha
        target_producted_color = self.product_two_color(target_texture_color, color)
        target_texture.color = Color(target_producted_color.rgb)
        target_texture.alpha = target_producted_color.a
        target_texture.draw(srcrect=new_srcrect, dstrect=new_dstrect, angle=angle, flip_x=flip_x, flip_y=flip_y)
        target_texture.color = Color(target_texture_color.rgb)
        target_texture.alpha = target_texture_color.a
        
        self.renderer.draw_color = self.clear_color.rgba
        self.renderer.target = None
        if dest_texture is not None:
            return new_dest_texture
        return None
        
        
    def clear_background(self):
        if self.target:
            self.renderer.target = self.background_texture_layer
            self.renderer.draw_color = self.clear_color.rgba
            self.renderer.clear()
        else:
            raise ValueError("This TextureLayer is not a target")
    
    def clear_text_shadow(self):
        if self.target:
            self.renderer.target = self.text_shadow_texture_layer
            self.renderer.draw_color = self.clear_color.rgba
            self.renderer.clear()
            # print("clear_text_shadow")
        else:
            raise ValueError("This TextureLayer is not a target")
        
    def clear_text(self):
        if self.target:
            self.renderer.target = self.text_texture_layer
            self.renderer.draw_color = self.clear_color.rgba
            self.renderer.clear()
            # print("clear_text")
        else:
            raise ValueError("This TextureLayer is not a target")
        
    def clear_top(self):
        if self.target:
            self.renderer.target = self.top_texture_layer
            self.renderer.draw_color = self.clear_color.rgba
            self.renderer.clear()
            # print(f"clear_top {self.clear_color.rgba}")
        else:
            raise ValueError("This TextureLayer is not a target")
    
    def clear_effect(self):
        self.renderer.target = self.effect_texture_layer
        self.renderer.draw_color = self.clear_color.rgba
        self.renderer.clear()
        
    def clear_father(self):
        self.renderer.target = self.father_texture
        self.renderer.draw_color = self.clear_color.rgba
        self.renderer.clear()
        
    def clear_image(self):
        self.image_texture_layer = self.copy_texture(self.empty_texture)
        self.image_texture_layer_data = {
            "srcrect" : self.image_texture_layer.get_rect().copy(),
            "dstrect" : self.image_texture_layer.get_rect().copy(),
            "angle" : 0,
            "flip_x" : False,
            "flip_y" : False,
            "color" : Color("#FFFFFFFF")
        }
        
    def clear_all(self):
        self.clear_render_layer()
        self.clear_image()
        # print("clear_all")
    
    def clear_render_layer(self):
        if self.target:
            self.clear_background()
            self.clear_text_shadow()
            self.clear_text()
            self.clear_top()
        self.clear_father()
        # self.clear_effect()
        # print("clear_render_layer")
        
    def rebuild_father_texture(self, size: Tuple[int, int] = None):
        '''这个方法将还原所有的clip，与scale不同。'''
        self.father_texture = Texture(self.renderer, size=size, target=True, scale_quality=2)
        self.father_texture_data = {
            "srcrect" : self.father_texture.get_rect().copy(),
            "dstrect" : self.father_texture.get_rect().copy(),
            "angle" : 0,
            "flip_x" : False,
            "flip_y" : False
        }
        self.father_color = Color(255, 255, 255, 255)
        self.rebuild_render_layer()
        self.set_blend_mode()
        self.clear_all()
        # print("rebuild_father_texture")
    
    def rebuild_render_layer(self):
        # self.clear_render_layer()
        if self.target:
            self.background_texture_layer = Texture(self.renderer, size=self.father_texture.get_rect().size, target=True, scale_quality=2)
            self.text_shadow_texture_layer = Texture(self.renderer, size=self.father_texture.get_rect().size, target=True, scale_quality=2)
            self.text_texture_layer = Texture(self.renderer, size=self.father_texture.get_rect().size, target=True, scale_quality=2)
            self.top_texture_layer = Texture(self.renderer, size=self.father_texture.get_rect().size, target=True, scale_quality=2)
        self.effect_texture_layer = Texture(self.renderer, size=self.father_texture.get_rect().size, target=True, scale_quality=2)
        self.clear_render_layer()
    
    def blit(self, texture: Union[Texture, Surface], dest: Union[Tuple, Rect] = None, area: Rect = None, special_flags=0):
        self.render_to_background(texture, dest=dest, area=area)
        
    def add_effect_texture(self, effect_texture: Union[Texture, Surface]):
        self.effect_texture_list.append(effect_texture)
        pass # 后续设计特效的时候继续补充。目前的思路是使用一个字典记录这个纹理是为了什么特效，并且应该怎么执行
            
    def set_image_texture(self, image_texture: Union[Texture, Surface], scale_type=SCALE_EMBED):
        if isinstance(image_texture, Surface):
            image_texture = Texture.from_surface(self.renderer, image_texture)
        image_rect = image_texture.get_rect()
        target_image_rect = TextureLayer.scale_rect_to_fill(image_rect, self.father_texture.get_rect(), scale_type)
        self.image_texture_layer = self.copy_texture(image_texture)
        self.image_texture_layer_data = {
            "srcrect" : image_rect,
            "dstrect" : target_image_rect,
            "angle" : 0,
            "flip_x" : False,
            "flip_y" : False,
            "color" : Color("#FFFFFFFF")
        }
    
    def merge(self, texture_layer, srcrect: Rect=None, dstrect: Rect=None, dest: Union[Tuple, Rect] = None, scale_type=ORIGINAL, color = Color('#FFFFFFFF')):
        if isinstance(texture_layer, TextureLayer):
            if not srcrect is None or not dstrect is None or not dest is None:
                if srcrect is None:
                    srcrect = texture_layer.father_texture_data["dstrect"].copy()
                else:
                    srcrect = srcrect.copy()
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
                target_rect = dstrect
            else:
                srcrect = texture_layer.father_texture.get_rect()
                target_rect = self.scale_rect_to_fill(texture_layer.father_texture.get_rect(), self.father_texture.get_rect(), scale_type)
            texture_layer.father_texture_data["color"] = texture_layer.father_color
            new_merge_target_data = self.adjust_texture_data_to_draw(texture_layer.father_texture_data, srcrect, target_rect, adjust_color=color)
            new_srcrect = new_merge_target_data["srcrect"]
            new_dstrect = new_merge_target_data["dstrect"]
            new_angle = new_merge_target_data["angle"]
            new_flip_x = new_merge_target_data["flip_x"]
            new_flip_y = new_merge_target_data["flip_y"]
            new_color = new_merge_target_data["color"]
            texture_layer.father_texture_data.pop("color")
            if texture_layer.target:
                self.render_to_background(texture_layer.background_texture_layer, srcrect=new_srcrect, dstrect=new_dstrect, angle=new_angle, flip_x=new_flip_x, flip_y=new_flip_y, color=new_color)
                self.render_to_text_shadow(texture_layer.text_shadow_texture_layer, srcrect=new_srcrect, dstrect=new_dstrect, angle=new_angle, flip_x=new_flip_x, flip_y=new_flip_y, color=new_color)
                self.render_to_text(texture_layer.text_texture_layer, srcrect=new_srcrect, dstrect=new_dstrect, angle=new_angle, flip_x=new_flip_x, flip_y=new_flip_y, color=new_color)
                self.render_to_top(texture_layer.top_texture_layer, srcrect=new_srcrect, dstrect=new_dstrect, angle=new_angle, flip_x=new_flip_x, flip_y=new_flip_y, color=new_color)
            self.image_texture_layer = self.copy_texture(texture_layer.image_texture_layer)
            # self.image_texture_layer_data = {"srcrect" : texture_layer.image_texture_layer_data["srcrect"],
            #                                 "dstrect" : texture_layer.image_texture_layer_data["dstrect"],
            #                                 "angle" : texture_layer.image_texture_layer_data["angle"],
            #                                 "flip_x" : texture_layer.image_texture_layer_data["flip_x"],
            #                                 "flip_y" : texture_layer.image_texture_layer_data["flip_y"],
            #                                 "color" : texture_layer.image_texture_layer_data["color"].rgba}
            
            self.image_texture_layer_data = self.adjust_texture_data_to_draw(texture_layer.image_texture_layer_data, srcrect, target_rect, adjust_color=color)
            # print(self.image_texture_layer_data)
            self.effect_texture_list.extend(texture_layer.effect_texture_list)
            # print("merge")
        else:
            raise ValueError("texture_layer should be a TextureLayer")
        
    def merge_text(self, texture_layer, srcrect: Rect=None, dstrect: Rect=None):
        '''用来合并两个纹理的文字，注意被合并的文字layer是不可以进行变换的，否则不会生效'''
        self.clear_text()
        self.clear_text_shadow()
        if isinstance(texture_layer, TextureLayer):
            if not srcrect is None or not dstrect is None:
                if srcrect is None:
                    srcrect = texture_layer.father_texture.get_rect()
                else:
                    srcrect = srcrect.copy()
                if dstrect is None:
                    dstrect = srcrect.copy()
                else:
                    dstrect = dstrect.copy()
                target_rect = dstrect
            else:
                srcrect = texture_layer.father_texture.get_rect()
                target_rect = self.father_texture.get_rect()
            if texture_layer.target:
                self.render_to_text_shadow(texture_layer.text_shadow_texture_layer, srcrect=srcrect, dstrect=target_rect)
                self.render_to_text(texture_layer.text_texture_layer, srcrect=srcrect, dstrect=target_rect)
            # print("merge")
        else:
            raise ValueError("texture_layer should be a TextureLayer")
    
    def append(self, texture: Union[Texture, Surface], scale_type=ORIGINAL, color = Color('#FFFFFFFF')):
        if isinstance(texture, Surface):
            texture = Texture.from_surface(self.renderer, texture)
        target_rect = self.scale_rect_to_fill(texture.get_rect(), self.father_texture.get_rect(), scale_type)
        self.render_to_top(texture, dstrect=target_rect, color=color)
    
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
        
        if rect2 == rect3:
            return rect1.copy(), rect4.copy()
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
    
    def adjust_texture_data_to_draw(self, texture_data: dict, adjust_srcrect: Rect=None, adjust_dstrect: Union[Tuple, Rect] = None, adjust_angle=0, adjust_flip_x=False, adjust_flip_y=False, adjust_color = Color('#FFFFFFFF')) -> dict:
        new_texture_data = {}
        new_srcrect, new_dstrect = self.clip_and_adjust_from_father_to_renderer(texture_data["srcrect"], texture_data["dstrect"], adjust_srcrect, adjust_dstrect)
        
        new_texture_data["srcrect"] = new_srcrect
        new_texture_data["dstrect"] = new_dstrect
        new_texture_data["angle"] = texture_data["angle"] + adjust_angle
        new_texture_data["flip_x"] = texture_data["flip_x"] ^ adjust_flip_x
        new_texture_data["flip_y"] = texture_data["flip_y"] ^ adjust_flip_y
        new_texture_data["color"] = self.product_two_color(texture_data["color"], adjust_color)
        return new_texture_data
    
    def check_if_empty(self, texture_data):
        if texture_data is None:
            return True
        elif texture_data["dstrect"].width <= 1 or texture_data["dstrect"].height <= 1:
            return True
        else:
            return False
        
    # def check_if_override(self, texture_data: dict):
    #     if texture_data["can_override"]:
    #         if texture_data["dstrect"].contains(self.father_dstrect) or texture_data["dstrect"] == self.father_dstrect:
    #             if texture_data["color"].a == 255:
    #                 return True
        
    #     return False
    
    def copy(self):
        new_texture_layer = TextureLayer(self.renderer, size=self.father_texture.get_rect().size, maxlen=self.effect_texture_list_maxlen, target=self.target)
        new_texture_layer.father_texture_data = {"srcrect" : self.father_texture_data["srcrect"].copy(), 
                                                 "dstrect" : self.father_texture_data["dstrect"].copy(), 
                                                 "angle" : self.father_texture_data["angle"], 
                                                 "flip_x" : self.father_texture_data["flip_x"],
                                                 "flip_y" : self.father_texture_data["flip_x"]}                     
        new_texture_layer.father_color = self.father_color.rgba
        for texture in self.effect_texture_list:
            new_texture_layer.effect_texture_list.append(texture)
        # new_texture_layer.blend_mode = self.blend_mode
        new_texture_layer.image_texture_layer = self.copy_texture(self.image_texture_layer)
        new_texture_layer.image_texture_layer_data = {"srcrect" : self.image_texture_layer_data["srcrect"].copy(),
                                                    "dstrect" : self.image_texture_layer_data["dstrect"].copy(),
                                                    "angle" : self.image_texture_layer_data["angle"],
                                                    "flip_x" : self.image_texture_layer_data["flip_x"],
                                                    "flip_y" : self.image_texture_layer_data["flip_y"],
                                                    "color" : self.image_texture_layer_data["color"].rgba}
        
        if self.target:
            new_texture_layer.background_texture_layer = self.copy_texture(self.background_texture_layer)
            new_texture_layer.text_shadow_texture_layer = self.copy_texture(self.text_shadow_texture_layer)
            new_texture_layer.text_texture_layer = self.copy_texture(self.text_texture_layer)
            new_texture_layer.top_texture_layer = self.copy_texture(self.top_texture_layer)
        # print("copy")
        return new_texture_layer
    
    def copy_background(self) -> Texture:
        if self.target:
            return self.copy_texture(self.background_texture_layer)
        raise ValueError("This TextureLayer is not a target")
    
    def copy_text_shadow(self) -> Texture:
        if self.target:
            return self.copy_texture(self.text_shadow_texture_layer)
        raise ValueError("This TextureLayer is not a target")
    
    def copy_text(self) -> Texture:
        if self.target:
            return self.copy_texture(self.text_texture_layer)
        raise ValueError("This TextureLayer is not a target")
    
    def copy_top(self) -> Texture:
        if self.target:
            return self.copy_texture(self.top_texture_layer)
        raise ValueError("This TextureLayer is not a target")
    
    def draw(self, srcrect: Rect=None, dstrect: Rect=None, dest: Union[Tuple, Rect] = None, area: Rect = None, angle=0, flip_x=False, flip_y=False, color = Color('#FFFFFFFF'), target_texture: Texture=None):
        if srcrect is None:
            srcrect = self.father_texture_data["dstrect"].copy()
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
        new_father_texture_data = {
            "srcrect" : self.father_texture_data["srcrect"],
            "dstrect" : self.father_texture_data["dstrect"],
            "angle" : self.father_texture_data["angle"],
            "flip_x" : self.father_texture_data["flip_x"],
            "flip_y" : self.father_texture_data["flip_y"],
            "color" : self.father_color
        }
        new_father_texture_data = self.adjust_texture_data_to_draw(new_father_texture_data, srcrect, dstrect, angle, flip_x, flip_y)
        if self.check_if_empty(new_father_texture_data):
            pass
        else:
            self.clear_father()
            if self.target:
                self.render_to_father(self.background_texture_layer)
                self.render_to_father(self.image_texture_layer, **self.image_texture_layer_data)
                self.render_to_father(self.text_shadow_texture_layer)
                self.render_to_father(self.text_texture_layer)
                self.render_to_father(self.top_texture_layer)
            else:
                self.render_to_father(self.image_texture_layer, **self.image_texture_layer_data)
            self.render_to_father(self.effect_texture_layer)
            
            return self.render_to_target(self.father_texture, target_texture, **new_father_texture_data)
    
    def scale_by(self, scale: Tuple[float, float]):
        father_dstrect = self.father_texture_data["dstrect"] 
        scale_x = scale[0]
        scale_y = scale[1]
        father_dstrect.left = father_dstrect.left * scale_x
        father_dstrect.top = father_dstrect.top * scale_y
        father_dstrect.width = father_dstrect.width * scale_x
        father_dstrect.height = father_dstrect.height * scale_y
        return self
    
    def scale_to(self, size: Tuple[int, int]):
        father_dstrect = self.father_texture_data["dstrect"] 
        scale_x = size[0] / father_dstrect.width
        scale_y = size[1] / father_dstrect.height
        father_dstrect.left = father_dstrect.left * scale_x
        father_dstrect.top = father_dstrect.top * scale_y
        father_dstrect.width = father_dstrect.width * scale_x
        father_dstrect.height = father_dstrect.height * scale_y
        return self
    
    # def calculate_rotate(self, texture_data: dict, angle):
    #     """Rotate a point around another point."""
    #     x = texture_data["dstrect"].centerx
    #     y = texture_data["dstrect"].centery
    #     center_x = self.father_dstrect.centerx
    #     center_y = self.father_dstrect.centery
    #     angle_rad = np.radians(angle)
        
    #     new_x = center_x + (x - center_x) * np.cos(angle_rad) - (y - center_y) * np.sin(angle_rad)
    #     new_y = center_y + (x - center_x) * np.sin(angle_rad) + (y - center_y) * np.cos(angle_rad)
        
    #     texture_data["dstrect"].centerx = new_x
    #     texture_data["dstrect"].centery = new_y
        
    #     return (new_x, new_y)
        
        
    def rotate(self, angle: float):
        self.father_texture_data["angle"] = self.father_texture_data["angle"] + angle
        return self
    
    def flip(self, flip_x=False, flip_y=False):
        self.father_texture_data["flip_x"] = self.father_texture_data["flip_x"] ^ flip_x
        self.father_texture_data["flip_y"] = self.father_texture_data["flip_y"] ^ flip_y
        return self
    
    def fill_to_background(self, color, rect: Rect=None, special_flags=0):
        color = self.transfer_colortype_to_color(color)
        # print(f"set a color {color}")
        if rect is None:
            dstrect = self.father_texture.get_rect()
        else:
            dstrect = rect.copy()
        self.render_to_background(self._color_texture, dstrect=dstrect, color=color)
        # print("fill_to_background")
        return self
    
    def fill_to_text_shadow(self, color, rect: Rect=None, special_flags=0):
        color = self.transfer_colortype_to_color(color)
        # print(f"set a color {color}")
        if rect is None:
            dstrect = self.father_texture.get_rect()
        else:
            dstrect = rect.copy()
        self.render_to_text_shadow(self._color_texture, dstrect=dstrect, color=color)
        # print("fill_to_text_shadow")
        return self
    
    def fill_to_text(self, color, rect: Rect=None, special_flags=0):
        color = self.transfer_colortype_to_color(color)
        # print(f"set a color {color}")
        if rect is None:
            dstrect = self.father_texture.get_rect()
        else:
            dstrect = rect.copy()
        self.render_to_text(self._color_texture, dstrect=dstrect, color=color)
        # print("fill_to_text")
        return self
    
    def fill_to_top(self, color, rect: Rect=None, special_flags=0):
        color = self.transfer_colortype_to_color(color)
        # print(f"set a color {color}")
        if rect is None:
            dstrect = self.father_texture.get_rect()
        else:
            dstrect = rect.copy()
        self.render_to_top(self._color_texture, dstrect=dstrect, color=color)
        return self
    
    def fill_to_render_layer(self, color, rect: Rect=None, special_flags=0):
        if self.target:
            color = self.transfer_colortype_to_color(color)
            # print(f"set a color {color}")
            if rect is None:
                dstrect = self.father_texture.get_rect()
            else:
                dstrect = rect.copy()
            self.render_to_background(self._color_texture, dstrect=dstrect, color=color)
            self.render_to_text_shadow(self._color_texture, dstrect=dstrect, color=color)
            self.render_to_text(self._color_texture, dstrect=dstrect, color=color)
            self.render_to_top(self._color_texture, dstrect=dstrect, color=color)
            # print("fill_to_render_layer")
        else:
            raise ValueError("This TextureLayer is not a target")
    
    def fill_to_target(self, texture:Union[Texture, Surface], color, rect: Rect=None, special_flags=0) -> Texture:
        color = self.transfer_colortype_to_color(color)
        if isinstance(texture, Surface):
            texture = Texture.from_surface(self.renderer, texture)
        if rect is None:
            dstrect = texture.get_rect()
        else:
            dstrect = rect.copy()
        return self.render_to_target(self._color_texture, texture, dstrect=dstrect, color=color)
    
    def clip(self, rect: Rect):
        father_srcrect, father_dstrect = self.clip_to_target(self.father_texture_data["srcrect"], self.father_texture_data["dstrect"], rect)
        self.father_texture_data["srcrect"] = father_srcrect
        self.father_texture_data["dstrect"] = father_dstrect
        return self
    
    def get_effect_texture_list_number(self):
        return len(self.effect_texture_list)
    
    def get_alpha(self):
        return self.father_color.a
    
    def set_alpha(self, alpha: int):
        self.father_color.a = alpha
        return self.father_color.a
    
    def product_alpha(self, alpha: int):
        convert_alpha = alpha / 255
        convert_alpha = min(max(convert_alpha, 0), 1)
        convert_father_alpha = self.father_color.a / 255
        self.father_color.a = int(min(max(convert_father_alpha * convert_alpha * 255, 0), 255))
        return self.father_color.a
    
    def set_alpha_to_texture(self, dest_texture: Texture, alpha: int, dstrect: Rect=None):
        dest_texture_rect = dest_texture.get_rect()
        if dstrect is None:
            dstrect = dest_texture_rect.copy()
        dstrect = dstrect.clip(dest_texture_rect)
        new_dest_texture = Texture(self.renderer, size=dest_texture_rect.size, target=True, scale_quality=2)
        dest_texture.blend_mode = self.blend_mode
        new_dest_texture.blend_mode = self.blend_mode
        self.renderer.target = new_dest_texture
        self.renderer.draw_color = self.clear_color.rgba
        self.renderer.clear()
        if alpha != 255:
            dest_texture.alpha = 255
            top_rect = Rect(0, 0, dest_texture_rect.width, dstrect.top)
            bottom_rect = Rect(0, dstrect.bottom, dest_texture_rect.width, dest_texture_rect.height - dstrect.bottom)
            left_rect = Rect(0, dstrect.top, dstrect.left, dstrect.height)
            right_rect = Rect(dstrect.right, dstrect.top, dest_texture_rect.width - dstrect.right, dstrect.height)
            dest_texture.draw(srcrect=top_rect, dstrect=top_rect)
            dest_texture.draw(srcrect=bottom_rect, dstrect=bottom_rect)
            dest_texture.draw(srcrect=left_rect, dstrect=left_rect)
            dest_texture.draw(srcrect=right_rect, dstrect=right_rect)
            dest_texture.alpha = alpha
            dest_texture.draw(srcrect=dstrect, dstrect=dstrect)
        else:
            dest_texture.alpha = 255
            dest_texture.draw()
        dest_texture.alpha = 255
        self.renderer.target = None
        return new_dest_texture
    
    def get_color(self):
        return self.father_color.rgba
    
    def set_color(self, color):
        color = self.transfer_colortype_to_color(color)
        self.father_color = color
        return self.father_color.rgba
            
    def product_color(self, color):
        color = self.transfer_colortype_to_color(color)
        father_product_color = self.product_two_color(self.father_color, color)
        self.father_color = father_product_color
        return self.father_color.rgba
        
    def get_blend_mode(self):
        return self.blend_mode
    
    def set_blend_mode(self, blend_mode: int = 1):
        self.blend_mode = blend_mode
        self.renderer.draw_blend_mode = blend_mode
        self.father_texture.blend_mode = blend_mode
        for texture in self.render_list:
            texture.blend_mode = blend_mode
        for texture in self.effect_texture_list:
            texture.blend_mode = blend_mode
    
    # def refresh(self, surface: Union[Surface, Texture]):
    #     if isinstance(surface, Surface):
    #         self.father_texture = Texture.from_surface(self.renderer, surface)
    #     else:
    #         self.father_texture = surface
    #     self.father_srcrect = self.father_texture.get_rect().copy()
    #     self.texture_list.clear()
    #     # print("texture refreshed")
        
    def draw_rect(self, color: Color, rect: Rect=None, width : int=0):
        fresh_surface = Surface(self.father_texture.get_rect().size, flags=SRCALPHA, depth=32)
        fresh_surface.fill(Color(0,0,0,0))
        draw.rect(fresh_surface, color, rect, width)
        self.render_to_background(fresh_surface, dstrect=fresh_surface.get_rect())
    
    def draw_line(self, color: Color, start_pos: tuple, end_pos: tuple, width : int=1):
        fresh_surface = Surface(self.father_texture.get_rect().size, flags=SRCALPHA, depth=32)
        fresh_surface.fill(Color(0,0,0,0))
        draw.line(fresh_surface, color, start_pos, end_pos, width)
        self.render_to_background(fresh_surface, dstrect=fresh_surface.get_rect())
        
    def draw_circle(self, color: Color, center: tuple, radius : int=1, width : int=0):
        fresh_surface = Surface(self.father_texture.get_rect().size, flags=SRCALPHA, depth=32)
        fresh_surface.fill(Color(0,0,0,0))
        draw.circle(fresh_surface, color, center, radius, width)
        self.render_to_background(fresh_surface, dstrect=fresh_surface.get_rect())
        
    def draw_ellipse(self, color: Color, bounding_rect: Rect, width : int=0):
        fresh_surface = Surface(self.father_texture.get_rect().size, flags=SRCALPHA, depth=32)
        fresh_surface.fill(Color(0,0,0,0))
        draw.ellipse(fresh_surface, color, bounding_rect, width)
        self.render_to_background(fresh_surface, dstrect=fresh_surface.get_rect())
        
    def convert_alpha(self):
        return self
    
    def get_real_rect(self):
        return self.father_texture.get_rect().copy()
    
    def get_dstrect(self):
        return self.father_texture_data["dstrect"].copy()
        
    def get_real_size(self):
        return self.father_texture.get_rect().size
    
    def get_dstrect_size(self):
        return self.father_texture_data["dstrect"].size
    
    def get_real_width(self):
        return self.father_texture.get_rect().width
    
    def get_real_height(self):
        return self.father_texture.get_rect().height
    
    def get_dstrect_width(self):
        return self.father_texture_data["dstrect"].width
    
    def get_dstrect_height(self):
        return self.father_texture_data["dstrect"].height
    
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
        if color2 == Color('#FFFFFFFF'):
            return color1.rgba
        elif color1 == Color('#FFFFFFFF'):
            return color2.rgba
        else:
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
            return color.rgba
      
    @staticmethod  
    def scale_rect_to_fill(target_rect: Rect, father_rect: Rect, scale_type = default_scale_type):
        target_rect = target_rect.copy()
        if scale_type == ORIGINAL:
            target_rect.center = father_rect.center
            return target_rect
        if scale_type == FILL:
            return father_rect.copy()
        if scale_type == SCALE_EMBED:
            scale = min(father_rect.width / target_rect.width, father_rect.height / target_rect.height)
            target_rect.scale_by_ip(scale, scale)
            target_rect.center = father_rect.center
            return target_rect
        if scale_type == SCALE_SURROUND:
            scale = max(father_rect.width / target_rect.width, father_rect.height / target_rect.height)
            target_rect.scale_by_ip(scale, scale)
            target_rect.center = father_rect.center
            return target_rect
        
        raise ValueError("scale_type should be ORIGINAL, FILL, SCALE_EMBED or SCALE_SURROUND")
    
    @staticmethod
    def copy_texture(target_texture: Texture):
        renderer = target_texture.renderer
        copy_texture = Texture(renderer, size=target_texture.get_rect().size, target=True, scale_quality=2)
        copy_texture.blend_mode = target_texture.blend_mode
        renderer.draw_color = Color("#00000000")
        renderer.target = copy_texture
        renderer.clear()
        target_texture.draw()
        renderer.target = None
        return copy_texture
    
    @staticmethod
    def clear_target(target_texture: Texture):
        target_texture.renderer.draw_color = Color("#00000000")
        target_texture.renderer.target = target_texture
        target_texture.renderer.clear()
        target_texture.renderer.target = None
        return target_texture
    