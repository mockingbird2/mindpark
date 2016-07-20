import collections
import itertools
import os
import time
import numpy as np
import gym
from vizbot.core import Trainer, Agent, StopTraining
from vizbot.utility import ensure_directory


class Benchmark:

    def __init__(self, directory, repeats, **trainer_kwargs):
        """
        Train multiple agents on multiple environments and plot a comparison
        chart. Store all results in an unique experiment directory.

        Args:
            directory (path): Root directory for experiments.
            repeats (int): How often to train the agent on the same
                environment. Used to estimate the standard deviation.
            **trainer_kwargs: Parameters to forward to the trainer instances.
        """
        if directory:
            directory = os.path.abspath(os.path.expanduser(directory))
        self._directory = directory
        self._repeats = repeats
        self._trainer_kwargs = trainer_kwargs

    def __call__(self, name, envs, agents):
        """
        Train each agent on each environment for multiple repeats. Store gym
        monitorings and scores into sub directories of the experiment. Return
        the path to the experiment, and episode scores and durations, both
        grouped by environment, agent, and repeat.
        """
        experiment = self._start_experiment(name)
        scores = collections.defaultdict(dict)
        durations = collections.defaultdict(dict)
        for env, agent in itertools.product(envs, agents):
            print('Benchmark', agent.__name__, 'on', env)
            directory = None
            if experiment:
                directory = os.path.join(
                    experiment, '{}-{}'.format(env, agent.__name__))
            score, duration = self._benchmark(directory, env, agent)
            best = [max(x) for x in score]
            print('Mean best score {}'.format(round(sum(best) / len(best), 3)))
            scores[env][agent] = score
            durations[env][agent] = duration
        if not experiment:
            return None, scores, durations
        scores, durations = self.read(experiment)
        return experiment, scores, durations

    @classmethod
    def read(cls, experiment):
        """
        Read and return scores of an experiment from its sub directories.
        """
        scores = collections.defaultdict(dict)
        durations = collections.defaultdict(dict)
        for benchmark in cls._get_subdirs(experiment):
            env, agent = os.path.basename(benchmark).rsplit('-', 1)
            scores[env][agent] = []
            durations[env][agent] = []
            for repeat in cls._get_subdirs(benchmark):
                score = np.load(os.path.join(repeat, 'scores.npy'))
                duration = np.load(os.path.join(repeat, 'durations.npy'))
                scores[env][agent].append(score)
                durations[env][agent].append(duration)
        return scores, durations

    def _benchmark(self, directory, env, agent):
        """
        Train an agent for several repeats and store and return scores and
        durations of each episode, grouped by repeats.
        """
        scores, durations = [], []
        template = 'repeat-{:0>' + str(len(str(self._repeats - 1))) + '}'
        for repeat in range(self._repeats):
            subdirectory = None
            if directory:
                subdirectory = os.path.join(directory, template.format(repeat))
            trainer = Trainer(subdirectory, env, **self._trainer_kwargs)
            try:
                agent(trainer)()
            except StopTraining:
                pass
            scores.append(trainer.scores)
            durations.append(trainer.durations)
        return scores, durations

    def _start_experiment(self, name):
        if not self._directory:
            print('Start experiment. Dry run, no results will be saved.')
            return None
        timestamp = time.strftime('%Y-%m-%dT%H-%M-%S', time.gmtime())
        name = '{}-{}'.format(timestamp, name)
        experiment = os.path.join(self._directory, name)
        print('Start experiment', experiment)
        return experiment

    @staticmethod
    def _get_subdirs(directory):
        subdirs = os.listdir(directory)
        subdirs = [os.path.join(directory, x) for x in subdirs]
        subdirs = [x for x in subdirs if os.path.isdir(x)]
        return sorted(subdirs)