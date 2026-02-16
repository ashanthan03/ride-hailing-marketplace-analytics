import numpy as np

class QAllocator:

    def __init__(self, num_zones):
        self.q_table = {}
        self.num_zones = num_zones
        self.alpha = 0.1
        self.gamma = 0.9
        self.epsilon = 0.1

    def get_state(self, zone, ratio):
        ratio_bucket = round(ratio, 1)
        return (zone, ratio_bucket)

    def choose_action(self, state):
        if np.random.rand() < self.epsilon:
            return np.random.choice(["allocate", "skip"])
        return self.q_table.get(state, {}).get("best_action", "allocate")

    def update(self, state, action, reward):
        if state not in self.q_table:
            self.q_table[state] = {"allocate": 0, "skip": 0, "best_action": "allocate"}

        old_value = self.q_table[state][action]
        new_value = old_value + self.alpha * (reward - old_value)
        self.q_table[state][action] = new_value

        # update best action
        best_action = max(
            ["allocate", "skip"],
            key=lambda a: self.q_table[state][a]
        )
        self.q_table[state]["best_action"] = best_action
