![OpenWrt on Alcatel HH40V](assets/banner.webp)

# OpenWrt on Alcatel HH40V

Step-by-step guide for installing official OpenWrt 25.12.5 on the Alcatel HH40V 4G LTE
router, **without opening the case or using a serial cable**. Everything is done over
Ethernet: the stock web UI's config backup is modified to enable SSH, then OpenWrt is
written from the stock shell.

Tested on a real unit (hardware V2.0, stock firmware `HH40_ER_02.00_29`), from macOS.

The firmware images are on the [Releases](../../releases/latest) page. They are unmodified
official OpenWrt builds.

> **Unofficial guide.** Flashing replaces the vendor firmware. Back up the flash first
> (step 4). You do this at your own risk.

## Hardware

| Component | Details |
|---|---|
| SoC | Qualcomm Atheros QCA9531, MIPS 24Kc @ 650 MHz |
| RAM | 128 MiB |
| Flash | 16 MiB SPI-NOR |
| Wi-Fi | QCA9531 built-in, 2.4 GHz 802.11b/g/n |
| Ethernet | 2x 100 Mbit |
| LTE modem | internal, shows up as an RNDIS USB device (`usb0`) |
| OpenWrt target | `ath79/generic`, profile `alcatel_hh40v`, supported since 23.05.0 |

### Stock flash layout

| Partition | Size | Notes |
|---|---|---|
| `u-boot` | 256 KiB | |
| `u-boot-env` | 64 KiB | `bootcmd` lives here |
| `oem` | 1 MiB | |
| `rootfs` | ~13.2 MiB | |
| `rootfs_data` | ~2.6 MiB | inside `rootfs` |
| `kernel` | 1.4 MiB | |
| `art` | 64 KiB | **Wi-Fi calibration, unique to your unit** |
| `firmware` | ~14.6 MiB | `rootfs` + `kernel`, written by the installer |

Stock U-Boot boots with `bootcmd=bootm 0x9fe80000`. The OpenWrt factory image needs
`bootm 0x9f150000`; the installer script changes it.

## What you need

- A computer with Python 3, OpenSSL and **GNU tar**, connected to the router's LAN port
- The router's web UI login (default `admin` / `admin`)
- [`enable_sshd.py`](https://gist.github.com/andyboeh/d295c80a57d62379b926640762f3d5dd)
  by Andreas Böhler, which turns a config backup into one that starts SSH
- From this repo: [`tools/hh40v_webapi.py`](tools/hh40v_webapi.py),
  [`tools/ssh-stock.sh`](tools/ssh-stock.sh), [`tools/upgrade.sh`](tools/upgrade.sh)
- `openwrt-25.12.5-ath79-generic-alcatel_hh40v-squashfs-factory.bin` from Releases

## Installation

### 1. Download a config backup

Either in the stock web UI (*System → Backup*), or with the helper script, which talks to
the same JSON API the web UI uses:

```sh
python3 tools/hh40v_webapi.py admin admin info
python3 tools/hh40v_webapi.py admin admin backup configure.bin
```

### 2. Make an SSH-enabling backup

```sh
python3 enable_sshd.py configure.bin
```

This writes `configure.bin_mod.bin`. The script decrypts the backup, adds a startup entry
that launches dropbear, and re-packs it.

**macOS:** the script needs GNU tar. With Homebrew (`brew install gnu-tar`), put it first in
`PATH` as `tar` and stop macOS from adding `._` files:

```sh
mkdir -p shim && ln -sf "$(brew --prefix)/bin/gtar" shim/tar
COPYFILE_DISABLE=1 PATH="$PWD/shim:$PATH" python3 enable_sshd.py configure.bin
```

### 3. Restore it

Upload `configure.bin_mod.bin` in the web UI (*System → Restore*), or:

```sh
python3 tools/hh40v_webapi.py admin admin restore configure.bin_mod.bin
```

The router reboots. After that, SSH is open: user `root`, password `oelinux123`. The stock
dropbear only offers old algorithms, [`tools/ssh-stock.sh`](tools/ssh-stock.sh) adds the
needed options:

```sh
sh tools/ssh-stock.sh 'cat /proc/mtd'
```

### 4. Back up the whole flash

The OpenWrt wiki says a backup needs a serial console. It does not: with SSH open you can
read every partition. Keep these files, `art` especially.

```sh
for i in 0 1 2 3 4 5 6 7; do
  sh tools/ssh-stock.sh "cat /dev/mtdblock$i" > mtd$i.bin
done
sh tools/ssh-stock.sh 'cat /proc/mtd; fw_printenv' > mtd-info.txt
```

Compare each file with `md5sum < /dev/mtdblockN` on the router. `rootfs_data` changes while
the system runs, so one or two differing blocks there are normal.

### 5. Copy the image and the installer

Pipe the files through `ssh`:

```sh
F=openwrt-25.12.5-ath79-generic-alcatel_hh40v-squashfs-factory.bin
sh tools/ssh-stock.sh "cat > /tmp/$F" < $F
sh tools/ssh-stock.sh 'cat > /tmp/upgrade.sh && chmod +x /tmp/upgrade.sh' < tools/upgrade.sh
sh tools/ssh-stock.sh "md5sum /tmp/$F"   # compare with: md5sum $F
```

### 6. Flash

Run the installer **in the foreground** (the stock firmware has no `nohup`; a backgrounded
job is killed when the session ends):

```sh
sh tools/ssh-stock.sh "/tmp/upgrade.sh /tmp/$F"
```

It sets `bootcmd` to `bootm 0x9f150000`, writes the image to `firmware` and reboots. The SSH
session drops. **Do not cut power** while it runs. The first boot can take a few minutes.

OpenWrt then answers at `192.168.1.1`.

## After installing

| Setting | Value |
|---|---|
| LAN | `192.168.1.1`, DHCP server |
| Login | `root`, **no password**. Set one first (`passwd` or LuCI) |
| Wi-Fi | disabled (OpenWrt default) |
| Web UI | LuCI at `http://192.168.1.1` |

### LTE as WAN

The modem appears as `usb0` (`dmesg | grep -i rndis`). Point `wan` at it:

```sh
uci set network.wan=interface
uci set network.wan.proto='dhcp'
uci set network.wan.device='usb0'
uci commit network
/etc/init.d/network reload
```

APN and PIN live inside the LTE module. On the test unit the stock settings kept working
without any change.

## Credits

- Andreas Böhler: OpenWrt support for the HH40V and `enable_sshd.py`
  ([Linux/OpenWrt on the Alcatel HH40V](https://www.aboehler.at/doku/doku.php/projects:hh40v))
- [`tools/upgrade.sh`](tools/upgrade.sh) is taken from the
  [OpenWrt wiki Alcatel HH40V page](https://openwrt.org/toh/alcatel/hh40v), written by
  Andreas Böhler and the OpenWrt wiki contributors, licensed CC BY-SA 4.0.

## License

- This guide: [CC BY 4.0](LICENSE).
- `tools/hh40v_webapi.py` and `tools/ssh-stock.sh`: [MIT](LICENSE-tools).
- `tools/upgrade.sh`: **CC BY-SA 4.0**, from the OpenWrt wiki (see Credits). It is **not**
  covered by the MIT license in `LICENSE-tools`.
- Firmware images: unmodified official OpenWrt 25.12.5, GPL-2.0. Source:
  [openwrt/openwrt @ v25.12.5](https://github.com/openwrt/openwrt/tree/v25.12.5), downloads:
  [downloads.openwrt.org](https://downloads.openwrt.org/releases/25.12.5/targets/ath79/generic/).
