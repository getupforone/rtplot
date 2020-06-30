#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

import zmq

#ENDPOINT = "ipc://routing.ipc"
ENDPOINT = "tcp://localhost:7777"


def main():
    context = zmq.Context.instance()
    worker = context.socket(zmq.SUB)
    worker.connect(ENDPOINT)

    worker.setsockopt_string(zmq.SUBSCRIBE, '')
    while True:
        request = worker.recv_string()
        print("[Sub] received request: ", request)


if __name__ == "__main__":
    main()
