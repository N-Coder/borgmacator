import datetime
import json
import os
from collections import Counter
from threading import Thread, Event

import dateutil.parser
import gi
import requests
import sh
from appdirs import user_config_dir
from pystemd.systemd1 import Unit

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GLib

gi.require_version('AppIndicator3', '0.1')
from gi.repository import AppIndicator3 as appindicator

gi.require_version('Notify', '0.7')
from gi.repository import Notify as notify

APPINDICATOR_ID = "borgmacator"
DIR = os.path.dirname(os.path.abspath(__file__))
with open(user_config_dir("borgmacator.json"), "r") as f:
    CONFIG = json.load(f)


class Borgmacator(object):
    def __init__(self):
        self.indicator = appindicator.Indicator.new(APPINDICATOR_ID, os.path.join(DIR, "img", "borgmatic-lightgreen.svg"), appindicator.IndicatorCategory.SYSTEM_SERVICES)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_label("", "0!")
        self.menu = gtk.Menu()

        self.item_systemd_status = gtk.MenuItem.new_with_label("???")
        self.item_systemd_status.set_sensitive(False)
        self.menu.append(self.item_systemd_status)

        self.item_healthchecks_status = gtk.MenuItem.new_with_label("???")
        self.item_healthchecks_status.set_sensitive(False)
        self.menu.append(self.item_healthchecks_status)

        self.item_journalctl_tail = gtk.MenuItem.new_with_label("???")
        self.item_journalctl_tail.set_sensitive(False)
        # self.item_journalctl_tail.get_child().set_line_wrap(True)
        # self.item_journalctl_tail.get_child().set_max_width_chars(75)
        self.submenu_log_item = gtk.MenuItem.new_with_label("Log")
        self.menu.append(self.submenu_log_item)
        self.submenu_log = gtk.Menu()
        self.submenu_log_item.set_submenu(self.submenu_log)
        self.submenu_log.append(self.item_journalctl_tail)

        self.menu.append(gtk.SeparatorMenuItem())

        self.item_goto_healthchecks = gtk.MenuItem.new_with_label("Go to Healthchecks")
        self.item_goto_healthchecks.connect("activate", self.goto_healthchecks)
        self.menu.append(self.item_goto_healthchecks)

        self.item_show_log = gtk.MenuItem.new_with_label("Show Log")
        self.item_show_log.connect("activate", self.show_log)
        self.menu.append(self.item_show_log)

        self.item_show_status = gtk.MenuItem.new_with_label("Show Status")
        self.item_show_status.connect("activate", self.show_status)
        self.menu.append(self.item_show_status)

        self.item_start_borgmatic = gtk.MenuItem.new_with_label("Start Backup")
        self.item_start_borgmatic.connect("activate", self.start_service)
        self.menu.append(self.item_start_borgmatic)

        self.menu.show_all()
        self.indicator.set_menu(self.menu)

        self.notification = notify.Notification.new("<b>Borgmatic</b>", "", "drive-harddisk-symbolic")

        self.borgmatic_unit = Unit(b'borgmatic.service')
        self.checks = []
        self.journal = []

        self.running = Event()
        self.update_now = Event()

    def show_log(self, source):
        sh.gnome_terminal("--", "/usr/bin/journalctl", "-fet", "borgmatic")

    def show_status(self, source):
        sh.gnome_terminal("--", "/usr/bin/systemctl", "status", "borgmatic.service")

    def start_service(self, source):
        sh.gnome_terminal("--", "/usr/bin/systemctl", "start", "borgmatic.service")

    def goto_healthchecks(self, source):
        gtk.show_uri(None, "https://healthchecks.io/", gdk.CURRENT_TIME)

    def update_status(self):
        state = self.borgmatic_unit.Unit.ActiveState
        if state == b"inactive":
            conds = self.borgmatic_unit.Unit.Conditions
            # self.borgmatic_unit.Unit.ConditionTimestamp
            for cond_type, trig_cond, reversed_cond, cond_value, cond_status in conds:
                if cond_status < 1:
                    self.indicator.set_icon(os.path.join(DIR, "img", "borgmatic-yellow.svg"))
            else:
                self.indicator.set_icon(os.path.join(DIR, "img", "borgmatic-white.svg"))
        elif state == b"failed":
            self.indicator.set_icon(os.path.join(DIR, "img", "borgmatic-red.svg"))
        else:
            proc = self.borgmatic_unit.Service.GetProcesses()
            for service, pid, cmd in proc:
                if cmd.startswith(b"/usr/bin/sleep"):
                    self.indicator.set_icon(os.path.join(DIR, "img", "borgmatic-lightgreen.svg"))
                    break
            else:
                self.indicator.set_icon(os.path.join(DIR, "img", "borgmatic-green.svg"))

        stati = Counter()
        infos = []
        for check in self.checks:
            if CONFIG["healthchecks"]["filter"] and check["unique_key"] not in CONFIG["healthchecks"]["filter"]:
                continue
            last_ping = dateutil.parser.isoparse(check["last_ping"])
            ping_diff = datetime.datetime.now(tz=datetime.timezone.utc) - last_ping
            ping_diff = ping_diff - (ping_diff % datetime.timedelta(seconds=1))
            infos.append("%s: %s (%s ago)" % (check["name"], check["status"], ping_diff))
            stati.update((check["status"],))
        if stati["down"]:
            self.indicator.set_label("%s!" % stati["down"], "0!")
        else:
            self.indicator.set_label("", "0!")

        stati_list = []
        # if stati["up"]:
        #     stati_list.append("%s" % stati["up"])
        # if stati["started"]:
        #     stati_list.append("<span foreground=\"green\">%s</span>" % stati["started"])
        # if stati["down"]:
        #     stati_list.append("<b foreground=\"red\">%s</b>" % stati["down"])
        # label = "/".join(str(v) for v in [stati["up"], stati["started"], stati["down"]])

        last_log = self.journal.stdout.strip().decode()
        status_diff = datetime.datetime.now() - datetime.datetime.fromtimestamp(self.borgmatic_unit.Unit.StateChangeTimestamp / 1000000)
        status_diff = status_diff - (status_diff % datetime.timedelta(seconds=1))
        self.item_systemd_status.set_label("%s (%s) since %s" % (
            self.borgmatic_unit.Unit.ActiveState.decode(), self.borgmatic_unit.Unit.SubState.decode(), status_diff
        ))
        self.item_journalctl_tail.set_label(last_log)
        self.item_healthchecks_status.set_label("\n".join(infos))

    def auto_update(self):
        self.running.wait()
        while self.running.is_set():
            self.borgmatic_unit.load()
            self.checks = requests.get("https://healthchecks.io/api/v1/checks/", headers={"X-Api-Key": CONFIG["healthchecks"]["api_key"]}).json()["checks"]
            self.journal = sh.journalctl(unit="borgmatic.service", lines=CONFIG["log_lines"], quiet=True, output="cat")
            GLib.idle_add(self.update_status)
            self.update_now.clear()
            self.update_now.wait(CONFIG["update_interval"])

    def main(self):
        t = Thread(target=self.auto_update, daemon=True)
        try:
            notify.init(APPINDICATOR_ID)
            t.start()
            GLib.idle_add(self.running.set)
            GLib.idle_add(self.update_now.set)
            gtk.main()
        finally:
            self.update_now.set()
            self.running.clear()
            t.join()
            notify.uninit()

    def quit(self):
        gtk.main_quit()
