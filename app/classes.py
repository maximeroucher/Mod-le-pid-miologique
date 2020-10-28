import json
import os
import random
import sqlite3
import time
from threading import Thread
from tkinter import messagebox

# Mute l'import de pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'True'
# Postionne la fenêtre de l'application
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

import easygui
import pygame

from tools import *

