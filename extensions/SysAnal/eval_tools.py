from operator import le, ge
from typing import List, Any, Type, Callable

from pydantic import BaseModel, Field


class Entity(BaseModel):
    dimensions: List[Any]
    score: float = Field(default=0)
    dimensions_scores: List[float] = Field(default_factory=list)


class EvalMapping(BaseModel):
    eval_funcs: List[Callable[[Any], float]]
    dimensions_type: List[Type]
    dimensions_score_weight: List[float]

    def check_align(self):
        if not (len(self.eval_funcs) == len(self.dimensions_type) == len(self.dimensions_score_weight)):
            raise ValueError("eval_funcs, dimensions_type, dimensions_score_weight should have same length")

    def eval_entity(self, entity: Entity) -> Entity:
        self.check_align()

        scores: List[float] = []
        weighted_score: float = 0
        for eval_func, dimension_type, dimension, weight in zip(
            self.eval_funcs, self.dimensions_type, entity.dimensions, self.dimensions_score_weight
        ):
            if not isinstance(dimension, dimension_type):
                raise ValueError("dimension type not match")
            dimension_score = eval_func(dimension)
            scores.append(dimension_score)
            weighted_score += dimension_score * weight
        entity.score = weighted_score
        entity.dimensions_scores = scores
        return entity


import numpy as np


def is_sorted(arr):
    return np.all(np.diff(arr) > 0) or np.all(np.diff(arr) < 0)


from typing import List, Callable


def disp_evaler_constructor(score_level: List[float], baselines: List[float]) -> Callable[[float], float]:
    """
    Construct a function that evaluates a given dimension against a set of baselines
    and returns the corresponding score level.

    Args:
        score_level (List[float]): A list of score levels
        baselines (List[float]): A list of baseline values

    Returns:
        Callable[[float], float]: A function that takes a dimension as input and returns
        the corresponding score level based on the baselines
    """
    if not is_sorted(baselines):
        raise ValueError("baselines should be sorted")
    method = ge if baselines[0] > baselines[-1] else le

    if len(score_level) != len(baselines) + 1:
        raise ValueError("score_level should have one more element than baselines")

    def _evaler(dimension: float) -> float:
        """
        Evaluate the given dimension against the baselines and return the score level.

        Args:
            dimension (float): The dimension value to evaluate

        Returns:
            float: The corresponding score level based on the baselines

        Raises:
            ValueError: If the dimension value is not within the baselines range
        """
        for level, baseline in zip(score_level, baselines):
            if method(dimension, baseline):
                return level
        return score_level[-1]

    return _evaler
