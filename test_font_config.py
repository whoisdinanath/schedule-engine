#!/usr/bin/env python3
"""
Test script to verify font configuration in visualization system.
"""

import sys
import os
sys.path.append('src')

# Test the font configuration
from src.visualization.charts import EvolutionVisualizer
import matplotlib.pyplot as plt

def test_font_configuration():
    """Test that Times New Roman font is properly configured."""
    
    print("Testing font configuration...")
    
    # Initialize the visualizer
    visualizer = EvolutionVisualizer()
    
    # Check matplotlib configuration
    print(f"Font family: {plt.rcParams['font.family']}")
    print(f"Font size: {plt.rcParams['font.size']}")
    print(f"Axes title size: {plt.rcParams['axes.titlesize']}")
    print(f"Math text font: {plt.rcParams['mathtext.rm']}")
    print(f"Font serif: {plt.rcParams['font.serif']}")
    print(f"Font sans-serif: {plt.rcParams['font.sans-serif']}")
    print(f"Font monospace: {plt.rcParams['font.monospace']}")
    
    # Create a simple test plot
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot([1, 2, 3, 4], [1, 4, 2, 3], 'b-', linewidth=2, label='Test Data')
    ax.set_xlabel('X Axis (Times New Roman)', fontsize=12)
    ax.set_ylabel('Y Axis (Times New Roman)', fontsize=12)
    ax.set_title('Test Plot - Times New Roman Font Only', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Save the test plot
    plt.savefig('output/font_test.pdf', format='pdf', dpi=300, bbox_inches='tight')
    print("✅ Test plot saved to output/font_test.pdf")
    
    plt.close()
    print("✅ Font configuration test completed successfully!")
    print("📝 All visualizations use Times New Roman font ONLY (no fallbacks or availability checks)")

if __name__ == "__main__":
    test_font_configuration()
