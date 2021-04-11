from __future__ import annotations
from inspect import cleandoc
from utils import *


class PNTState:
    """Represents a pick numbered-tokens state"""

    def __init__(self, total_tokens: int, num_taken_tokens: int, taken_tokens: list, max_depth: int):
        self._total_tokens: int = total_tokens
        self._num_taken_tokens: int = num_taken_tokens
        self._taken_tokens: list = taken_tokens
        # If the given depth is > 0, assign it normally. Otherwise, infinite depth (go all the way to the leaves)
        self._max_depth: int = max_depth if max_depth > 0 else float('inf')
        self._current_depth: int = 0

    def __str__(self):
        return cleandoc(f"""
        PNT State
        Total tokens: {self._total_tokens}
        Num taken token: {self._num_taken_tokens}
        Tokens taken: {self._taken_tokens}
        Max Depth: {self._max_depth}
        Current Depth: {self._current_depth}
        """)

    @property
    def current_depth(self):
        return self._current_depth

    @current_depth.setter
    def current_depth(self, new_depth):
        self._current_depth = new_depth

    @property
    def total_tokens(self):
        return self._total_tokens

    @property
    def num_taken_tokens(self):
        return self._num_taken_tokens

    @property
    def taken_tokens(self):
        return self._taken_tokens

    @property
    def max_depth(self):
        return self._max_depth

    @property
    def winner(self) -> int:
        if len(self.next_possible_tokens()) == 0 and self._num_taken_tokens > 0:
            return 2 - self._num_taken_tokens % 2
        return 0

    @property
    def next_player(self) -> int:
        if self._num_taken_tokens % 2 == 0:
            return 1
        return 2

    @property
    def last_taken_token(self) -> int:
        return self._taken_tokens[-1]  # TODO: This causes a "list index out of range" exception. Handle better?

    def _take_token(self, token) -> int:
        self._num_taken_tokens += 1
        self._taken_tokens.append(token)
        return token

    def get_token(self, token) -> int:
        if token in self.next_possible_tokens():
            return self._take_token(token)
        raise ValueError("Invalid token.")

    def next_possible_tokens(self) -> list:
        # First move
        if self._num_taken_tokens == 0:
            return [token for token in range(1, (self._total_tokens + 1) // 2)
                    if token not in self._taken_tokens and
                    token % 2 == 1]
        # Not first move
        else:
            return [token for token in range(1, (self._total_tokens + 1))
                    if token not in self._taken_tokens and
                    is_factor_or_multiple(token, self.last_taken_token)]

    def static_board_evaluation(self) -> float:
        if self.winner == 1:
            return 1.0
        elif self.winner == 2:
            return -1.0

        evaluation_value = 0
        if 1 not in self.taken_tokens:
            evaluation_value = 0
        elif self.last_taken_token == 1:
            if len(self.next_possible_tokens()) % 2 == 1:
                evaluation_value = 0.5
            else:
                evaluation_value = -0.5
        elif is_prime(self.last_taken_token):
            last_move = self.last_taken_token
            multiples_of_last_token = [token for token in self.next_possible_tokens() if token % last_move == 0]

            if len(multiples_of_last_token) % 2 == 0:
                evaluation_value = -0.7
            else:
                evaluation_value = 0.7
        else:
            last_move = self.last_taken_token
            possible_prime_factors = [token for token in self.next_possible_tokens() if
                                      last_move % token == 0 and is_prime(token)]
            largest_prime = max(possible_prime_factors)
            multiples_of_largest_prime = [token for token in self.next_possible_tokens() if token % largest_prime == 0]

            if len(multiples_of_largest_prime) % 2 == 0:
                evaluation_value = -0.6
            else:
                evaluation_value = 0.6

        return evaluation_value if self.next_player == 1 else -evaluation_value

    def alpha_beta_search(self) -> int:
        """ Performs the Alpha-Beta search algorithm

        :return: The token to take
        """
        # player = self.to_move()
        alpha: float = float('-inf')
        beta: float = float('inf')
        value, move = self.max_value(self, alpha, beta)

        return move

    @staticmethod
    def max_value(state: PNTState, alpha: float, beta: float):
        if state.is_terminal() or state.current_depth > state.max_depth:
            return state.utility(), None

        v = float('-inf')
        move = None

        for token in state.next_possible_tokens():

            v2, a2 = state.min_value(state.result(token), alpha, beta)

            if v2 > v:
                v, move = v2, token
                alpha = max(alpha, v)

            if v >= beta:
                return v, move
        return v, move

    @staticmethod
    def min_value(state: PNTState, alpha: float, beta: float):
        if state.is_terminal() or state.current_depth > state.max_depth:
            return state.utility(), None

        v = float('inf')
        move = None

        for token in state.next_possible_tokens():

            v2, a2 = state.max_value(state.result(token), alpha, beta)

            if v2 < v:
                v, move = v2, token
                beta = min(beta, token)

            if v <= alpha:
                return v, move
        return v, move

    def result(self, action: int) -> PNTState:
        """ The transition model which defines the state resulting from taking the given action in the current state

        :param action: The given action
        :return: A new PNTState resulting from the action
        """

        # Makes a copy of the current state's taken_tokens so we can append to it
        # without appending to both states' taken_tokens
        new_list = self.taken_tokens.copy()
        new_list.append(action)

        new_depth = self.current_depth + 1

        # Create a new PNTState to explore
        new_state = PNTState(self.total_tokens - 1, self.num_taken_tokens + 1, new_list, self.max_depth)
        new_state.current_depth = new_depth

        # # Append the token to the new_states taken_tokens instead of this states taken_tokens
        # new_state.taken_tokens.append(action)

        return new_state

    def to_move(self) -> int:
        """ The player whose turn it is to move in the current state

        :return: The number of the player
        """
        return self.next_player

    def actions(self) -> list:
        """ The set of legal moves in the current state

        :return: The list of possible tokens to take
        """
        return self.next_possible_tokens()

    def is_terminal(self) -> bool:
        """ Returns whether the current State is a terminal state.
        i.e Whether there exist any more moves to make from the current state

        :return: True or False
        """
        return self.next_possible_tokens() == []

    def utility(self) -> float:
        """ Defines final numeric value when game ends in terminal state

        :return: The static board evaluation
        """
        return self.static_board_evaluation()
