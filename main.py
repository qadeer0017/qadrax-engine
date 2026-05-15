# =========================================================
# QADRAX / QUANT HEDGE FUND ENGINE v5.2 PARITY
# Kivy UI — Android + Desktop (PC tkinter logic ported)
# =========================================================

import os
import certifi

# CRITICAL ANDROID 15 SSL FIX:
# yfinance aur internet requests ke liye ye lines lazmi hain
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['SSL_CERT_DIR'] = os.path.dirname(certifi.where())

import yfinance as yf
import pandas as pd
from datetime import datetime
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.switch import Switch
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView

from kivymd.app import MDApp

from plyer import vibrator
from plyer import notification
from plyer import filechooser

from kivy.utils import platform as kv_platform

# =========================================================
# SETTINGS
# =========================================================
SYMBOL = "GC=F"
LTF = "15m"
H1 = "1h"
H4 = "4h"
PERIOD = "10d"
# PC tkinter used 900000 ms = 15 min between refreshes
REFRESH_SECONDS = 900

last_bos_alert = ""
last_sweep_alert = ""

# =========================================================
# UI (KV Language)
# =========================================================
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
        text: "QADRAX ENGINE v5.2 FULL"
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

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def val(x):
    try:
        if isinstance(x, pd.Series):
            return float(x.iloc[0])
        return float(x)
    except:
        return 0.0

def get_data(interval):
    try:
        df = yf.download(SYMBOL, interval=interval, period=PERIOD, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[["Open", "High", "Low", "Close", "Volume"]]
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"Data Error: {e}")
        return None

def structure(df):
    try:
        recent = df.tail(50)
        highs = recent["High"].values
        lows = recent["Low"].values
        hh = highs[-1] > highs[-10]
        hl = lows[-1] > lows[-10]
        lh = highs[-1] < highs[-10]
        ll = lows[-1] < lows[-10]
        if hh and hl: return "BULLISH"
        elif lh and ll: return "BEARISH"
        return "RANGE"
    except: return "UNKNOWN"

def detect_bos(df):
    try:
        recent = df.tail(30)
        close = val(recent["Close"].iloc[-1])
        prev_high = val(recent["High"].iloc[:-3].max())
        prev_low = val(recent["Low"].iloc[:-3].min())
        if close > prev_high: return "BULLISH BOS"
        elif close < prev_low: return "BEARISH BOS"
        return "NO BOS"
    except: return "ERROR"

def get_atr(df, window=14):
    """Wilder ATR — pandas only (no `ta` package; builds reliably on Android/p4a)."""
    try:
        high = df["High"].astype(float)
        low = df["Low"].astype(float)
        close = df["Close"].astype(float)
        prev_close = close.shift(1)
        tr = pd.concat(
            [
                high - low,
                (high - prev_close).abs(),
                (low - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        atr = tr.ewm(alpha=1.0 / window, adjust=False).mean()
        return val(atr.iloc[-1])
    except Exception:
        return 0.0

def confirmation(df):
    try:
        last = df.iloc[-1]
        openp = val(last["Open"])
        close = val(last["Close"])
        high = val(last["High"])
        low = val(last["Low"])
        rng = high - low
        if rng == 0:
            return "NO CONFIRMATION"
        body = abs(close - openp) / rng
        if body > 0.65:
            return "BULLISH CONFIRMATION" if close > openp else "BEARISH CONFIRMATION"
        return "WEAK CANDLE"
    except Exception:
        return "NO CONFIRMATION"

def clean_levels(levels, distance):
    levels = sorted(levels)
    cleaned = []
    for level in levels:
        if not cleaned:
            cleaned.append(level)
        elif abs(level - cleaned[-1]) > distance:
            cleaned.append(level)
    return cleaned

def daily_range(df):
    try:
        daily = df.tail(96)
        high = val(daily["High"].max())
        low = val(daily["Low"].min())
        rng = high - low
        eq = low + (rng / 2)
        return high, low, rng, (eq, high), (low, eq), eq
    except: return 0,0,0,(0,0),(0,0),0

def liquidity(df):
    """Quant v5.2: external + internal liquidity with ATR touch filter."""
    try:
        recent = df.tail(150)
        highs = recent["High"].values
        lows = recent["Low"].values
        current = val(recent["Close"].iloc[-1])
        atr = get_atr(df)
        if atr <= 0:
            return [], [], [], []

        external_sell = []
        external_buy = []
        internal_sell = []
        internal_buy = []

        for i in range(5, len(recent) - 5):
            high = highs[i]
            low = lows[i]

            if high > max(highs[i - 4 : i]) and high > max(highs[i + 1 : i + 5]):
                touches = sum(1 for h in highs if abs(h - high) < atr * 0.10)
                if touches >= 3 and high > current:
                    external_sell.append(high)

            if low < min(lows[i - 4 : i]) and low < min(lows[i + 1 : i + 5]):
                touches = sum(1 for lo in lows if abs(lo - low) < atr * 0.10)
                if touches >= 3 and low < current:
                    external_buy.append(low)

        local_highs = highs[-30:]
        local_lows = lows[-30:]

        for h in local_highs:
            if h > current and h < current + (atr * 3):
                internal_sell.append(h)

        for lo in local_lows:
            if lo < current and lo > current - (atr * 3):
                internal_buy.append(lo)

        external_sell = clean_levels(external_sell, atr * 0.25)[-6:]
        external_buy = clean_levels(external_buy, atr * 0.25)[:6]
        internal_sell = clean_levels(internal_sell, atr * 0.15)[:5]
        internal_buy = clean_levels(internal_buy, atr * 0.15)[-5:]

        return external_sell, external_buy, internal_sell, internal_buy
    except Exception:
        return [], [], [], []

def sweeps(df, sell_liq, buy_liq):
    """Quant v5.2 sweeps: body filter + candle direction vs liquidity."""
    signals = []
    try:
        last = df.iloc[-1]
        high = val(last["High"])
        low = val(last["Low"])
        close = val(last["Close"])
        openp = val(last["Open"])
        rng = high - low
        if rng == 0:
            return []
        body = abs(close - openp) / rng

        for level in sell_liq:
            if (
                high > level
                and close < level
                and close < openp
                and body > 0.50
            ):
                signals.append(f"SELL SWEEP @ {level:.2f}")

        for level in buy_liq:
            if (
                low < level
                and close > level
                and close > openp
                and body > 0.50
            ):
                signals.append(f"BUY SWEEP @ {level:.2f}")
    except Exception:
        pass
    return signals

def session_liquidity(df):
    try:
        recent = df.tail(96)
        return val(recent["High"].max()), val(recent["Low"].min())
    except Exception:
        return 0.0, 0.0

# =========================================================
# MAIN APP CLASS
# =========================================================
class QadraxApp(MDApp):
    dashboard_text = StringProperty("Initializing Engine...")
    mute = BooleanProperty(False)
    vibration_enabled = BooleanProperty(True)
    popup_enabled = BooleanProperty(True)
    alert_duration = NumericProperty(5)
    # Khali = Android par phone ki default ringtone (jnius). CUSTOM se file set hoti hai.
    sound_path = StringProperty("")
    use_default_phone_ringtone = BooleanProperty(True)
    _android_ringtone_ref = None

    def build(self):
        self.theme_cls.theme_style = "Dark"
        Clock.schedule_interval(self.analyze_market, REFRESH_SECONDS)
        # Pehli baar thora late start karte hain taake UI load ho jaye
        Clock.schedule_once(self.analyze_market, 2)
        return Builder.load_string(KV)

    def pick_sound(self):
        try:
            filechooser.open_file(on_selection=self._on_sound_select, filters=[("Audio", "*.mp3", "*.wav")])
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
            ltf, h1df, h4df = get_data(LTF), get_data(H1), get_data(H4)
            if ltf is None or h1df is None or h4df is None:
                self.dashboard_text = "CONNECTION ERROR: Check Internet"
                return

            current = val(ltf["Close"].iloc[-1])
            h1 = structure(h1df)
            h4 = structure(h4df)

            if h1 == h4 and h1 != "RANGE":
                alignment = f"ALIGNED ({h1})"
            else:
                alignment = "NOT ALIGNED"

            bos = detect_bos(ltf)
            confirm = confirmation(ltf)

            (
                sell_external,
                buy_external,
                sell_internal,
                buy_internal,
            ) = liquidity(ltf)

            active_sweeps = sweeps(ltf, sell_external, buy_external)

            # Alerts — same rules as PC tkinter
            if bos != last_bos_alert:
                if bos == "BULLISH BOS":
                    self.trigger_alert(
                        "BULLISH BOS", "BUY continuation possible"
                    )
                    last_bos_alert = bos
                elif bos == "BEARISH BOS":
                    self.trigger_alert(
                        "BEARISH BOS", "SELL continuation possible"
                    )
                    last_bos_alert = bos

            if active_sweeps:
                latest = active_sweeps[-1]
                if latest != last_sweep_alert:
                    self.trigger_alert("LIQUIDITY SWEEP", latest)
                    last_sweep_alert = latest

            d_high, d_low, d_range, premium, discount, eq = daily_range(ltf)
            london_high, london_low = session_liquidity(ltf)

            probability = 50
            if alignment.startswith("ALIGNED"):
                probability += 10
            if "BOS" in bos:
                probability += 10
            if "CONFIRMATION" in confirm:
                probability += 10
            if active_sweeps:
                probability += 5
            probability = min(probability, 90)

            if h1 == "BULLISH" and h4 == "BULLISH":
                trade = "BUY"
            elif h1 == "BEARISH" and h4 == "BEARISH":
                trade = "SELL"
            else:
                trade = "WAIT"

            def lines_block(title, levels, empty_msg):
                s = f"\n{'='*18}\n{title}\n{'='*18}\n"
                if levels:
                    for x in levels:
                        s += f"• {x:.2f}\n"
                else:
                    s += empty_msg + "\n"
                return s

            out = f"""
QADRAX ENGINE v5.2 FULL
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*18}
CURRENT PRICE
{'='*18}
{current:.2f}

{'='*18}
H1 STRUCTURE
{'='*18}
{h1}

H4 STRUCTURE:
{h4}

MTF ALIGNMENT:
{alignment}

BOS:
{bos}

CONFIRMATION:
{confirm}

{'='*18}
FINAL TRADE
{'='*18}
{trade}

PROBABILITY:
{probability}%

{'='*18}
DAILY RANGE
{'='*18}
HIGH: {d_high:.2f}
LOW: {d_low:.2f}
RANGE: {d_range:.2f}
"""
            out += lines_block(
                "EXTERNAL SELL SIDE LIQUIDITY",
                sell_external,
                "NO SELL LIQUIDITY",
            )
            out += lines_block(
                "EXTERNAL BUY SIDE LIQUIDITY",
                buy_external,
                "NO BUY LIQUIDITY",
            )
            out += lines_block(
                "INTERNAL SELL SIDE LIQUIDITY",
                sell_internal,
                "NO INTERNAL SELL LIQUIDITY",
            )
            out += lines_block(
                "INTERNAL BUY SIDE LIQUIDITY",
                buy_internal,
                "NO INTERNAL BUY LIQUIDITY",
            )

            out += f"\n{'='*18}\nACTIVE SWEEPS\n{'='*18}\n"
            if active_sweeps:
                for s_sig in active_sweeps:
                    out += f"• {s_sig}\n"
            else:
                out += "NO ACTIVE SWEEP\n"

            out += f"""
{'='*18}
PREMIUM ZONE
{'='*18}
{premium[0]:.2f} → {premium[1]:.2f}

DISCOUNT ZONE:
{discount[0]:.2f} → {discount[1]:.2f}

EQUILIBRIUM:
{eq:.2f}

{'='*18}
SESSION LIQUIDITY
{'='*18}
LONDON HIGH: {london_high:.2f}
LONDON LOW: {london_low:.2f}

{'='*18}
PRO NOTES
{'='*18}
• External liquidity = main targets
• Internal liquidity = inducement
• Trade with HTF alignment
• Avoid equilibrium entries
• Wait for BOS + confirmation
• Risk management mandatory
"""
            self.dashboard_text = out.strip()
        except Exception as e:
            self.dashboard_text = f"CRITICAL ERROR:\n{e}"

    def trigger_alert(self, title, msg):
        if self.mute: return
        try:
            # FIX: Android me vibrate float nahi integer milliseconds leta hai (0.5 se crash hota tha, ab 500ms kiya hai)
            if self.vibration_enabled: 
                try:
                    vibrator.vibrate(500 if kv_platform == "android" else 0.5)
                except:
                    pass
                    
            notification.notify(title=title, message=msg, timeout=int(self.alert_duration))
            if self.popup_enabled:
                p = Popup(title=title, content=Label(text=msg), size_hint=(0.8, 0.3))
                p.open()
                Clock.schedule_once(lambda dt: p.dismiss(), self.alert_duration)
            self._play_alert_sound()
        except Exception as e: 
            print(f"Alert Trigger Error: {e}")

    def _stop_active_android_ringtone(self):
        rt = getattr(self, "_android_ref", None)
        if not rt:
            return
        try:
            if rt.isPlaying():
                rt.stop()
        except Exception:
            pass
        self._android_ref = None

    def _play_android_default_ringtone(self):
        try:
            from jnius import autoclass
            self._stop_active_android_ringtone()
            
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            RingtoneManager = autoclass("android.media.RingtoneManager")
            
            # FIX: Android 14/15 framework crash fix
            activity = PythonActivity.mActivity
            uri = RingtoneManager.getActualDefaultRingtoneUri(
                activity, RingtoneManager.TYPE_NOTIFICATION # Notification sound is safer than TYPE_RINGTONE
            )
            if uri is None:
                return
            rt = RingtoneManager.getRingtone(activity, uri) # Directly use activity as context
            if not rt:
                return
            self._android_ref = rt
            rt.play()
            Clock.schedule_once(
                lambda dt: self._stop_active_android_ringtone(),
                float(self.alert_duration),
            )
        except Exception as e:
            print(f"Default ringtone: {e}")

    def _play_alert_sound(self):
        if kv_platform == "android":
            if self.use_default_phone_ringtone:
                self._play_android_default_ringtone()
                return
            if self.sound_path and os.path.isfile(self.sound_path):
                s = SoundLoader.load(self.sound_path)
                if s:
                    s.play()
            return
        if self.sound_path and os.path.isfile(self.sound_path):
            s = SoundLoader.load(self.sound_path)
            if s:
                s.play()

if __name__ == "__main__":
    QadraxApp().run()