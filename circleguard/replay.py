import abc

import osrparse
import numpy as np

from circleguard import config

class Check():

    def __init__(self, replays, replays2=None, thresh=config.thresh, silent=config.silent, cache=config.cache):
        self.replays = replays # list of ReplayMap and ReplayPath objects, not yet processed
        self.replays2 = replays2
        self.mode = "double" if replays2 else "single"
        self.loaded = False
        self.thresh = thresh
        self.silent = silent
        self.cache = cache

    def load(self, loader):
        if(self.loaded):
            print("The replays in this Check object have already been loaded")
            return
        for replay in self.replays:
            replay.load(loader)
        if(self.replays2):
            for replay in self.replays2:
                replay.load(loader)
        self.loaded = True


class Replay():

    def __init__(self):
        self.replay_id = None
        self.replay_data = None

    @abc.abstractclassmethod
    def load(self, loader):
        ...

    def as_list_with_timestamps(self):
        """
        Gets the playdata as a list of tuples of absolute time, x and y.

        Returns:
            A list of tuples of (t, x, y).
        """
        # pylint: disable=not-an-iterable
        # it may be None now but we call this after loading!
        # get all offsets sum all offsets before it to get all absolute times
        timestamps = np.array([e.time_since_previous_action for e in self.replay_data])
        timestamps = timestamps.cumsum()

        # zip timestamps back to data and convert t, x, y to tuples
        txy = [[z[0], z[1].x, z[1].y] for z in zip(timestamps, self.replay_data)]
        # sort to ensure time goes forward as you move through the data
        # in case someone decides to make time go backwards anyway
        txy.sort(key=lambda p: p[0])
        return txy

class ReplayMap(Replay):

    def __init__(self, map_id, user_id, mods=None):
        self.map_id = map_id
        self.user_id = user_id
        self.username = user_id
        self.mods = mods
        self.replay_data = None

    def load(self, loader):
        info = loader.user_info(self.map_id, user_id=self.user_id, mods=self.mods)
        self.replay_data = loader.replay_data(info)
        self.user_info = info
        self.replay_id = info.replay_id

class ReplayPath(Replay):

    def __init__(self, path):
        self.path = path
        self.loaded = False
        self.user_id = None
        self.username = None
        self.mods = None
        self.replay_data = None


    def load(self, loader):
        # no, we don't need loader for ReplayPath, but to reduce type checking when calling we make the method signatures homogeneous
        loaded = osrparse.parse_replay_file(self.path)
        self.replay_data = loaded.play_data
        self.username = loaded.player_name
        self.mods = loaded.mod_combination
        self.replay_id = loaded.replay_id if loaded.replay_id != 0 else None # if score is 0 it wasn't submitted (?)
