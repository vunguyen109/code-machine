#!/usr/bin/env python3
"""
Math Sequence Calculator CLI

Command-line interface for calculating factorials and Fibonacci sequences.
"""

import argparse
import sys

from calculator import factorial, fibonacci, fibonacci_sequence


VERSION = "1.0.0"


def create_parser() -> argparse.ArgumentParser:
    """
    Tạo và cấu hình argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="mathcalc",
        description="Math Sequence Calculator - Calculate factorials and Fibonacci sequences",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mathcalc.py factorial 5          Calculate 5! = 120
  python mathcalc.py fibonacci 10         Calculate F(10) = 55
  python mathcalc.py fibonacci 5 --seq    Show sequence [F(0)..F(5)]
"""
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Factorial command
    factorial_parser = subparsers.add_parser(
        "factorial",
        help="Calculate factorial n!"
    )
    factorial_parser.add_argument(
        "n",
        type=int,
        help="Non-negative integer to calculate factorial"
    )
    
    # Fibonacci command
    fib_parser = subparsers.add_parser(
        "fibonacci",
        help="Calculate Fibonacci number F(n)"
    )
    fib_parser.add_argument(
        "n",
        type=int,
        help="Non-negative integer index in Fibonacci sequence"
    )
    fib_parser.add_argument(
        "--seq",
        "--sequence",
        action="store_true",
        dest="sequence",
        help="Print the entire sequence from F(0) to F(n)"
    )
    fib_parser.add_argument(
        "--method",
        choices=["iterative", "recursive", "memoized"],
        default="iterative",
        help="Calculation method (default: iterative)"
    )
    
    return parser


def print_error(message: str) -> None:
    """
    In thông báo lỗi ra stderr.
    
    Args:
        message: Thông báo lỗi cần in
    """
    print(f"Error: {message}", file=sys.stderr)


def run_factorial(args: argparse.Namespace) -> int:
    """
    Execute factorial command.
    
    Args:
        args: Parsed arguments
        
    Returns:
        Exit code: 0 (success) hoặc 1 (error)
    """
    try:
        result = factorial(args.n)
        print(result)
        return 0
    except TypeError as e:
        print_error(str(e))
        return 1
    except ValueError as e:
        print_error(str(e))
        return 1


def run_fibonacci(args: argparse.Namespace) -> int:
    """
    Execute fibonacci command.
    
    Args:
        args: Parsed arguments
        
    Returns:
        Exit code: 0 (success) hoặc 1 (error)
    """
    try:
        if args.sequence:
            result = fibonacci_sequence(args.n)
            print(" ".join(map(str, result)))
        else:
            result = fibonacci(args.n, method=args.method)
            print(result)
        return 0
    except TypeError as e:
        print_error(str(e))
        return 1
    except ValueError as e:
        print_error(str(e))
        return 1


def main() -> int:
    """
    Entry point cho CLI.
    
    Returns:
        Exit code: 0 (success) hoặc 1 (error)
    """
    parser = create_parser()
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    if args.command == "factorial":
        return run_factorial(args)
    elif args.command == "fibonacci":
        return run_fibonacci(args)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
