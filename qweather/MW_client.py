from .constants import *
import zmq
import pickle
from zmq.asyncio import Context, Poller
import re
import asyncio
import time
import logging
from PyQt5.QtCore import pyqtSignal
class QWeatherClient_MW:

    def __init__(self):
        print("Trying to raise exception")
        raise Exception('lol')
        