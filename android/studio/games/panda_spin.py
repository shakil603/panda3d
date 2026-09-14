#
# Panda Spin — the classic Panda3D demo.
#
# The panda model spins on the spot.  Hold the screen and drag to look
# around (the camera orbits with a trackball).
#
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import LColor, Task


class PandaSpin(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.setBackgroundColor(LColor(0.16, 0.35, 0.65, 1.0))

        # A model that ships inside the app's assets.
        self.model = self.loader.loadModel("models/panda.egg")
        self.model.reparentTo(self.render)
        self.model.setPos(0, 0, -1.5)
        self.model.setScale(0.4)
        self.model.setH(0)

        self.taskMgr.add(self.spin, "spin")

        OnscreenText(
            text="Panda Spin — hold & drag to look around",
            pos=(0, -0.95), scale=0.06,
            fg=(1, 1, 1, 1), align=1,
        )

    def spin(self, dt):
        self.model.setH(self.model.getH() + 60 * dt)
        return Task.cont


app = PandaSpin()
app.run()
