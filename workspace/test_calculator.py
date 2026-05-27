"""
Unit tests for calculator module.
"""

import pytest
from calculator import factorial, fibonacci, fibonacci_sequence


class TestFactorial:
    """Test cases cho hàm factorial."""
    
    def test_factorial_of_zero(self):
        """TC-F01: 0! = 1"""
        assert factorial(0) == 1
    
    def test_factorial_of_one(self):
        """TC-F02: 1! = 1"""
        assert factorial(1) == 1
    
    def test_factorial_small_positive(self):
        """TC-F03: 5! = 120"""
        assert factorial(5) == 120
    
    def test_factorial_large_positive(self):
        """TC-F04: 10! = 3628800"""
        assert factorial(10) == 3628800
    
    def test_factorial_negative_raises_value_error(self):
        """TC-F05: Input âm → ValueError"""
        with pytest.raises(ValueError):
            factorial(-5)
    
    def test_factorial_float_raises_type_error(self):
        """TC-F06: Float input → TypeError"""
        with pytest.raises(TypeError):
            factorial(3.5)
    
    def test_factorial_string_raises_type_error(self):
        """TC-F07: String input → TypeError"""
        with pytest.raises(TypeError):
            factorial("abc")
    
    def test_factorial_of_twenty(self):
        """Test large factorial: 20!"""
        assert factorial(20) == 2432902008176640000


class TestFibonacci:
    """Test cases cho hàm fibonacci."""
    
    def test_fibonacci_of_zero(self):
        """TC-FIB01: F(0) = 0"""
        assert fibonacci(0) == 0
    
    def test_fibonacci_of_one(self):
        """TC-FIB02: F(1) = 1"""
        assert fibonacci(1) == 1
    
    def test_fibonacci_of_two(self):
        """TC-FIB03: F(2) = 1"""
        assert fibonacci(2) == 1
    
    def test_fibonacci_positive(self):
        """TC-FIB04: F(10) = 55"""
        assert fibonacci(10) == 55
    
    def test_fibonacci_large(self):
        """TC-FIB05: F(20) = 6765"""
        assert fibonacci(20) == 6765
    
    def test_fibonacci_negative_raises_value_error(self):
        """TC-FIB06: Input âm → ValueError"""
        with pytest.raises(ValueError):
            fibonacci(-1)
    
    def test_fibonacci_float_raises_type_error(self):
        """Float input → TypeError"""
        with pytest.raises(TypeError):
            fibonacci(3.5)
    
    def test_fibonacci_string_raises_type_error(self):
        """String input → TypeError"""
        with pytest.raises(TypeError):
            fibonacci("abc")


class TestFibonacciSequence:
    """Test cases cho hàm fibonacci_sequence."""
    
    def test_fibonacci_sequence_of_zero(self):
        """Sequence với n=0: [0]"""
        assert fibonacci_sequence(0) == [0]
    
    def test_fibonacci_sequence_of_one(self):
        """Sequence với n=1: [0, 1]"""
        assert fibonacci_sequence(1) == [0, 1]
    
    def test_fibonacci_sequence_of_five(self):
        """TC-FIB07: Sequence từ 0 đến 5"""
        assert fibonacci_sequence(5) == [0, 1, 1, 2, 3, 5]
    
    def test_fibonacci_sequence_of_ten(self):
        """Sequence với n=10"""
        assert fibonacci_sequence(10) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    
    def test_fibonacci_sequence_negative_raises_value_error(self):
        """Input âm → ValueError"""
        with pytest.raises(ValueError):
            fibonacci_sequence(-1)
    
    def test_fibonacci_sequence_float_raises_type_error(self):
        """Float input → TypeError"""
        with pytest.raises(TypeError):
            fibonacci_sequence(3.5)


class TestFibonacciMethods:
    """Test các phương pháp tính Fibonacci khác nhau."""
    
    def test_iterative_matches_recursive(self):
        """Kết quả các phương pháp phải giống nhau."""
        for n in range(15):
            assert fibonacci(n, "iterative") == fibonacci(n, "recursive"), \
                f"Mismatch at n={n}"
    
    def test_memoized_matches_iterative(self):
        """Memoized phải cho kết quả giống iterative."""
        for n in range(20):
            assert fibonacci(n, "memoized") == fibonacci(n, "iterative"), \
                f"Mismatch at n={n}"
    
    def test_recursive_matches_memoized(self):
        """Recursive phải cho kết quả giống memoized."""
        for n in range(15):
            assert fibonacci(n, "recursive") == fibonacci(n, "memoized"), \
                f"Mismatch at n={n}"
    
    def test_invalid_method_raises_error(self):
        """Method không hợp lệ → ValueError"""
        with pytest.raises(ValueError):
            fibonacci(10, method="invalid")


class TestEdgeCases:
    """Test các edge cases bổ sung."""
    
    def test_factorial_two(self):
        """2! = 2"""
        assert factorial(2) == 2
    
    def test_factorial_three(self):
        """3! = 6"""
        assert factorial(3) == 2 * 3
    
    def test_fibonacci_three(self):
        """F(3) = 2"""
        assert fibonacci(3) == 2
    
    def test_fibonacci_four(self):
        """F(4) = 3"""
        assert fibonacci(4) == 3
    
    def test_fibonacci_five(self):
        """F(5) = 5"""
        assert fibonacci(5) == 5
