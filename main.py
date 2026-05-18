import os
import requests
from datetime import datetime
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivymd.app import MDApp
from plyer import vibrator, notification, filechooser
from kivy.utils import platform as kv_platform

SERVER_URL = "https://qadeer0017.pythonanywhere.com/analyze"
REFRESH_SECONDS = 900

last_bos_alert = ""
last_sweep_alert = ""

KV = '''
BoxLayout:
    orientation: "vertical"
    canvas.before:
        Color:
            rgba: 0.05, 0.05, 0.05, 1
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: "QADRAX ENGINE v5.2 NETWORK"
        size_hint_y: None
        height: "60dp"
        font_size: "22sp"
        bold: True
        color: 0, 1, 0.5, 1

    BoxLayout:
        size_hint_y: None
        height: "55dp"
        padding: "5dp"
        spacing: "5dp"

        Button:
            text: "ANALYZE"
            on_release: app.analyze_market()

        Button:
            text: "MUTE"
            on_release: app.toggle_mute()

        Button:
            text: "CUSTOM"
            on_release: app.pick_sound()

    BoxLayout:
        size_hint_y: None
        height: "50dp"
        Label:
            text: "VIBRATION"
        Switch:
            active: app.vibration_enabled
            on_active: app.vibration_enabled = self.active
        Label:
            text: "POPUP"
        Switch:
            active: app.popup_enabled
            on_active: app.popup_enabled = self.active

    BoxLayout:
        size_hint_y: None
        height: "50dp"
        Label:
            text: "ALERT SEC"
        Slider:
            min: 1
            max: 20
            value: app.alert_duration
            on_value: app.alert_duration = int(self.value)

    ScrollView:
        TextInput:
            text: app.dashboard_text
            readonly: True
            font_size: "14sp"
            foreground_color: 0, 1, 0.5, 1
            background_color: 0.1, 0.1, 0.1, 1
            size_hint_y: None
            height: max(self.minimum_height, self.parent.height)
'''

class QadraxApp(MDApp):
    dashboard_text = StringProperty("Ready to Sync with Cloud Engine Matrix...")
    mute = BooleanProperty(False)
    vibration_enabled = BooleanProperty(True)
    popup_enabled = BooleanProperty(True)
    alert_duration = NumericProperty(5)
    sound_path = StringProperty("")
    use_default_phone_ringtone = BooleanProperty(True)
    _android_ref = None

    def build(self):
        self.theme_cls.theme_style = "Dark"
        Clock.schedule_interval(self.analyze_market, REFRESH_SECONDS)
        Clock.schedule_once(self.analyze_market, 2)
        return Builder.load_string(KV)

    def pick_sound(self):
        try: filechooser.open_file(on_selection=self._on_sound_select, filters=[("Audio", "*.mp3", "*.wav")])
        except: pass

    def _on_sound_select(self, selection):
        if selection:
            self.sound_path = selection[0]
            self.use_default_phone_ringtone = False

    def toggle_mute(self):
        self.mute = not self.mute

    def analyze_market(self, *args):
        global last_bos_alert, last_sweep_alert
        try:
            r = requests.get(SERVER_URL, timeout=15)
            if r.status_code != 200:
                self.dashboard_text = "SERVER EXECUTOR RESPONSE ERROR"
                return
            
            data = r.json()
            bos = data["bos"]
            active_sweeps = data["active_sweeps"]

            if bos != last_bos_alert:
                if bos in ["BULLISH BOS", "BEARISH BOS"]:
                    self.trigger_alert(bos, "Market Break Context Detected")
                    last_bos_alert = bos

            if active_sweeps:
                latest = active_sweeps[-1]
                if latest != last_sweep_alert:
                    self.trigger_alert("LIQUIDITY SWEEP", latest)
                    last_sweep_alert = latest

            def format_list(levels):
                return "".join([f"• {float(x):.2f}\\n" for x in levels]) if levels else "NO ACTIVE LEVELS\\n"

            out = f"""
QADRAX ENGINE v5.2 FULL NETWORK
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

==================
CURRENT PRICE
==================
{float(data['current_price']):.2f}

==================
H1 STRUCTURE: {data['h1']}
H4 STRUCTURE: {data['h4']}
MTF ALIGNMENT: {data['alignment']}
==================
BOS DETECTION: {bos}
CONFIRMATION: {data['confirmation']}

==================
FINAL TRADE STRATEGY
==================
ACTION TARGET: {data['trade']}
PROBABILITY ALIGNMENT: {data['probability']}%

==================
DAILY PROFILES
==================
HIGH: {float(data['d_high']):.2f}
LOW: {float(data['d_low']):.2f}
RANGE SPREAD: {float(data['d_range']):.2f}
EQUILIBRIUM: {float(data['eq']):.2f}

== EXTERNAL SELL SIDE LIQUIDITY ==
{format_list(data['sell_external'])}
== EXTERNAL BUY SIDE LIQUIDITY ==
{format_list(data['buy_external'])}
== INTERNAL SELL SIDE LIQUIDITY ==
{format_list(data['sell_internal'])}
== INTERNAL BUY SIDE LIQUIDITY ==
{format_list(data['buy_internal'])}

==================
ACTIVE SWEEPS DETECTED
==================
"""
            if active_sweeps:
                for s in active_sweeps: out += f"• {s}\\n"
            else: out += "NO ACTIVE SWEEPS OPEN\\n"

            out += f"""
==================
PREMIUM / DISCOUNT MAP
==================
PREMIUM: {float(data['premium'][0]):.2f} → {float(data['premium'][1]):.2f}
DISCOUNT: {float(data['discount'][0]):.2f} → {float(data['discount'][1]):.2f}

SESSION CHANNELS:
LONDON HIGH: {float(data['london_high']):.2f}
LONDON LOW: {float(data['london_low']):.2f}
"""
            self.dashboard_text = out.strip()
        except Exception as e:
            self.dashboard_text = f"NETWORK SYNC ACTIVE:\\nWaiting for Cloud Server Node Endpoint Deployment..."

    def trigger_alert(self, title, msg):
        if self.mute: return
        try:
            if self.vibration_enabled: 
                try: vibrator.vibrate(500 if kv_platform == "android" else 0.5)
                except: pass
            notification.notify(title=title, message=msg, timeout=int(self.alert_duration))
            if self.popup_enabled:
                p = Popup(title=title, content=Label(text=msg), size_hint=(0.8, 0.3))
                p.open()
                Clock.schedule_once(lambda dt: p.dismiss(), self.alert_duration)
            self._play_alert_sound()
        except: pass

    def _stop_active_android_ringtone(self):
        rt = getattr(self, "_android_ref", None)
        if rt:
            try:
                if rt.isPlaying(): rt.stop()
            except: pass
            self._android_ref = None

    def _play_android_default_ringtone(self):
        try:
            from jnius import autoclass
            self._stop_active_android_ringtone()
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            RingtoneManager = autoclass("android.media.RingtoneManager")
            activity = PythonActivity.mActivity
            uri = RingtoneManager.getActualDefaultRingtoneUri(activity, RingtoneManager.TYPE_NOTIFICATION)
            if uri is None: return
            rt = RingtoneManager.getRingtone(activity, uri)
            if not rt: return
            self._android_ref = rt
            rt.play()
            Clock.schedule_once(lambda dt: self._stop_active_android_ringtone(), float(self.alert_duration))
        except: pass

    def _play_alert_sound(self):
        if kv_platform == "android":
            if self.use_default_phone_ringtone:
                self._play_android_default_ringtone()
                return
        if self.sound_path and os.path.isfile(self.sound_path):
            s = SoundLoader.load(self.sound_path)
            if s: s.play()

if __name__ == "__main__":
    QadraxApp().run()
