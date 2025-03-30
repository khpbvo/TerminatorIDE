def test_import_debug():
    import sys

    print("\n".join(sys.path))

    try:
        import agents

        print(f"Found agents at: {agents.__file__}")
    except ImportError as e:
        print(f"Import error: {e}")


if __name__ == "__main__":
    test_import_debug()
