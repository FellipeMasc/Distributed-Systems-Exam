import subprocess
import time
import threading
import tkinter as tk
from tkinter import ttk



def get_pods():
    try:
        out = subprocess.check_output(
            ["kubectl", "get", "pods", "-l", "run=php-apache", "--no-headers"],
            stderr=subprocess.STDOUT,
            text=True,
        )

        pods = []
        for line in out.splitlines():
            cols = line.split()

            name = cols[0]

            status = cols[2]

            pods.append((name, status))
        return pods
    except:
        return []


def get_hpa():
    """Retorna número de réplicas desejadas pelo HPA (coluna REPLICAS)"""
    try:
        out = subprocess.check_output(
            ["kubectl", "get", "hpa", "php-apache", "--no-headers"],
            stderr=subprocess.STDOUT,
            text=True,
        )

        cols = out.split()

        if len(cols) >= 2:
            replicas_col = cols[-2]
            if replicas_col.isdigit():
                return int(replicas_col)

        return None

    except Exception:
        return None



class MonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kubernetes Chaos Simulation Monitor - CSC-27")
        self.root.geometry("700x500")

        self.total_pods = tk.StringVar(value="0")
        self.running_pods = tk.StringVar(value="0")
        self.terminating_pods = tk.StringVar(value="0")
        self.dead_count = tk.StringVar(value="0")
        self.hpa_replicas = tk.StringVar(value="-")

        self.replicas_history = []

        ttk.Label(root, text="Painel de Simulação Kubernetes", font=("Segoe UI", 14, "bold")).pack(pady=10)

        frame = ttk.Frame(root)
        frame.pack()

        ttk.Label(frame, text="Total de Pods:", width=20).grid(row=0, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.total_pods).grid(row=0, column=1, sticky="w")

        ttk.Label(frame, text="Running:", width=20).grid(row=1, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.running_pods).grid(row=1, column=1, sticky="w")

        ttk.Label(frame, text="Terminating:", width=20).grid(row=2, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.terminating_pods).grid(row=2, column=1, sticky="w")

        ttk.Label(frame, text="Pods Mortos:", width=20).grid(row=3, column=0)
        ttk.Label(frame, textvariable=self.dead_count).grid(row=3, column=1)

        ttk.Label(frame, text="HPA réplicas desejadas:", width=20).grid(row=4, column=0)
        ttk.Label(frame, textvariable=self.hpa_replicas).grid(row=4, column=1)

        self.canvas = tk.Canvas(root, width=650, height=250, bg="white")
        self.canvas.pack(pady=15)

        self.stop_flag = False
        threading.Thread(target=self.update_loop, daemon=True).start()

    def update_loop(self):
        prev_pods = set()

        while not self.stop_flag:
            pods = get_pods()
            pod_names = set([p[0] for p in pods])

            dead_now = len(prev_pods - pod_names)
            if dead_now > 0:
                current = int(self.dead_count.get())
                self.dead_count.set(str(current + dead_now))

            prev_pods = pod_names

            running = sum(1 for _, st in pods if st == "Running")
            terminating = sum(1 for _, st in pods if st != "Running")

            self.total_pods.set(str(len(pods)))
            self.running_pods.set(str(running))
            self.terminating_pods.set(str(terminating))

            hpa = get_hpa()
            if hpa is not None:
                self.hpa_replicas.set(str(hpa))
                self.replicas_history.append(hpa)
                if len(self.replicas_history) > 40:
                    self.replicas_history.pop(0)

            self.draw_chart()
            
            time.sleep(1)

    def draw_chart(self):
        self.canvas.delete("all")

        data = self.replicas_history[-40:]

        h = 200
        w = 600
        margin_left = 30
        margin_bottom = 30
        
        self.canvas.create_line(margin_left, h, margin_left + w, h, fill="black", width=2)
        self.canvas.create_line(margin_left, h, margin_left, 0, fill="black", width=2)

        if len(data) < 2:
            return

        max_rep = max(data) + 1 if max(data) > 0 else 5

        step = max(1, int(max_rep / 5))
        for i in range(0, max_rep + 1, step):
             y_pos = h - (i / max_rep) * h
             self.canvas.create_text(margin_left - 5, y_pos, text=str(i), anchor="e", font=("Segoe UI", 8))
             self.canvas.create_line(margin_left - 2, y_pos, margin_left + 2, y_pos, fill="gray")

        self.canvas.create_text(margin_left + w/2, h + 15, text="Tempo (s)", font=("Segoe UI", 9))

        points = []
        for i, r in enumerate(data):
            x = margin_left + (i / (len(data) - 1)) * w
            y = h - (r / max_rep) * h
            points.append((x, y))

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]

            self.canvas.create_line(
                x1, y1, x2, y2,
                fill="#357DED",
                width=3,
                capstyle=tk.ROUND
            )

            if i == len(points) - 2:
                self.canvas.create_oval(
                    x2 - 4, y2 - 4, x2 + 4, y2 + 4,
                    fill="#357DED",
                    outline=""
                )

        self.canvas.create_text(
            325, 15,
            text="Histórico de réplicas (HPA)",
            font=("Segoe UI", 12, "bold")
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = MonitorGUI(root)
    root.mainloop()
