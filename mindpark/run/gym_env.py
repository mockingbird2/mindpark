import gym
from gym import wrappers
from mindpark.core import Env


class GymEnv(Env):

    def __init__(self, env_name, directory=None, videos=False):
        super().__init__()
        self._env = gym.make(env_name)
        self._directory = directory
        if self._directory:
            # self._env.monitor.start(self._directory, videos)
            self._env = wrappers.Monitor(self._env, self._directory, videos)

    @property
    def observs(self):
        return self._env.observation_space

    @property
    def actions(self):
        return self._env.action_space

    def reset(self):
        observation = self._env.reset()
        return observation

    def step(self, action):
        assert self.actions.contains(action)
        observation, reward, done, _ = self._env.step(action)
        assert self.observs.contains(observation)
        assert isinstance(reward, (int, float))
        if done:
            # May not be None if Gym aborted after too many time steps.
            observation = None
        return reward, observation

    def close(self):
        if self._directory:
            self._env.monitor.close()
        self._env.close()
