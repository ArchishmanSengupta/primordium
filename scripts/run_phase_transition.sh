#!/bin/bash
# Phase Transition Experiment
# ==========================
# Run a longer experiment to detect phase transitions.
# Based on Blaise Agüera y Arcas BFF experiment.

echo "Running phase transition experiment..."
echo "This will take longer but should show emergent behavior."
echo ""

# Run with more interactions to see phase transition
primordium run configs/phase_transition.yaml

echo ""
echo "Experiment complete!"
echo ""
echo "Key things to watch for:"
echo "  - Compression ratio should drop over time"
echo "  - Instruction density should increase"
echo "  - Replicators should appear"
echo "  - If '*** LIFE EMERGED ***' appears, criteria are met"
