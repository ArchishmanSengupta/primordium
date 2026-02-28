"""Task evaluation for PRIMORDIUM.

This script runs the soup and evaluates fitness on a copy task.
"""

import numpy as np
from primordium.chaos import Soup
from primordium.aether import engine
import os

def evaluate_copy_fitness(tape, max_steps=350, tape_length=48):
    """Evaluate how well a program copies data.

    Setup: tape has data at position 0, we want it copied to position 1
    Fitness = how close the byte at position 1 is to position 0
    """
    # Create a test tape with known data
    test_data = np.array([42] + [0] * (tape_length - 1), dtype=np.uint8)

    # Combine with the program
    combined = np.concatenate([tape, test_data])

    # Run the program
    try:
        result_a, result_b, steps = engine.run_bf_c(
            tape, test_data,
            max_steps=max_steps,
            tape_length=tape_length
        )

        # Check: did position 1 (or nearby) get the value from position 0?
        # Look for the value 42 appearing near position 1
        target_value = 42

        # Check positions 1-5 for the copied value
        copied = False
        for offset in range(1, 6):
            if offset < len(result_b) and result_b[offset] == target_value:
                copied = True
                break

        # Also check if position 0 changed (moved data)
        position_preserved = (result_b[0] == 42)

        if copied:
            return 1.0
        elif position_preserved:
            return 0.5
        else:
            return 0.0

    except Exception as e:
        return 0.0

def evaluate_all_scrolls(soup):
    """Evaluate fitness for all scrolls."""
    fitnesses = []

    for scroll in soup.scrolls:
        fitness = evaluate_copy_fitness(scroll.tape)
        scroll.fitness = fitness
        fitnesses.append(fitness)

    return fitnesses

def main():
    # Initialize soup
    soup = Soup(size=256, tape_length=48, seed=42)

    print("Initial evaluation...")
    initial_fitness = evaluate_all_scrolls(soup)
    print(f"Initial max fitness: {max(initial_fitness):.2f}")
    print(f"Initial avg fitness: {np.mean(initial_fitness):.4f}")

    # Run interactions
    interactions = 10_000_000  # 10M (about 2 min)

    print(f"\nRunning {interactions} interactions...")

    for i in range(interactions):
        soup.interact(max_steps=350)

        if (i + 1) % 100000 == 0:
            fitnesses = evaluate_all_scrolls(soup)
            max_fit = max(fitnesses)
            avg_fit = np.mean(fitnesses)
            density = soup.instruction_density()

            print(f"Interaction {i+1:>10} | Max fitness: {max_fit:.2f} | Avg: {avg_fit:.4f} | Density: {density:.4f}")

            if max_fit >= 0.9:
                print("SUCCESS! Found high-fitness program!")
                break

    # Final evaluation
    print("\nFinal evaluation:")
    fitnesses = evaluate_all_scrolls(soup)
    print(f"Final max fitness: {max(fitnesses):.2f}")
    print(f"Final avg fitness: {np.mean(fitnesses):.4f}")
    print(f"Density: {soup.instruction_density():.4f}")

    # Save checkpoint
    soup.save('./chronicle/task_copy/final_soup.npy')
    print("\nSaved to ./chronicle/task_copy/final_soup.npy")

if __name__ == '__main__':
    main()
