"""C backend compiler and wrapper for AETHER."""

import os
import ctypes
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def compile_engine():
    """Compile the C engine and return the library."""
    # Get the directory of this file
    aether_dir = Path(__file__).parent

    # Try to find or compile the library
    lib_path = aether_dir / "libengine.so"

    if not lib_path.exists():
        # Compile the C code
        c_path = aether_dir / "engine.c"

        if not c_path.exists():
            raise FileNotFoundError(f"C source not found: {c_path}")

        # Compile
        result = os.system(
            f"gcc -O3 -shared -fPIC -o {lib_path} {c_path} 2>&1"
        )

        if result != 0:
            raise RuntimeError("Failed to compile C engine")

    # Load the library
    lib = ctypes.CDLL(str(lib_path))

    # Define argument and return types
    lib.run_bf_c.argtypes = [
        np.ctypeslib.ndpointer(dtype=np.uint8),  # scroll_a
        np.ctypeslib.ndpointer(dtype=np.uint8),  # scroll_b
        np.ctypeslib.ndpointer(dtype=np.uint8),  # out_a
        np.ctypeslib.ndpointer(dtype=np.uint8),  # out_b
        ctypes.c_int32,  # tape_length
        ctypes.c_int32,  # max_steps
    ]
    lib.run_bf_c.restype = ctypes.c_int32

    lib.run_bf_single_c.argtypes = [
        np.ctypeslib.ndpointer(dtype=np.uint8),  # tape
        np.ctypeslib.ndpointer(dtype=np.uint8),  # out
        ctypes.c_int32,  # tape_length
        ctypes.c_int32,  # max_steps
    ]
    lib.run_bf_single_c.restype = ctypes.c_int32

    return lib


def get_engine():
    """Get or create the C engine."""
    global _engine

    if '_engine' not in globals():
        try:
            _engine = compile_engine()
        except Exception as e:
            logger.warning(f"Failed to compile C engine: {e}")
            _engine = None

    return _engine


def run_bf_c(scroll_a, scroll_b, max_steps=350, tape_length=None):
    """Run the C implementation of the BF interpreter."""
    engine = get_engine()

    if engine is None:
        # Fall back to Python
        from primordium.aether.interpreter import run_bf
        return run_bf(scroll_a, scroll_b, max_steps=max_steps)

    if tape_length is None:
        tape_length = len(scroll_a)

    # Ensure contiguous arrays
    scroll_a = np.ascontiguousarray(scroll_a, dtype=np.uint8)
    scroll_b = np.ascontiguousarray(scroll_b, dtype=np.uint8)

    out_a = np.empty(tape_length, dtype=np.uint8)
    out_b = np.empty(tape_length, dtype=np.uint8)

    steps = engine.run_bf_c(
        scroll_a,
        scroll_b,
        out_a,
        out_b,
        tape_length,
        max_steps,
    )

    return out_a, out_b, steps


def run_bf_single_c(tape, max_steps=350):
    """Run single-tape version using C backend."""
    engine = get_engine()

    if engine is None:
        from primordium.aether.interpreter import Interpreter
        interp = Interpreter(tape_length=len(tape), max_steps=max_steps)
        return interp.run_single(tape, max_steps)

    tape = np.ascontiguousarray(tape, dtype=np.uint8)
    out = np.empty(len(tape), dtype=np.uint8)

    steps = engine.run_bf_single_c(tape, out, len(tape), max_steps)

    return out, steps
