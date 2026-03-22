import sys
import pandas as pd
import pkg_resources

print(f"Python Executable: {sys.executable}")
print(f"Python Path: {sys.path}")

installed_packages = [d.project_name for d in pkg_resources.working_set]
print(f"Is 'tabulate' in installed packages? {'tabulate' in installed_packages}")

try:
    import tabulate
    print("Successfully imported tabulate directly.")
except ImportError:
    print("Failed to import tabulate directly.")

try:
    df = pd.DataFrame({'a': [1]})
    print("Testing pandas to_markdown...")
    print(df.to_markdown())
except Exception as e:
    print(f"Error calling to_markdown: {e}")
