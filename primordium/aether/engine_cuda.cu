/* AETHER: CUDA implementation of BrainFuck interpreter for PRIMORDIUM.
 *
 * This provides massive parallelism by running multiple BF interactions
 * simultaneously on GPU. Target: 100M+ interactions/second.
 */

#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <cuda_runtime.h>

#define OP_RIGHT 62  /* > */
#define OP_LEFT 60   /* < */
#define OP_INC 43    /* + */
#define OP_DEC 45    /* - */
#define OP_COPY 46   /* . */
#define OP_LOOP_START 91 /* [ */
#define OP_LOOP_END 93   /* ] */

// Error checking macro
#define CUDA_CHECK(call) \
    do { \
        cudaError_t err = call; \
        if (err != cudaSuccess) { \
            return -1; \
        } \
    } while(0)

/* Precompute matching brackets on host */
__host__ void precompute_brackets_host(const uint8_t* tape, int32_t* match, int32_t n) {
    int32_t* stack = (int32_t*)malloc(n * sizeof(int32_t));
    int32_t stack_top = 0;

    for (int32_t i = 0; i < n; i++) {
        match[i] = -1;
        if (tape[i] == OP_LOOP_START) {
            stack[stack_top++] = i;
        } else if (tape[i] == OP_LOOP_END) {
            if (stack_top > 0) {
                int32_t start = stack[--stack_top];
                match[start] = i;
                match[i] = start;
            }
        }
    }
    free(stack);
}

/* Single BF interaction kernel */
__device__ int32_t run_bf_kernel(
    const uint8_t* scroll_a,
    const uint8_t* scroll_b,
    uint8_t* out_a,
    uint8_t* out_b,
    int32_t tape_length,
    int32_t max_steps
) {
    int32_t n = tape_length * 2;
    uint8_t combined[256];  // Max tape length

    // Combine tapes
    for (int32_t i = 0; i < tape_length; i++) {
        combined[i] = scroll_a[i];
        combined[i + tape_length] = scroll_b[i];
    }

    // Precompute bracket matching inline
    int32_t match[256];
    for (int32_t i = 0; i < n; i++) {
        match[i] = -1;
    }

    // Simple stack-based bracket matching
    int32_t stack[128];
    int32_t stack_top = 0;

    for (int32_t i = 0; i < n; i++) {
        if (combined[i] == OP_LOOP_START) {
            stack[stack_top++] = i;
        } else if (combined[i] == OP_LOOP_END) {
            if (stack_top > 0) {
                int32_t start = stack[--stack_top];
                match[start] = i;
                match[i] = start;
            }
        }
    }

    // Run interpreter
    int32_t ip = 0;
    int32_t dp = 0;
    int32_t steps = 0;

    while (ip < n && steps < max_steps) {
        uint8_t op = combined[ip];

        switch (op) {
            case OP_RIGHT:
                dp = (dp + 1) % n;
                ip++;
                steps++;
                break;

            case OP_LEFT:
                dp = (dp - 1 + n) % n;
                ip++;
                steps++;
                break;

            case OP_INC:
                combined[dp] = (combined[dp] + 1) % 256;
                ip++;
                steps++;
                break;

            case OP_DEC:
                combined[dp] = (combined[dp] - 1 + 256) % 256;
                ip++;
                steps++;
                break;

            case OP_COPY: {
                int32_t target = (dp + 1) % n;
                combined[target] = combined[dp];
                ip++;
                steps++;
                break;
            }

            case OP_LOOP_START:
                if (combined[dp] == 0) {
                    int32_t matched = match[ip];
                    if (matched != -1) {
                        ip = matched + 1;
                    } else {
                        ip++;
                    }
                } else {
                    ip++;
                }
                steps++;
                break;

            case OP_LOOP_END:
                if (combined[dp] != 0) {
                    int32_t matched = match[ip];
                    if (matched != -1) {
                        ip = matched;
                    } else {
                        ip++;
                    }
                } else {
                    ip++;
                }
                steps++;
                break;

            default:
                ip++;
                steps++;
                break;
        }
    }

    // Split back
    for (int32_t i = 0; i < tape_length; i++) {
        out_a[i] = combined[i];
        out_b[i] = combined[i + tape_length];
    }

    return steps;
}

/* CUDA kernel for batch BF interactions */
__global__ void run_bf_batch_kernel(
    const uint8_t* scrolls_a,  // [batch_size * tape_length]
    const uint8_t* scrolls_b,  // [batch_size * tape_length]
    uint8_t* out_a,            // [batch_size * tape_length]
    uint8_t* out_b,           // [batch_size * tape_length]
    int32_t* steps_out,       // [batch_size]
    int32_t tape_length,
    int32_t max_steps,
    int32_t batch_size
) {
    int32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= batch_size) return;

    const uint8_t* scroll_a = scrolls_a + idx * tape_length;
    const uint8_t* scroll_b = scrolls_b + idx * tape_length;
    uint8_t* out_a_ptr = out_a + idx * tape_length;
    uint8_t* out_b_ptr = out_b + idx * tape_length;

    steps_out[idx] = run_bf_kernel(
        scroll_a, scroll_b,
        out_a_ptr, out_b_ptr,
        tape_length, max_steps
    );
}

/* Host wrapper for batch processing */
extern "C" int32_t run_bf_cuda_batch(
    const uint8_t* h_scrolls_a,
    const uint8_t* h_scrolls_b,
    uint8_t* h_out_a,
    uint8_t* h_out_b,
    int32_t* h_steps_out,
    int32_t tape_length,
    int32_t max_steps,
    int32_t batch_size
) {
    size_t scroll_size = tape_length * sizeof(uint8_t);
    size_t batch_scroll_size = batch_size * scroll_size;
    size_t steps_size = batch_size * sizeof(int32_t);

    // Allocate device memory
    uint8_t *d_scrolls_a, *d_scrolls_b, *d_out_a, *d_out_b;
    int32_t *d_steps_out;

    CUDA_CHECK(cudaMalloc(&d_scrolls_a, batch_scroll_size));
    CUDA_CHECK(cudaMalloc(&d_scrolls_b, batch_scroll_size));
    CUDA_CHECK(cudaMalloc(&d_out_a, batch_scroll_size));
    CUDA_CHECK(cudaMalloc(&d_out_b, batch_scroll_size));
    CUDA_CHECK(cudaMalloc(&d_steps_out, steps_size));

    // Copy input to device
    CUDA_CHECK(cudaMemcpy(d_scrolls_a, h_scrolls_a, batch_scroll_size, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_scrolls_b, h_scrolls_b, batch_scroll_size, cudaMemcpyHostToDevice));

    // Launch kernel
    int32_t threads = 256;
    int32_t blocks = (batch_size + threads - 1) / threads;

    run_bf_batch_kernel<<<blocks, threads>>>(
        d_scrolls_a, d_scrolls_b,
        d_out_a, d_out_b,
        d_steps_out,
        tape_length, max_steps, batch_size
    );

    cudaDeviceSynchronize();

    // Copy results back
    CUDA_CHECK(cudaMemcpy(h_out_a, d_out_a, batch_scroll_size, cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaMemcpy(h_out_b, d_out_b, batch_scroll_size, cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaMemcpy(h_steps_out, d_steps_out, steps_size, cudaMemcpyDeviceToHost));

    // Free device memory
    cudaFree(d_scrolls_a);
    cudaFree(d_scrolls_b);
    cudaFree(d_out_a);
    cudaFree(d_out_b);
    cudaFree(d_steps_out);

    return 0;
}

/* Single interaction wrapper (for compatibility) */
extern "C" int32_t run_bf_cuda(
    const uint8_t* scroll_a,
    const uint8_t* scroll_b,
    uint8_t* out_a,
    uint8_t* out_b,
    int32_t tape_length,
    int32_t max_steps
) {
    return run_bf_kernel(scroll_a, scroll_b, out_a, out_b, tape_length, max_steps);
}
