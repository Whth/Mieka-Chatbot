import copy
from math import pow
from typing import Self, Iterable

from pydantic import BaseModel, Field

DEFAULT_INDEX_RATE = 0.1


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
    if rate == 0:
        return present_value
    if rate < 0:
        raise ValueError("Interest rate cannot be negative")
    if period_length < 0:
        raise ValueError("Period length cannot be negative")

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
    if rate == 0:
        return present_value / period_length

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
    if rate == 0:
        return future_value
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
    if rate == 0:
        return future_value / period_length
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
    if rate == 0:
        return addup_value * period_length
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
    if rate == 0:
        return addup_value * period_length
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

    def to_(
        self,
        index_rate: float,
        abs_sequential_index: int = None,
        rel_sequential_index: int = 0,
        target_duration: int = 1,
    ) -> "Worth":
        """
        Returns a new instance of the 'Worth' class with modified values.

        Args:
            index_rate (float, optional): The index rate.
            abs_sequential_index (int, optional): The absolute sequential index. Defaults to None.
            rel_sequential_index (int, optional): The relative sequential index. Defaults to 0.
            target_duration (int, optional): The target duration. Defaults to 1.

        Returns:
            Worth: A new instance of the 'Worth' class.

        Raises:
            ValueError: If both 'abs_sequential_index' and 'rel_sequential_index' are specified.
            RuntimeError: If the code reaches an unexpected point.

        """
        # Make sure only one of 'abs_sequential_index' and 'rel_sequential_index' is specified
        if abs_sequential_index is not None and rel_sequential_index != 0:
            raise ValueError("Cannot specify both abs_sequential_index and rel_sequential_index")

        # If no index is specified or the indices are equal to the current indices
        if (abs_sequential_index is None and rel_sequential_index == 0) or (
            abs_sequential_index == self.sequential_index and rel_sequential_index == 0
        ):
            # If the target duration is equal to the current duration, return a deep copy of the current instance
            if target_duration == self.duration:
                return copy.deepcopy(self)

            # Calculate the modified value using 'present_to_addup' and 'addup_to_present' functions
            modified_value = present_to_addup(
                addup_to_present(self.value, rate=index_rate, period_length=self.duration),
                rate=index_rate,
                period_length=target_duration,
            )

            # Return a new instance of 'Worth' class with modified values
            return Worth(
                value=modified_value,
                sequential_index=self.sequential_index,
                duration=target_duration,
            )

        # Calculate the target index based on the given indices
        target_index = abs_sequential_index or (rel_sequential_index + self.sequential_index)

        # If the target index is less than the current index
        if target_index < self.sequential_index:
            # Calculate the distance between the current index and the target index
            distance = self.sequential_index - target_index

            # Calculate the modified value using
            # 'present_to_addup', 'future_to_present', and 'addup_to_present' functions
            target_value = present_to_addup(
                future_to_present(addup_to_present(self.value, index_rate, self.duration), index_rate, distance),
                index_rate,
                target_duration,
            )
        # If the target index is greater than the current index
        elif target_index > self.sequential_index:
            # Calculate the distance between the target index and the current index
            distance = target_index - self.sequential_index

            # Calculate the modified value using
            # 'present_to_addup', 'present_to_future', and 'addup_to_present' functions
            target_value = present_to_addup(
                present_to_future(addup_to_present(self.value, index_rate, self.duration), index_rate, distance),
                index_rate,
                target_duration,
            )
        else:
            # This should not be reached
            raise RuntimeError("Should not reach here")

        # Return a new instance of 'Worth' class with modified values
        return Worth(value=target_value, sequential_index=target_index, duration=target_duration)

    def __add__(self, other: Self | float) -> "Worth":
        if isinstance(other, float):
            return Worth(value=self.value + other, sequential_index=self.sequential_index, duration=self.duration)
        elif isinstance(other, Worth):
            if self.duration == other.duration and self.sequential_index == other.sequential_index:
                return Worth(
                    value=self.value + other.value, sequential_index=self.sequential_index, duration=self.duration
                )
            raise ValueError(f"Cannot add 'Worth' instances with different 'duration' and 'sequential_index' values")
        else:
            raise ValueError(f"Cannot add {type(other)} to 'Worth'")

    def __sub__(self, other: Self | float) -> "Worth":
        if isinstance(other, float):
            return Worth(value=self.value - other, sequential_index=self.sequential_index, duration=self.duration)
        elif isinstance(other, Worth):
            if self.duration == other.duration and self.sequential_index == other.sequential_index:
                return Worth(
                    value=self.value - other.value, sequential_index=self.sequential_index, duration=self.duration
                )
            raise ValueError(
                f"Cannot subtract 'Worth' instances with different 'duration' and 'sequential_index' values"
            )
        else:
            raise ValueError(f"Cannot subtract {type(other)} from 'Worth'")

    def __mul__(self, other: float) -> "Worth":
        return Worth(value=self.value * other, sequential_index=self.sequential_index, duration=self.duration)

    def __truediv__(self, other: float) -> "Worth":
        return Worth(value=self.value / other, sequential_index=self.sequential_index, duration=self.duration)

    def __eq__(self, other: Self | float) -> bool:
        if isinstance(other, float):
            return self.value == other
        if isinstance(other, Worth):
            if self.duration == other.duration and self.sequential_index == other.sequential_index:
                return self.value == other.value
            return self.to_(DEFAULT_INDEX_RATE).value == other.to_(DEFAULT_INDEX_RATE).value

    def __lt__(self, other: Self | float) -> bool:
        if isinstance(other, float):
            return self.value < other
        if isinstance(other, Worth):
            if self.duration == other.duration and self.sequential_index == other.sequential_index:
                return self.value < other.value
            return self.to_(DEFAULT_INDEX_RATE).value < other.to_(DEFAULT_INDEX_RATE).value

    def __gt__(self, other: Self | float) -> bool:
        if isinstance(other, float):
            return self.value > other
        if isinstance(other, Worth):
            if self.duration == other.duration and self.sequential_index == other.sequential_index:
                return self.value > other.value
            return self.to_(DEFAULT_INDEX_RATE).value > other.to_(DEFAULT_INDEX_RATE).value

    def __le__(self, other: Self | float) -> bool:
        if isinstance(other, float):
            return self.value <= other
        if isinstance(other, Worth):
            if self.duration == other.duration and self.sequential_index == other.sequential_index:
                return self.value <= other.value
            return self.to_(DEFAULT_INDEX_RATE).value <= other.to_(DEFAULT_INDEX_RATE).value

    def __ge__(self, other: Self | float) -> bool:
        if isinstance(other, float):
            return self.value >= other
        if isinstance(other, Worth):
            if self.duration == other.duration and self.sequential_index == other.sequential_index:
                return self.value >= other.value
            return self.to_(DEFAULT_INDEX_RATE).value >= other.to_(DEFAULT_INDEX_RATE).value

    @staticmethod
    def sum_up(values: Iterable["Worth"], index_rate: float, target_sequential_index: int = 0) -> "Worth":
        """
        Calculate the sum of a sequence of values, each multiplied by a given index rate.

        Parameters:
        - values: An iterable of Worth objects representing the values to be summed up.
        - index_rate: A float representing the rate at which each value should be multiplied.
        - target_sequential_index: An optional integer representing the target sequential index.

        Returns:
        - sum_up: A Worth object representing the sum of the values after applying the index rate.


        """
        sum_up: "Worth" = Worth(value=0)
        for value in values:
            sum_up += value.to_(index_rate, target_sequential_index)
        return sum_up
