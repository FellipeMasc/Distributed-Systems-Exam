import subprocess
import time
import threading
import tkinter as tk
from tkinter import ttk

# ================================
# Funções auxiliares
# ================================


def get_pods():
    try:
        out = subprocess.check_output(
            ["kubectl", "get", "pods", "-l", "app=php-apache", "--no-headers"],
            stderr=subprocess.STDOUT,
            text=True,
        )

        pods = []
        for line in out.splitlines():
            cols = line.split()

            # Nome do pod
            name = cols[0]

            # STATUS pode ser multi-palavra ("CrashLoopBackOff", "ContainerCreating", "Terminating", etc.)
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

        # Estrutura típica:
        # NAME  REF  TARGETS  MINPODS  MAXPODS  REPLICAS  AGE
        # REPLICAS é sempre a penúltima coluna (antes de AGE)
        if len(cols) >= 2:
            replicas_col = cols[-2]
            if replicas_col.isdigit():
                return int(replicas_col)

        return None

    except Exception:
        return None


# ================================
# Painel Tkinter
# ================================
class MonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kubernetes Chaos Simulation Monitor - CSC-27")
        self.root.geometry("700x500")

        # Variáveis do painel
        self.total_pods = tk.StringVar(value="0")
        self.running_pods = tk.StringVar(value="0")
        self.terminating_pods = tk.StringVar(value="0")
        self.dead_count = tk.StringVar(value="0")
        self.hpa_replicas = tk.StringVar(value="-")

        # Histórico (para gráfico simplificado)
        self.replicas_history = []

        # Labels
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

        # Canvas do gráfico
        self.canvas = tk.Canvas(root, width=650, height=250, bg="white")
        self.canvas.pack(pady=15)

        # Iniciar thread de atualização
        self.stop_flag = False
        threading.Thread(target=self.update_loop, daemon=True).start()

    # ============================================
    # Loop de atualização (roda a cada 1s no fundo)
    # ============================================
    def update_loop(self):
        prev_pods = set()  # para detectar pods removidos

        while not self.stop_flag:
            pods = get_pods()
            pod_names = set([p[0] for p in pods])

            # detecta pods mortos
            dead_now = len(prev_pods - pod_names)
            if dead_now > 0:
                current = int(self.dead_count.get())
                self.dead_count.set(str(current + dead_now))

            prev_pods = pod_names

            # status counts
            running = sum(1 for _, st in pods if st == "Running")
            terminating = sum(1 for _, st in pods if st != "Running")

            self.total_pods.set(str(len(pods)))
            self.running_pods.set(str(running))
            self.terminating_pods.set(str(terminating))

            # Atualizar HPA
            hpa = get_hpa()
            if hpa is not None:
                self.hpa_replicas.set(str(hpa))
                self.replicas_history.append(hpa)
                if len(self.replicas_history) > 40:
                    self.replicas_history.pop(0)

            # Atualizar gráfico
            self.draw_chart()
            
            time.sleep(1)

    # ============================================
    # Desenho do mini-gráfico (réplicas do HPA)
    # ============================================
    def draw_chart(self):
        self.canvas.delete("all")

        data = self.replicas_history[-40:]  # manter janela móvel

        if len(data) < 2:
            return

        h = 220
        w = 630
        max_rep = max(data) + 1

        # Normalização dos pontos
        points = []
        for i, r in enumerate(data):
            x = (i / (len(data) - 1)) * w
            y = h - (r / max_rep) * h
            points.append((x, y))

        # Desenhar linhas como animação autêntica
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]

            # criar efeito de deslizamento / fade-in
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill="#357DED",       # azul bonito
                width=3,
                capstyle=tk.ROUND
            )

            # animação sutil: ponto pulsante no final
            if i == len(points) - 2:
                self.canvas.create_oval(
                    x2 - 4, y2 - 4, x2 + 4, y2 + 4,
                    fill="#357DED",
                    outline=""
                )

        # Título do gráfico
        self.canvas.create_text(
            325, 15,
            text="Histórico de réplicas (HPA)",
            font=("Segoe UI", 12, "bold")
        )

# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    root = tk.Tk()
    app = MonitorGUI(root)
    root.mainloop()
