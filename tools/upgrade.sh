#!/bin/sh
# Flashes an OpenWrt factory image from the stock firmware and points U-Boot at it.
#
# Source: OpenWrt wiki, "Alcatel HH40V" page, https://openwrt.org/toh/alcatel/hh40v
# Authors: Andreas Böhler and the OpenWrt wiki contributors
# License: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
# Not covered by this repository's MIT license (LICENSE-tools).

IMAGE_NAME="$1"

if [ ! -e ${IMAGE_NAME} ]; then
  echo "Image file not found: ${IMAGE_NAME}"
  exit 1
fi

. /lib/upgrade/common.sh

fw_setenv bootcmd "bootm 0x9f150000"

kill_remaining TERM
sleep 3
kill_remaining KILL

run_ramfs mtd write ${IMAGE_NAME} firmware
sleep 2
reboot -f
