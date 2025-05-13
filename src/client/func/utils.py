from typing import List
class WindowData:
    def __init__(self, window_size):
        self.data = list()
        self.total = 0
        self.window_size = window_size

    def add_data(self, new_data:List):
        self.total += len(new_data)
        self.data.extend(new_data)
        self.data = self.data[-self.window_size:]