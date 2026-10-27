"""Motion Watch world simulator - camera on a pan / tilt head, servos, thermal camera, sensors and a world full of people,
animals and traffic. Motion Watch itself runs as its own program and connects over the network (simulator protocol 1,
see hardware/EIGENEN_SIMULATOR_ANBINDEN.md)."""

VERSION = "PY-1.4"                     # own prefix, so it is never mixed up with the 3D simulator's versions
NAME = f"MW Sim · Welt {VERSION}"      # unique name: Motion Watch lists the simulators by it and reads the version in it
TITLE = "MW Sim · Welt"                # the windows
