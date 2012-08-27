import sys
import logging

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout,
    level=logging.DEBUG,
)
