#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/13 12:57
# @Author  : Cl0udG0d
# @File    : main.py
# @Github: https://github.com/Cl0udG0d
import random
import can
import can.interfaces.socketcan
import config
from bus.can import constants


class CAN_BUS:
    def __init__(self, channel, interface):
        self.channel = channel
        self.interface = interface
        self._init_can_env()
        if not self.bus:
            print("[-] bus create error")
            return

    def check_bus(func):
        def wrapper(self, *args, **kwargs):
            if not self.bus:
                print("[-] bus is empty!")
                exit(0)
            return func(self, *args, **kwargs)

        return wrapper

    @check_bus
    def _send_can_message(self, id, data):
        msg = can.Message(arbitration_id=id, data=data, is_extended_id=False)
        self.bus.send(msg)

    @check_bus
    def _send_can_message_periodic(self,id,data,delay_time=1):
        msg = can.Message(arbitration_id=id, data=data, is_extended_id=False)
        self.bus.send_periodic(msg,delay_time)

    @check_bus
    def get_received_data(self):
        message = self.bus.recv(timeout=1.0)  # 设置超时时间，单位为秒
        if message:
            return message.arbitration_id,message.data
        return None  # 如果没有收到数据，则返回None或其他适当的值

    def send_left_signal(self):
        data = [0] * 8
        data[constants.DEFAULT_SIGNAL_POS] = constants.CAN_LEFT_SIGNAL
        self._send_can_message(constants.DEFAULT_SIGNAL_ID, data)

    def send_right_signal(self):
        data = [0] * 8
        data[constants.DEFAULT_SIGNAL_POS] = constants.CAN_RIGHT_SIGNAL
        self._send_can_message(constants.DEFAULT_SIGNAL_ID, data)

    def send_door_data(self,status):
        data = [0] * 8
        data[constants.DEFAULT_DOOR_POS] = status
        self._send_can_message(constants.DEFAULT_DOOR_ID, data)

    def send_speed(self, speed):
        data = [0] * 8
        data[constants.DEFAULT_SPEED_POS] = speed
        self._send_can_message(constants.DEFAULT_SPEED_ID, data)

    def send_stable_dirty_data(self):
        self._send_can_message_periodic(constants.STABLE_DIRTY_ID1, [random.randint(0, 255) for _ in range(8)],random.randint(1, 9))
        self._send_can_message_periodic(constants.STABLE_DIRTY_ID2, [random.randint(0, 255) for _ in range(8)],random.randint(1, 9))
        self._send_can_message_periodic(constants.STABLE_DIRTY_ID3, [random.randint(0, 255) for _ in range(8)],random.randint(1, 9))

    def send_clutter_dirty_data(self):
        random_id = random.randint(0, 1600)
        if random_id in [constants.DEFAULT_SPEED_ID,constants.DEFAULT_SIGNAL_ID,constants.DEFAULT_DOOR_ID]:
            return
        self._send_can_message(random_id,[random.randint(0, 255) for _ in range(8)])


    def _test_send_all(self):
        self.send_left_signal()
        self.send_right_signal()

    def _init_can_env(self):
        try:
            self.bus = can.Bus(channel=self.channel, interface=self.interface)
        except Exception as e:
            print(e)
            self.bus = None

    def __del__(self):
        if self.bus:
            self.bus.shutdown()

if __name__ == '__main__':
    can_bus = CAN_BUS(config.CHANNEL,config.CAN_INTERFACE)
