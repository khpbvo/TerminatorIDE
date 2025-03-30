# Save as test_debug.py in your tests directory
def test_debug_import():
    import sys

    print("\nPYTEST PATH:")
    print("\n".join(sys.path))

    try:
        import agents

        print(f"Found agents at: {agents.__file__}")
    except ImportError as e:
        print(f"Import error: {e}")
