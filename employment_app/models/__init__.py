from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .model import *
from .model_fields import *