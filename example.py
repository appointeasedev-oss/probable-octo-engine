```python
from typing import Union, Optional

# Define a type alias for numbers supported by the library
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
        ZeroDivisionError: If b is zero.
    """
    # Let Python handle the native ZeroDivisionError for cleaner code
    return a / b

def power(base: Number, exponent: Number) -> Number:
    """Return base raised to the power of exponent."""
    return base ** exponent

def modulo(dividend: Number, divisor: Number) -> Number:
    """Return the remainder of dividend divided by divisor.

    Raises:
        ZeroDivisionError: If divisor is zero.
    """
    # Let Python handle the native ZeroDivisionError
    return dividend % divisor

# --- Utility and Safe Operations ---

def is_number(value: object) -> bool:
    """Check if a value is a number (int or float)."""
    return isinstance(value, (int, float))

def validate_number(value: object, name: str) -> None:
    """Validate that a value is a number, raising TypeError if not."""
    if not is_number(value):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}.")

def safe_divide(a: Number, b: Number) -> Optional[Number]:
    """Return the quotient of a and b, returning None if b is zero."""
    if b == 0:
        return None
    return a / b

def safe_modulo(dividend: Number, divisor: Number) -> Optional[Number]:
    """Return the remainder of dividend divided by divisor, returning None if divisor is zero."""
    if divisor == 0:
        return None
    return dividend % divisor
```