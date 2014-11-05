#!/usr/bin/python3


class vdrFrontend:
    def __init__(self, main, name):
        self.main = main
        self.name = name
        self.state = 0  # 0=detached, 1=active, 2=suspended

    def attach(self, options=None):
        self.state = 1

    def detach(self):
        self.state = 0

    def status(self):
        return self.state

    def resume(self):
        if self.state == 2:
            self.state = 1
        elif self.state == 0:
            self.state = 1
