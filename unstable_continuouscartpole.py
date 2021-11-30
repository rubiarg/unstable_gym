"""
Classic cart-pole system implemented by Rich Sutton et al.
Copied from http://incompleteideas.net/sutton/book/code/pole.c
permalink: https://perma.cc/C9ZM-652R
"""

import math
import gym
from gym import spaces, logger
from gym.utils import seeding
import numpy as np
from os import path

class Unstable_ContinuousCartPoleEnv(gym.Env):

    metadata = {"render.modes": ["human", "rgb_array"], "video.frames_per_second": 50}

    def __init__(self, wind_type="sine", max_wind=1.0):
        self.gravity = 9.8
        self.masscart = 1.0
        self.masspole = 0.1
        self.total_mass = self.masspole + self.masscart
        self.length = 0.5  # actually half the pole's length
        self.polemass_length = self.masspole * self.length
        self.tau = 0.02  # seconds between state updates
        self.min_action = -10.0
        self.max_action = 10.0

        # Angle at which to fail the episode
        self.theta_threshold_radians = 12 * 2 * math.pi / 360
        self.x_threshold = 2.4

        self.t = 0.
        self.w = 0.
        self.prev_w = 0.
        self.wind_type = wind_type
        self.max_w = max_wind

        # Angle limit set to 2 * theta_threshold_radians so failing observation
        # is still within bounds.
        high = np.array(
            [
                np.finfo(np.float32).max,
                self.x_threshold * 2,
                np.finfo(np.float32).max,
                np.finfo(np.float32).max,
                self.theta_threshold_radians * 2,
                np.finfo(np.float32).max
            ],
            dtype=np.float32
        )

        self.action_space = spaces.Box(
            low = self.min_action,
            high = self.max_action,
            shape=(1,),
            dtype=np.float32
        )
        self.observation_space = spaces.Box(-high, high, dtype=np.float32)

        self.seed()
        self.viewer = None
        self.state = None

        self.steps_beyond_done = None

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def update_wind(self, t):
        if self.wind_type == "random":
            dw = self.np_random.uniform(low=-0.5, high=0.5)
            w = max(min(self.prev_w + dw, self.max_w), -self.max_w)
            self.prev_w = w
        elif self.wind_type == "sine":
            w = self.max_w*np.sin(t)
        else:
            raise NotImplementedError("Not Implemented Wind Type !!")
        return w

    def step(self, action):

        x, x_dot, theta, theta_dot = self.state
        force = float(action)
        costheta = math.cos(theta)
        sintheta = math.sin(theta)
        self.t += self.tau

        w = self.update_wind(self.t)
        self.last_w = w
        print(w)
        wind_torque = 2.0 * w * self.length * costheta / self.masspole

        # For the interested reader:
        # https://coneural.org/florian/papers/05_cart_pole.pdf
        temp = (
            force + self.polemass_length * theta_dot ** 2 * sintheta
        ) / self.total_mass
        thetaacc = (self.gravity * sintheta - costheta * temp + wind_torque) / (
            self.length * (4.0 / 3.0 - self.masspole * costheta ** 2 / self.total_mass)
        )
        xacc = temp - self.polemass_length * thetaacc * costheta / self.total_mass
       
        x = x + self.tau * x_dot
        x_dot = x_dot + self.tau * xacc
        theta = theta + self.tau * theta_dot
        theta_dot = theta_dot + self.tau * thetaacc

        self.state = (x, x_dot, theta, theta_dot)

        done = bool(
            x < -self.x_threshold
            or x > self.x_threshold
            #or theta < -self.theta_threshold_radians
            #or theta > self.theta_threshold_radians
        )

        if not done:
            reward = 1.0
        elif self.steps_beyond_done is None:
            # Pole just fell!
            self.steps_beyond_done = 0
            reward = 1.0
        else:
            if self.steps_beyond_done == 0:
                logger.warn(
                    "You are calling 'step()' even though this "
                    "environment has already returned done = True. You "
                    "should always call 'reset()' once you receive 'done = "
                    "True' -- any further steps are undefined behavior."
                )
            self.steps_beyond_done += 1
            reward = 0.0

        return np.array(self.state, dtype=np.float32), reward, done, {}

    def reset(self):
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        self.state[2] += np.pi
        self.steps_beyond_done = None
        self.last_w = None
        self.t = self.np_random.uniform(low=0.0, high=2*math.pi)
        return np.array(self.state, dtype=np.float32)

    def render(self, mode="human"):
        screen_width = 600
        screen_height = 400

        world_width = self.x_threshold * 2
        scale = screen_width / world_width
        carty = 100  # TOP OF CART
        polewidth = 10.0
        polelen = scale * (2 * self.length)
        cartwidth = 50.0
        cartheight = 30.0

        if self.viewer is None:
            from gym.envs.classic_control import rendering

            self.viewer = rendering.Viewer(screen_width, screen_height)
            l, r, t, b = -cartwidth / 2, cartwidth / 2, cartheight / 2, -cartheight / 2
            axleoffset = cartheight / 4.0
            cart = rendering.FilledPolygon([(l, b), (l, t), (r, t), (r, b)])
            self.carttrans = rendering.Transform()
            cart.add_attr(self.carttrans)
            self.viewer.add_geom(cart)
            l, r, t, b = (
                -polewidth / 2,
                polewidth / 2,
                polelen - polewidth / 2,
                -polewidth / 2,
            )
            pole = rendering.FilledPolygon([(l, b), (l, t), (r, t), (r, b)])
            pole.set_color(0.8, 0.6, 0.4)
            self.poletrans = rendering.Transform(translation=(0, axleoffset))
            pole.add_attr(self.poletrans)
            pole.add_attr(self.carttrans)
            self.viewer.add_geom(pole)
            self.axle = rendering.make_circle(polewidth / 2)
            self.axle.add_attr(self.poletrans)
            self.axle.add_attr(self.carttrans)
            self.axle.set_color(0.5, 0.5, 0.8)
            self.viewer.add_geom(self.axle)
            fname = path.join(path.dirname(__file__), "assets/wind.png")
            self.wind_img = rendering.Image(fname, 100.0, 100.0) #width, height
            self.track = rendering.Line((0, carty), (screen_width, carty))
            self.track.set_color(0, 0, 0)
            self.viewer.add_geom(self.track)

            self._pole_geom = pole

            self.wind_imgtrans = rendering.Transform()
            self.wind_img.add_attr(self.wind_imgtrans)

        self.viewer.add_onetime(self.wind_img)

        if self.state is None:
            return None

        # Edit the pole polygon vertex
        pole = self._pole_geom
        l, r, t, b = (
            -polewidth / 2,
            polewidth / 2,
            polelen - polewidth / 2,
            -polewidth / 2,
        )
        pole.v = [(l, b), (l, t), (r, t), (r, b)]

        x = self.state
        cartx = x[0] * scale + screen_width / 2.0  # MIDDLE OF CART
        self.carttrans.set_translation(cartx, carty)
        self.poletrans.set_rotation(-x[2])

        self.wind_imgtrans.scale = (-self.last_w, np.abs(self.last_w) )
        wind_x = 550 if self.last_w > 0 else 50
        self.wind_imgtrans.set_translation(wind_x, 200)

        return self.viewer.render(return_rgb_array=mode == "rgb_array")

    def close(self):
        if self.viewer:
            self.viewer.close()
            self.viewer = None

if __name__ == "__main__":
    env = Unstable_ContinuousCartPoleEnv(wind_type="random", max_wind=1.0)
    #env = gym.wrappers.Monitor(env, '/tmp/unstable_gym', force=True)
    import time

    for ep in range(10):
        obs = env.reset()
        for step in range(500):
            action = env.action_space.sample()
            nobs, reward, done, info = env.step(action)
            env.render()
            if done:
                break
