import sys
import os

# Add the parent directory to sys.path so pytest can find modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
