# Parser Generator

[![Español](https://img.shields.io/badge/Leer_en-Español-yellow.svg)](README.es.md)

This project is an interactive tool designed for creating, visualizing, and simulating grammars using various parsing algorithms. Developed as part of the Languages and Compilers course, it allows users to define grammars and obtain parsing tables, First and Follow sets, and real-time derivation simulations.

## Supported Algorithms

The generator includes full support for the following parsing algorithms (Bottom-Up and Top-Down):

- **LL(1)**: Predictable top-down analysis.
- **LR(0)**: Bottom-up analysis with canonical closure states.
- **SLR(1)**: Simple bottom-up analysis using Follow sets.
- **CLR(1)**: Canonical bottom-up analysis with lookahead symbols.
- **LALR(1)**: Bottom-up analysis with merging of states with identical cores.

## Main Features

- **Graphical User Interface (GUI)**: Designed with PyQt6 for a smooth and intuitive user experience.
- **Sets Calculation**: Automatic generation of **First** and **Follow** sets.
- **Canonical Collection Visualization**: Detailed visualization of states and their items.
- **Analysis Simulation**: Interactive tool to test input strings and visualize stack steps.
- **Data Export**:
    - Parsing tables in **CSV** format.
    - State and canonical collection reports in **PDF**.
- **Special Symbol Handling**: Native support for empty production symbols (λ / ε).

## System Requirements

To run this project, you will need:

- **Python 3.8+**
- **PyQt6**: For the graphical interface.
- **ReportLab**: Required for exporting PDF reports.

## Installation and Execution

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/JimSegovia/ParserGenerator.git
    cd ParserGenerator
    ```

2.  **Install dependencies:**
    ```bash
    pip install PyQt6 reportlab
    ```

3.  **Run the application:**
    ```bash
    python pargen_gui.py
    ```

## Usage Guide

1.  **Define the Grammar**:
    - Enter **Non-Terminals** separated by `|` (e.g., `S|A|B`).
    - Enter **Terminals** separated by `|` (e.g., `id|+|*|(|)`).
    - Define **Production Rules** (one per line, using `->` or `→`).
2.  **Select Algorithm**: Use the dropdown menu to choose between LL(1), LR(0), SLR(1), CLR(1), or LALR(1).
3.  **Build Parser**: Click the green **"Build Parser"** button.
4.  **Analyze Strings**: In the **"Parse Tree"** tab, enter a space-separated token string (e.g., `id + id`) and press **"Parse Input"**.

---
**Developed by:** Jim Segovia
