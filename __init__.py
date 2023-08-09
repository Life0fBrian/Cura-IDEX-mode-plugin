# Copyright (c) 2023 LifeOfBrian

from . import IDEXModePlugin


def getMetaData():
    return {}

def register(app):
    return {"extension": IDEXModePlugin.IDEXModePlugin()}
