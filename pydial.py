"""
Module that implements UPNP protocol to discover Chromecasts
"""

# Based on code from PyChromecast - https://github.com/balloob/pychromecast
import select
import socket
import urlparse
import logging
import datetime as dt

DISCOVER_TIMEOUT = 10

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900
SSDP_MX = 1
SSDP_ST = "urn:dial-multiscreen-org:service:dial:1"

SSDP_REQUEST = 'M-SEARCH * HTTP/1.1\r\n' + \
                  'HOST: {}:{:d}\r\n'.format(SSDP_ADDR, SSDP_PORT) + \
                  'MAN: "ssdp:discover"\r\n' + \
                  'MX: {:d}\r\n'.format(SSDP_MX) + \
                  'ST: {}\r\n'.format(SSDP_ST) + \
                  '\r\n'


class DialClient(object):
     def __init__(self, host=None):
          self.host = host

def discover_servers(max_devices=None, timeout=DISCOVER_TIMEOUT):
     """
     Sends a message over the network to discover DIAL servers and returns
     a list of found IP addresses.

     Inspired by Crimsdings
     https://github.com/crimsdings/ChromeCast/blob/master/cc_discovery.py
     """
     ips = []

     calc_now = dt.datetime.now
     start = calc_now()

     try:
          sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

          sock.sendto(SSDP_REQUEST, (SSDP_ADDR, SSDP_PORT))

          sock.setblocking(0)

          while True:
               time_diff = calc_now() - start

               seconds_left = timeout - time_diff.seconds

               if seconds_left <= 0:
                    return ips

               ready = select.select([sock], [], [], seconds_left)[0]

               if ready:
                    response = sock.recv(1024)

                    found_ip = found_st = None

                    headers = response.split("\r\n\r\n", 1)[0]

                    for header in headers.split("\r\n"):
                         parts = header.split(": ", 1)

                         # Headers start with something like 'HTTP/1.1 200 OK'
                         # We cannot split that up in key-value pair, so skip
                         if len(parts) != 2:
                              continue

                         key, value = parts

                         if key == "LOCATION":
                              url = urlparse.urlparse(value)

                              found_ip = url.hostname

                         elif key == "ST":
                              found_st = value

                    if found_st == SSDP_ST and found_ip:
                         ips.append(found_ip)

                         if max_devices and len(ips) == max_devices:
                              return ips

     except socket.error:
          logging.getLogger(__name__).exception(
               "Socket error while discovering servers")

     finally:
          sock.close()

     return ips