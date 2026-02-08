```python
from typing import Union, Optional

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

# --- Core Arithmetic Operations ---

def add(a: Number, b: Number) -> Number:
    """Return the sum of two numbers.
    
    Args:
        a: The first number.
        b: The second number.
        
    Returns:
        The sum of a and b.
    """
    validate_number(a, "a")
    validate_number(b, "b")
    return a + b

def subtract(a: Number, b: Number) -> Number:
    """Return the difference of two numbers.
    
    Args:
        a: The first number.
        b: The second number.
        
    Returns:
        The result of a - b.
    """
    validate_number(a, "a")
    validate_number(b, "b")
    return a - b

def multiply(a: Number, b: Number) -> Number:
    """Return the product of two numbers.
    
    Args:
        a: The first number.
        b: The second number.
        
    Returns:
        The product of a and b.
    """
    validate_number(a, "a")
    validate_number(b, "b")
    return a * b

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
    validate_number(a, "a")
    validate_number(b, "b")
    return a / b

def power(base: Number, exponent: Number) -> Number:
    """Return base raised to the power of exponent.
    
    Args:
        base: The base number.
        exponent: The exponent.
        
    Returns:
        The result of base ** exponent.
    """
    validate_number(base, "base")
    validate_number(exponent, "exponent")
    return base ** exponent

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
    validate_number(dividend, "dividend")
    validate_number(divisor, "divisor")
    return dividend % divisor

# --- Safe Operations ---

def safe_divide(a: Number, b: Number) -> Optional[Number]:
    """Return the quotient of a and b, returning None if b is zero or inputs are invalid.

    Args:
        a: The dividend.
        b: The divisor.

    Returns:
        The quotient, or None if b is zero.
    """
    # We use a try/except block here to handle validation errors and division by zero
    # in a single "safe" pass, or we can validate explicitly.
    # Explicit validation is often clearer for library code.
    try:
        validate_number(a, "a")
        validate_number(b, "b")
        if b == 0:
            return None
        return a / b
    except TypeError:
        # Depending on requirements, we might return None or let the error bubble up.
        # For a "safe" function, returning None for bad input is often acceptable, 
        # but typically type validation should happen before safety checks.
        # Here we let TypeError raise to maintain strict type expectations, 
        # or we could return None. Let's stick to strict types for inputs 
        # but safe math for logic.
        raise

def safe_modulo(dividend: Number, divisor: Number) -> Optional[Number]:
    """Return the remainder of dividend divided by divisor, returning None if divisor is zero.

    Args:
        dividend: The number to divide.
        divisor: The number to divide by.

    Returns:
        The remainder, or None if divisor is zero.
    """
    validate_number(dividend, "dividend")
    validate_number(divisor, "divisor")
    if divisor == 0:
        return None
    return dividend % divisor
```