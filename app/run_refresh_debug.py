import sys, logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s | %(name)s | %(message)s')
sys.path.insert(0, '.')
from refresh import run_refresh
result = run_refresh()
print("Result:", result)
