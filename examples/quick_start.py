#!/usr/bin/env python3
"""
UniPCB Quick Start Example

This script demonstrates basic usage of the UniPCB benchmark.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main():
    """Quick start demonstration."""
    
    print("=" * 60)
    print("UniPCB Quick Start Guide")
    print("=" * 60)
    
    # 1. Import modules
    print("\n1. Importing modules...")
    try:
        from unipcb.data import UniPCBDataset
        from unipcb.models import PCBGPT
        from unipcb.eval import UniPCBEvaluator
        print("   ✓ Modules imported successfully")
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        print("   Please install dependencies: pip install -r requirements.txt")
        return
    
    # 2. Load dataset (placeholder)
    print("\n2. Loading dataset...")
    print("   Note: Data will be available after paper acceptance.")
    print("   Example usage:")
    print("""
    dataset = UniPCBDataset(
        data_path="data/",
        scenario="component_detection",
        split="test"
    )
    """)
    
    # 3. Load model (placeholder)
    print("\n3. Loading PCB-GPT model...")
    print("   Note: Model weights will be available after paper acceptance.")
    print("   Example usage:")
    print("""
    model = PCBGPT.from_pretrained("pcb-gpt-base")
    """)
    
    # 4. Run inference (placeholder)
    print("\n4. Running inference...")
    print("   Example usage:")
    print("""
    result = model.inspect(
        image="examples/pcb_sample.jpg",
        task="Find all soldering defects"
    )
    print(result)
    """)
    
    # 5. Evaluate (placeholder)
    print("\n5. Running evaluation...")
    print("   Example usage:")
    print("""
    evaluator = UniPCBEvaluator(output_dir="results/")
    results = evaluator.evaluate(model, dataset)
    print(results.summary())
    """)
    
    print("\n" + "=" * 60)
    print("For more information, visit:")
    print("  - Paper: https://arxiv.org/abs/2601.19222")
    print("  - Documentation: docs/")
    print("=" * 60)


if __name__ == "__main__":
    main()
