#!/usr/bin/env python3
"""Dynamic swap manager using zRAM."""
from __future__ import annotations

import argparse
import subprocess
import time

import argcomplete
import psutil

# PYTHON_ARGCOMPLETE_OK
# MINFREE = 2000000000  # Min free memory (default 1000000000 : 1G)
# MAXFREE = 4000000000  # Max used memory (default 2000000000 : 2G)
# SWAPSIZE = "1G"
# SLEEPTIME = .1


parser = argparse.ArgumentParser()

parser.add_argument(
    "--minfree", help="Minimum free RAM in GB", type=int, default=2,
    required=False
)
parser.add_argument(
    "--maxfree", help="Maximum free RAM in GB", type=int, default=4,
    required=False
)
parser.add_argument(
    '--swapsize', help="Size of created swap in GB", type=int, default=1,
    required=False
)

parser.add_argument(
    '--sleeptime', help="Time between checks in seconds, a smaller value " +
                        "will increase the stability of the system",
    default=1, type=int, required=False
)

argcomplete.autocomplete(parser)
args = parser.parse_args()

MINFREE = args.minfree*1000*1000*1000
MAXFREE = args.maxfree*1000*1000*1000
SWAPSIZE = str(args.swapsize*1000*1000*1000)
SLEEPTIME = args.sleeptime
SWAPLIMIT = 20
MAXCACHE = 1  # 1G
MAXCACHE = MAXCACHE*1000*1000*1000


def gettotalmemory() -> int:
    """Get total memory of system."""
    totalram = int(psutil.virtual_memory().total)
    totalswap = int(psutil.swap_memory().total)
    return totalram + totalswap


def getavailablememory() -> int:
    """Get available memory of system."""
    availableram = int(psutil.virtual_memory().available)
    availableswap = int(psutil.swap_memory().free)
    return availableram + availableswap


def gettotalcache() -> int:
    """Get total cache in RAM."""
    return int(psutil.virtual_memory().cached)


def getusedmemory() -> int:
    """Get used memory of system."""
    return gettotalmemory() - getavailablememory()


def getpercentageofram(inputsize) -> float:
    """Get percentage of ram used by input size."""
    return inputsize / psutil.virtual_memory().total


def dropcaches():
    """Drop caches to free up memory."""
    with open("/proc/sys/vm/drop_caches", "w") as dropcachesfile:
        try:
            dropcachesfile.write("3")
            return True

        except (PermissionError, FileNotFoundError):
            return False


def execute(args: list[str], runasync=False) -> bool | None:
    """Execute command."""
    try:
        if runasync:
            subprocess.Popen(args=args)
            return None
        subprocess.run(args=args, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def getoutput(args: list[str]) -> str:
    """Get output of a command."""
    return str(subprocess.check_output(args=args))


def swapon(path: str) -> str:
    """Mount swap."""
    args = ["/usr/sbin/swapon", path]
    execute(args=args)
    return path


def swapoff(path: str) -> str:
    """Umount swap."""
    args = ["/usr/sbin/swapoff", path]
    execute(args=args)
    return path


def listswaps() -> list[list[str]]:
    """List mounted swaps."""
    args = ["swapon", "--show=NAME,SIZE", "--show", "--bytes"]
    outputstr = getoutput(args)
    outputlist = outputstr[2:].split("\\n")[1:][:-1]
    swaplistsorted = []
    swappaths = []
    swapsizes = []
    swappathssorted = []
    swapsizessorted = []
    for i in outputlist:
        swappaths.append(i.split(" ")[0])
        swapsizes.append(int(i.split(" ")[-1]))
    while swapsizes:
        for item, value in enumerate(swapsizes):
            if min(swapsizes) == value:
                swaplistsorted.append([swappaths[item], str(value)])
                swappathssorted.append(swappaths[item])
                swapsizessorted.append(str(value))
                del swappaths[item], swapsizes[item]
                break
    # swappathssorted = []
    # swapsizessorted = ["2000000000"]
    # for i in range(30):
    #     swappathssorted.append(str(i))
    #     swapsizessorted.append("2000000000")
    return [swappathssorted, swapsizessorted]


def deleteswap(runasync=False) -> str | bool:
    """Delete swap file to free up memory."""
    swaplist = listswaps()
    try:
        path = swaplist[0][0]
    except IndexError:
        return False
    print("Deleting swap", path)
    if not runasync:
        swapoff(path)
        args = ["/usr/sbin/zramctl", "--reset", path]
        execute(args=args)
        print("Deleted swap", path)
    else:
        args = ["/usr/bin/bash", "-c", f"/usr/sbin/swapoff {path} &&\
/usr/sbin/zramctl --reset {path}"]
        execute(args, runasync=runasync)
        # subprocess.Popen(args=args)
    return path


def createswap(size: str = SWAPSIZE) -> str:
    """Create swap file to free up memory."""
    shoulddeleteswap = False
    swaplist = listswaps()
    if len(swaplist[0]) >= SWAPLIMIT:  # If the limit is reached
        shoulddeleteswap = True  # Mark of a swap need to be deleted
        # While the size if less than the min swap size
        swapsizesint = [int(i) for i in swaplist[1]]
        print(int(size), int(min(swapsizesint)))
        while int(size) < min(swapsizesint):
            print(size)
            # Increase the limit
            size = str(int(size) + 1*1000*1000*1000)
        size = str(int(size) + 1*1000*1000*1000)  # End size increasing
        sizereadable = f"{str(int(size)/1000/1000/1000)} GB"
        print("Swap size have been increased to", sizereadable)
    else:
        sizereadable = f"{str(int(size)/1000/1000/1000)} GB"
        print("Creating a swap of", sizereadable)
    args = ["/usr/sbin/zramctl", "--find", "--size", size]
    path = getoutput(args=args)[:-3][2:]
    print(path)
    args = ["/usr/sbin/mkswap", path]
    execute(args=args)
    swapon(path)
    if shoulddeleteswap:
        # print(listswaps())
        # deleteswap()
        deleteswap(runasync=True)
        # print(listswaps())
    return path


while True:
    time.sleep(SLEEPTIME)
    availablememory = getavailablememory()
    # print(availablememory)
    if availablememory < MINFREE:
        if MAXCACHE > gettotalcache():
            dropcaches()
        try:
            print("Creating swap")
            createswap(SWAPSIZE)
        except subprocess.CalledProcessError:
            print("Error when creating swap")
            # print("Trying to drop cache instead")
    elif availablememory > MAXFREE:
        # dropcaches()
        deleteswap()
