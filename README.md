

# Pygame GUI
A GUI system for pygame._sdl2.

 - [Documentation](https://pygame-gui.readthedocs.io/)
 - [GitHub](https://github.com/MyreMylar/pygame_gui)
 - [Examples](https://github.com/MyreMylar/pygame_gui_examples)
 - [PyPi](https://pypi.org/project/pygame-gui/)

[![pypi](https://badge.fury.io/py/pygame-gui.svg)](https://pypi.python.org/pypi/pygame-gui) [![Documentation Status](https://readthedocs.org/projects/pygame-gui/badge/?version=latest)](https://pygame-gui.readthedocs.io/en/latest/?badge=latest) [![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/release/python-380/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Master](https://travis-ci.com/MyreMylar/pygame_gui.svg?branch=master)](https://travis-ci.com/MyreMylar/pygame_gui) [![codecov](https://codecov.io/gh/MyreMylar/pygame_gui/branch/main/graph/badge.svg?token=zZhkvhgTki)](https://codecov.io/gh/MyreMylar/pygame_gui) [![Downloads](https://pepy.tech/badge/pygame-gui)](https://pepy.tech/project/pygame-gui)
## !!Attention!!
This Fork is created for personal use only, utilizing the contents of the `pygame._sdl2` library for hardware acceleration or GPU rendering purposes base on pygame_gui 0.6.10.

This version employs a custom `TextureLayer` class (note: **NOT** `pygame._sdl2.video.Texture`!) to record texture rendering information and render it. Therefore, when using it, you need to import from `pygame.core`, with the filename being `ui_texture.py`.

Due to this modification, all instances using the `Surface` class are replaced with `TextureLayer`, and similar methods are implemented, except for some components (such as text input, progress bars, etc.) that may not work perfectly due to the layer limit of TextureLayer's texture overlap. You can choose to increase the maximum allowable overlapping layers appropriately or optimize the logic to resolve this issue.

## Points to note when using this version:
 - If you encounter problems, please resolve them on your own. **I do not guarantee being able to resolve most issues**.
 - There is no guarantee of future feature updates. If needed, **refer to the first point**.
 - There is no guarantee of issue-free operation. If problems arise, **refer to the first point**.

## Requirements

 - Python 3.8+
 - Pygame Community Edition 2.4.0+
 - python-i18n (does localization to different languages)

## How to install

1. cd to root folder and run this command in a command prompt:
```
pip install .
```
The package should be `pygame_gui_sdl2`.

2. If all goes well you should see a message about pygame_gui_sdl2 being installed successfully and will be able to find pygame_gui_sdl2 in the list of installed packages for your python interpreter (PyCharm displays these as a nice list under File->Settings->Project:project_name->Project Interpreter). 

3. Should you need to delete pygame_gui for any reason then PyCharm will also let you do that from the same Project Interpreter settings window using the red minus symbol button.

## A Simple Start

You may need a `Window` object and use the `Renderer.from_window` method to obtain a `Renderer` object. Currently, the most reliable way to create a `Window` object is to create one using 
```
pygame.display.set_mode()
```
and then use 
```
Window.from_display_module()
``` 
to create a `Window` object, after which you will no longer need to use the `pygame.display.set_mode` method.

Next, you will need to create a `UIManager` object, which requires passing in a `Renderer`. When creating other UI objects, the first parameter also defaults to `Renderer`. During each frame rendering, you need to first call 
```
renderer.clear()
```
then 
```
manager.update(time_delta)
manager.draw_ui()
```
and finally 
```
renderer.present()
```
which should display the content. Note that no parameters should be passed into `draw_ui()`, and `time_delta` should in second.

## How to upgrade to the latest version
### Currently not supported

Run this command in a command prompt:

```
pip install pygame_gui -U
```

Or, you may be able to use your IDE to update the library (PyCharm lets you update modules in it's interpreter settings).

## Making use of the library

There is documentation available [here](https://pygame-gui.readthedocs.io/en/latest/index.html), you can also try out the examples at the [pygame_gui_examples repository](https://github.com/MyreMylar/pygame_gui_examples).

## Screenshots of Pygame GUI

![pygame_gui_example_1](https://user-images.githubusercontent.com/13382426/69264498-57ec8980-0bbf-11ea-9883-cac9c854615d.png)

![example_2](https://user-images.githubusercontent.com/13382426/69264921-2f18c400-0bc0-11ea-8a11-d9abd4e969b4.png)

![pygame_gui_example_3](https://user-images.githubusercontent.com/13382426/68039142-5ec06480-fcc3-11e9-91f4-3e401f459886.png)

![pygame_gui_example_4](https://user-images.githubusercontent.com/13382426/68041632-e52b7500-fcc8-11e9-8b72-4cf8817c5fa3.png)
