#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/15 1:01
# @Author  : Cl0udG0d
# @File    : dashboard.py
# @Github: https://github.com/Cl0udG0d
import sys
import threading
import time
from tkinter import *
from math import cos, sin, pi
import can
import config
from bus.can import constants
from bus.can.main import CAN_BUS


class CarControl:
    def __init__(self, master):
        self.root = master

        self._init()

        self.draw_car_control()

        self.turn_on(constants.MIN_SPEED, constants.MAX_SPEED)
        self.change_to(self.speed)
        self.can_bus = CAN_BUS(config.CHANNEL, config.CAN_INTERFACE)

        # 启动线程监听CAN消息
        self.receive_thread = threading.Thread(target=self.receive_data)
        self.receive_thread.start()

        # 定时任务
        self._decline_speed()
        self._send_clutter_dirty_data()
        self.can_bus.send_stable_dirty_data()

        # 注册关闭窗口回调函数
        self.root.protocol("WM_DELETE_WINDOW", self.exit_program)

    def handle_key(self, event):
        if event.keysym == 'Up':
            self.decline_speed_flag = False
            self.speed += self.speed_step
            if self.speed > constants.MAX_SPEED:
                self.speed = constants.MAX_SPEED
            self.can_bus.send_speed(self.speed)
        elif event.keysym == 'Down':
            self.speed -= self.speed_step
            if self.speed < constants.MIN_SPEED:
                self.speed = constants.MIN_SPEED
            self.can_bus.send_speed(self.speed)
        elif event.keysym == 'Left':
            self.can_bus.send_left_signal()
        elif event.keysym == 'Right':
            self.can_bus.send_right_signal()
        elif event.keysym.isdigit():
            self.can_bus.send_door_data(int(event.keysym))

    def handle_key_release(self, event):
        if event.keysym == 'Up':  # 如果松开的是向上键
            self.decline_speed_flag = True

    def _decline_speed(self):
        if self.decline_speed_flag:
            if self.speed > constants.MIN_SPEED:
                self.speed -= 1
                if self.speed == 0:
                    self.can_bus.send_speed(self.speed)
            if self.speed < constants.MIN_SPEED:
                self.speed = constants.MIN_SPEED
            if self.can_bus.bus and self.speed > constants.MIN_SPEED:
                self.can_bus.send_speed(self.speed)
        self.root.after(100, self._decline_speed)

    def _init(self):
        self.length = 400
        self.speed = 0
        self.speed_step = 1
        self.first_line_X = 25
        self.first_line_Y = 120
        self.second_line_X = 145
        self.second_line_Y = 220
        self.change_x = 25
        self.change_y = 60
        self.flag = False
        self.decline_speed_flag = True
        # 绑定键盘事件
        self.root.bind_all('<KeyPress>', self.handle_key)
        self.root.bind_all('<KeyRelease>', self.handle_key_release)  # 监听键盘松开事件

    def draw_car_left_control(self):
        self.left_frame = Frame(master=self.root, width=400, height=400, bg="black")
        self.left_arc = Canvas(self.left_frame, width=400, height=400, bg="black", bd=0, highlightthickness=0)

        self.left_key = self.left_arc.create_polygon(10, 50, 40, 20, 40, 30, 20, 50, 40, 70, 40, 80, 10, 50,
                                                     fill="white")

        self.right_key = self.left_arc.create_polygon(160, 50, 130, 20, 130, 30, 150, 50, 130, 70, 130, 80, 160, 50,
                                                      fill="white")

        # 车门
        self.door1 = self.left_arc.create_line(self.first_line_X, self.first_line_Y, self.first_line_X,
                                               self.first_line_Y + self.change_y, fill="white", width=2)
        self.door2 = self.left_arc.create_line(self.first_line_X, self.second_line_Y, self.first_line_X,
                                               self.second_line_Y + self.change_y, fill="white", width=2)
        self.door3 = self.left_arc.create_line(self.second_line_X, self.first_line_Y, self.second_line_X,
                                               self.first_line_Y + self.change_y, fill="white", width=2)
        self.door4 = self.left_arc.create_line(self.second_line_X, self.second_line_Y, self.second_line_X,
                                               self.second_line_Y + self.change_y, fill="white", width=2)

        self.left_arc.place(relx=0.8, rely=0.5, anchor="center")  # 居中显示
        self.left_frame.pack(side="left", fill="both")

    def draw_car_right_control(self):
        # 仪表盘
        self.right_frame = Frame(master=self.root, width=400, height=400, bg="black")
        self.right_arc = Canvas(self.right_frame, width=400, height=400, bg="black", bd=0, highlightthickness=0)
        self.right_arc.create_arc(5, 5, self.length - 5, self.length - 5, start=0, extent=225, style=ARC,
                                  outline="white", width=2)
        self.right_arc.create_rectangle(0.5 * self.length, 0.6 * self.length, 0.9 * self.length, 0.9 * self.length,
                                        outline="white", width=2)
        self.r = self.length / 2 - 5
        self.center = (int(self.length / 2), int(self.length / 2))
        self.right_arc.pack()
        self.right_frame.pack(side="right", fill="both")

    def draw_car_control(self):
        self.draw_car_left_control()
        self.draw_car_right_control()

    def _parse_can_data(self, canid, data):
        print("revice data , id : {} , data : {}".format(canid, data))
        if canid == constants.DOS_ID:
            if all(i == 0 for i in data):
                self.receive_thread = threading.Thread(target=self.remind_control_fault)
                self.receive_thread.start()
        elif canid == constants.DEFAULT_SIGNAL_ID:
            if data[constants.DEFAULT_SIGNAL_POS] == constants.CAN_LEFT_SIGNAL:
                self.receive_thread = threading.Thread(target=self.update_signal_status, args=(self.left_key,))
                self.receive_thread.start()
            if data[constants.DEFAULT_SIGNAL_POS] == constants.CAN_RIGHT_SIGNAL:
                self.receive_thread = threading.Thread(target=self.update_signal_status, args=(self.right_key,))
                self.receive_thread.start()
        elif canid == constants.DEFAULT_DOOR_ID:
            if 9 >= data[constants.DEFAULT_DOOR_POS] >= 5:
                self.receive_thread = threading.Thread(target=self.unlock_car_door,
                                                       args=(data[constants.DEFAULT_DOOR_POS],))
                self.receive_thread.start()
            elif 0 <= data[constants.DEFAULT_DOOR_POS] <= 4:
                self.receive_thread = threading.Thread(target=self.lock_car_door,
                                                       args=(data[constants.DEFAULT_DOOR_POS],))
                self.receive_thread.start()
        elif canid == constants.DEFAULT_SPEED_ID:
            self.receive_thread = threading.Thread(target=self.change_to,
                                                   args=(data[constants.DEFAULT_SPEED_POS],))
            self.receive_thread.start()

    def receive_data(self):
        try:
            revice_bus = can.interface.Bus(channel=config.CHANNEL, interface=config.CAN_INTERFACE)
            while True:
                message = revice_bus.recv(1.0)
                if message:
                    canid, data = message.arbitration_id, message.data
                    self._parse_can_data(canid, data)
                if self.flag:
                    return
        except Exception as e:
            print("receive_data error ")
            print(e)
            pass

    def remind_control_fault(self):
        self.error_label = Label(master=self.left_frame, text="Error", fg="red", font=("Arial", 14))
        self.error_label.pack(side="bottom", pady=20)
        self.root.after(2000, self.delete_error_label)

    def delete_error_label(self):
        self.error_label.destroy()
        self.draw_car_left_control()

    def unlock_car_door(self, status=constants.CAN_DOOR_UNLOCK):
        if status == constants.CAN_DOOR_UNLOCK:
            self.left_arc.coords(self.door1, self.first_line_X, self.first_line_Y, self.first_line_X - self.change_x,
                                 self.first_line_Y + self.change_y)
            self.left_arc.coords(self.door2, self.first_line_X, self.second_line_Y, self.first_line_X - self.change_x,
                                 self.second_line_Y + self.change_y)
            self.left_arc.coords(self.door3, self.second_line_X, self.first_line_Y, self.second_line_X + self.change_x
                                 , self.first_line_Y + self.change_y)
            self.left_arc.coords(self.door4, self.second_line_X, self.second_line_Y,
                                 self.second_line_X + self.change_x,
                                 self.second_line_Y + self.change_y)
        elif status == constants.CAN_DOOR1_UNLOCK:
            self.left_arc.coords(self.door1, self.first_line_X, self.first_line_Y, self.first_line_X - self.change_x,
                                 self.first_line_Y + self.change_y)
        elif status == constants.CAN_DOOR2_UNLOCK:
            self.left_arc.coords(self.door2, self.first_line_X, self.second_line_Y, self.first_line_X - self.change_x,
                                 self.second_line_Y + self.change_y)
        elif status == constants.CAN_DOOR3_UNLOCK:
            self.left_arc.coords(self.door3, self.second_line_X, self.first_line_Y, self.second_line_X + self.change_x
                                 , self.first_line_Y + self.change_y)
        elif status == constants.CAN_DOOR4_UNLOCK:
            self.left_arc.coords(self.door4, self.second_line_X, self.second_line_Y,
                                 self.second_line_X + self.change_x,
                                 self.second_line_Y + self.change_y)

    def lock_car_door(self, status=constants.CAN_DOOR_LOCK):
        if status == constants.CAN_DOOR_LOCK:
            self.left_arc.coords(self.door1, self.first_line_X, self.first_line_Y, self.first_line_X,
                                 self.first_line_Y + self.change_y)
            self.left_arc.coords(self.door2, self.first_line_X, self.second_line_Y, self.first_line_X,
                                 self.second_line_Y + self.change_y)
            self.left_arc.coords(self.door3, self.second_line_X, self.first_line_Y, self.second_line_X
                                 , self.first_line_Y + self.change_y)
            self.left_arc.coords(self.door4, self.second_line_X, self.second_line_Y, self.second_line_X,
                                 self.second_line_Y + self.change_y)
        elif status == constants.CAN_DOOR1_LOCK:
            self.left_arc.coords(self.door1, self.first_line_X, self.first_line_Y, self.first_line_X,
                                 self.first_line_Y + self.change_y)
        elif status == constants.CAN_DOOR2_LOCK:
            self.left_arc.coords(self.door2, self.first_line_X, self.second_line_Y, self.first_line_X,
                                 self.second_line_Y + self.change_y)
        elif status == constants.CAN_DOOR3_LOCK:
            self.left_arc.coords(self.door3, self.second_line_X, self.first_line_Y, self.second_line_X
                                 , self.first_line_Y + self.change_y)
        elif status == constants.CAN_DOOR4_LOCK:
            self.left_arc.coords(self.door4, self.second_line_X, self.second_line_Y, self.second_line_X,
                                 self.second_line_Y + self.change_y)

    def update_signal_status(self, key):
        self.left_arc.itemconfig(key, fill="yellow")
        time.sleep(config.BLINK_TIME)
        self.left_arc.itemconfig(key, fill="white")

    def _send_clutter_dirty_data(self):
        self.can_bus.send_clutter_dirty_data()
        self.root.after(100, self._send_clutter_dirty_data)

    def turn_on(self, val_min, val_max):
        self.val_max = val_max
        self.val_min = val_min
        self.right_arc.create_text(0.25 * self.length, 0.8 * self.length, text=str(val_min), fill="white",
                                   font=("Menlo", int(self.length / 15)))
        self.right_arc.create_text(0.9 * self.length, 0.55 * self.length, text=str(val_max), fill="white",
                                   font=("Menlo", int(self.length / 15)))
        self.text = self.right_arc.create_text(0.7 * self.length, 0.75 * self.length, text="", fill="yellow",
                                               font=("Menlo", int(self.length / 15)))
        self.pointer = self.right_arc.create_line(self.center, (
            self._val2pos(0)[0] + self.center[0], self.length - (self._val2pos(0)[1] + self.center[1])), fill="blue",
                                                  width=3)
        self.right_arc.pack()

    def change_to(self, val):
        self.right_arc.coords(self.pointer, self.center[0], self.center[1], self._val2pos(val)[0] + self.center[0],
                              self.length - (self._val2pos(val)[1] + self.center[1]))
        self.right_arc.itemconfig(self.text, text=str(val))
        self.right_arc.pack()

    def _val2pos(self, val):
        return (
            int(cos((self.val_max - val) / (self.val_max - self.val_min) * (5 / 4) * pi) * self.r),
            int(sin((self.val_max - val) / (self.val_max - self.val_min) * (5 / 4) * pi) * self.r)
        )

    def exit_program(self):
        # 执行程序退出操作
        self.root.destroy()
        self.flag = True
        self.can_bus.bus.shutdown()
        # self.threadPool.shutdown(wait=False)
        sys.exit(0)


if __name__ == "__main__":
    root = Tk()
    engine_light = CarControl(root)
    root.mainloop()
