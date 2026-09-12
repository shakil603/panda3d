#
# default_app.py — the default Panda3D application inside the Android APK.
#
# When the "Panda Python" launcher icon is opened *without* choosing a .py
# file, the app runs this script.  It shows the classic Panda3D panda model
# rotating on screen with a trackball camera.
#
# Tip: to run your own script instead, open it from the file manager (or use
# an app that can send a "view" intent with a .py file) and "Panda Python"
# will run it.
#
import math

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import LColor


class DefaultApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.setBackgroundColor(LColor(0.16, 0.35, 0.65, 1.0))

        # Load a model that ships inside the APK's assets (models/ directory).
        self.model = None
        for name in ("models/panda.egg", "models/teapot.egg", "models/box.egg"):
            try:
                self.model = self.loader.loadModel(name)
                break
            except Exception:
                continue

        if self.model is not None:
            self.model.reparentTo(self.render)
            self.model.setPos(0, 0, -1.2)
            self.model.setScale(0.45)
            self.model.setH(0)
            self.taskMgr.add(self.animate, "animate")
        else:
            # Extremely unlikely: no model available at all.
            OnscreenText(
                text="No bundled models found",
                pos=(0, -0.9),
                scale=0.07,
                fg=(1, 0.4, 0.4, 1),
                align=1,
            )

        OnscreenText(
            text="Panda3D on Android",
            pos=(0, 0.93),
            scale=0.08,
            fg=(1, 1, 1, 1),
            align=1,
        )
        OnscreenText(
            text="drag to orbit  |  pinch to zoom  |  ESC to quit",
            pos=(0, -0.94),
            scale=0.055,
            fg=(1, 1, 1, 0.8),
            align=1,
        )

    def animate(self, task):
        # Spin around the vertical axis and wobble a little.
        self.model.setH(task.time * 45)
        self.model.setP(8 * math.sin(task.time))
        return task.cont


app = DefaultApp()
app.run()
