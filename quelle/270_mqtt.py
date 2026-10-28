#@ Motion Watch – Teil 270: MQTT / Home Assistant. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# MQTT / Home Assistant: state (armed, person, motion, animal, recording, battery, temperature), events and the alarm picture
#   go to an MQTT broker (e.g. the Mosquitto add-on of Home Assistant); commands come back (arm / disarm, lights).
#   Home Assistant finds MoveEye by itself (MQTT discovery): alarm panel, sensors, camera picture.
#   Own small MQTT 3.1.1 client (no extra package), optional TLS.
# ----------------------------------------------------------------------------
class MiniMQTT:
    def __init__(self, host, port, client_id, user="", pw="", tls=False, will=None):
        self.host, self.port, self.cid, self.user, self.pw, self.tls, self.will = host, int(port), client_id, user, pw, tls, will
        self.sock = None; self.lock = threading.Lock(); self.pid = 1; self.on_message = None; self.last_tx = 0.0

    @staticmethod
    def _len(n):
        out = bytearray()
        while True:
            b = n % 128; n //= 128
            out.append(b | (0x80 if n else 0))
            if not n:
                return bytes(out)

    @staticmethod
    def _str(x):
        b = x.encode() if isinstance(x, str) else x
        return len(b).to_bytes(2, "big") + b

    def _send(self, ptype, body):
        with self.lock:
            self.sock.sendall(bytes([ptype]) + self._len(len(body)) + body)
            self.last_tx = time.time()

    def _recv_exact(self, n):
        b = b""
        while len(b) < n:
            c = self.sock.recv(n - len(b))
            if not c:
                raise ConnectionError("broker closed the connection")
            b += c
        return b

    def _read_packet(self):
        h = self._recv_exact(1)[0]                       # may time out (nothing there) - the rest of a packet may not
        old = self.sock.gettimeout()
        try:
            self.sock.settimeout(20.0)
            mult, n = 1, 0
            for _i in range(4):
                d = self._recv_exact(1)[0]
                n += (d & 0x7F) * mult; mult *= 128
                if not d & 0x80:
                    break
            else:
                raise ConnectionError("invalid packet from the broker")
            if n > 256 * 1024:
                raise ConnectionError("packet from the broker too big")
            body = self._recv_exact(n) if n else b""
        finally:
            self.sock.settimeout(old)
        self.last_rx = time.time()
        return h, body

    def connect(self):
        import socket, ssl
        s_ = socket.create_connection((self.host, self.port), timeout=10)
        if self.tls:
            s_ = ssl.create_default_context().wrap_socket(s_, server_hostname=self.host)
        self.sock = s_
        flags = 0x02
        payload = self._str(self.cid)
        if self.will:
            flags |= 0x04 | 0x20; payload += self._str(self.will[0]) + self._str(self.will[1])
        if self.user:
            flags |= 0x80; payload += self._str(self.user)
            if self.pw:
                flags |= 0x40; payload += self._str(self.pw)
        self._send(0x10, self._str("MQTT") + bytes([4, flags]) + (60).to_bytes(2, "big") + payload)
        h, body = self._read_packet()
        if h >> 4 != 2 or len(body) < 2:
            raise ConnectionError("no answer from the broker")
        if body[1] != 0:
            raise ConnectionError({4: "user name / password wrong", 5: "not allowed (user / password?)"}.get(body[1], f"refused ({body[1]})"))
        self.sock.settimeout(1.0); self.last_rx = time.time()

    def publish(self, topic, payload, retain=False):
        if isinstance(payload, str):
            payload = payload.encode()
        self._send(0x30 | (1 if retain else 0), self._str(topic) + payload)

    def subscribe(self, topic):
        self.pid = self.pid % 65000 + 1
        self._send(0x82, self.pid.to_bytes(2, "big") + self._str(topic) + b"\x00")

    def poll(self):
        """Read what the broker sends (1 s at most). Keeps the connection alive."""
        import socket
        if time.time() - self.last_tx > 30:
            self._send(0xC0, b"")
        if time.time() - getattr(self, "last_rx", time.time()) > 95:
            raise ConnectionError("no answer from the broker for 95 s")
        try:
            h, body = self._read_packet()
        except socket.timeout:
            return
        if h >> 4 == 3:
            tl = int.from_bytes(body[:2], "big"); topic = body[2:2 + tl].decode(errors="replace")
            off = 2 + tl + (2 if (h >> 1) & 3 else 0)
            if self.on_message:
                self.on_message(topic, body[off:])

    def close(self):
        try:
            self._send(0xE0, b"")
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass


MQTT = {"status": "off", "client": None}


class MqttBridge:
    def __init__(self):
        self.last = None; self.last_t = 0.0; self.prev_ev = None
        threading.Thread(target=self.loop, daemon=True, name="mqtt").start()

    def base(self):
        return (CFG["mqtt_prefix"].strip().strip("/") or "motionwatch") + "/" + device_uid()

    def loop(self):
        backoff = 5
        while True:
            if not (CFG["mqtt_on"] and CFG["mqtt_host"].strip()):
                MQTT["status"] = "off"; time.sleep(2); continue
            b = self.base()
            c = MiniMQTT(CFG["mqtt_host"].strip(), int(CFG["mqtt_port"] or 1883), "motionwatch-" + device_uid(), CFG["mqtt_user"], CFG["mqtt_password"],
                         CFG["mqtt_tls"], will=(b + "/availability", "offline"))
            try:
                c.connect()
                c.on_message = self.command
                c.publish(b + "/availability", "online", retain=True)
                c.subscribe(b + "/cmd/#")
                zb = CFG["sens_on"] and CFG["zigbee_on"]
                if zb:
                    c.subscribe("zigbee2mqtt/+")                   # Zigbee sensors (Zigbee2MQTT) for the extra sensors
                MQTT["client"] = c; MQTT["status"] = "connected"; backoff = 5
                log_event("web", f"MQTT connected to {CFG['mqtt_host']}:{CFG['mqtt_port']}")
                if CFG["mqtt_discovery"]:
                    self.discovery(c)
                self.last = None
                key = (CFG["mqtt_host"], CFG["mqtt_port"], CFG["mqtt_user"], CFG["mqtt_password"], CFG["mqtt_tls"], CFG["mqtt_prefix"], CFG["mqtt_on"], zb)
                while (CFG["mqtt_host"], CFG["mqtt_port"], CFG["mqtt_user"], CFG["mqtt_password"], CFG["mqtt_tls"], CFG["mqtt_prefix"], CFG["mqtt_on"],
                       CFG["sens_on"] and CFG["zigbee_on"]) == key:
                    c.poll()
                    self.push_state(c)
                c.publish(b + "/availability", "offline", retain=True)
                MQTT["status"] = "off" if not CFG["mqtt_on"] else "reconnecting"; backoff = 1
            except Exception as e:
                msg = str(e) or e.__class__.__name__
                if len(CFG["mqtt_password"]) >= 6:
                    msg = msg.replace(CFG["mqtt_password"], "***")
                if MQTT["status"] != "error: " + msg[:120]:
                    log_event("web", f"MQTT: {msg}"[:200])
                MQTT["status"] = "error: " + msg[:120]
            finally:
                MQTT["client"] = None
                c.close()
            time.sleep(backoff); backoff = min(120, backoff * 2)

    def state(self):
        b = STATE.get("battery") or {}
        present = set(STATE.get("present") or [])
        arm = STATE["arm_state"]
        ha = "triggered" if arm == "armed" and STATE["persons"] else {"armed": "armed_away", "arming": "arming"}.get(arm, "disarmed")
        return {"arm": arm, "alarm_panel": ha, "person": "ON" if STATE["persons"] else "OFF", "motion": "ON" if "motion" in present else "OFF",
                "animal": "ON" if "animal" in present else "OFF", "recording": "ON" if STATE.get("recording") else "OFF",
                "persons": STATE["persons"], "battery": b.get("pct"), "cpu_temp": STATE.get("cpu_temp"), "fps": STATE.get("fps"),
                "tamper": (STATE.get("tamper") or {}).get("last", ""), "version": APP_VERSION, "name": CFG["device_name"] or "MoveEye"}

    def push_state(self, c):
        st = self.state(); now = time.time()
        cmp = {k: v for k, v in st.items() if k not in ("fps", "cpu_temp")}
        if cmp != self.last or now - self.last_t > 60:
            c.publish(self.base() + "/state", json.dumps(st), retain=True)
            if self.last and st["person"] == "ON" and self.last.get("person") != "ON":
                c.publish(self.base() + "/event", json.dumps({"event": "person", "time": datetime.now().isoformat(timespec="seconds")}))
                self.picture(c)
            self.last = cmp; self.last_t = now

    def picture(self, c):
        w = WATCH_REF["w"]
        if w is None or w.frame_out is None:
            return
        f = w.frame_out; h, wd = f.shape[:2]
        if wd > 960:
            f = cv2.resize(f, (960, int(h * 960 / wd)), interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 75])
        if ok:
            c.publish(self.base() + "/snapshot", buf.tobytes(), retain=True)

    def command(self, topic, payload):
        if topic.startswith("zigbee2mqtt/"):
            zb_message(topic[12:], payload); return
        cmd = topic.rsplit("/cmd/", 1)[-1]; val = payload.decode(errors="replace").strip()
        log_event("web", f"MQTT command: {cmd} = {val[:40]}")
        if cmd in ("arm", "alarm"):
            v = val.upper()
            if v in ("ARM", "ARM_AWAY", "ARM_HOME", "ARM_NIGHT", "ON"):
                arm()
            elif v in ("ARM_NOW",):
                arm(0)
            elif v in ("DISARM", "OFF"):
                was = is_armed() or bool(CFG["armed"])
                disarm()
                if was:                                  # 2.95.33: the owner learns when MQTT switched the camera off
                    try:
                        WATCH_REF["w"].notifier.info(tr("Disarmed via MQTT / Home Assistant"))
                    except Exception:
                        pass
        elif cmd in ("light_white", "light_ir") and val.lower() in LIGHT_MODES:
            light_set(cmd[6:], val.lower())
        elif cmd == "snapshot" and MQTT["client"] is not None:
            self.picture(MQTT["client"])

    def discovery(self, c):
        """Home Assistant MQTT discovery: the device and its entities appear by themselves."""
        b = self.base(); uid = device_uid(); name = CFG["device_name"] or "MoveEye"
        dev = {"identifiers": ["motionwatch_" + uid], "name": name, "manufacturer": "MoveEye", "model": "Raspberry Pi camera", "sw_version": APP_VERSION}
        avail = {"availability_topic": b + "/availability"}
        ents = [
            ("alarm_control_panel", "alarm", {"name": "Alarm", "state_topic": b + "/state", "value_template": "{{ value_json.alarm_panel }}",
                                              "command_topic": b + "/cmd/arm", "payload_arm_away": "ARM_AWAY", "payload_disarm": "DISARM",
                                              "supported_features": ["arm_away"], "code_arm_required": False, "code_disarm_required": False}),
            ("binary_sensor", "person", {"name": "Person", "state_topic": b + "/state", "value_template": "{{ value_json.person }}", "device_class": "occupancy"}),
            ("binary_sensor", "motion", {"name": "Motion", "state_topic": b + "/state", "value_template": "{{ value_json.motion }}", "device_class": "motion"}),
            ("binary_sensor", "animal", {"name": "Animal", "state_topic": b + "/state", "value_template": "{{ value_json.animal }}", "icon": "mdi:paw"}),
            ("binary_sensor", "recording", {"name": "Recording", "state_topic": b + "/state", "value_template": "{{ value_json.recording }}", "icon": "mdi:record-rec"}),
            ("sensor", "battery", {"name": "Battery", "state_topic": b + "/state", "value_template": "{{ value_json.battery }}", "device_class": "battery", "unit_of_measurement": "%"}),
            ("sensor", "cpu_temp", {"name": "CPU temperature", "state_topic": b + "/state", "value_template": "{{ value_json.cpu_temp }}", "device_class": "temperature", "unit_of_measurement": "°C"}),
            ("camera", "snapshot", {"name": "Last alarm picture", "topic": b + "/snapshot"}),
        ]
        for comp, key, cfg in ents:
            cfg = dict(cfg, unique_id=f"motionwatch_{uid}_{key}", object_id=f"motionwatch_{key}", device=dev, **avail)
            c.publish(f"homeassistant/{comp}/motionwatch_{uid}/{key}/config", json.dumps(cfg), retain=True)


MQTT_BRIDGE = None

