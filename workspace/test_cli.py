"""
Integration tests for CLI.
"""

import pytest
import subprocess
import sys
import os

# Get the directory where this test file is located
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
MATHCALC_PATH = os.path.join(TEST_DIR, "mathcalc.py")


def run_cli(args: list) -> tuple:
    """
    Helper: chạy CLI và trả về (stdout, stderr, exit_code).
    
    Args:
        args: List of command-line arguments
        
    Returns:
        Tuple of (stdout, stderr, exit_code)
    """
    result = subprocess.run(
        [sys.executable, MATHCALC_PATH] + args,
        capture_output=True,
        text=True,
        cwd=TEST_DIR
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


class TestCLI:
    """Integration tests cho CLI."""
    
    def test_valid_factorial_command(self):
        """TC-CLI01: python mathcalc.py factorial 5 → 120, exit 0"""
        stdout, stderr, code = run_cli(["factorial", "5"])
        assert stdout == "120"
        assert code == 0
    
    def test_valid_fibonacci_command(self):
        """TC-CLI02: python mathcalc.py fibonacci 10 → 55, exit 0"""
        stdout, stderr, code = run_cli(["fibonacci", "10"])
        assert stdout == "55"
        assert code == 0
    
    def test_invalid_negative_input_factorial(self):
        """TC-CLI03: Input âm cho factorial → error, exit 1"""
        stdout, stderr, code = run_cli(["factorial", "-5"])
        assert code == 1
        assert stderr != ""  # Có error message
    
    def test_invalid_negative_input_fibonacci(self):
        """Input âm cho fibonacci → error, exit 1"""
        stdout, stderr, code = run_cli(["fibonacci", "-1"])
        assert code == 1
        assert stderr != ""
    
    def test_invalid_type_input(self):
        """TC-CLI04: Input không phải số → error, exit 1"""
        stdout, stderr, code = run_cli(["fibonacci", "abc"])
        assert code == 1
        assert stderr != "" or stdout != ""  # Có error message
    
    def test_help_flag(self):
        """TC-CLI05: --help → usage info, exit 0"""
        stdout, stderr, code = run_cli(["--help"])
        output = stdout.lower() + stderr.lower()
        assert "usage" in output
        assert code == 0
    
    def test_fibonacci_sequence_flag(self):
        """TC-CLI06: fibonacci 5 --sequence → 0 1 1 2 3 5"""
        stdout, stderr, code = run_cli(["fibonacci", "5", "--sequence"])
        assert stdout == "0 1 1 2 3 5"
        assert code == 0
    
    def test_fibonacci_sequence_short_flag(self):
        """fibonacci 5 --seq → 0 1 1 2 3 5"""
        stdout, stderr, code = run_cli(["fibonacci", "5", "--seq"])
        assert stdout == "0 1 1 2 3 5"
        assert code == 0
    
    def test_factorial_zero(self):
        """factorial 0 → 1"""
        stdout, stderr, code = run_cli(["factorial", "0"])
        assert stdout == "1"
        assert code == 0
    
    def test_factorial_one(self):
        """factorial 1 → 1"""
        stdout, stderr, code = run_cli(["factorial", "1"])
        assert stdout == "1"
        assert code == 0
    
    def test_fibonacci_zero(self):
        """fibonacci 0 → 0"""
        stdout, stderr, code = run_cli(["fibonacci", "0"])
        assert stdout == "0"
        assert code == 0
    
    def test_fibonacci_one(self):
        """fibonacci 1 → 1"""
        stdout, stderr, code = run_cli(["fibonacci", "1"])
        assert stdout == "1"
        assert code == 0
    
    def test_version_flag(self):
        """--version → version info"""
        stdout, stderr, code = run_cli(["--version"])
        output = stdout + stderr
        assert "mathcalc" in output.lower()
        assert code == 0
    
    def test_fibonacci_with_method_iterative(self):
        """fibonacci 10 --method iterative → 55"""
        stdout, stderr, code = run_cli(["fibonacci", "10", "--method", "iterative"])
        assert stdout == "55"
        assert code == 0
    
    def test_fibonacci_with_method_recursive(self):
        """fibonacci 10 --method recursive → 55"""
        stdout, stderr, code = run_cli(["fibonacci", "10", "--method", "recursive"])
        assert stdout == "55"
        assert code == 0
    
    def test_fibonacci_with_method_memoized(self):
        """fibonacci 10 --method memoized → 55"""
        stdout, stderr, code = run_cli(["fibonacci", "10", "--method", "memoized"])
        assert stdout == "55"
        assert code == 0
    
    def test_no_command_shows_help(self):
        """No command → shows help"""
        stdout, stderr, code = run_cli([])
        # Should show help when no command is given
        assert code == 0
    
    def test_large_factorial(self):
        """factorial 20 → large number"""
        stdout, stderr, code = run_cli(["factorial", "20"])
        assert stdout == "2432902008176640000"
        assert code == 0
    
    def test_large_fibonacci(self):
        """fibonacci 30 → 832040"""
        stdout, stderr, code = run_cli(["fibonacci", "30"])
        assert stdout == "832040"
        assert code == 0
    
    def test_sequence_zero(self):
        """fibonacci 0 --sequence → 0"""
        stdout, stderr, code = run_cli(["fibonacci", "0", "--sequence"])
        assert stdout == "0"
        assert code == 0
    
    def test_sequence_one(self):
        """fibonacci 1 --sequence → 0 1"""
        stdout, stderr, code = run_cli(["fibonacci", "1", "--sequence"])
        assert stdout == "0 1"
        assert code == 0


class TestCLIErrorHandling:
    """Test error handling trong CLI."""
    
    def test_float_input_factorial(self):
        """Float input cho factorial → error"""
        stdout, stderr, code = run_cli(["factorial", "3.5"])
        assert code == 1
    
    def test_float_input_fibonacci(self):
        """Float input cho fibonacci → error"""
        stdout, stderr, code = run_cli(["fibonacci", "3.5"])
        assert code == 1
    
    def test_invalid_method(self):
        """Invalid method → error"""
        stdout, stderr, code = run_cli(["fibonacci", "10", "--method", "invalid"])
        assert code == 2  # argparse returns 2 for invalid choice
