```python
import functools
import inspect
from typing import Union, Optional, Callable, Any, TypeVar

# Define a type alias for numbers supported by the library
Number = Union[float, int]

# Define public interface
__all__ = [
    "add",
    "subtract",
    "multiply",
    "divide",
    "power",
    "modulo",
    "is_number",
    "validate_number",
    "safe_divide",
    "safe_modulo",
    "Number",
]

# --- Utility and Type Safety ---

def is_number(value: object) -> bool:
    """Check if a value is a valid Number (int or float).

    Args:
        value: The value to check.

    Returns:
        True if the value is an int or float, False otherwise.
    """
    return isinstance(value, (int, float))

def validate_number(value: object, name: str) -> None:
    """Validate that a value is a Number, raising TypeError if not.

    Args:
        value: The value to validate.
        name: The name of the variable (for error messages).

    Raises:
        TypeError: If the value is not an int or float.
    """
    if not is_number(value):
        raise TypeError(f"'{name}' must be a number (int or float), got {type(value).__name__}.")

# --- Decorator for Validation ---

F = TypeVar("F", bound=Callable[..., Any])

def _validate_inputs(func: F) -> F:
    """Decorator to validate that all arguments are numbers (int or float)."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Get function signature to map arguments to parameter names
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        for name, value in bound_args.arguments.items():
            # We only validate numeric inputs. If the function accepts other types,
            # this check ensures we don't falsely flag them, though strictly
            # typed arithmetic functions usually only accept numbers.
            if not is_number(value):
                # Raising TypeError with the argument name
                raise TypeError(f"'{name}' must be a number (int or float), got {type(value).__name__}.")

        return func(*args, **kwargs)
    return wrapper  # type: ignore

# --- Core Arithmetic Operations ---

@_validate_inputs
def add(a: Number, b: Number) -> Number:
    """Return the sum of two numbers.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The sum of a and b.
    """
    return a + b

@_validate_inputs
def subtract(a: Number, b: Number) -> Number:
    """Return the difference of two numbers.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The result of a - b.
    """
    return a - b

@_validate_inputs
def multiply(a: Number, b: Number) -> Number:
    """Return the product of two numbers.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The product of a and b.
    """
    return a * b

@_validate_inputs
def divide(a: Number, b: Number) -> Number:
    """Return the quotient of two numbers.

    Args:
        a: The dividend.
        b: The divisor.

    Returns:
        The quotient of a and b.

    Raises:
        ZeroDivisionError: If b is zero.
        TypeError: If a or b are not numbers.
    """
    if b == 0:
        raise ZeroDivisionError("division by zero")
    return a / b

@_validate_inputs
def power(base: Number, exponent: Number) -> Number:
    """Return base raised to the power of exponent.

    Args:
        base: The base number.
        exponent: The exponent.

    Returns:
        The result of base ** exponent.
    """
    return base ** exponent

@_validate_inputs
def modulo(dividend: Number, divisor: Number) -> Number:
    """Return the remainder of dividend divided by divisor.

    Args:
        dividend: The number to divide.
        divisor: The number to divide by.

    Returns:
        The remainder of the division.

    Raises:
        ZeroDivisionError: If divisor is zero.
        TypeError: If inputs are not numbers.
    """
    if divisor == 0:
        raise ZeroDivisionError("modulo by zero")
    return dividend % divisor

# --- Safe Operations ---

def safe_divide(a: Number, b: Number) -> Optional[Number]:
    """Return the quotient of a and b, returning None if b is zero or inputs are invalid.

    Args:
        a: The dividend.
        b: The divisor.

    Returns:
        The quotient, or None if b is zero or inputs are invalid.
    """
    if not is_number(a) or not is_number(b):
        return None
    if b == 0:
        return None
    return a / b

def safe_modulo(dividend: Number, divisor: Number) -> Optional[Number]:
    """Return the remainder of dividend divided by divisor, returning None if divisor is zero or inputs are invalid.

    Args:
        dividend: The number to divide.
        divisor: The number to divide by.

    Returns:
        The remainder, or None if divisor is zero or inputs are invalid.
    """
    if not is_number(dividend) or not is_number(divisor):
        return None
    if divisor == 0:
        return None
    return dividend % divisor
```