import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math
import wave
import struct
import os

# Инициализация параметров для звукового движка (генерация WAV во временную память)
SAMPLE_RATE = 44100

def generate_chord_wave(freqs, noise_level, duration=0.4):
    """Генерирует волновой файл чистого аккорда планет с подмешиванием шума кошки"""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    # Суммируем синусоиды планет (наш космический аккорд)
    signal = np.zeros_like(t)
    for f in freqs:
        if f > 0:
            signal += 0.3 * np.sin(2 * np.pi * f * t)
            
    # Добавляем "шипение кошки" (белый шум), зависящее от ошибки дискретизации матрицы
    if noise_level > 0.01:
        noise = (np.random.rand(len(t)) * 2 - 1) * (noise_level * 0.4)
        signal += noise
        
    # Нормализация
    signal = signal / np.max(np.abs(signal) if np.max(np.abs(signal)) > 0 else 1)
    audio_data = struct.pack('<' + 'h' * len(signal), *(np.int16(signal * 32767)))
    
    filename = "temp_chord.wav"
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(audio_data)
    return filename

class OrbitalSynthApp:
    # ... внутри класса OrbitalSynthApp ...
    def on_closing(self):
        # 1. Закрываем все фигуры Matplotlib, чтобы освободить память
        plt.close("all")

        # 2. Останавливаем главный цикл Tkinter и уничтожаем окно
        root.quit()  # Останавливает mainloop
        root.destroy()  # Удаляет виджеты из памяти

    def __init__(self, root):
        self.root = root
        self.root.title("Орбитальный Лиссажу-Синтезатор Аккордов")
        # Назначаем функцию, которая выполнится при нажатии на "крестик" окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Физические базовые параметры (усредненные частоты)
        self.days = 0
        
        # Настройка интерфейса (Слайдеры)
        control_frame = ttk.Frame(root, padding="10")
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(control_frame, text="УПРАВЛЕНИЕ ОРБИТАЛЬНЫМ АККОРДОМ", font=('Arial', 10, 'bold')).pack(pady=10)
        
        # Слайдер Времени (Проход по аналемме)
        ttk.Label(control_frame, text="Календарный день (сдвиг по петле):").pack(anchor=tk.W)
        self.time_slider = ttk.Scale(control_frame, from_=0, to=780, orient=tk.HORIZONTAL, command=self.update_plot)
        self.time_slider.pack(fill=tk.X, pady=5)
        
        # Слайдер разрешения матрицы возмущений (3х3 ... 1х1)
        ttk.Label(control_frame, text="Разрешение матрицы (шаг усреднения):").pack(anchor=tk.W)
        self.matrix_slider = ttk.Scale(control_frame, from_=1, to=10, orient=tk.HORIZONTAL, command=self.update_plot)
        self.matrix_slider.set(3) # по дефолту наша матрица 3х3
        self.matrix_slider.pack(fill=tk.X, pady=5)
        
        # Кнопка прослушивания аккорда
        self.sound_btn = ttk.Button(control_frame, text="🔊 Слушать звук траектории", command=self.play_sound)
        self.sound_btn.pack(pady=20, fill=tk.X)
        
        # Вывод текущих параметров теории карт
        self.info_text = tk.StringVar()
        ttk.Label(control_frame, textvariable=self.info_text, justify=tk.LEFT).pack(pady=10, anchor=tk.W)
 

        # 1. Сначала объявляем переменные со значением None
#        self.ax1 = None
#        self.ax2 = None

#        # 2. Только потом создаем графический блок Matplotlib       
        # Графический блок Matplotlib
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.update_plot()
        
    def calculate_positions(self, t, matrix_res):
        # Периоды обращения (Земля ~365 дней, Марс ~687 дней)
        # Получаем углы средних аномалий
        w_earth = 2 * np.pi / 365.25
        w_mars = 2 * np.pi / 686.98
        
        # Положение Земли (считаем орбиту почти круговой для простоты проекции аналеммы)
        r_earth = 1.0
        x_e = r_earth * np.cos(w_earth * t)
        y_e = r_earth * np.sin(w_earth * t)
        
        # Эллиптическая орбита Марса (эксцентриситет e=0.093)
        e_mars = 0.093
        a_mars = 1.524
        
        # Средняя аномалия Марса
        M_m = w_mars * t
        # Приближенное уравнение Кеплера (первые гармоники синусоиды на прямой)
        E_m = M_m + e_mars * np.sin(M_m) + (e_mars**2 / 2) * np.sin(2 * M_m)
        
        x_m = a_mars * (np.cos(E_m) - e_mars)
        y_m = a_mars * np.sqrt(1 - e_mars**2) * np.sin(E_m)
        
        # Имитируем ошибку дискретизации матрицы 3х3:
        # Чем грубее шаг матрицы (низкий matrix_res), тем сильнее накапливается фазовый шум ("шипение")
#        error_factor = math.abs(3 - matrix_res) / 10.0
        error_factor = abs(3 - matrix_res) / 10.0
        noise_out = math.sin(t * 0.05) * error_factor
        
        return x_e, y_e, x_m, y_m, noise_out

    def update_plot(self, *args):
        # Проверяем, созданы ли оси. Если нет — выходим из метода
        if not hasattr(self, "ax1") or not hasattr(self, "ax2"):
            return
        t = self.time_slider.get()
        m_res = round(self.matrix_slider.get())
        
        x_e, y_e, x_m, y_m, error = self.calculate_positions(t, m_res)
        
        # 1. Левый график: Орбитальный аккорд (Вид сверху)
        # 1. Сначала объявляем переменные со значением None
#        self.ax1 = None
#        self.ax2 = None
        self.ax1.clear()
#        self.ax2.clear()
        self.ax1.plot(0, 0, 'yo', markersize=10, label="Солнце")
        
        # Рисуем орбиты
        t_arr = np.linspace(0, 687, 200)
        xe_arr, ye_arr, xm_arr, ym_arr, _ = zip(*[self.calculate_positions(ti, m_res) for ti in t_arr])
        self.ax1.plot(xe_arr, ye_arr, 'b--', alpha=0.5)
        self.ax1.plot(xm_arr, ym_arr, 'r--', alpha=0.5)
        
        # Текущие положения планет
        self.ax1.plot(x_e, y_e, 'bo', label="Земля")
        self.ax1.plot(x_m, y_m, 'ro', label="Марс")
        # Луч зрения (обратная трассировка)
        self.ax1.plot([x_e, x_m], [y_e, y_m], 'g-', alpha=0.7, label="Луч аналеммы")
        
        self.ax1.set_xlim(-2, 2)
        self.ax1.set_ylim(-2, 2)
        self.ax1.set_aspect('equal')
        self.ax1.set_title("Орбиты и Взаимный Семплинг")
        self.ax1.legend(loc="upper right")
        
        # 2. Правый график: Наблюдаемая с Земли Аналемма Марса (Лиссажу-проекция)
        self.ax2.clear()
        
        # Строим полную петлю аналеммы за синодический период (~780 дней)
        t_loop = np.linspace(0, 780, 300)
        loop_x = []
        loop_y = []
        for tl in t_loop:
            xe_l, ye_l, xm_l, ym_l, _ = self.calculate_positions(tl, m_res)
            # Вектор направления от Земли на Марс (Телесный угол зрения)
            dx = xm_l - xe_l
            dy = ym_l - ye_l
            distance = np.sqrt(dx**2 + dy**2)
            # Геоцентрическая долгота (угол петли Лиссажу)
            longi = np.arctan2(dy, dx)
            loop_x.append(longi)
            loop_y.append(1.0 / distance) # Видимый размер/блеск как вторая координата аналеммы
            
        self.ax2.plot(loop_x, loop_y, 'g-', label="Петля Аналеммы Марса")
        
        # Текущая точка на аналемме
        dx_c = x_m - x_e
        dy_c = y_m - y_e
        dist_c = np.sqrt(dx_c**2 + dy_c**2)
        curr_longi = np.arctan2(dy_c, dx_c)
        self.ax2.plot(curr_longi, 1.0 / dist_c, 'ro', markersize=8, label="Марс сегодня")
        
        self.ax2.set_title("Фигура Лиссажу (Проекция с Земли)")
        self.ax2.set_xlabel("Угол обзора (Долгота)")
        self.ax2.set_ylabel("Видимый блеск (1/Дистанция)")
        self.ax2.legend()
        
        # Обновление инфотекста
        self.info_text.set(
            f"Текущий день: {int(t)}\n"
            f"Разрешение сетки: {m_res}x{m_res}\n"
            f"Накопленный фазовый шум: {abs(error):.4f}\n"
            f"Статус аккорда: {'⚠️ ШИПЕНИЕ КОШКИ' if abs(error) > 0.05 else '🎵 КРИСТАЛЬНЫЙ СТРОЙ'}"
        )
        
        self.fig.tight_layout()
        self.canvas.draw()
        
    def play_sound(self):
        """Переводит текущие орбитальные частоты в звуковой спектр"""
        t = self.time_slider.get()
        m_res = round(self.matrix_slider.get())
        _, _, _, _, error = self.calculate_positions(t, m_res)
        
        # Транслируем "среднее движение" в слышимые звуковые ноты ноты Марс 243, Юпитер 216
        # Базовая частота Земли (Тоника) = 220 Гц (Нота Ля)
        # Марс движется медленнее, его частота в аккорде пропорциональна орбитальной
        freq_earth = 220.0
        freq_mars = 220.0 * (365.25 / 686.98) # Квинта/Кварта в зависимости от нелинейности
        freq_jupiter = 220.0 * (365.25 / 4332.59) # Глубокий бас
        
        # Уровень шума кошки зависит от того, насколько мы ушли от идеальной матрицы 3х3
        noise_level = abs(error)
        
        # Генерация и воспроизведение
        wav_file = generate_chord_wave([freq_earth, freq_mars, freq_jupiter], noise_level)

        # Воспроизведение в зависимости от ОС
        if os.name == 'nt': 
            # Windows
            import winsound
            winsound.PlaySound(wav_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif os.name == 'posix': 
            # macOS / Linux
            os.system(f"afplay {wav_file} &" if sys.platform == "darwin" else f"aplay {wav_file} &")

if __name__ == "__main__":
    import sys
    root = tk.Tk()
    app = OrbitalSynthApp(root)
    root.mainloop()

