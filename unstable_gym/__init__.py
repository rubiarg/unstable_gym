from .unstable_cartpole_cont import UnstableCartPoleContEnv
from .unstable_acrobot_cont import UnstableAcrobotContEnv
from .unstable_pendulum import UnstablePendulumEnv

from gymnasium.envs.registration import register

register(
    id='UnstablePendulum-v0',
    entry_point='unstable_gym.unstable_pendulum:UnstablePendulumEnv'
)

register(
    id='UnstableCartpole-v0',
    entry_point='unstable_gym.unstable_cartpole_cont:UnstableCartPoleContEnv'
)

register(
    id='UnstableAcrobot-v0',
    entry_point='unstable_gym.unstable_acrobot_cont:UnstableAcrobotContEnv'
)
