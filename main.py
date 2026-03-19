# ================= SMART SPOILAGE MONITOR — POLISHED =================

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading, time, csv, os, statistics
from collections import deque
from datetime import datetime

from src.prediction import predict_spoilage
from src.fetch_sensor import open_serial, get_sensor_data

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


PORT = "COM4"
ROLLING_WINDOW = 20
MAX_POINTS = 60
CSV_FILE = "dataset.csv"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SpoilageApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Smart Spoilage Monitor")
        self.geometry("1200x720")

        self.serial = None
        self.running = True
        self.logging_enabled = False
        self.manual_label = "Good"

        self.fruit_var = tk.StringVar(value="Banana")
        self.graph_mode = tk.StringVar(value="Combined")

        self.buffer = deque(maxlen=ROLLING_WINDOW)
        self.log_buffer = deque(maxlen=5)

        self.temp_hist = deque(maxlen=MAX_POINTS)
        self.hum_hist = deque(maxlen=MAX_POINTS)
        self.light_hist = deque(maxlen=MAX_POINTS)
        self.risk_hist = deque(maxlen=MAX_POINTS)

        self._ensure_csv_header()
        self._build_ui()
        self._connect_serial()

        # overlay state at startup
        if not self.logging_enabled:
            self.after(200, self._refresh_overlay)

        # graceful close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        threading.Thread(target=self.update_loop, daemon=True).start()

    # ================= CSV =================
    def _ensure_csv_header(self):
        if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
            with open(CSV_FILE, "w", newline="") as f:
                csv.writer(f).writerow(
                    ["timestamp","fruit","temperature","humidity","light","manual_label"]
                )

    # ================= UI =================
    def _build_ui(self):

        header = ctk.CTkFrame(self, height=60)
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(header, text="SMART SPOILAGE MONITOR",
                     font=("Segoe UI", 20, "bold")).pack(side="left", padx=15)

        self.log_switch = ctk.CTkSwitch(header, text="CSV Logging",
                                        command=self.toggle_logging)
        self.log_switch.pack(side="right", padx=20)

        ctk.CTkOptionMenu(self,
                          values=["Banana","Tomato","Orange","Pineapple"],
                          variable=self.fruit_var).pack(pady=5)

        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.live_tab = tabs.add("Live")
        self.log_tab = tabs.add("Logging")

        self._build_live_tab()
        self._build_log_tab()

    # ================= LIVE TAB =================
    def _build_live_tab(self):

        top = ctk.CTkFrame(self.live_tab)
        top.pack(fill="x", pady=5)

        ctk.CTkLabel(top, text="Graph Mode:").pack(side="left", padx=10)
        ctk.CTkOptionMenu(top,
                          values=["Combined","Separate","None"],
                          variable=self.graph_mode,
                          command=lambda _: self._layout_live()).pack(side="left")

        self.content = ctk.CTkFrame(self.live_tab)
        self.content.pack(fill="both", expand=True)

        self.cards = ctk.CTkFrame(self.content)
        self.cards.pack(fill="x", pady=10)

        self.sensor_card = ctk.CTkFrame(self.cards, corner_radius=14)
        self.sensor_card.pack(side="left", expand=True, fill="both", padx=6, pady=4)

        self.pred_card = ctk.CTkFrame(self.cards, corner_radius=14)
        self.pred_card.pack(side="left", expand=True, fill="both", padx=6, pady=4)

        self.sensor_label = ctk.CTkLabel(self.sensor_card,
            text="Temp --\nHumidity --\nLight --",
            font=("Segoe UI",17,"bold"), justify="left")
        self.sensor_label.pack(anchor="w", padx=20, pady=20)

        self.pred_label = ctk.CTkLabel(self.pred_card,
            text="Status --",
            font=("Segoe UI",17,"bold"), justify="left")
        self.pred_label.pack(anchor="w", padx=20, pady=20)

        self.graph_frame = ctk.CTkFrame(self.content)
        self.graph_frame.pack(fill="both", expand=True)

        self.fig = Figure(figsize=(5,4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _layout_live(self):
        if self.graph_mode.get() == "None":
            self.graph_frame.pack_forget()
            self.cards.pack(fill="both", expand=True)
        else:
            self.cards.pack(fill="x")
            self.graph_frame.pack(fill="both", expand=True)

    # ================= LOG TAB =================
    def _build_log_tab(self):

        container = ctk.CTkFrame(self.log_tab)
        container.place(relx=0.5, rely=0.5, anchor="center")

        self.good_btn = ctk.CTkButton(container, text="Mark GOOD",
                                      command=lambda: self.set_manual_label("Good"))
        self.good_btn.grid(row=6, column=2, padx=10, pady=10)

        self.bad_btn = ctk.CTkButton(container, text="Mark BAD",
                                     command=lambda: self.set_manual_label("Bad"))
        self.bad_btn.grid(row=6, column=3, padx=10, pady=10)

        headers = ["Temp","Humidity","Light","Label"]
        for i,h in enumerate(headers):
            ctk.CTkLabel(container, text=h, font=("Segoe UI",13,"bold")).grid(
                row=0, column=i, padx=12, pady=6)

        self.log_rows = []
        for r in range(5):
            row_cells = []
            for c in range(4):
                lbl = ctk.CTkLabel(container, text="--", width=80)
                lbl.grid(row=r+1, column=c, padx=8, pady=3)
                row_cells.append(lbl)
            self.log_rows.append(row_cells)

        self.overlay = ctk.CTkFrame(self.log_tab, fg_color="#111111")
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        ctk.CTkLabel(self.overlay, text="LOGGING DISABLED",
                     font=("Segoe UI",28,"bold")).pack(expand=True)

    def _refresh_overlay(self):
        if not self.logging_enabled:
            self.overlay.lift()

    # ================= SERIAL =================
    def _connect_serial(self):
        try:
            self.serial = open_serial(PORT)
        except Exception as e:
            print("Serial connection failed:", e)
            self.serial = None

    # ================= LOOP =================
    def update_loop(self):

        while self.running:

            if not self.serial:
                self._connect_serial()
                time.sleep(2)
                continue

            try:
                data = get_sensor_data(self.serial)
                if not data:
                    continue
            except Exception as e:
                print("Serial read error:", e)
                self.serial = None
                time.sleep(2)
                continue

            try:
                t = float(data.get("temperature",0))
                h = float(data.get("humidity",0))
                l = float(data.get("light",0))
            except:
                continue

            self.temp_hist.append(t)
            self.hum_hist.append(h)
            self.light_hist.append(l)
            self.buffer.append({"temperature":t,"humidity":h,"light":l})

            avg = {
                "temperature": statistics.mean(x["temperature"] for x in self.buffer),
                "humidity": statistics.mean(x["humidity"] for x in self.buffer),
                "light": statistics.mean(x["light"] for x in self.buffer),
            }

            res = predict_spoilage(avg, self.fruit_var.get())
            self.risk_hist.append(float(res["spoilage_risk"]))

            # THREAD-SAFE GUI UPDATE
            self.after(0, self._update_gui, t, h, l, res)

            if self.logging_enabled:
                self._log_data(data)

            time.sleep(0.5)

    # ================= GUI =================
    def _update_gui(self,t,h,l,res):

        self.sensor_label.configure(
            text=f"Temperature : {t:.1f} °C\nHumidity : {h:.1f} %\nLight : {int(l)} lx")

        self.pred_label.configure(
            text=f"Status : {res['status']}\nRisk : {res['spoilage_risk']} %\n"
                 f"Confidence : {res['confidence']} %\nShelf Life : {res['shelf_life']}")

        self._update_graph()

    # ================= GRAPH =================
    def _update_graph(self):

        mode = self.graph_mode.get()

        if mode == "None":
            return

        self.fig.clear()

        # -------- Light dynamic scaling --------
        if len(self.light_hist) > 0:
            max_light = max(self.light_hist)
            light_limit = ((int(max_light / 500) + 1) * 500)
        else:
            light_limit = 500

        # ---------- COMBINED GRAPH ----------
        if mode == "Combined":
            ax = self.fig.add_subplot(111)

            ax.plot(self.temp_hist, label="Temp °C", color="#ff7b72")
            ax.plot(self.hum_hist, label="Humidity %", color="#79c0ff")
            ax.plot(self.light_hist, label="Light Lux", color="#ffd866")
            ax.plot(self.risk_hist, label="Risk %", color="#ff4d6d")

            # Axis limits
            ax.set_ylim(bottom=-10, top=max(100, light_limit, 50))

            ax.legend()
            ax.grid(True)
            ax.set_title("Combined Sensor Graph")

        # ---------- SEPARATE GRAPHS ----------
        elif mode == "Separate":

            # Temperature
            ax1 = self.fig.add_subplot(411)
            ax1.plot(self.temp_hist, color="#ff7b72")
            ax1.set_ylim(-10, 50)
            ax1.set_title("Temperature (°C)")
            ax1.grid(True)

            # Humidity
            ax2 = self.fig.add_subplot(412)
            ax2.plot(self.hum_hist, color="#79c0ff")
            ax2.set_ylim(0, 100)
            ax2.set_title("Humidity (%)")
            ax2.grid(True)

            # Light (Dynamic)
            ax3 = self.fig.add_subplot(413)
            ax3.plot(self.light_hist, color="#ffd866")
            ax3.set_ylim(0, light_limit)
            ax3.set_title(f"Light (Lux) 0-{light_limit}")
            ax3.grid(True)

            # Risk
            ax4 = self.fig.add_subplot(414)
            ax4.plot(self.risk_hist, color="#ff4d6d")
            ax4.set_ylim(0, 100)
            ax4.set_title("Spoilage Risk (%)")
            ax4.grid(True)

        self.fig.tight_layout()
        self.canvas.draw()

    # ================= LOGGING =================
    def toggle_logging(self):

        self.logging_enabled = not self.logging_enabled

        if self.logging_enabled:
            self.overlay.place_forget()
            self.good_btn.configure(state="normal")
            self.bad_btn.configure(state="normal")
        else:
            self.overlay.place(relx=0,rely=0,relwidth=1,relheight=1)
            self.overlay.lift()
            self.good_btn.configure(state="disabled")
            self.bad_btn.configure(state="disabled")

    def _log_data(self,data):

        row = [data["temperature"], data["humidity"], data["light"], self.manual_label]
        self.log_buffer.append(row)

        with open(CSV_FILE,"a",newline="") as f:
            csv.writer(f).writerow(
                [datetime.now(), self.fruit_var.get(), *row]
            )

        for i in range(5):
            if i < len(self.log_buffer):
                r = self.log_buffer[i]
                for c in range(4):
                    self.log_rows[i][c].configure(text=str(r[c]))
            else:
                for c in range(4):
                    self.log_rows[i][c].configure(text="--")

    def set_manual_label(self,label):
        self.manual_label = label

    def on_close(self):
        self.running = False
        self.destroy()


if __name__ == "__main__":
    app = SpoilageApp()
    app.mainloop()
