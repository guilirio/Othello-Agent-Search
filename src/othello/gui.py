"""Tkinter UI; model calls run on a copy of the game in a background thread."""
from copy import deepcopy
from dataclasses import asdict
import json
import os
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .game import Game
from .matches import make_agent


class OthelloApp:
    def __init__(self, root):
        self.root = root
        root.title("Othello Agent Search")
        root.configure(bg="#14221f")
        self.game, self.turns, self.agents = Game(), [], {}
        self.queue = Queue()
        self.generation, self.busy, self.paused = 0, False, True
        self.black = tk.StringVar(value="human")
        self.white = tk.StringVar(value="llm")
        self.model = tk.StringVar(value=os.getenv("OTHELLO_MODEL", "qwen2.5:3b"))
        self.status = tk.StringVar(value="Configure os jogadores e clique em Nova partida.")
        self.config = {1: "human", -1: "llm"}
        controls = ttk.Frame(root, padding=12)
        controls.pack(fill="x")
        for column, (label, variable) in enumerate((("Pretas", self.black), ("Brancas", self.white))):
            ttk.Label(controls, text=label).grid(row=0, column=column * 2, padx=4)
            ttk.Combobox(controls, textvariable=variable, values=("human", "llm", "heuristic", "random"),
                         state="readonly", width=12).grid(row=0, column=column * 2 + 1)
        ttk.Label(controls, text="Modelo Ollama").grid(row=1, column=0, pady=8)
        ttk.Entry(controls, textvariable=self.model, width=24).grid(row=1, column=1, columnspan=2)
        ttk.Button(controls, text="Nova partida", command=self.new_game).grid(row=2, column=0, padx=4)
        ttk.Button(controls, text="Pausar / continuar", command=self.toggle_pause).grid(row=2, column=1, padx=4)
        ttk.Button(controls, text="Exportar partida", command=self.export).grid(row=2, column=2, padx=4)
        body = ttk.Frame(root, padding=12)
        body.pack()
        self.canvas = tk.Canvas(body, width=496, height=496, bg="#14221f", highlightthickness=0)
        self.canvas.grid(row=0, column=0)
        self.canvas.bind("<Button-1>", self.click)
        self.log = tk.Text(body, width=48, height=28, wrap="word", state="disabled", font=("Segoe UI", 10))
        self.log.grid(row=0, column=1, padx=(12, 0))
        ttk.Label(root, textvariable=self.status, padding=12, wraplength=850).pack(fill="x")
        self.draw()
        root.after(100, self.poll)

    def new_game(self):
        self.generation += 1
        self.game, self.turns, self.agents = Game(), [], {}
        self.config = {1: self.black.get(), -1: self.white.get()}
        self.active_model = self.model.get().strip() or "qwen2.5:3b"
        self.busy, self.paused = False, False
        self.draw()
        self.root.after(100, self.advance)

    def toggle_pause(self):
        self.paused = not self.paused
        self.draw()
        if not self.paused:
            if not hasattr(self, "active_model"):
                self.new_game()
            else:
                self.advance()

    def draw(self):
        self.canvas.delete("all")
        legal = self.game.board.legal_moves(self.game.player)
        for r in range(8):
            for c in range(8):
                x, y = 24 + c * 56, 24 + r * 56
                self.canvas.create_rectangle(x, y, x + 56, y + 56, fill="#267259", outline="#164e3b")
                piece = self.game.board.cells[r * 8 + c]
                if piece:
                    self.canvas.create_oval(x + 7, y + 7, x + 49, y + 49,
                                            fill="#121817" if piece == 1 else "#f3f0e5", outline="#99b6a9")
                elif (r, c) in legal:
                    self.canvas.create_oval(x + 24, y + 24, x + 32, y + 32, fill="#9ed0ad", outline="")
        for i in range(8):
            self.canvas.create_text(52 + 56 * i, 12, text=chr(65 + i), fill="white")
            self.canvas.create_text(12, 52 + 56 * i, text=str(i + 1), fill="white")
        status = self.game.status()
        score = status["score"]
        if status["finished"]:
            label = {1: "Vitória das pretas", -1: "Vitória das brancas", 0: "Empate"}[status["winner"]]
        else:
            label = f"Vez das {'pretas' if self.game.player == 1 else 'brancas'} ({self.config[self.game.player]})"
            if self.paused:
                label += " • Pausado"
            elif self.busy:
                label += " • Agente analisando…"
        self.status.set(f"{label} | Pretas {score['black']} × {score['white']} Brancas")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        for event in self.game.history:
            move = event["move"]
            coordinate = f"{chr(65 + move[1])}{move[0] + 1}" if move is not None else "passe"
            side = "Pretas" if event["player"] == 1 else "Brancas"
            self.log.insert("end", f"{event['turn']}. {side}: {coordinate}\n{event['explanation']}\n\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def click(self, event):
        if self.busy or self.paused or self.game.board.terminal or self.config[self.game.player] != "human":
            return
        row, column = (event.y - 24) // 56, (event.x - 24) // 56
        try:
            self.game.apply((row, column), "Jogada humana.")
        except ValueError:
            return
        self.draw()
        self.root.after(100, self.advance)

    def advance(self):
        if self.busy or self.paused or self.game.board.terminal:
            return
        player = self.game.player
        if self.config[player] == "human":
            if not self.game.board.legal_moves(player):
                self.game.apply(None, "Passe obrigatório.")
                self.draw()
                self.root.after(300, self.advance)
            return
        self.busy = True
        snapshot, generation = deepcopy(self.game), self.generation
        name, model = self.config[player], self.active_model
        agent = self.agents.get(player)
        self.draw()

        def work():
            try:
                current_agent = agent or make_agent(name, seed=0 if player == 1 else 1, model=model)
                result = current_agent.take_turn(snapshot)
                self.queue.put((generation, snapshot, current_agent, result, None))
            except Exception as exc:
                self.queue.put((generation, snapshot, None, None, str(exc)))
        Thread(target=work, daemon=True).start()

    def poll(self):
        try:
            while True:
                generation, game, agent, result, error = self.queue.get_nowait()
                if generation != self.generation:
                    continue
                self.busy = False
                if error:
                    self.paused = True
                    self.draw()
                    self.status.set(f"Turno interrompido: {error}")
                else:
                    self.agents[result.event["player"]] = agent
                    self.game = game
                    self.turns.append(asdict(result))
                    self.draw()
                    self.root.after(350, self.advance)
        except Empty:
            pass
        self.root.after(100, self.poll)

    def export(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            try:
                with open(path, "w", encoding="utf-8") as stream:
                    json.dump({"black": self.config[1], "white": self.config[-1],
                               "model": getattr(self, "active_model", self.model.get()),
                               "status": self.game.status(), "history": self.game.history,
                               "turns": self.turns}, stream, ensure_ascii=False, indent=2)
            except OSError as exc:
                messagebox.showerror("Erro ao exportar", str(exc))


def launch():
    root = tk.Tk()
    OthelloApp(root)
    root.mainloop()
