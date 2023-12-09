from math import pow

from pydantic import BaseModel, Field


def present_to_future(present_value: float, rate: float, period_length: int) -> float:
    """
    Calculate the future value of an investment based on the present value, interest rate, and period length.

    Parameters:
        present_value (float): The present value of the investment.
        rate (float): The interest rate as a decimal.
        period_length (int): The length of the investment period in years.

    Returns:
        float: The future value of the investment.

    Example:
    >>> present_to_future(100, 0.1, 1)
    110.00000000000001
    >>> present_to_future(100, 0.1, 2)
    121.00000000000001
    >>> present_to_future(100, 0.1, 3)
    133.10000000000005
    """
    return present_value * pow((1 + rate), period_length)


def present_to_addup(present_value: float, rate: float, period_length: int) -> float:
    """
    Calculate the future value of a present value using compound interest.

    Args:
        present_value (float): The present value of the investment.
        rate (float): The interest rate per period.
        period_length (int): The number of periods.

    Returns:
        float: The future value of the investment.
    Examples:
        >>> present_to_addup(100, 0.1, 1)
        109.99999999999991
        >>> present_to_addup(100, 0.1, 2)
        57.619047619047585
        >>> present_to_addup(100, 0.1, 3)
        40.211480362537735
    """
    factor = pow((rate + 1), period_length)
    numerator = rate * factor
    denominator = factor - 1
    return present_value * numerator / denominator


def future_to_present(future_value: float, rate: float, period_length: int) -> float:
    """
    Calculate the present value of a future cash flow.

    Args:
        future_value (float): The value of the future cash flow.
        rate (float): The discount rate used to calculate the present value.
        period_length (int): The number of periods until the future cash flow is received.

    Returns:
        float: The present value of the future cash flow.
    Examples:
        >>> future_to_present(100, 0.1, 1)
        90.9090909090909
        >>> future_to_present(100, 0.1, 2)
        82.64462809917354
        >>> future_to_present(100, 0.1, 3)
        75.13148009015775
    """
    return future_value / pow((1 + rate), period_length)


def future_to_addup(future_value: float, rate: float, period_length: int) -> float:
    """
    Calculate the present value of a future cash flow.

    Args:
        future_value (float): The value of the future cash flow.
        rate (float): The discount rate.
        period_length (int): The length of the period in which the future cash flow will be received.

    Returns:
        float: The present value of the future cash flow.

    Examples:
        >>> future_to_addup(100, 0.1, 1)
        99.99999999999991
        >>> future_to_addup(100, 0.1, 2)
        47.61904761904758
        >>> future_to_addup(100, 0.1, 3)
        30.211480362537728
    """
    numerator = rate
    denominator = pow(rate + 1, period_length) - 1
    return future_value * numerator / denominator


def addup_to_present(addup_value: float, rate: float, period_length: int) -> float:
    """
    Calculate the present value of a future cash flow.

    Args:
        addup_value (float): The value of the future cash flow.
        rate (float): The discount rate.
        period_length (int): The length of the period in which the future cash flow will be received.

    Returns:
        float: The present value of the future cash flow.

    Examples:
        >>> addup_to_present(100, 0.1, 1)
        90.90909090909098
        >>> addup_to_present(100, 0.1, 2)
        173.55371900826458
        >>> addup_to_present(100, 0.1, 3)
        248.68519909842243
    """
    factor = pow((rate + 1), period_length)
    denominator = rate * factor
    numerator = factor - 1
    return addup_value * numerator / denominator


def addup_to_future(addup_value: float, rate: float, period_length: int) -> float:
    """
    Calculate the present value of a future cash flow.

    Args:
        addup_value (float): The value of the future cash flow.
        rate (float): The discount rate.
        period_length (int): The length of the period in which the future cash flow will be received.

    Returns:
        float: The present value of the future cash flow.

    Examples:
        >>> addup_to_future(100, 0.1, 1)
        100.00000000000009
        >>> addup_to_future(100, 0.1, 2)
        210.00000000000017
        >>> addup_to_future(100, 0.1, 3)
        331.00000000000034

    """
    denominator = rate
    numerator = pow(rate + 1, period_length) - 1
    return addup_value * numerator / denominator


class Worth(BaseModel):
    class Config:
        allow_mutation = True
        validate_assignment = True

    value: float

    sequential_index: int = Field(default=0)
    duration: int = Field(default=1)

    def to_(self, target_sequential_index: int, target_duration: int) -> "Worth":
        # TODO: to in-bound/off-bound value
        pass
