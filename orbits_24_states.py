#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Зацикленная демонстрация 24 состояний.
Солнце в центре. Три орбиты: Венера, Земля, Марс.
Луна обращается вокруг Земли; в симметричных состояниях
Земля и Луна меняются ролями (Луна идёт по околосолнечной орбите,
Земля — вокруг Луны).
Кнопка "Следующее состояние" переключает состояние и показывает
дату и номер строки (1..24).
"""
import tkinter as tk
import math
from datetime import date, timedelta

W, H = 780, 840
CX, CY = W // 2, 380
R_VENUS, R_EARTH, R_MARS, R_MOON = 115, 205, 305, 36

# (Земля, Луна, Марс, Венера) — смещения в знаках от Солнца
STATES = {
    1:(6,6,6,0),  2:(6,6,6,1),  3:(6,6,6,-1), 4:(6,6,6,2),  5:(6,6,6,-2),
    6:(6,6,5,1),  7:(6,6,5,-1), 8:(6,6,7,2),  9:(6,6,7,-2),
    10:(6,6,4,0), 11:(6,6,4,2), 12:(6,6,4,-2),13:(6,6,8,2), 14:(6,6,8,-2),
    15:(6,5,6,0), 16:(6,4,6,0), 17:(6,3,6,0), 18:(6,2,6,0), 19:(6,1,6,0),
    20:(5,6,6,0), 21:(4,6,6,0), 22:(3,6,6,0), 23:(2,6,6,0), 24:(1,6,6,0),
}

# порядок состояний вдоль года (непрерывный переход по цепочкам)
SEQUENCE = [13,8,4,2,6,1,3,7,5,9,14,19,18,17,16,15,24,23,22,21,20,10,11,12]

START = date(2026, 1, 1)
STEP  = 365.2422 / 24          # ≈15.218 суток на состояние

COL = {'sun':'#F2B705', 'venus':'#E07B1E', 'earth':'#2F6FD0',
       'mars':'#C0392B', 'moon':'#9AA0A6', 'orbit':'#D8DDE3'}


def pxy(ang_deg, r):
    a = math.radians(ang_deg)
    return CX + r * math.cos(a), CY - r * math.sin(a)


class App:
    def __init__(self, root):
        self.root = root
        root.title('24 состояния · Солнце в центре')
        self.canvas = tk.Canvas(root, width=W, height=H, bg='white')
        self.canvas.pack()
        self.idx = 0
        self.phase = 0.0
        tk.Button(root, text='Следующее состояние ▶', font=('Arial', 14),
                  command=self.next_state).pack(pady=8)
        self.animate()

    def next_state(self):
        self.idx = (self.idx + 1) % len(SEQUENCE)

    def animate(self):
        self.phase += 1.5
        self.draw()
        self.root.after(40, self.animate)

    def draw(self):
        c = self.canvas
        c.delete('all')
        for r in (R_VENUS, R_EARTH, R_MARS):
            c.create_oval(CX-r, CY-r, CX+r, CY+r, outline=COL['orbit'], width=2)

        c.create_oval(CX-16, CY-16, CX+16, CY+16, fill=COL['sun'], outline='')
        c.create_text(CX, CY+30, text='Солнце', fill='#555', font=('Arial', 10))

        state = SEQUENCE[self.idx]
        E, M, Ma, V = STATES[state]

        vx, vy = pxy(V*30, R_VENUS)
        c.create_oval(vx-9, vy-9, vx+9, vy+9, fill=COL['venus'], outline='')
        c.create_text(vx, vy-18, text='Венера', fill=COL['venus'],
                      font=('Arial', 10, 'bold'))

        mx, my = pxy(Ma*30, R_MARS)
        c.create_oval(mx-11, my-11, mx+11, my+11, fill=COL['mars'], outline='')
        c.create_text(mx, my-20, text='Марс', fill=COL['mars'],
                      font=('Arial', 10, 'bold'))

        if E == 6:
            hub, hub_delta, comp, comp_delta = 'earth', E, 'moon', M
        else:
            hub, hub_delta, comp, comp_delta = 'moon', M, 'earth', E

        hx, hy = pxy(hub_delta*30, R_EARTH)
        c.create_oval(hx-R_MOON, hy-R_MOON, hx+R_MOON, hy+R_MOON,
                      outline=COL['orbit'], dash=(2, 3))

        hr = 12 if hub == 'earth' else 8
        c.create_oval(hx-hr, hy-hr, hx+hr, hy+hr, fill=COL[hub], outline='')
        c.create_text(hx, hy-26,
                      text=('Земля' if hub == 'earth' else 'Луна') + ' — центр',
                      fill=COL[hub], font=('Arial', 9, 'bold'))

        cang = comp_delta*30 + self.phase
        px, py = hx + R_MOON*math.cos(math.radians(cang)), \
                 hy - R_MOON*math.sin(math.radians(cang))
        pr = 8 if comp == 'moon' else 12
        c.create_oval(px-pr, py-pr, px+pr, py+pr, fill=COL[comp], outline='')

        d = START + timedelta(days=round(self.idx*STEP))
        c.create_text(W//2, 30, text='Строка %d  ·  %s' % (state, d.strftime('%d.%m.%Y')),
                      font=('Arial', 18, 'bold'), fill='#222')
        c.create_text(W//2, 58, text='смещения (Земля, Луна, Марс, Венера) = %s'
                      % (STATES[state],), font=('Arial', 11), fill='#666')

        legend = [('Солнце', COL['sun']), ('Венера', COL['venus']),
                  ('Земля', COL['earth']), ('Марс', COL['mars']),
                  ('Луна', COL['moon'])]
        x = 40
        for name, col in legend:
            c.create_oval(x, H-40, x+14, H-26, fill=col, outline='')
            c.create_text(x+20, H-33, text=name, anchor='w',
                          fill='#444', font=('Arial', 11))
            x += 145


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
