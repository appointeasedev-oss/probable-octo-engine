```python
from typing import Union

Number = Union[float, int]

def add(a: Number, b: Number) -> Number:
    """Return the sum of a and b."""
    return a + b

def subtract(a: Number, b: Number) -> Number:
    """Return the difference of a and b."""
    return a - b

def multiply(a: Number, b: Number) -> Number:
    """Return the product of a and b."""
    return a * b

def divide(a: Number, b: Number) -> Number:
    """Return the quotient of a and b.

    Raises:
        ValueError: If b is zero.
    """
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

def power(base: Number, exponent: Number) -> Number:
    """Return base raised to the power of exponent."""
    return base ** exponent

def modulo(dividend: Number, divisor: Number) -> Number:
    """Return the remainder of dividend divided by divisor.

    Raises:
        ValueError: If divisor is zero.
    """
    if divisor == 0:
        raise ValueError("Cannot perform modulo by zero.")
    return dividend % divisor
```