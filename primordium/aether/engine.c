/* AETHER: C implementation of BrainFuck interpreter for PRIMORDIUM.
 *
 * This provides ~50x speedup over the Python implementation.
 */

#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define OP_RIGHT 62  /* > */
#define OP_LEFT 60   /* < */
#define OP_INC 43    /* + */
#define OP_DEC 45    /* - */
#define OP_COPY 46   /* . */
#define OP_LOOP_START 91 /* [ */
#define OP_LOOP_END 93   /* ] */

/* Precompute matching brackets */
static void precompute_brackets(const uint8_t* tape, int32_t* match, int32_t n) {
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

/* Run BF interpreter on combined tape
 * Returns number of steps executed
 */
int32_t run_bf_c(
    const uint8_t* scroll_a,
    const uint8_t* scroll_b,
    uint8_t* out_a,
    uint8_t* out_b,
    int32_t tape_length,
    int32_t max_steps
) {
    int32_t n = tape_length * 2;
    uint8_t* combined = (uint8_t*)malloc(n * sizeof(uint8_t));

    /* Combine tapes */
    memcpy(combined, scroll_a, tape_length);
    memcpy(combined + tape_length, scroll_b, tape_length);

    /* Precompute bracket matching */
    int32_t* match = (int32_t*)malloc(n * sizeof(int32_t));
    precompute_brackets(combined, match, n);

    /* Run interpreter */
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

    /* Split back */
    memcpy(out_a, combined, tape_length);
    memcpy(out_b, combined + tape_length, tape_length);

    free(combined);
    free(match);

    return steps;
}

/* Single-tape version for testing */
int32_t run_bf_single_c(
    const uint8_t* tape,
    uint8_t* out,
    int32_t tape_length,
    int32_t max_steps
) {
    uint8_t* combined = (uint8_t*)malloc(tape_length * sizeof(uint8_t));
    memcpy(combined, tape, tape_length);

    int32_t* match = (int32_t*)malloc(tape_length * sizeof(int32_t));
    precompute_brackets(combined, match, tape_length);

    int32_t ip = 0;
    int32_t dp = 0;
    int32_t steps = 0;
    int32_t n = tape_length;

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

    memcpy(out, combined, tape_length);

    free(combined);
    free(match);

    return steps;
}
