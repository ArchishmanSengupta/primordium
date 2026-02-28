"""AETHER: The core BrainFuck interpreter for PRIMORDIUM.

This module implements the modified BrainFuck variant where code and data
share a unified tape, enabling self-reference and self-replication.

The 7 valid instructions:
  62  >    Move data pointer right (wraps at tape_length)
  60  <    Move data pointer left (wraps at 0)
  43  +    Increment byte (wraps at 255)
  45  -    Decrement byte (wraps at 0)
  91  [    If byte at data pointer is 0, jump forward to matching ]
  93  ]    If byte at data pointer is nonzero, jump back to matching [
  46  .    COPY: copy byte at data pointer to next cell (data pointer + 1)

All other byte values (0-255 excluding above) are no-ops.
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


# Instruction constants
OP_RIGHT = ord('>')  # 62
OP_LEFT = ord('<')   # 60
OP_INC = ord('+')    # 43
OP_DEC = ord('-')    # 45
OP_LOOP_START = ord('[')  # 91
OP_LOOP_END = ord(']')   # 93
OP_COPY = ord('.')   # 46

VALID_OPS = {OP_RIGHT, OP_LEFT, OP_INC, OP_DEC, OP_LOOP_START, OP_LOOP_END, OP_COPY}


def precompute_brackets(tape: np.ndarray) -> np.ndarray:
    """Precompute matching bracket positions for fast loop handling.

    Args:
        tape: The instruction tape

    Returns:
        Array where match[i] = matching bracket position, or -1 if not a bracket
    """
    n = len(tape)
    match = np.full(n, -1, dtype=np.int32)
    stack = []

    for i in range(n):
        if tape[i] == OP_LOOP_START:
            stack.append(i)
        elif tape[i] == OP_LOOP_END:
            if stack:
                start = stack.pop()
                match[start] = i
                match[i] = start

    return match


def run_bf(
    scroll_a: np.ndarray,
    scroll_b: np.ndarray,
    max_steps: int = 350,
    tape_length: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray, int]:
    """Run the BrainFuck interpreter on two scrolls.

    This implements the APEIRON interaction rule:
    1. Concatenate scroll_a + scroll_b into combined tape
    2. Run interpreter with ip=0, dp=0
    3. Split combined tape at midpoint back into two scrolls
    4. Return (new_a, new_b, steps_executed)

    Args:
        scroll_a: First scroll (tape) as numpy array
        scroll_b: Second scroll (tape) as numpy array
        max_steps: Maximum execution steps before halting
        tape_length: Original tape length (used for splitting)

    Returns:
        Tuple of (modified_scroll_a, modified_scroll_b, steps_executed)
    """
    if tape_length is None:
        tape_length = len(scroll_a)

    # Create combined tape: scroll_a + scroll_b
    combined = np.concatenate([scroll_a, scroll_b])
    n = len(combined)

    # Precompute bracket matching for loop handling
    bracket_match = precompute_brackets(combined)

    # Initialize pointers
    ip = 0  # instruction pointer
    dp = 0  # data pointer
    steps = 0

    # Run the interpreter
    while ip < n and steps < max_steps:
        op = combined[ip]

        if op == OP_RIGHT:
            # Move data pointer right, wrap at tape length
            dp = (dp + 1) % n
            ip += 1
            steps += 1

        elif op == OP_LEFT:
            # Move data pointer left, wrap at 0
            dp = (dp - 1) % n
            ip += 1
            steps += 1

        elif op == OP_INC:
            # Increment byte at data pointer, wrap at 255
            combined[dp] = np.uint8((int(combined[dp]) + 1) % 256)
            ip += 1
            steps += 1

        elif op == OP_DEC:
            # Decrement byte at data pointer, wrap at 0
            combined[dp] = np.uint8((int(combined[dp]) - 1) % 256)
            ip += 1
            steps += 1

        elif op == OP_COPY:
            # COPY: copy byte at dp to dp+1 (wrapping)
            target = (dp + 1) % n
            combined[target] = combined[dp]
            ip += 1
            steps += 1

        elif op == OP_LOOP_START:
            # If byte at dp is 0, jump to matching ]
            if combined[dp] == 0:
                matched = bracket_match[ip]
                if matched != -1:
                    ip = matched + 1
                else:
                    # Unmatched [, skip to next instruction
                    ip += 1
            else:
                ip += 1
            steps += 1

        elif op == OP_LOOP_END:
            # If byte at dp is nonzero, jump back to matching [
            if combined[dp] != 0:
                matched = bracket_match[ip]
                if matched != -1:
                    ip = matched
                else:
                    # Unmatched ], continue forward
                    ip += 1
            else:
                ip += 1
            steps += 1

        else:
            # No-op: any other byte value is ignored
            ip += 1
            steps += 1

    # Split combined tape back into two scrolls
    new_a = combined[:tape_length].copy()
    new_b = combined[tape_length:].copy()

    return new_a, new_b, steps


class Interpreter:
    """BrainFuck interpreter class with state tracking.

    This class provides a more convenient interface for running
    the interpreter with additional state and debugging capabilities.
    """

    def __init__(self, tape_length: int = 48, max_steps: int = 350):
        """Initialize the interpreter.

        Args:
            tape_length: Length of each scroll tape
            max_steps: Maximum steps per interaction
        """
        self.tape_length = tape_length
        self.max_steps = max_steps

    def run(
        self,
        scroll_a: np.ndarray,
        scroll_b: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        """Run the interpreter on two scrolls.

        Args:
            scroll_a: First scroll
            scroll_b: Second scroll

        Returns:
            Tuple of (new_a, new_b, steps)
        """
        return run_bf(
            scroll_a,
            scroll_b,
            max_steps=self.max_steps,
            tape_length=self.tape_length,
        )

    def run_single(
        self,
        tape: np.ndarray,
        max_steps: Optional[int] = None,
    ) -> Tuple[np.ndarray, int]:
        """Run interpreter on a single tape (for testing).

        The single-tape version treats the entire tape as both code and data,
        starting with ip=0 and dp=0.

        Args:
            tape: The tape to execute
            max_steps: Override for max steps

        Returns:
            Tuple of (modified_tape, steps_executed)
        """
        if max_steps is None:
            max_steps = self.max_steps

        combined = tape.copy()
        n = len(combined)
        bracket_match = precompute_brackets(combined)

        ip = 0
        dp = 0
        steps = 0

        while ip < n and steps < max_steps:
            op = combined[ip]

            if op == OP_RIGHT:
                dp = (dp + 1) % n
                ip += 1
                steps += 1
            elif op == OP_LEFT:
                dp = (dp - 1) % n
                ip += 1
                steps += 1
            elif op == OP_INC:
                combined[dp] = np.uint8((int(combined[dp]) + 1) % 256)
                ip += 1
                steps += 1
            elif op == OP_DEC:
                combined[dp] = np.uint8((int(combined[dp]) - 1) % 256)
                ip += 1
                steps += 1
            elif op == OP_COPY:
                target = (dp + 1) % n
                combined[target] = combined[dp]
                ip += 1
                steps += 1
            elif op == OP_LOOP_START:
                if combined[dp] == 0:
                    matched = bracket_match[ip]
                    if matched != -1:
                        ip = matched + 1
                    else:
                        ip += 1
                else:
                    ip += 1
                steps += 1
            elif op == OP_LOOP_END:
                if combined[dp] != 0:
                    matched = bracket_match[ip]
                    if matched != -1:
                        ip = matched
                    else:
                        ip += 1
                else:
                    ip += 1
                steps += 1
            else:
                ip += 1
                steps += 1

        return combined, steps


def count_instructions(tape: np.ndarray) -> dict:
    """Count valid instructions in a tape.

    Args:
        tape: The tape to analyze

    Returns:
        Dictionary with counts for each instruction
    """
    counts = {
        'right': 0,
        'left': 0,
        'inc': 0,
        'dec': 0,
        'loop_start': 0,
        'loop_end': 0,
        'copy': 0,
        'noop': 0,
        'total': len(tape),
    }

    for byte in tape:
        if byte == OP_RIGHT:
            counts['right'] += 1
        elif byte == OP_LEFT:
            counts['left'] += 1
        elif byte == OP_INC:
            counts['inc'] += 1
        elif byte == OP_DEC:
            counts['dec'] += 1
        elif byte == OP_LOOP_START:
            counts['loop_start'] += 1
        elif byte == OP_LOOP_END:
            counts['loop_end'] += 1
        elif byte == OP_COPY:
            counts['copy'] += 1
        else:
            counts['noop'] += 1

    return counts


def instruction_density(tape: np.ndarray) -> float:
    """Calculate the fraction of valid instructions in a tape.

    Args:
        tape: The tape to analyze

    Returns:
        Fraction of tape that are valid instructions (0.0 to 1.0)
    """
    if len(tape) == 0:
        return 0.0

    valid_count = sum(1 for byte in tape if byte in VALID_OPS)
    return valid_count / len(tape)
