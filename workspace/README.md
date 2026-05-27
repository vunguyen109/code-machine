# Math Sequence Calculator CLI

Command-line interface for calculating factorials and Fibonacci sequences.

## Features

- **Factorial Calculation**: Calculate n! for any non-negative integer
- **Fibonacci Calculation**: Calculate F(n) using different methods (iterative, recursive, memoized)
- **Fibonacci Sequence**: Display the full sequence from F(0) to F(n)
- **Error Handling**: Clear error messages for invalid inputs
- **100% Test Coverage**: Comprehensive unit and integration tests

## Installation

No external dependencies required. Uses Python 3.8+ standard library only.

For testing, install pytest:

```bash
pip install pytest
```

## Usage

### Factorial

Calculate factorial of a number:

```bash
python mathcalc.py factorial 5
# Output: 120

python mathcalc.py factorial 0
# Output: 1

python mathcalc.py factorial 20
# Output: 2432902008176640000
```

### Fibonacci

Calculate Fibonacci number at position n:

```bash
python mathcalc.py fibonacci 10
# Output: 55

python mathcalc.py fibonacci 0
# Output: 0

python mathcalc.py fibonacci 20
# Output: 6765
```

Display full sequence from F(0) to F(n):

```bash
python mathcalc.py fibonacci 5 --sequence
# Output: 0 1 1 2 3 5

python mathcalc.py fibonacci 10 --seq
# Output: 0 1 1 2 3 5 8 13 21 34 55
```

Choose calculation method:

```bash
python mathcalc.py fibonacci 10 --method iterative
python mathcalc.py fibonacci 10 --method recursive
python mathcalc.py fibonacci 10 --method memoized
```

### Help

```bash
python mathcalc.py --help
python mathcalc.py factorial --help
python mathcalc.py fibonacci --help
```

### Version

```bash
python mathcalc.py --version
# Output: mathcalc 1.0.0
```

## Error Handling

The CLI validates inputs and provides clear error messages:

```bash
# Negative input
python mathcalc.py factorial -5
# Error: Factorial is not defined for negative numbers: -5

# Invalid type
python mathcalc.py fibonacci abc
# Error: invalid argument type

# All errors return exit code 1
```

## Running Tests

Run all tests:

```bash
pytest workspace/ -v
```

Run specific test file:

```bash
pytest workspace/test_calculator.py -v
pytest workspace/test_cli.py -v
```

Run with coverage:

```bash
pip install pytest-cov
pytest workspace/ --cov=. --cov-report=term-missing
```

## Project Structure

```
workspace/
├── mathcalc.py          # CLI entry point
├── calculator.py        # Core math functions
├── test_calculator.py   # Unit tests for calculator
├── test_cli.py          # Integration tests for CLI
└── README.md            # This file
```

## API Reference

### calculator module

#### factorial(n: int) -> int

Calculate factorial of n.

- **Args**: n - Non-negative integer
- **Returns**: n!
- **Raises**: TypeError if n is not int, ValueError if n < 0

#### fibonacci(n: int, method: str = "iterative") -> int

Calculate Fibonacci number F(n).

- **Args**: 
  - n - Non-negative integer (position in sequence)
  - method - Calculation method: "iterative", "recursive", "memoized"
- **Returns**: F(n)
- **Raises**: TypeError if n is not int, ValueError if n < 0

#### fibonacci_sequence(n: int) -> list

Get Fibonacci sequence from F(0) to F(n).

- **Args**: n - Non-negative integer (end position)
- **Returns**: List [F(0), F(1), ..., F(n)]
- **Raises**: TypeError if n is not int, ValueError if n < 0

## Fibonacci Definition

This implementation uses 0-indexed Fibonacci sequence:

- F(0) = 0
- F(1) = 1
- F(n) = F(n-1) + F(n-2) for n > 1

## License

MIT License
