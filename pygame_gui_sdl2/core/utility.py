"""
This code owes a lot to pyperclip by Al Sweigart al@inventwithpython.com.

"""
import platform
import subprocess
import time
import contextlib
import os
import sys
import io
import base64
import numpy as np

from pathlib import Path
from typing import Union, Dict, Tuple, Optional

from threading import Thread
from queue import Queue

import i18n

import pygame
from pygame._sdl2 import Texture, Renderer
# from pygame_gui_sdl2.global_renderer import global_renderer

from pygame_gui_sdl2.core.interfaces import IUIManagerInterface, IGUIFontInterface
from pygame_gui_sdl2.core.gui_font_freetype import GUIFontFreetype
from pygame_gui_sdl2.core.gui_font_pygame import GUIFontPygame
# from pygame_gui_sdl2.core.ui_texture import TextureLayer


__default_manager = None  # type: Optional[IUIManagerInterface]


def get_default_manager():
    global __default_manager
    return __default_manager


def set_default_manager(manager: Optional[IUIManagerInterface] = None):
    global __default_manager
    __default_manager = manager


if sys.version_info < (3, 9):
    import importlib_resources as resources
else:
    from importlib import resources

PLATFORM = platform.system().upper()
if PLATFORM == 'WINDOWS':
    import ctypes
    # from ctypes import c_size_t, sizeof, c_wchar_p, c_wchar
    from ctypes.wintypes import HGLOBAL, LPVOID, BOOL, UINT, HANDLE, HWND
    from ctypes.wintypes import DWORD, INT, HMENU, HINSTANCE, LPCSTR

    @contextlib.contextmanager
    def __windows_clipboard(hwnd):
        ctypes.windll.user32.OpenClipboard.argtypes = [HWND]
        ctypes.windll.user32.OpenClipboard.restype = BOOL

        ctypes.windll.user32.CloseClipboard.argtypes = []
        ctypes.windll.user32.CloseClipboard.restype = BOOL

        time_to_stop_checking = time.time() + 0.5
        success = False
        while time.time() < time_to_stop_checking:
            success = ctypes.windll.user32.OpenClipboard(hwnd)
            if success:
                break
            time.sleep(0.01)
        if not success:
            raise Exception

        try:
            yield
        finally:
            ctypes.windll.user32.CloseClipboard()

    def __windows_paste():
        ctypes.windll.user32.GetClipboardData.argtypes = [UINT]
        ctypes.windll.user32.GetClipboardData.restype = HANDLE
        with __windows_clipboard(None):
            cf_unicode_text = 13
            handle = ctypes.windll.user32.GetClipboardData(cf_unicode_text)
            if not handle:
                return ""
            return ctypes.c_wchar_p(handle).value

    # noinspection PyUnresolvedReferences
    # pylint: disable=no-member
    class CheckedCall:
        """
        Wrapper for platform functions.
        """
        def __init__(self, func):
            super().__setattr__("func", func)
            self.argtypes = []
            self.restype = None

        def __call__(self, *args):
            return self.func(*args)

        def __setattr__(self, key, value):
            setattr(self.func, key, value)

    def __windows_copy(data: str):
        msvcrt = ctypes.CDLL('msvcrt')

        safe_create_window = CheckedCall(ctypes.windll.user32.CreateWindowExA)
        safe_create_window.argtypes = [DWORD, LPCSTR, LPCSTR, DWORD, INT, INT,
                                       INT, INT, HWND, HMENU, HINSTANCE, LPVOID]
        safe_create_window.restype = HWND

        safe_destroy_window = CheckedCall(ctypes.windll.user32.DestroyWindow)
        safe_destroy_window.argtypes = [HWND]
        safe_destroy_window.restype = BOOL

        safe_empty = ctypes.windll.user32.EmptyClipboard
        safe_empty.argtypes = []
        safe_empty.restype = BOOL

        safe_alloc = CheckedCall(ctypes.windll.kernel32.GlobalAlloc)
        safe_alloc.argtypes = [UINT, ctypes.c_size_t]
        safe_alloc.restype = HGLOBAL

        safe_lock = CheckedCall(ctypes.windll.kernel32.GlobalLock)
        safe_lock.argtypes = [HGLOBAL]
        safe_lock.restype = LPVOID

        safe_unlock = CheckedCall(ctypes.windll.kernel32.GlobalUnlock)
        safe_unlock.argtypes = [HGLOBAL]
        safe_unlock.restype = BOOL

        safe_set_clipboard = CheckedCall(ctypes.windll.user32.SetClipboardData)
        safe_set_clipboard.argtypes = [UINT, HANDLE]
        safe_set_clipboard.restype = HANDLE

        wcslen = msvcrt.wcslen
        wcslen.argtypes = [ctypes.c_wchar_p]
        wcslen.restype = UINT

        # weirdly this temporary window handle seems to work for pasting where the
        # normal pygame window handle does not
        hwnd = safe_create_window(0, b"STATIC", None, 0, 0, 0, 0, 0,
                                  None, None, None, None)

        with __windows_clipboard(hwnd):
            safe_empty()

            data = str(data)
            if data:
                count = wcslen(data) + 1
                handle = safe_alloc(0x0002, count * ctypes.sizeof(ctypes.c_wchar))

                ctypes.memmove(ctypes.c_wchar_p(safe_lock(handle)),
                               ctypes.c_wchar_p(data),
                               count * ctypes.sizeof(ctypes.c_wchar))

                safe_unlock(handle)
                safe_set_clipboard(13, handle)  # cf_unicode_text = 13

        safe_destroy_window(hwnd)
elif PLATFORM == 'LINUX':

    def __linux_copy(data: str):
        with subprocess.Popen(['xsel', '-b', '-i'],
                              stdin=subprocess.PIPE,
                              close_fds=True) as process:
            process.communicate(input=data.encode('utf-8'))

    def __linux_paste():
        with subprocess.Popen(['xsel', '-b', '-o'],
                              stdout=subprocess.PIPE,
                              close_fds=True) as process:
            stdout, _ = process.communicate()
            return stdout.decode('utf-8')

else:
    def __mac_copy(data: str):
        with subprocess.Popen('pbcopy',
                              env={'LANG': 'en_US.UTF-8'},
                              stdin=subprocess.PIPE) as process:

            process.communicate(data.encode('utf-8'))

    def __mac_paste():
        return subprocess.check_output(
            'pbpaste', env={'LANG': 'en_US.UTF-8'}).decode('utf-8')


def clipboard_copy(data: str):
    """
    Hopefully cross platform, copy to a clipboard.

    :return: A platform specific copy function.

    """
    if pygame.vernum.major == 2 and pygame.vernum.minor >= 2:
        pygame.scrap.put_text(data)
    else:
        current_platform = platform.system().upper()
        if current_platform == 'WINDOWS':
            __windows_copy(data)
        elif current_platform == 'LINUX':
            __linux_copy(data)
        else:
            __mac_copy(data)


def clipboard_paste():
    """
    Hopefully cross platform, paste from a clipboard.

    :return: A platform specific paste function.

    """
    if pygame.vernum.major == 2 and pygame.vernum.minor >= 2:
        return pygame.scrap.get_text()
    else:
        current_platform = platform.system().upper()
        if current_platform == 'WINDOWS':
            return __windows_paste()
        elif current_platform == 'LINUX':
            return __linux_paste()
        else:
            return __mac_paste()


def create_resource_path(relative_path: Union[str, Path]):
    """
    Get absolute path to resource, works for dev and for PyInstaller's 'onefile' mode

    :param relative_path: A relative path to a file of some kind.

    """

    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # pylint: disable=no-member,protected-access
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def premul_col(original_colour: pygame.Color) -> pygame.Color:
    """
    Perform a pre-multiply alpha operation on a pygame colour
    """
    alpha_mul = original_colour.a / 255
    return pygame.Color(int(original_colour.r * alpha_mul),
                        int(original_colour.g * alpha_mul),
                        int(original_colour.b * alpha_mul),
                        original_colour.a)


def restore_premul_col(premul_colour: pygame.Color) -> pygame.Color:
    """
    Restore a pre-multiplied alpha colour back to an approximation of it's initial value.

    NOTE: Because of the rounding to integers this cannot be exact.
    """
    inverse_alpha_mul = 1.0 / max(0.001, (premul_colour.a / 255))

    return pygame.Color(int(premul_colour.r * inverse_alpha_mul),
                        int(premul_colour.g * inverse_alpha_mul),
                        int(premul_colour.b * inverse_alpha_mul),
                        premul_colour.a)


def premul_alpha_surface(surface: pygame.surface.Surface) -> pygame.surface.Surface:
    """
    Perform a pre-multiply alpha operation on a pygame surface's colours.
    """
    surf_copy = surface.copy()
    surf_copy.fill(pygame.Color('#FFFFFF00'), special_flags=pygame.BLEND_RGB_MAX)
    manipulate_surf = pygame.surface.Surface(surf_copy.get_size(),
                                             flags=pygame.SRCALPHA, depth=32)
    # Can't be exactly transparent black or we trigger SDL1 'bug'
    manipulate_surf.fill(pygame.Color('#00000001'))
    manipulate_surf.blit(surf_copy, (0, 0))
    surface.blit(manipulate_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    return surface

# def premul_alpha_texture(texture: TextureLayer) -> TextureLayer:
#     """
#     Perform a pre-multiply alpha operation on a pygame surface's colours.
#     """
#     texture_copy = texture.copy()
#     texture_copy.fill(pygame.Color('#FFFFFF00'), special_flags=pygame.BLEND_RGB_MAX)
#     manipulate_texture = texture_copy.copy()
#     # Can't be exactly transparent black or we trigger SDL1 'bug'
#     manipulate_texture.fill(pygame.Color('#00000001'))
#     manipulate_texture.extend(texture_copy, dest=(0, 0))
#     texture.extend(manipulate_texture, dest=(0, 0))
#     return texture


def render_white_text_alpha_black_bg(font: IGUIFontInterface,
                                     text: str) -> pygame.surface.Surface:
    """
    Render text with a zero alpha background with 0 in the other colour channels. Appropriate for
    use with BLEND_PREMULTIPLIED and for colour/gradient multiplication.
    """
    text_surface = font.render_premul(text, pygame.Color("white"))
    return text_surface


def basic_render(destination: Texture,
               source: Texture,
               pos: Union[Tuple[int, int], pygame.Rect] = (0, 0),
               area: Union[pygame.Rect, None] = None):
    """
    The basic blitting function to use. WE need to wrap this so we can support pre-multiplied alpha
    on post 2.0.0.dev10 versions of pygame and regular blitting on earlier versions.

    :param destination: Destination surface to blit on to.
    :param source: Source surface to blit from.
    :param pos: The position of our blit.
    :param area: The area of the source to blit from.

    """
    renderer = destination.renderer
    if area is None:
        area = source.get_rect()
    if pos is None:
        dstrect = area.copy()
    elif isinstance(pos, pygame.Rect):
        dstrect = pos.copy()
    else:
        dstrect = pygame.Rect(pos, area.size)
    destination.blend_mode = 1
    source.blend_mode = 1
    renderer.target = destination
    source.draw(dstrect=dstrect, srcrect=area)
    renderer.target = None
 
def clear_texture(texture: Texture):
    renderer = texture.renderer
    renderer.target = texture
    renderer.draw_color = pygame.Color("#00000000") 
    renderer.clear()
    renderer.target = None
   
def copy_texture(target_texture: Texture):
    renderer = target_texture.renderer
    target_texture.blend_mode = 1
    copy_texture = Texture(renderer, size=target_texture.get_rect().size, target=True, scale_quality=2)
    copy_texture.blend_mode = 1
    renderer.target = copy_texture
    clear_texture(copy_texture)
    target_texture.draw()
    renderer.target = None
    return copy_texture

def scale_by_texture(texture: Texture, scale: Tuple[float, float]):
    renderer = texture.renderer
    scaled_texture = Texture(renderer, size=(int(texture.get_rect().width * scale[0]), int(texture.get_rect().height * scale[1])), target=True, scale_quality=2)
    clear_texture(scaled_texture)
    texture.blend_mode = 1
    scaled_texture.blend_mode = 1
    renderer.target = scaled_texture
    texture.draw()
    renderer.target = None
    return scaled_texture

def scale_to_texture(texture: Texture, size: Tuple[int, int]):
    renderer = texture.renderer
    scaled_texture = Texture(renderer, size=size, target=True, scale_quality=2)
    clear_texture(scaled_texture)
    texture.blend_mode = 1
    scaled_texture.blend_mode = 1
    renderer.target = scaled_texture
    texture.draw()
    renderer.target = None
    return scaled_texture

def rotate_texture(texture: Texture, angle: float):
    renderer = texture.renderer
    new_size = (abs(int(texture.get_rect().width * np.cos(angle) + texture.get_rect().height * np.sin(angle))), 
                abs(int(texture.get_rect().height * np.cos(angle) + texture.get_rect().width * np.sin(angle))))
    rotated_texture = Texture(renderer, size=new_size, target=True, scale_quality=2)
    clear_texture(rotated_texture)
    texture.blend_mode = 1
    rotated_texture.blend_mode = 1
    rotated_rect = rotated_texture.get_rect()
    target_rect = texture.get_rect()
    target_rect.center = rotated_rect.center
    renderer.target = rotated_texture
    texture.draw(dstrect=target_rect, angle=angle)
    renderer.target = None
    return rotated_texture
    
def flip_texture(texture: Texture, x: bool, y: bool):
    renderer = texture.renderer
    flipped_texture = Texture(renderer, size=texture.get_rect().size, target=True, scale_quality=2)
    clear_texture(flipped_texture)
    texture.blend_mode = 1
    flipped_texture.blend_mode = 1
    renderer.target = flipped_texture
    texture.draw(flip_x=x, flip_y=y)
    renderer.target = None
    return flipped_texture

def apply_colour_to_texture(colour: pygame.Color,
                            shape_texture: Texture,
                            rect: Union[pygame.Rect, None] = None):
    """
    Apply a colour to a shape surface by multiplication blend. This works best when the shape
    surface is predominantly white.

    :param colour: The colour to apply.
    :param shape_surface: The shape surface to apply the colour to.
    :param rect: A rectangle to apply the colour inside of.

    """
    color_surface = pygame.Surface(size=(1,1), flags=pygame.SRCALPHA, depth=32)
    color_surface.fill(colour)
    renderer = shape_texture.renderer
    color_texture = Texture.from_surface(shape_texture.renderer, surface=color_surface)
    if rect is not None:
        basic_render(shape_texture, color_texture, pos=rect)
    else:
        basic_render(shape_texture, color_texture, pos=shape_texture.get_rect())


def apply_colour_to_surface(colour: pygame.Color,
                            shape_surface: pygame.surface.Surface,
                            rect: Union[pygame.Rect, None] = None):
    """
    Apply a colour to a shape surface by multiplication blend. This works best when the shape
    surface is predominantly white.

    :param colour: The colour to apply.
    :param shape_surface: The shape surface to apply the colour to.
    :param rect: A rectangle to apply the colour inside of.

    """
    if rect is not None:
        colour_surface = pygame.surface.Surface(rect.size, flags=pygame.SRCALPHA, depth=32)
        colour_surface.fill(colour)
        shape_surface.blit(colour_surface, rect, special_flags=pygame.BLEND_RGBA_MULT)
    else:
        colour_surface = pygame.surface.Surface(shape_surface.get_size(),
                                                flags=pygame.SRCALPHA, depth=32)
        colour_surface.fill(colour)
        shape_surface.blit(colour_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
# def apply_colour_to_texture(colour: pygame.Color,
#                             shape_texture: TextureLayer,
#                             rect: Union[pygame.Rect, None] = None):
#     """
#     Apply a colour to a shape surface by multiplication blend. This works best when the shape
#     surface is predominantly white.

#     :param colour: The colour to apply.
#     :param shape_surface: The shape surface to apply the colour to.
#     :param rect: A rectangle to apply the colour inside of.

#     """
#     if rect is not None:
#         shape_texture.fill(colour, rect)
#     else:
#         shape_texture.extend(colour)


class PackageResource:
    """
    A data class to handle input for importlib.resources as single parameter.

    :param package: The python package our resource is located in (e.g. 'pygame_gui_sdl2.data')
    :param resource: The name of the resource (e.g. 'default_theme.json')
    """
    def __init__(self, package: str, resource: str):
        self.package = package
        self.resource = resource

    def __repr__(self):
        return self.package + '.' + self.resource

    def to_path(self) -> str:
        """
        If we don't have any importlib module to use, we can try to turn the resource into a file
        path.

        :return: A string path.
        """
        root_path = ''
        relative_path = self.package.replace('.', '/') + '/' + self.resource
        if self.package.find('pygame_gui_sdl2') == 0:
            # This is default data from pygame_gui_sdl2 so relative to pygame_gui_sdl2 rather than app
            root_path = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        return create_resource_path(os.path.join(root_path, relative_path))


class FontResource:
    """
    A resource class to handle all the data we need to load a python font object from a
    file.

    :param font_id: A string ID for the font so we can find it again.
    :param size: The font size.
    :param style: A Style dictionary for bold and italic styling.
    :param location: A location for the font file - a PackageResource, or a file path.
    """
    def __init__(self,
                 renderer,
                 font_id: str,
                 size: int,
                 style: Dict[str, bool],
                 location: Tuple[Union[str, PackageResource, bytes], bool]):
        self.renderer = renderer
        self.font_id = font_id
        self.size = size
        self.style = style
        self.location = location[0]
        self.force_style = location[1]
        self.loaded_font = None  # type: Union[IGUIFontInterface, None]

        self.font_type_to_use = "freetype"

    def load(self):
        """
        Load the font from wherever it is located.

        :return: An exception. We don't handle this here because exception handling in threads
                 seems to be a bit of a mess.
        """
        error = None
        if isinstance(self.location, PackageResource):
            try:
                if self.font_type_to_use == "freetype":
                    self.loaded_font = GUIFontFreetype(self.renderer,
                        io.BytesIO((resources.files(self.location.package) /
                                    self.location.resource).read_bytes()),
                        self.size, self.force_style, self.style)
                elif self.font_type_to_use == "pygame":
                    self.loaded_font = GUIFontPygame(self.renderer,
                        io.BytesIO((resources.files(self.location.package) /
                                    self.location.resource).read_bytes()),
                        self.size, self.force_style, self.style)
            except (pygame.error, FileNotFoundError, OSError):
                error = FileNotFoundError('Unable to load resource with path: ' +
                                          str(self.location))

        elif isinstance(self.location, str):
            try:
                if self.font_type_to_use == "freetype":
                    self.loaded_font = GUIFontFreetype(self.renderer, self.location, self.size, self.force_style, self.style)
                elif self.font_type_to_use == "pygame":
                    self.loaded_font = GUIFontPygame(self.renderer, self.location, self.size, self.force_style, self.style)
            except (pygame.error, FileNotFoundError, OSError):
                error = FileNotFoundError('Unable to load resource with path: ' +
                                          str(self.location))

        elif isinstance(self.location, bytes):
            try:
                file_obj = io.BytesIO(base64.standard_b64decode(self.location))
                if self.font_type_to_use == "freetype":
                    self.loaded_font = GUIFontFreetype(self.renderer, file_obj, self.size, self.force_style, self.style)
                elif self.font_type_to_use == "pygame":
                    self.loaded_font = GUIFontPygame(self.renderer, file_obj, self.size, self.force_style, self.style)
            except (pygame.error, FileNotFoundError, OSError):
                error = FileNotFoundError('Unable to load resource with path: ' +
                                          str(self.location))

        return error


class ImageResource:
    """
    Resource representing an image to be loaded into memory.

    This is an intermediate state for our final Surface resources because many sub surfaces may
    refer to a single Image surface.

    :param image_id: A string ID for identifying this image in particular.
    :param location: A location for this image, a PackageResource, or a file path.
    """
    def __init__(self,
                 renderer,
                 image_id: str,
                 location: Union[PackageResource, str]):
        self.renderer = renderer
        self.image_id = image_id
        self.location = location
        self.loaded_surface: Optional[pygame.Surface] = None
        self.loaded_texture: Optional[Texture] = None

    def load(self) -> Union[Exception, None]:
        """
        Load the image from wherever it is located.

        :return: An exception. We don't handle this here because exception handling in threads
                 seems to be a bit of a mess.
        """
        error = None
        if isinstance(self.location, PackageResource):
            try:
                with (resources.files(self.location.package) /
                      self.location.resource).open('rb') as open_resource:
                    self.loaded_surface = pygame.image.load(open_resource).convert_alpha()
            except (pygame.error, FileNotFoundError, OSError):
                error = FileNotFoundError('Unable to load resource with path: ' +
                                          str(self.location))

        elif isinstance(self.location, str):
            try:
                self.loaded_surface = pygame.image.load(self.location).convert_alpha()
            except (pygame.error, FileNotFoundError, OSError):
                error = FileNotFoundError('Unable to load resource with path: ' +
                                          str(self.location))

        # perform pre-multiply alpha operation
        if error is None and self.loaded_surface is not None:
            premul_alpha_surface(self.loaded_surface)
            self.loaded_texture = Texture.from_surface(self.renderer, surface=self.loaded_surface)
            self.loaded_texture.blend_mode = 1
        return error


class SurfaceResource:
    """
    Resource representing a finished, ready-for-use surface.

    Because a surface may be a sub-surface of another one, these SurfaceResource are
    'loaded' after images are loaded from files.

    :param image_resource: The parent ImageResource of this surface.
    :param sub_surface_rect: An optional Rect for sub-surfacing.
    """
    def __init__(self,
                 image_resource: ImageResource,
                 sub_surface_rect: pygame.Rect = None):

        self.image_resource = image_resource
        self.sub_surface_rect = sub_surface_rect
        self._surface: Optional[pygame.surface.Surface] = None

    def load(self) -> Union[Exception, None]:
        """
        'Load' the surface. Basically performs the subsurface operation, if it is required.
        :return: An Exception if something went wrong, we bubble it out of the danger zone of
                 Threads to handle neatly later.
        """
        error = None
        if self.sub_surface_rect and self.image_resource.loaded_surface is not None:
            try:
                self.surface = self.image_resource.loaded_surface.subsurface(self.sub_surface_rect)
            except(pygame.error, OSError) as err:
                error = err
        return error

    @property
    def surface(self) -> pygame.surface.Surface:
        """
        Get the Pygame Surface
        """
        if self._surface is not None:
            return self._surface
        elif self.image_resource.loaded_surface is not None:
            return self.image_resource.loaded_surface

        # Return an empty surface here, error elsewhere
        return pygame.surface.Surface((0, 0),
                                      depth=32,
                                      flags=pygame.SRCALPHA)

    @surface.setter
    def surface(self, surface: pygame.surface.Surface):
        """
        Set the Pygame surface.

        :param surface: The Surface to set to.
        """
        self._surface = surface

class TextureResource:
    """
    Resource representing a finished, ready-for-use surface.

    Because a surface may be a sub-surface of another one, these SurfaceResource are
    'loaded' after images are loaded from files.

    :param image_resource: The parent ImageResource of this surface.
    :param sub_surface_rect: An optional Rect for sub-surfacing.
    """
    def __init__(self,
                 renderer,
                 image_resource: ImageResource,
                 sub_texture_rect: pygame.Rect = None):
        self.renderer = renderer
        self.image_resource = image_resource
        self.sub_texture_rect = sub_texture_rect
        self._texture: Optional[Texture] = None

    def load(self) -> Union[Exception, None]:
        """
        'Load' the surface. Basically performs the subsurface operation, if it is required.
        :return: An Exception if something went wrong, we bubble it out of the danger zone of
                 Threads to handle neatly later.
        """
        error = None
        if self.sub_texture_rect and self.image_resource.loaded_texture is not None:
            try:
                # self.texture = self.image_resource.loaded_texture.subtexture(self.sub_texture_rect)
                sub_texture = Texture(self.renderer, size=self.sub_texture_rect.size, target=True, scale_quality=2)
                self.renderer.target = sub_texture
                self.image_resource.loaded_texture.draw(srcrect=self.sub_texture_rect)
                self.renderer.target = None
                self.texture = sub_texture
            except(pygame.error, OSError) as err:
                error = err
        return error

    @property
    def texture(self) -> Texture:
        """
        Get the Pygame Surface
        """
        if self._texture is not None:
            return self._texture
        elif self.image_resource.loaded_texture is not None:
            return self.image_resource.loaded_texture

        # Return an empty surface here, error elsewhere
        return Texture(self.renderer, size=(0, 0))

    @texture.setter
    def texture(self, texture: Texture):
        """
        Set the Pygame surface.

        :param surface: The Surface to set to.
        """
        self._texture = texture
        self._texture.blend_mode = 1


class ClosableQueue(Queue):
    """
    A synchronised Queue for loading resources in (sort-of) parallel.

    The idea is that there is some time spent waiting for OS's to respond to file loading requests
    and it is worth firing off a bunch of them in different threads to improve loading performance.

    It seems to work OK.
    """
    SENTINEL = object()

    def close(self):
        """
        Close this queue to new items.
        """
        self.put(self.SENTINEL)

    def __iter__(self):
        while True:
            item = self.get()
            try:
                if item is self.SENTINEL:
                    return  # Cause the thread to exit
                yield item
            finally:
                self.task_done()


class StoppableOutputWorker(Thread):
    """
    A worker thread that loads resources.

    :param func: The loading function.
    :param in_queue: Queue of resources to load.
    :param out_queue: Queue of resources finished loading.
    :param error_queue: A Queue of any errors generated while loading to display at the end.
    """
    def __init__(self,
                 func,
                 in_queue: ClosableQueue,
                 out_queue: ClosableQueue,
                 error_queue: ClosableQueue):

        super().__init__()
        self.func = func
        self.in_queue = in_queue
        self.out_list = out_queue
        self.errors = error_queue

    def run(self):
        """
        Runs the thread, taking resources off the load queue, loading them and then putting
        them onto the out queue.

        The queues are shared between multiple threads.
        """
        for item in self.in_queue:
            result, error = self.func(item)
            self.out_list.put(result)
            if error:
                self.errors.put(error)


def translate(text_to_translate: str, **keywords) -> str:
    """
    Translate a translatable string to the current locale.

    :param text_to_translate: Some sort of ID string that points to a variety of different
                              translation files containing the real text.
    :param keywords: Some translation strings have keywords to insert into the translation (e.g.
                     a file name)
    :return: The translated string if translated successfully, otherwise the original string
             is passed back.
    """
    return i18n.t(text_to_translate, **keywords)
