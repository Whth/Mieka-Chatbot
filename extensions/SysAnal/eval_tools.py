from collections import OrderedDict
from operator import le, ge
from typing import List, Any, Type, Callable, Tuple, TypeAlias

import numpy as np
from pydantic import BaseModel, Field

RI: TypeAlias = OrderedDict[str, float | None]
BRI: TypeAlias = OrderedDict[str, float]
Weights: TypeAlias = OrderedDict[str, float]


def weighted_sum(values: List[float], weights: List[float]) -> float:
    """
    Calculate the weighted sum of values.

    Args:
        values (List[float]): A list of values.
        weights (List[float]): A list of weights.

    Returns:
        float: The weighted sum of values.
    Examples:
        >>> weighted_sum([1, 1, 1], [2, 3, 5])
        1.0
    """
    # 将权重归一化到[0, 1]范围内，并使它们的和为1
    weights = np.array(weights)

    weights = weights / weights.sum()

    # 计算加权和
    return np.dot(values, weights)


def is_sorted(arr):
    return np.all(np.diff(arr) > 0) or np.all(np.diff(arr) < 0)


# region Correlation matrix method
class Entity(BaseModel):
    dimensions: List[Any]
    score: float = Field(default=0)
    dimensions_scores: List[float] = Field(default_factory=list)


class EvalMapping(BaseModel):
    eval_funcs: List[Callable[[Any], float]]
    dimensions_type: List[Type]
    dimensions_score_weight: List[float]

    def check_align(self):
        """
        Check if the lengths of eval_funcs, dimensions_type, and dimensions_score_weight are equal.

        This function raises a ValueError if the lengths are not equal.


        Returns:
            None
        """
        if not (len(self.eval_funcs) == len(self.dimensions_type) == len(self.dimensions_score_weight)):
            raise ValueError("eval_funcs, dimensions_type, dimensions_score_weight should have same length")

    def eval_entity(self, entity: Entity) -> Entity:
        """
        Evaluates an entity and calculates its score.

        Args:
            entity (Entity): The entity to be evaluated.

        Returns:
            Entity: The evaluated entity with the calculated score.

        Raises:
            ValueError: If the type of dimension in the entity does not match the expected type.

        """
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


# endregion


class KleeModel(BaseModel):
    """
    Klee Model

    R_j Relative importance
    Fuzzy values only be given from human evaluation

    K_j Benchmarked relative importance
    K_j = R_j*K_(j-1)

    W_j Item weight
    W_j = K_j/sum(K)

    """

    class Config:
        validate_assignment = True
        validate_all = True

    item_labels: Tuple[str, ...] = Field(allow_mutation=False)

    benchmarked_relative_importance: Tuple[float, ...] = Field(default=None, allow_mutation=True)

    @staticmethod
    def make_benchmark_relative_importance(relative_importance: RI) -> BRI:
        """
        Calculates the relative importance of each label in the given ordered dictionary.

        Args:
            relative_importance (OrderedDict[str, float | None]): The ordered dictionary containing the
                relative importance values for each label. The keys represent the labels and the values
                represent the importance values. The values can be either a float or None.

        Returns:
            OrderedDict[str, float]: The ordered dictionary containing the relative importance of each
                label. The keys represent the labels and the values represent the calculated relative
                importance values.

        Examples:
            >>> KleeModel.make_benchmark_relative_importance(OrderedDict({"a": 3.0, "b": 3.0, "c": 0.5, "d": 4.0, "e": None}))
            OrderedDict([('a', 18.0), ('b', 6.0), ('c', 2.0), ('d', 4.0), ('e', 1.0)])
        """
        labels = list(relative_importance.keys())
        output = OrderedDict.fromkeys(labels, 1.0)
        labels.reverse()
        last_label = None
        for label in labels:
            if last_label:
                output[label] = relative_importance[label] * output[last_label]
            last_label = label
        return output

    @staticmethod
    def make_weight(benchmarked_relative_importance: BRI) -> Weights:
        """
        Calculate the weight of each element in the given `benchmarked_relative_importance` dictionary.

        Args:
            benchmarked_relative_importance (OrderedDict[str, float]): A dictionary containing the labels as keys
                and the relative importance as values.

        Returns:
            OrderedDict[str, float]: A new dictionary with the same keys as `benchmarked_relative_importance`,
                but with the values normalized to sum up to 1.0.
        Examples:
            >>> KleeModel.make_weight(OrderedDict([('a', 18.0), ('b', 6.0), ('c', 2.0), ('d', 4.0), ('e', 1.0)]))
            OrderedDict([('a', 0.5806451612903226), ('b', 0.1935483870967742), ('c', 0.06451612903225806), ('d', 0.12903225806451613), ('e', 0.03225806451612903)])

        """
        sum_up = sum(benchmarked_relative_importance.values())
        output = OrderedDict.fromkeys(benchmarked_relative_importance.keys(), 0.0)
        for label in benchmarked_relative_importance.keys():
            output[label] = benchmarked_relative_importance[label] / sum_up
        return output

    @staticmethod
    def make_weight_from_raw(relative_importance: RI) -> Weights:
        """
        Generate the weight from the given relative importance.

        Parameters:
            relative_importance (RI): The relative importance object.

        Returns:
            Weights: The generated weights object.
        """
        return KleeModel.make_weight(KleeModel.make_benchmark_relative_importance(relative_importance))
