import tkinter as tk  # Importăm biblioteca Tkinter pentru interfață grafică
from tkinter import ttk  # Importăm widget-uri mai moderne din Tkinter (buton, label, spinbox)
import random  # Importăm modulul random pentru generare de numere aleatorii

# ================= CONSTANTE =================
COLOR_MAP = {
    0: '#eeeeee',  # Culoare pentru celulele goale
    1: '#e74c3c',  # Culoare pentru bomboana roșie
    2: '#f39c12',  # Culoare pentru bomboana portocalie
    3: '#2ecc71',  # Culoare pentru bomboana verde
    4: '#3498db'   # Culoare pentru bomboana albastră
}

CELL_SIZE = 40  # Dimensiunea fiecărei celule în pixeli
PADDING = 6  # Spațiul dintre celule
SWAP_COLOR = 'white'   # Culoare pentru evidențierea celulelor mutate
MATCH_COLOR = '#3498db'  # Culoare pentru evidențierea match-urilor (albastru)

# ================= LOGICA =================
class Formation:
    def __init__(self, cells):
        self.cells = set(cells)  # Stocăm celulele care fac parte dintr-un match
        self.score = len(cells) * 10  # Scorul pentru această formație (10 puncte per celulă)

class Board:
    def __init__(self, rows, cols, seed=None):
        self.rows, self.cols = rows, cols  # Numărul de rânduri și coloane
        self.rng = random.Random(seed)  # Generator random, poate fi controlat cu seed
        # Creăm tabla inițială cu valori random între 1 și 4
        self.grid = [[self.rng.randint(1, 4) for _ in range(cols)] for _ in range(rows)]

    def in_bounds(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols  # Verificăm dacă coordonatele sunt valide

    def cell(self, r, c):
        return self.grid[r][c]  # Returnăm valoarea celulei la poziția (r, c)

    def swap(self, a, b):
        (r1, c1), (r2, c2) = a, b  # Destructurăm coordonatele celor două celule
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]  # Le schimbăm între ele

    def detect_formations(self):
        forms = []  # Lista de formații detectate
        # Detectăm match-uri orizontale
        for r in range(self.rows):
            c = 0
            while c < self.cols - 2:  # Verificăm cel puțin 3 celule
                v = self.grid[r][c]  # Valoarea bomboanei curente
                if v != 0 and self.grid[r][c+1] == v and self.grid[r][c+2] == v:
                    cells = [(r, c), (r, c+1), (r, c+2)]  # Începem o formație
                    c2 = c + 3
                    while c2 < self.cols and self.grid[r][c2] == v:
                        cells.append((r, c2))  # Adăugăm celulele adiționale
                        c2 += 1
                    forms.append(Formation(cells))  # Adăugăm formația în listă
                    c = c2  # Sărim peste formația deja detectată
                else:
                    c += 1
        # Detectăm match-uri verticale
        for c in range(self.cols):
            r = 0
            while r < self.rows - 2:
                v = self.grid[r][c]
                if v != 0 and self.grid[r+1][c] == v and self.grid[r+2][c] == v:
                    cells = [(r, c), (r+1, c), (r+2, c)]
                    r2 = r + 3
                    while r2 < self.rows and self.grid[r2][c] == v:
                        cells.append((r2, c))
                        r2 += 1
                    forms.append(Formation(cells))
                    r = r2
                else:
                    r += 1
        return forms  # Returnăm toate formațiile detectate

    def apply_eliminations(self, forms):
        for f in forms:
            for r, c in f.cells:
                self.grid[r][c] = 0  # Setăm celulele care fac parte din match la 0

    def apply_gravity_and_refill(self):
        for c in range(self.cols):
            write = self.rows - 1  # Începem de jos pentru "gravitație"
            for r in range(self.rows - 1, -1, -1):
                if self.grid[r][c] != 0:
                    self.grid[write][c] = self.grid[r][c]  # Mutăm bomboanele în jos
                    write -= 1
            for r in range(write, -1, -1):
                self.grid[r][c] = self.rng.randint(1, 4)  # Umplem golurile cu bomboane random

# ================= UI =================
class CandyUI:
    def __init__(self, root):
        self.root = root
        self.board = Board(11, 11)  # Creăm tabla de 11x11
        self.score = 0  # Scorul jucătorului
        self.swaps = 0  # Numărul de mutări efectuate
        self.running = False  # Flag pentru rularea automată
        self.swap_cells = set()  # Celulele evidențiate pentru mutare
        self.match_cells = set()  # Celulele evidențiate pentru match
        self.speed = 1400  # Viteza animației în ms

        # Frame pentru butoane și controale
        ctrl = ttk.Frame(root)
        ctrl.pack(pady=6)
        ttk.Button(ctrl, text="Play", command=self.start).pack(side='left')  # Buton Start
        ttk.Button(ctrl, text="Stop", command=self.stop).pack(side='left', padx=5)  # Buton Stop
        ttk.Label(ctrl, text="Speed (ms):").pack(side='left', padx=10)
        self.speed_var = tk.IntVar(value=self.speed)
        ttk.Spinbox(ctrl, from_=300, to=3000, increment=200, textvariable=self.speed_var, width=6).pack(side='left')
        self.status = ttk.Label(ctrl, text="")  # Label pentru scor și mutări
        self.status.pack(side='left', padx=20)

        w = 11 * (CELL_SIZE + PADDING) + PADDING  # Lățimea canvas-ului
        h = 11 * (CELL_SIZE + PADDING) + PADDING  # Înălțimea canvas-ului
        self.canvas = tk.Canvas(root, width=w, height=h, bg='white')  # Creăm canvas-ul
        self.canvas.pack()

        self.draw()  # Desenăm tabla inițial
        self.update_status()  # Afișăm scorul și mutările

    def start(self):
        self.running = True  # Activăm rularea automată
        self.loop()  # Începem bucla jocului

    def stop(self):
        self.running = False
        self.swap_cells.clear()  # Ștergem evidențierea mutărilor
        self.match_cells.clear()  # Ștergem evidențierea match-urilor
        self.draw()  # Redesenăm tabla

    def loop(self):
        if not self.running:
            return
        self.speed = max(200, int(self.speed_var.get()))  # Luăm viteza din spinbox, minim 200ms
        move = self.find_any_swap()  # Căutăm prima mutare validă
        if not move:
            self.running = False
            return
        a, b = move
        self.swap_cells = {a, b}  # Evidențiem mutarea
        self.draw()
        self.root.after(self.speed, lambda: self.apply_swap(a, b))  # Aplicăm swap-ul după delay

    def apply_swap(self, a, b):
        self.swap_cells.clear()  # Ștergem evidențierea
        self.board.swap(a, b)  # Aplicăm swap-ul pe tabla reală
        self.swaps += 1  # Creștem numărul de mutări
        self.draw()
        self.update_status()
        self.root.after(self.speed, self.resolve_step)  # Continuăm cu match-urile

    def resolve_step(self):
        forms = self.board.detect_formations()  # Detectăm formațiile
        if not forms:
            self.root.after(self.speed, self.loop)  # Dacă nu sunt match-uri, continuăm cu următoarea mutare
            return
        self.match_cells = set()
        for f in forms:
            self.match_cells |= f.cells  # Evidențiem toate celulele care fac match
        self.draw()
        self.root.after(self.speed, lambda: self.apply_forms(forms))  # Aplicăm eliminările

    def apply_forms(self, forms):
        self.score += sum(f.score for f in forms)  # Adăugăm scorul
        self.board.apply_eliminations(forms)  # Eliminăm bomboanele
        self.board.apply_gravity_and_refill()  # Gravitate + refill
        self.match_cells.clear()
        self.draw()
        self.update_status()
        self.root.after(self.speed, self.resolve_step)  # Continuăm cu următoarele match-uri

    def find_any_swap(self):
        for r in range(11):
            for c in range(11):
                for dr, dc in ((1, 0), (0, 1)):  # Verificăm sus-jos și stânga-dreapta
                    r2, c2 = r+dr, c+dc
                    if not self.board.in_bounds(r2, c2): continue
                    copy = Board(11, 11)
                    copy.grid = [row[:] for row in self.board.grid]  # Copiem tabla pentru simulare
                    copy.swap((r, c), (r2, c2))
                    if copy.detect_formations():  # Dacă swap-ul generează match
                        return (r, c), (r2, c2)  # Returnăm mutarea
        return None  # Nicio mutare validă găsită

    def draw(self):
        self.canvas.delete("all")  # Ștergem canvas-ul
        for r in range(11):
            for c in range(11):
                v = self.board.cell(r, c)  # Valoarea celulei
                x1 = PADDING + c * (CELL_SIZE + PADDING)
                y1 = PADDING + r * (CELL_SIZE + PADDING)
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
                outline, width = 'black', 2  # Contur standard
                if (r, c) in self.swap_cells:  # Evidențiere mutare
                    outline, width = SWAP_COLOR, 5
                elif (r, c) in self.match_cells:  # Evidențiere match
                    outline, width = MATCH_COLOR, 5
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_MAP[v], outline=outline, width=width)

    def update_status(self):
        self.status.config(text=f"Score: {self.score} | Swaps: {self.swaps}")  # Actualizăm scorul și mutările

# ================= MAIN =================
if __name__ == "__main__":
    root = tk.Tk()  # Creăm fereastra principală
    root.title("Candy Crush Simplified")  # Setăm titlul
    CandyUI(root)  # Inițializăm interfața
    root.mainloop()  # Pornim bucla principală Tkinter
