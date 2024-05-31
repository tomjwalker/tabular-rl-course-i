import numpy as np
from rl.utils.general import argmax
from typing import Tuple, Union


# TODO: make even more general with vector actions

class QValueTable:
    def __init__(self, state_space_shape: Tuple[int, ...], action_space_shape: int):
        self.values = np.zeros(state_space_shape + (action_space_shape,))

    def get(self, state: Tuple[int, ...], action: Union[int, None] = None) -> Union[float, np.ndarray]:
        if action is not None:
            # If action is specified, return the value of that action in the state
            return self.values[state][action]
        else:
            # If action is not specified, return the values of all actions in the state
            return self.values[state]

    def update(self, state: Tuple[int, ...], action: int, value: float) -> None:
        self.values[state][action] = value

    def get_max_action(self, state: Tuple[int, ...]) -> int:
        return argmax(self.values[state])
