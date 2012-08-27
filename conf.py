import sys
import json
import logging


logging.basicConfig(format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout,
    level=logging.DEBUG,
)

config = json.load(open('config.json', 'r'))
