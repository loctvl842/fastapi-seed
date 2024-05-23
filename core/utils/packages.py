def has(package: str) -> bool:
    """
    Check if a package is installed.

    Args:
        package (str): Name of the package.
    """
    try:
        __import__(package)
        return True
    except ImportError:
        return False
