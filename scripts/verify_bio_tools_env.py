#!/usr/bin/env python3
"""Smoke check for bio-tools conda env: Biopython, Meeko. PyRosetta optional."""
import sys

def main():
    ok = True
    # Biopython
    try:
        import Bio
        print("Biopython:", Bio.__version__, "OK")
    except Exception as e:
        print("Biopython: FAIL", e)
        ok = False

    # Meeko (AutoDock-GPU workflow)
    try:
        import meeko
        print("Meeko: OK")
    except Exception as e:
        print("Meeko: FAIL", e)
        ok = False

    # PyRosetta (optional; requires license / large download)
    try:
        import pyrosetta
        pyrosetta.init()
        print("PyRosetta: OK")
    except ImportError:
        print("PyRosetta: not installed (optional). Install with:")
        print("  conda install -c https://conda.rosettacommons.org -c conda-forge pyrosetta")
    except Exception as e:
        print("PyRosetta: init FAIL", e)
        ok = False

    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
