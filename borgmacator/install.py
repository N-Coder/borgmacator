import json
import os

import sh
from appdirs import user_config_dir


def install():
    with open(os.path.join(user_config_dir("autostart"), "borgmacator.desktop"), "w") as f:
        f.write("""[Desktop Entry]
Type=Application
Exec=%s
Hidden=false
X-GNOME-Autostart-enabled=true
Name=Borgmacator
""" % sh.which("borgmacator"))
    config = user_config_dir("borgmacator.json")
    if not os.path.exists(config):
        with open(config, "w") as f:
            json.dump({
                "healthchecks": {"api_key": "TODO", "filter": []},
                "terminal": {"path": "gnome-terminal", "args": ["--"], "kwargs": {}},
                "log_lines": 10,
                "update_interval": 15
            }, f)


def restart():
    pids = set(sh.pgrep("-f", "borgmacator").stdout.decode().splitlines())
    pids.discard(str(os.getpid()))
    if pids:
        sh.kill(*pids)
    p = sh.dbus_send("--session", "--type=method_call", "--dest=org.gnome.Shell",
                     "/org/gnome/Shell", "org.gnome.Shell.Eval",
                     "string:'const Util = imports.misc.util; Util.spawnCommandLine(\"%s\");'" % sh.which("borgmacator"))
    print("Run the following if borgmacator didn't start")
    print(b" ".join(p.cmd).decode())


if __name__ == "__main__":
    install()
