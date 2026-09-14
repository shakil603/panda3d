#
# Star Catcher — a simple 3D game you can play with your finger!
#
# Hold the screen and slide your finger left or right to move the panda.
# Catch the falling stars before they drift past you.  Catch them all and
# a new set appears!
#
import random

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import LColor, Task


class StarCatcher(ShowBase):
    TOTAL_STARS = 5
    PLAYER_Z = -8.0
    SPAWN_Z = -16.0

    def __init__(self):
        ShowBase.__init__(self)

        self.setBackgroundColor(LColor(0.06, 0.08, 0.22, 1.0))

        # Keep the camera fixed: the game uses the screen for control,
        # so detach ShowBase's trackball (drag would orbit the camera).
        if self.trackball is not None:
            self.trackball.detachNode()

        # The player.
        self.player = self.loader.loadModel("models/panda.egg")
        self.player.reparentTo(self.render)
        self.player.setScale(0.4)
        self.player.setPos(0, 0, self.PLAYER_Z)
        self.playerX = 0.0
        self.targetX = 0.0
        self.touching = False

        # The stars (little glowing boxes).
        self.box = self.loader.loadModel("models/box.egg")
        self.stars = []
        for i in range(self.TOTAL_STARS):
            self.spawn_star()

        self.score = 0
        self.scoreText = OnscreenText(
            text="Score: 0 / %d" % self.TOTAL_STARS,
            pos=(0.97, 0.95), scale=0.07,
            fg=(1, 0.9, 0.2, 1), align=2)
        self.msgText = OnscreenText(
            text="Hold the screen and slide to move!",
            pos=(0, -0.93), scale=0.06,
            fg=(1, 1, 1, 1), align=1)

        # On Android, a touch shows up as mouse button 1.
        self.accept("mouse1Down", self.on_down)
        self.accept("mouse1Drag", self.on_drag)
        self.accept("mouse1Up", self.on_up)

        self.taskMgr.add(self.update, "update")

    def spawn_star(self):
        star = self.box.copyTo(self.render)
        star.setColor(LColor(1.0, 0.9, 0.2, 1.0))
        star.setScale(0.45)
        star.setH(random.randint(0, 360))
        star.setPos(random.uniform(-3, 3), 0,
                   random.uniform(self.SPAWN_Z, self.SPAWN_Z + 6))
        self.stars.append(star)

    def screen_to_world_x(self, screen_x):
        w = self.win.getXSize()
        return (screen_x - w / 2.0) / (w / 2.0) * 4.0

    def on_down(self, event):
        self.touching = True
        self.targetX = self.screen_to_world_x(event.getX())

    def on_drag(self, event):
        if self.touching:
            self.targetX = self.screen_to_world_x(event.getX())

    def on_up(self, event):
        self.touching = False

    def update(self, dt):
        # Ease the player toward the finger.
        self.playerX += (self.targetX - self.playerX) * min(1.0, 10.0 * dt)
        self.playerX = max(-4.0, min(4.0, self.playerX))
        self.player.setPos(self.playerX, 0, self.PLAYER_Z)

        for star in self.stars[:]:
            z = star.getZ() + 5.0 * dt
            star.setZ(z)
            star.setH(star.getH() + 120 * dt)

            if abs(z - self.PLAYER_Z) < 0.7 and \
                    abs(star.getX() - self.playerX) < 1.2:
                # Caught it!
                star.removeNode()
                self.stars.remove(star)
                self.score += 1
                self.scoreText.setText("Score: %d / %d" %
                                       (self.score, self.TOTAL_STARS))
                if self.score == self.TOTAL_STARS:
                    # All caught: a fresh batch!
                    self.msgText.setText("You caught them all!")
                    for s in self.stars:
                        s.removeNode()
                    self.stars = []
                    for i in range(self.TOTAL_STARS):
                        self.spawn_star()
                    self.score = 0
                    self.scoreText.setText("Score: 0 / %d" %
                                           self.TOTAL_STARS)
            elif z > 4:
                # Drifted past the player.
                star.removeNode()
                self.stars.remove(star)

        return Task.cont


app = StarCatcher()
app.run()
