from utils.general import argmax

import gymnasium as gym
import numpy as np
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
matplotlib.use('TkAgg')


def _is_subelement_present(subelement, my_list):
    """
    Helps check if a subelement is present in a list of tuples. Used to check if state has already been seen.

    Simple example:
    _is_subelement_present((1, 2), [(1, 2, 3), (4, 5, 6)])
        True
    """
    for tpl in my_list:
        if subelement == tpl[:len(subelement)]:
            return True
    return False


class MCOnPolicy:

    def __init__(self, env, epsilon=0.1, gamma=1.0):
        self.env = env
        self.epsilon = epsilon
        self.gamma = gamma

        self.q_values = None
        self.policy = None
        self.returns = None
        self.reset()

    def reset(self):
        # Get env shape
        state_shape = ()
        for space in self.env.observation_space:
            state_shape += (space.n,)

        # Initialise q-values, policy, and returns
        state_and_action_shape = state_shape + (self.env.action_space.n,)
        self.q_values = np.zeros(state_and_action_shape)
        self.policy = np.zeros(state_and_action_shape)
        # Returns is a tensor same shape as q-values, but with each element being a list of returns
        self.returns = np.empty(state_and_action_shape, dtype=object)
        for index in np.ndindex(state_and_action_shape):
            self.returns[index] = []

    def act(self, state):
        """
        Epsilon-greedy policy already coded in the policy, which stores the probabilities of each action for each state.
        Just need to sample from the policy.
        """
        # If the policy is all 0s, then return a random action
        if np.all(self.policy[state][:] == 0):
            return np.random.randint(0, self.env.action_space.n)
        else:
            return np.random.choice(self.env.action_space.n, p=self.policy[state][:])

    def _generate_episode(self):

        episode = []
        state, info = self.env.reset()
        done = False
        while not done:
            action = self.act(state)
            next_state, reward, terminated, truncated, _ = self.env.step(action)
            episode.append((state, action, reward))
            state = next_state
            done = terminated or truncated
        return episode

    def _update_q_and_pi(self, episode):
        """Update q-values using first-visit MC"""
        returns = 0
        for state, action, reward in reversed(episode):
            returns = self.gamma * returns + reward
            if not _is_subelement_present((state, action), episode[:-1]):
                self.returns[state][action].append(returns)
                self.q_values[state][action] = np.mean(self.returns[state][action])
                self._update_policy(state)

    def _update_policy(self, state):
        """
        Update the policy using the q-values.
        Where there are ties, break them randomly.
        π(a|s) is:
            - probability 1 - epsilon - epsilon / |A(s)| for the action with the highest q-value
            - epsilon /  |A(s)| for all other actions
        """

        best_action = argmax(self.q_values[state][:])
        # Update the policy
        # TODO: this is A (for any s); make it A(s)
        self.policy[state][:] = self.epsilon / self.env.action_space.n
        self.policy[state][best_action] = 1 - self.epsilon + self.epsilon / self.env.action_space.n

        # Assert that the policy sums to 1 for each state
        assert np.isclose(np.sum(self.policy[state][:]), 1.0), \
            f"Policy does not sum to 1 for state {state}. Sum is {np.sum(self.policy[state][:])}"

    def train(self, num_episodes=10000):

        for episode in range(num_episodes):
            if episode % 1000 == 0:
                print(f"Episode {episode}/{num_episodes}")
            episode = self._generate_episode()
            self._update_q_and_pi(episode)


def get_3d_plot(mc_control, usable_ace=True, fig=None, subplot=111):
    # Get (state) values for a usable ace policy
    if usable_ace:
        values_usable_ace = np.max(mc_control.q_values[:, :, 1, :], axis=2)
    else:
        values_usable_ace = np.max(mc_control.q_values[:, :, 0, :], axis=2)

    # If ax is not provided, create a new 3D axis
    if fig is None:
        fig = plt.figure()

    # Clip the values_usable_ace axes to 12-21 and 1-10
    values_usable_ace = values_usable_ace[12:22, 1:11]

    ax = fig.add_subplot(subplot, projection='3d')

    # Determine meshgrid from state space shape
    x_start = 10
    y_start = 12
    x = np.arange(x_start, x_start + values_usable_ace.shape[1])
    y = np.arange(y_start, y_start + values_usable_ace.shape[0])
    x, y = np.meshgrid(x, y)

    # Use the plot_surface method
    surface = ax.plot_surface(x, y, values_usable_ace, cmap="viridis")

    # Limit z-axis to -1 to 1
    ax.set_zlim(-1, 1)

    return fig, ax


def plot_policy(mc_control):

    usable_ace = mc_control.policy[11:22, :, 0]
    usable_ace = pd.DataFrame(usable_ace)
    usable_ace.index = np.arange(11, 22)
    usable_ace.columns = np.arange(1, 11)
    no_usable_ace = mc_control.policy[11:22, :, 1]
    no_usable_ace = pd.DataFrame(no_usable_ace)
    no_usable_ace.index = np.arange(11, 22)
    no_usable_ace.columns = np.arange(1, 11)

    fig, ax = plt.subplots(1, 2)


def run():

    env = gym.make("Blackjack-v1", sab=True)  # `sab` means rules following Sutton and Barto
    TRAIN_EPISODES = 10000

    mc_control = MCOnPolicy(env)
    mc_control.train(num_episodes=TRAIN_EPISODES)

    # Plot the state value functions - with and without usable ace
    fig = plt.figure(figsize=plt.figaspect(0.5))
    fig, ax_0 = get_3d_plot(mc_control, usable_ace=True, fig=fig, subplot=121)
    ax_0.set_title("Usable ace")
    ax_0.set_xlabel("Dealer showing")
    ax_0.set_ylabel("Player sum")
    ax_0.set_zlabel("Value")
    fig, ax_1 = get_3d_plot(mc_control, usable_ace=False, fig=fig, subplot=122)
    ax_1.set_title("No usable ace")
    ax_1.set_xlabel("Dealer showing")
    ax_1.set_ylabel("Player sum")
    ax_1.set_zlabel("Value")

    plt.show()


if __name__ == "__main__":
    run()
