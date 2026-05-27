"""
Core math functions for Math Sequence Calculator.

This module provides mathematical functions for calculating factorials
and Fibonacci sequences.
"""


def factorial(n: int) -> int:
    """
    Tính giai thừa của n.
    
    Args:
        n: Số nguyên không âm
        
    Returns:
        n! = n × (n-1) × ... × 2 × 1
        
    Raises:
        TypeError: Nếu n không phải integer
        ValueError: Nếu n là số âm
    """
    if not isinstance(n, int):
        raise TypeError(f"Factorial requires an integer, got {type(n).__name__}")
    
    if n < 0:
        raise ValueError(f"Factorial is not defined for negative numbers: {n}")
    
    if n == 0 or n == 1:
        return 1
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def fibonacci(n: int, method: str = "iterative") -> int:
    """
    Tính số Fibonacci thứ n (0-indexed).
    
    Args:
        n: Vị trí trong dãy Fibonacci (không âm)
        method: Phương pháp tính ("iterative", "recursive", "memoized")
        
    Returns:
        F(n) theo chuẩn 0-indexed: F(0)=0, F(1)=1, F(2)=1...
        
    Raises:
        TypeError: Nếu n không phải integer
        ValueError: Nếu n là số âm
    """
    if not isinstance(n, int):
        raise TypeError(f"Fibonacci requires an integer, got {type(n).__name__}")
    
    if n < 0:
        raise ValueError(f"Fibonacci is not defined for negative numbers: {n}")
    
    if method == "iterative":
        return _fibonacci_iterative(n)
    elif method == "recursive":
        return _fibonacci_recursive(n)
    elif method == "memoized":
        return _fibonacci_memoized(n)
    else:
        raise ValueError(f"Unknown method: {method}. Use 'iterative', 'recursive', or 'memoized'")


def _fibonacci_iterative(n: int) -> int:
    """
    Tính Fibonacci bằng phương pháp lặp.
    
    Args:
        n: Vị trí trong dãy Fibonacci
        
    Returns:
        F(n)
    """
    if n == 0:
        return 0
    if n == 1:
        return 1
    
    prev, curr = 0, 1
    for _ in range(2, n + 1):
        prev, curr = curr, prev + curr
    return curr


def _fibonacci_recursive(n: int) -> int:
    """
    Tính Fibonacci bằng phương pháp đệ quy.
    
    Args:
        n: Vị trí trong dãy Fibonacci
        
    Returns:
        F(n)
    """
    if n == 0:
        return 0
    if n == 1:
        return 1
    return _fibonacci_recursive(n - 1) + _fibonacci_recursive(n - 2)


def _fibonacci_memoized(n: int, memo: dict = None) -> int:
    """
    Tính Fibonacci bằng phương pháp memoization.
    
    Args:
        n: Vị trí trong dãy Fibonacci
        memo: Dictionary lưu cache các giá trị đã tính
        
    Returns:
        F(n)
    """
    if memo is None:
        memo = {0: 0, 1: 1}
    
    if n in memo:
        return memo[n]
    
    memo[n] = _fibonacci_memoized(n - 1, memo) + _fibonacci_memoized(n - 2, memo)
    return memo[n]


def fibonacci_sequence(n: int) -> list:
    """
    Trả về dãy Fibonacci từ F(0) đến F(n).
    
    Args:
        n: Vị trí kết thúc (không âm)
        
    Returns:
        List [F(0), F(1), ..., F(n)]
        
    Raises:
        TypeError: Nếu n không phải integer
        ValueError: Nếu n là số âm
    """
    if not isinstance(n, int):
        raise TypeError(f"Fibonacci sequence requires an integer, got {type(n).__name__}")
    
    if n < 0:
        raise ValueError(f"Fibonacci sequence is not defined for negative numbers: {n}")
    
    if n == 0:
        return [0]
    
    sequence = [0, 1]
    for i in range(2, n + 1):
        sequence.append(sequence[i - 1] + sequence[i - 2])
    
    return sequence
