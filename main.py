#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/29 0:00
# @Author  : Cl0udG0d
# @File    : main.py
# @Github: https://github.com/Cl0udG0d
from tkinter import Tk
from gui.dashboard import CarControl

if __name__ == '__main__':
    root = Tk()
    carControl = CarControl(root)
    root.mainloop()