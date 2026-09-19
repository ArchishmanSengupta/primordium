"""Compiler for C/CUDA backends."""

import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def check_compiler():
    """Check if GCC is available."""
    try:
        result = subprocess.run(
            ['gcc', '--version'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def compile_c_engine(output_dir=None):
    """Compile the C engine."""
    if output_dir is None:
        output_dir = Path(__file__).parent

    c_file = Path(output_dir) / "engine.c"
    lib_file = Path(output_dir) / "libengine.so"

    if not c_file.exists():
        raise FileNotFoundError(f"C source not found: {c_file}")

    # Compile with optimizations
    cmd = [
        'gcc', '-O3', '-march=native', '-shared', '-fPIC',
        '-o', str(lib_file),
        str(c_file)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"Compilation failed: {result.stderr}")
        raise RuntimeError(f"Failed to compile C engine: {result.stderr}")

    logger.info(f"Compiled C engine to {lib_file}")
    return lib_file


def check_cuda():
    """Check if CUDA is available."""
    try:
        result = subprocess.run(
            ['nvcc', '--version'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def compile_cuda_engine(output_dir=None):
    """Compile the CUDA engine."""
    if output_dir is None:
        output_dir = Path(__file__).parent

    cu_file = Path(output_dir) / "engine_cuda.cu"
    lib_file = Path(output_dir) / "libengine_cuda.so"

    if not cu_file.exists():
        logger.warning(f"CUDA source not found: {cu_file}")
        return None

    if not check_cuda():
        logger.warning("CUDA compiler (nvcc) not available")
        return None

    # Compile CUDA
    cmd = [
        'nvcc', '-O3', '--shared', '-fPIC',
        '-o', str(lib_file),
        str(cu_file),
        '-Xcompiler', '-fPIC'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"CUDA compilation failed: {result.stderr}")
        return None

    logger.info(f"Compiled CUDA engine to {lib_file}")
    return lib_file


def build_all():
    """Build all available backends."""
    output_dir = Path(__file__).parent

    results = {}

    # Check for GCC
    if check_compiler():
        try:
            results['c'] = compile_c_engine(output_dir)
        except Exception as e:
            logger.error(f"C engine build failed: {e}")
            results['c'] = None
    else:
        logger.warning("GCC not available, skipping C backend")
        results['c'] = None

    # Check for CUDA
    if check_cuda():
        try:
            results['cuda'] = compile_cuda_engine(output_dir)
        except Exception as e:
            logger.error(f"CUDA engine build failed: {e}")
            results['cuda'] = None
    else:
        logger.warning("CUDA not available, skipping CUDA backend")
        results['cuda'] = None

    return results


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    build_all()
