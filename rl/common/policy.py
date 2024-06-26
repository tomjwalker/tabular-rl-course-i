import numpy as np
from typing import Tuple, Union
from rl.common.q_value_table import QValueTable


class BasePolicy:
    def __init__(self, action_space: Union[int, Tuple[int]]) -> None:
        self.action_space = action_space

    def select_action(self, state: Tuple[int, ...], q_values: QValueTable) -> int:
        raise NotImplementedError


class DeterministicPolicy:
    # TODO: unify with EpsilonGreedyPolicy / BasePolicy
    #   (including dtype)
    # TODO: "value" risks confusion with value function?
    def __init__(self, state_shape: Tuple[int, ...]) -> None:
        self.value = np.zeros(state_shape, dtype=np.int8)

    def select_action(self, state: Tuple[int, ...]) -> int:
        return self.value[state]

    def update(
            self,
            state: Tuple[int, ...],
            q_values: QValueTable,
            ties: str = "random",
    ) -> None:
        self.value[state] = q_values.get_max_action(state, ties=ties)


class EpsilonGreedyPolicy(BasePolicy):
    def __init__(self, epsilon: float, action_space: Union[int, Tuple[int]]) -> None:
        super().__init__(action_space)
        self.epsilon = epsilon

    def select_action(
            self,
            state: Tuple[int, ...],
            q_values: QValueTable,
            ties: str = "random",
    ) -> int:
        if np.random.random() < self.epsilon:
            return np.random.choice(self.action_space)
        else:
            return q_values.get_max_action(state, ties=ties)

    def compute_probs(self, state: Tuple[int, ...], q_values: QValueTable) -> np.ndarray:
        probs = np.ones(self.action_space) * self.epsilon / self.action_space
        best_action = q_values.get_max_action(state)
        probs[best_action] = 1 - self.epsilon + self.epsilon / self.action_space
        return probs
