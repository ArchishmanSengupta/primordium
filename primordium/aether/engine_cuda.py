"""CUDA backend for AETHER.

Provides GPU-accelerated BrainFuck interpreter for massive parallelism.
"""

import os
import ctypes
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def check_cuda_available():
    """Check if CUDA is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def compile_cuda_engine():
    """Compile the CUDA engine and return the library."""
    aether_dir = Path(__file__).parent
    lib_path = aether_dir / "libengine_cuda.so"

    if not lib_path.exists():
        # Compile the CUDA code
        cu_path = aether_dir / "engine_cuda.cu"

        if not cu_path.exists():
            raise FileNotFoundError(f"CUDA source not found: {cu_path}")

        # Check for nvcc
        try:
            result = os.system("nvcc --version > /dev/null 2>&1")
            if result != 0:
                raise RuntimeError("nvcc not found")
        except Exception:
            raise RuntimeError("CUDA compiler (nvcc) not available")

        # Compile
        cmd = f"nvcc -O3 --shared -fPIC -o {lib_path} {cu_path} -Xcompiler -fPIC 2>&1"
        result = os.system(cmd)

        if result != 0:
            raise RuntimeError("Failed to compile CUDA engine")

    # Load the library
    lib = ctypes.CDLL(str(lib_path))

    # Define argument and return types for single interaction
    lib.run_bf_cuda.argtypes = [
        np.ctypeslib.ndpointer(dtype=np.uint8),  # scroll_a
        np.ctypeslib.ndpointer(dtype=np.uint8),  # scroll_b
        np.ctypeslib.ndpointer(dtype=np.uint8),  # out_a
        np.ctypeslib.ndpointer(dtype=np.uint8),  # out_b
        ctypes.c_int32,  # tape_length
        ctypes.c_int32,  # max_steps
    ]
    lib.run_bf_cuda.restype = ctypes.c_int32

    # Batch version
    lib.run_bf_cuda_batch.argtypes = [
        np.ctypeslib.ndpointer(dtype=np.uint8),  # scrolls_a
        np.ctypeslib.ndpointer(dtype=np.uint8),  # scrolls_b
        np.ctypeslib.ndpointer(dtype=np.uint8),  # out_a
        np.ctypeslib.ndpointer(dtype=np.uint8),  # out_b
        np.ctypeslib.ndpointer(dtype=np.int32),  # steps_out
        ctypes.c_int32,  # tape_length
        ctypes.c_int32,  # max_steps
        ctypes.c_int32,  # batch_size
    ]
    lib.run_bf_cuda_batch.restype = ctypes.c_int32

    return lib


def get_cuda_engine():
    """Get or create the CUDA engine."""
    global _cuda_engine

    if '_cuda_engine' not in globals():
        try:
            _cuda_engine = compile_cuda_engine()
        except Exception as e:
            logger.warning(f"Failed to compile CUDA engine: {e}")
            _cuda_engine = None

    return _cuda_engine


def run_bf_cuda(scroll_a, scroll_b, max_steps=350, tape_length=None):
    """Run single interaction using CUDA backend."""
    engine = get_cuda_engine()

    if engine is None:
        # Fall back to C backend
        from primordium.aether.engine import run_bf_c
        return run_bf_c(scroll_a, scroll_b, max_steps=max_steps, tape_length=tape_length)

    if tape_length is None:
        tape_length = len(scroll_a)

    # Ensure contiguous arrays
    scroll_a = np.ascontiguousarray(scroll_a, dtype=np.uint8)
    scroll_b = np.ascontiguousarray(scroll_b, dtype=np.uint8)

    out_a = np.empty(tape_length, dtype=np.uint8)
    out_b = np.empty(tape_length, dtype=np.uint8)

    steps = engine.run_bf_cuda(
        scroll_a,
        scroll_b,
        out_a,
        out_b,
        tape_length,
        max_steps,
    )

    return out_a, out_b, steps


def run_bf_cuda_batch(scrolls_a, scrolls_b, max_steps=350, tape_length=None):
    """Run batch of interactions using CUDA backend.

    Args:
        scrolls_a: Array of shape (batch_size, tape_length)
        scrolls_b: Array of shape (batch_size, tape_length)
        max_steps: Maximum steps per interaction
        tape_length: Length of each tape

    Returns:
        Tuple of (out_a, out_b, steps) arrays
    """
    engine = get_cuda_engine()

    if engine is None:
        # Fall back to C backend
        from primordium.aether.engine import run_bf_c
        results = []
        for i in range(len(scrolls_a)):
            result = run_bf_c(
                scrolls_a[i], scrolls_b[i],
                max_steps=max_steps, tape_length=tape_length
            )
            results.append(result)
        out_a = np.array([r[0] for r in results])
        out_b = np.array([r[1] for r in results])
        steps = np.array([r[2] for r in results])
        return out_a, out_b, steps

    batch_size = len(scrolls_a)
    if tape_length is None:
        tape_length = scrolls_a.shape[1]

    # Ensure contiguous arrays
    scrolls_a = np.ascontiguousarray(scrolls_a, dtype=np.uint8)
    scrolls_b = np.ascontiguousarray(scrolls_b, dtype=np.uint8)

    out_a = np.empty((batch_size, tape_length), dtype=np.uint8)
    out_b = np.empty((batch_size, tape_length), dtype=np.uint8)
    steps_out = np.empty(batch_size, dtype=np.int32)

    engine.run_bf_cuda_batch(
        scrolls_a,
        scrolls_b,
        out_a,
        out_b,
        steps_out,
        tape_length,
        max_steps,
        batch_size,
    )

    return out_a, out_b, steps_out
