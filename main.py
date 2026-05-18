import os
import requests
from datetime import datetime
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivymd.app import MDApp
from plyer import vibrator, notification

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
        text: "QADRAX ENGINE v5.2 STABLE"
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
            text: "ANALYZE NOW"
            on_release: app.analyze_market()

    BoxLayout:
        size_hint_y: None
        height: "50dp"
        Label:
            text: "VIBRATION"
        Switch:
            active: app.vibration_enabled
            on_active: app.vibration_enabled = self.active
        Label:
            text: "POPUP ALERT"
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
    vibration_enabled = BooleanProperty(True)
    popup_enabled = BooleanProperty(True)
    alert_duration = NumericProperty(5)

    def build(self):
        self.theme_cls.theme_style = "Dark"
        Clock.schedule_interval(self.analyze_market, REFRESH_SECONDS)
        Clock.schedule_once(self.analyze_market, 2)
        return Builder.load_string(KV)

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
                return "".join([f"• {float(x):.2f}\n" for x in levels]) if levels else "NO ACTIVE LEVELS\n"

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
                for s in active_sweeps: out += f"• {s}\n"
            else: out += "NO ACTIVE SWEEPS OPEN\n"

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
            self.dashboard_text = f"NETWORK SYNC ACTIVE:\nWaiting for Cloud Server Node Endpoint Deployment..."

    def trigger_alert(self, title, msg):
        try:
            # Vibration Execution
            if self.vibration_enabled: 
                try: vibrator.vibrate(0.5)
                except: pass
            
            # System Push Notification via Plyer
            notification.notify(title=title, message=msg, timeout=int(self.alert_duration))
            
            # Visual Popup UI
            if self.popup_enabled:
                p = Popup(title=title, content=Label(text=msg), size_hint=(0.8, 0.3))
                p.open()
                Clock.schedule_once(lambda dt: p.dismiss(), self.alert_duration)
        except:
            pass

if __name__ == "__main__":
    QadraxApp().run()
