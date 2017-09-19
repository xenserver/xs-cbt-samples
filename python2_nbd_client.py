#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Nodalink, SARL.
#
# Simple nbd client used to connect to qemu-nbd
#
# author: Benoît Canet <benoit.canet@irqsave.net>
#
# This work is open source software, licensed under the terms of the
# BSD license as described in the LICENSE file in the top-level directory.
#

# Original file from
# https://github.com/cloudius-systems/osv/blob/master/scripts/nbd_client.py ,
# added support for (non-fixed) newstyle negotation.

import socket
import struct
import ssl


class new_nbd_client(object):

    READ = 0
    WRITE = 1
    DISCONNECT = 2
    FLUSH = 3

    FLAG_HAS_FLAGS = (1 << 0)
    FLAG_SEND_FLUSH = (1 << 2)

    NBD_OPT_EXPORT_NAME = 1
    NBD_OPT_STARTTLS = 5
    NBD_REP_ACK = (1)
    # Cflags contains the NBD_FLAG_C_FIXED_NEWSTYLE flag
    cflags = (1 << 0)

    NBD_REQUEST_MAGIC = 0x25609513
    NBD_REPLY_MAGIC = 0x67446698

    def __init__(self, hostname, export_name="", ca_cert=None, port=10809):
        self._flushed = True
        self._closed = True
        self._handle = 0
        self.ca_cert = ca_cert
        self._s = socket.create_connection((hostname, port))
        self._closed = False
        self._fixed_new_style_handshake(export_name)

    def __del__(self):
        self.close()

    def close(self):
        if not self._flushed:
            self.flush()
        if not self._closed:
            self._disconnect()
            self._closed = True

    def _upgrade_socket_to_TLS(self):
        thesocket = self._s
        # Forcing the client to use TLSv1_2
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.options &= ~ssl.OP_NO_TLSv1
        context.options &= ~ssl.OP_NO_TLSv1_1
        context.options &= ~ssl.OP_NO_SSLv2
        context.options &= ~ssl.OP_NO_SSLv3
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(cafile=self.ca_cert)
        self._s = context.wrap_socket(thesocket, server_side=False,
                                      do_handshake_on_connect=True)

    def _initiate_TLS_upgrade(self):
        # start TLS negotiation
        self._s.sendall(b'IHAVEOPT')
        tls_option = struct.pack('>L', self.NBD_OPT_STARTTLS)
        self._s.sendall(tls_option)
        length = struct.pack('>L', 0)
        self._s.sendall(length)
        # receive size - Don't need to do anything with this
        buf = self._s.recv(8)
        # receive option type e.g. NBD_OPT_STARTTLS
        buf = self._s.recv(4)
        option_type = struct.unpack(">I", buf)[0]
        assert(option_type == self.NBD_OPT_STARTTLS)
        # receive NBD_REP_ACK
        buf = self._s.recv(4)
        acknowledge = struct.unpack(">I", buf)[0]
        assert(acknowledge == self.NBD_REP_ACK)
        # receive option reply data length
        buf = self._s.recv(4)
        length = struct.unpack(">I", buf)[0]
        assert(length == 0)

    def _fixed_new_style_handshake(self, export_name):
        nbd_magic = self._s.recv(len("NBDMAGIC"))
        assert(nbd_magic == b'NBDMAGIC')
        nbd_magic = self._s.recv(len("IHAVEOPT"))
        assert(nbd_magic == b'IHAVEOPT')
        buf = self._s.recv(2)
        self._flags = struct.unpack(">H", buf)[0]
        assert(self._flags & self.FLAG_HAS_FLAGS != 0)
        # send fixed new style flags
        client_flags = struct.pack('>L', self.cflags)
        self._s.sendall(client_flags)

        if self.ca_cert:
            # start TLS negotiation
            self._initiate_TLS_upgrade()
            # upgrade socket to TLS
            self._upgrade_socket_to_TLS()

        # request export
        self._s.sendall(b'IHAVEOPT')
        option = struct.pack('>L', self.NBD_OPT_EXPORT_NAME)
        self._s.sendall(option)
        length = struct.pack('>L', len(export_name))
        self._s.sendall(length)
        self._s.sendall(str.encode(export_name))

        # fixed newstyle negotiation: we get this if the server is willing
        # to allow the export
        buf = self._s.recv(8)
        self._size = struct.unpack(">Q", buf)[0]
        # ignore the transmission flags (& zeroes)
        self._s.recv(2 + 124)

    def _build_header(self, request_type, offset, length):
        print "NBD request offset=%d length=%d" % (offset, length)
        command_flags = 0
        header = struct.pack('>LHHQQL', self.NBD_REQUEST_MAGIC, command_flags,
                             request_type, self._handle, offset, length)
        return header

    def _parse_reply(self, data_length=0):
        print "NBD parsing response, data_length=%d" % data_length
        reply = self._s.recv(4 + 4 + 8)
        (magic, errno, handle) = struct.unpack(">LLQ", reply)
        print "NBD response magic='%x' errno='%d' handle='%d'" % (magic, errno,
                                                                  handle)
        assert(magic == self.NBD_REPLY_MAGIC)
        assert(handle == self._handle)
        self._handle += 1
        data = bytes()
        while len(data) < data_length:
            data = data + self._s.recv(data_length - len(data))
        assert(len(data) == data_length)
        print "NBD response received data_length=%d bytes" % data_length
        return (data, errno)

    def _check_value(self, name, value):
        if not value % 512:
            return
        raise ValueError("%s=%i is not a multiple of 512" % (name, value))

    def write(self, data, offset):
        print "NBD_CMD_WRITE"
        self._check_value("offset", offset)
        self._check_value("size", len(data))
        self._flushed = False
        header = self._build_header(self.WRITE, offset, len(data))
        self._s.sendall(header + data)
        (_, errno) = self._parse_reply()
        assert(errno == 0)
        return len(data)

    def read(self, offset, length):
        print "NBD_CMD_READ"
        self._check_value("offset", offset)
        self._check_value("length", length)
        header = self._build_header(self.READ, offset, length)
        self._s.sendall(header)
        (data, errno) = self._parse_reply(length)
        assert(errno == 0)
        return data

    def need_flush(self):
        if self._flags & self.FLAG_SEND_FLUSH != 0:
            return True
        else:
            return False

    def flush(self):
        print "NBD_CMD_FLUSH"
        if self.need_flush() is False:
            self._flushed = True
            return True
        header = self._build_header(self.FLUSH, 0, 0)
        self._s.sendall(header)
        (_, errno) = self._parse_reply()
        if not errno:
            self._flushed = True
        return errno == 0

    def _disconnect(self):
        print "NBD_CMD_DISC"
        header = self._build_header(self.DISCONNECT, 0, 0)
        self._s.sendall(header)

    def size(self):
        return self._size
