# Copyright (C) 2021 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause
# See: https://spdx.org/licenses/

import numpy as np
import unittest
from functools import partial
import time

from message_infrastructure.multiprocessing import MultiProcessing

from message_infrastructure import (
    ChannelBackend,
    Channel,
    SendPort,
    RecvPort
)


def prepare_data():
    data = np.array([12, 24, 36, 48, 60], dtype=np.int32)
    return data


def send_proc(*args, **kwargs):
    actor = args[0]
    port = kwargs.pop("port")
    if not isinstance(port, SendPort):
        raise AssertionError()
    port.start()
    port.send(prepare_data())
    port.join()
    return 0


def recv_proc(*args, **kwargs):
    actor = args[0]
    port = kwargs.pop("port")
    port.start()
    if not isinstance(port, RecvPort):
        raise AssertionError()
    data = port.recv()
    print(data)
    if not np.array_equal(data, prepare_data()):
        raise AssertionError()
    port.join()
    return 0


class Builder:
    def build(self):
        pass


class TestShmemChannel(unittest.TestCase):
    mp = MultiProcessing()

    def test_shmemchannel(self):
        self.mp.start()
        size = 5
        predata = prepare_data()
        nbytes = np.prod(predata.shape) * predata.dtype.itemsize
        name = 'test_shmem_channel'

        shmem_channel = Channel(
            ChannelBackend.SHMEMCHANNEL,
            size,
            nbytes,
            name)

        send_port = shmem_channel.get_send_port()
        recv_port = shmem_channel.get_recv_port()

        recv_port_fn = partial(recv_proc, port=recv_port)
        send_port_fn = partial(send_proc, port=send_port)

        builder1 = Builder()
        builder2 = Builder()
        self.mp.build_actor(recv_port_fn, builder1)
        self.mp.build_actor(send_port_fn, builder2)

        time.sleep(5)
        self.mp.stop()


if __name__ == "__main__":
    unittest.main()