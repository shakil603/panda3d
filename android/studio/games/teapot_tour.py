#
# Teapot Tour — a relaxing 3D scene.
#
# The classic Utah teapot orbits slowly.  Hold the screen and drag to
# fly around it.  This is a good starting point for learning: look at
# how the model is loaded, moved, and animated.
#
import math

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import LColor, Task


class TeapotTour(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.setBackgroundColor(LColor(0.10, 0.12, 0.16, 1.0))

        # A second model, floating above the teapot.
        self.teapot = self.loader.loadModel("models/teapot.egg")
        self.teapot.reparentTo(self.render)
        self.teapot.setScale(2.0)

        self.box = self.loader.loadModel("models/box.egg")
        self.box.setColor(LColor(0.9, 0.5, 0.2, 1.0))
        self.box.reparentTo(self.teapot)
        self.box.setScale(0.5)
        self.box.setPos(1.6, 0, 1.2)

        self.time = 0.0
        self.taskMgr.add(self.animate, "animate")

        OnscreenText(
            text="Teapot Tour — hold & drag to fly around",
            pos=(0, -0.95), scale=0.06,
            fg=(1, 1, 1, 1), align=1,
        )

    def animate(self, dt):
        self.time += dt
        # The teapot orbits in a circle.
        r = 3.0
        self.teapot.setPos(r * math.sin(self.time * 0.4), 0,
                           -2.0 + r * math.cos(self.time * 0.4) * 0.3)
        self.teapot.setH(self.time * 40)
        return Task.cont


app = TeapotTour()
app.run()
