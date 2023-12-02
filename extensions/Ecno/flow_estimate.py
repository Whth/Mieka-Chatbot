from math import log10
from typing import List


def get_estimate_indexes(base_price: float, base_index: float, target_index: float) -> float:
    """
    Based on the cargo price indexes, the price could then be estimated.
    Calculates the estimated price given a base price, base index, and target index.

    Parameters:
        base_price (float): The base price of the item.
        base_index (float): The index value corresponding to the base price.
        target_index (float): The index value corresponding to the desired target price.

    Returns:
        float: The estimated price based on the given indexes and base price.

    References:
        book: "Engineering Economics",page: 17
    """
    return base_price * (target_index / base_index)


print(get_estimate_indexes(1, 1, 5))


def get_estimate_unit_price(unit_price: float, count: float) -> float:
    """
    Calculate the estimated price based on the unit price and count.

    Args:
        unit_price: The price of a single unit.
        count: The number of units.

    Returns:
        The estimated price.

    References:
        book: "Engineering Economics",page: 18
    """
    return unit_price * count


def get_estimate_factor(base_prices: List[float], factors_count: List[float], factor_unit_prices: List[float]):
    """
    Calculate the estimate factor based on the given parameters.


    Parameters:
        base_prices (List[float]): A list of base prices.
        factors_count (List[float]): A list of factor counts.
        factor_unit_prices (List[float]): A list of factor unit prices.

    Returns:
        float: The estimate factor calculated based on the given parameters.


    References:
        book: "Engineering Economics",page: 18
    """
    return sum(base_prices) + sum([f * m for f, m in zip(factors_count, factor_unit_prices)])


def get_estimate_power_sizing(
    base_production: float, new_production: float, fix_constant: float, pay_return_index: float
) -> float:
    """
    Calculate the estimated power sizing based on the given parameters.

    Parameters:
        base_production (float): The base production value.
        new_production (float): The new production value.
        fix_constant (float): The fix constant value.
        pay_return_index (float): The pay return index value.

    Returns:
        float: The estimated power sizing value.

    References:
        book: "Engineering Economics",page: 19
    """
    return base_production * ((new_production / base_production) ** pay_return_index) * fix_constant


def get_work_time_learning_curve(base_time: float, learning_rate: float, step: float) -> float:
    """
    Calculate the learning curve based on the given parameters.

    Parameters:
        base_time (float): The base time value.
        learning_rate (float): The learning rate value.
        step (float): The step value.

    Returns:
        float: The estimated learning curve value.

    References:
        book: "Engineering Economics",page: 21

    Examples:
        >>> get_work_time_learning_curve(1200, 0.8, 120)
        256.94157893450887
    """
    return base_time * (step ** (log10(learning_rate) / log10(2)))
