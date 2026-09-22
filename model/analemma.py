# analemma.py
# ==============================================================================
# НАЗНАЧЕНИЕ:
#   Расчёт и отрисовка аналеммы (траектории Солнца/планеты на небе в течение года)
#   с использованием wxPython и PyEphem.
#
# ЗАВИСИМОСТИ:
#   pip install wxPython ephem
#
# АВТОР: адаптировано под задачу интеграции в Tkinter-приложение
# ==============================================================================

import wx
from wx.lib.plot import PlotCanvas, PlotGraphics, PolyLine, PolyMarker
import math
import ephem
import datetime

# ------------------------------------------------------------------------------
# ГЛОБАЛЬНЫЕ НАСТРОЙКИ И НАЧАЛЬНЫЕ ДАННЫЕ
# ------------------------------------------------------------------------------
astro_str = "Sun"
astro_body = ephem.Sun()
observer = ephem.Observer()
observer.name = "Wichita Mountains"
observer.lon = '-98:31.92'
observer.lat = '34:44.64'
my_year = str(datetime.datetime.now().year)  # текущий год по умолчанию

# Массивы для выбора отображаемых часов и дней (1 — показывать, 0 — скрыть)
includeH = [0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0]  # по умолчанию полдень
show_allH = 0  # флаг «показать все часы» (переопределяет includeH)

includeD = [0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0]  # дни по умолчанию
show_allD = 0  # флаг «показать все дни» (переопределяет includeD)

deg_per_rad = 57.2957795  # перевод радиан в градусы

# ------------------------------------------------------------------------------
# ДЕМО-РАСЧЁТЫ ГЕОМЕТРИЧЕСКИХ ОБЪЕКТОВ (НЕ ВЛИЯЮТ НА АНАЛЕММУ)
# ------------------------------------------------------------------------------
# Эти формулы оставлены как демонстрационные примеры комбинаторики для многомерных тел.

# 1. Рёбра пентеракта (5-куба): 2^(n-k) * C(n,k), n=5, k=1
edges_penteract = (2**(5-1)) * 5  # 16 * 5 = 80

# 2. Трёхмерные грани (объёмы) 5-ортоплекса: 2^(k+1) * C(n, k+1), n=5, k=3
volumes_orthoplex = (2**4) * 5  # 16 * 5 = 80

# 3. Двумерные грани (k=2) у пентеракта и ортоплекса
faces2d_penteract = (2**3) * 10  # 8 * 10 = 80
faces2d_orthoplex = (2**3) * 10  # 8 * 10 = 80

print(f"Edges on Penteract: {edges_penteract}")
print(f"Volumes on 5-orthoplex: {volumes_orthoplex}")
print(f"2D faces on Penteract: {faces2d_penteract}")
print(f"2D faces on 5-orthoplex: {faces2d_orthoplex}")
print(f"Days in two sorokovniks: {2 * 40}")

# ------------------------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ПРОВЕРКИ ВВОДА
# ------------------------------------------------------------------------------
def is_int(s):
    """Проверяет, является ли строка целым числом."""
    try:
        int(s)
        return True
    except ValueError:
        return False

def is_float(s):
    """Проверяет, является ли строка числом с плавающей точкой."""
    try:
        float(s)
        return True
    except ValueError:
        return False

def is_valid_date(y, m, d):
    """Проверяет корректность даты (день/месяц/год)."""
    try:
        newDate = datetime.datetime(y, m, d)
        return True
    except ValueError:
        return False

# ------------------------------------------------------------------------------
# РАСЧЁТ КООРДИНАТ АНАЛЕММЫ
# ------------------------------------------------------------------------------
def analemma_xy_cable(date):
    """
    Экспериментальный расчёт координат с эвристическими поправками.
    Английские комментарии сохранены без изменений.
    """
    # 1. Базовый астрономический расчет
    adjtime = ephem.date(ephem.date(date) - float(observer.lon)*(12.0/math.pi)*ephem.hour)
    observer.date = adjtime
    astro_body.compute(observer)
    
    base_x = deg_per_rad * float(astro_body.az)
    base_y = deg_per_rad * float(astro_body.alt)
    
    # 2. Внедрение вашей эвристики: Коаксиальный волновой пробой
    t = float(ephem.date(date)) 
    
    # Эвристическая стоячая волна
    wave_core = math.sin(t * 2 * math.pi / 365.25) * 5.0
    wave_jet = math.sin(t * 2 * math.pi * 12.0) * math.cos(t * 2 * math.pi) * 2.0
    
    # 3. Модификация траектории
    mod_x = base_x + wave_core
    mod_y = base_y + wave_jet
    
    return (mod_x, mod_y)

def analemma_xy(date):
    """Стандартный расчёт азимута и высоты в градусах."""
    adjtime = ephem.date(ephem.date(date) - float(observer.lon)*(12.0/math.pi)*ephem.hour)
    observer.date = adjtime
    astro_body.compute(observer)
    x = deg_per_rad * float(astro_body.az)
    y = deg_per_rad * float(astro_body.alt)
    return (x, y)

# ------------------------------------------------------------------------------
# ОТРИСОВКА АНАЛЕММЫ (ГРУППА ТОЧЕК И ЛИНИЙ)
# ------------------------------------------------------------------------------
def drawAnalemma():
    """Формирует PlotGraphics-объект с точками аналеммы и вспомогательными линиями."""
    global my_year
    analemma_group = []
    data = []

    # Подготовка структуры данных: data[h] будет содержать список точек для часа h
    for i in range(25):
        data.append([])

    # Сбор данных по дням и часам
    for m in range(1, 13):
        for d in range(1, len(includeD)):
            if includeD[d] == 1 or show_allD == 1:
                if is_valid_date(int(my_year), m, d):
                    for h in range(len(includeH)):
                        if includeH[h] == 1 or show_allH == 1:
                            date_str = '{0:s}/{1:d}/{2:d} {3:d}:00'.format(my_year, m, d, h)
                            data[h].append(analemma_xy(date_str))

    # Создание маркеров для точек
    for h in range(len(includeH)):
        if includeH[h] == 1 or show_allH == 1:
            for j in range(len(data[h])):
                # Цвет зависит от высоты над горизонтом
                mycolor = "yellow" if data[h][j][1] > 0 else "blue"
                marker = PolyMarker(
                    data[h][j],
                    legend="{0:d}:00".format(h),
                    colour=mycolor,
                    marker='circle',
                    size=1
                )
                analemma_group.append(marker)

    # Вспомогательные линии сетки (меридианы и параллели)
    lines_data = [
        ((270, -90), (270, 90), 'black', 1),
        ((180, -90), (180, 90), 'black', 1),
        ((90, -90), (90, 90), 'black', 1),
        ((0, 45), (360, 45), 'black', 1),
        ((0, 0), (360, 0), 'black', 3),
        ((0, -45), (360, -45), 'black', 1),
    ]

    for p1, p2, color, width in lines_data:
        line = PolyLine([p1, p2], colour=color, width=width)
        analemma_group.append(line)

    # Формирование заголовка и подписей
    mylon = deg_per_rad * float(observer.lon)
    mylat = deg_per_rad * float(observer.lat)
    my_ns = "N" if mylat > 0 else "S"
    my_we = "W" if mylon < 0 else "E"

    mytitle = "{0:s} Analemma Plot for {1:.3f}{2:s} {3:.3f}{4:s}".format(
        my_year, abs(mylat), my_ns, abs(mylon), my_we
    )
    xDesc = "Direction [N=0, E=90, S=180, W=270] [Yellow = {0:s} above horizon, Blue = {0:s} below horizon]".format(astro_str)

    return PlotGraphics(analemma_group, mytitle, xDesc, "Elevation")

# ------------------------------------------------------------------------------
# КЛАСС ИНТЕРФЕЙСА (wx.Frame)
# ------------------------------------------------------------------------------
class MyGraph(wx.Frame):
    def __init__(self):
        """Инициализация окна графика и всех элементов управления."""
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Analemma Plot', size=(1024, 768))

        panel = wx.Panel(self, wx.ID_ANY)

        # Создание сайзеров (контейнеров для компоновки)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        checkSizer1 = wx.BoxSizer(wx.HORIZONTAL)
        checkSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        checkSizer3 = wx.BoxSizer(wx.HORIZONTAL)

        # Холст для отрисовки
        self.canvas = PlotCanvas(panel)
        self.canvas.SetBackgroundColour("GRAY")
        self.canvas.Draw(drawAnalemma(), xAxis=(0, 360), yAxis=(-90, 90))

        # Элементы управления: чекбоксы
        toggleShowAllD = wx.CheckBox(panel, label="Show All Days")
        toggleShowAllD.Bind(wx.EVT_CHECKBOX, self.onToggleShowAllD)
        toggleShowAllH = wx.CheckBox(panel, label="Show All Hours")
        toggleShowAllH.Bind(wx.EVT_CHECKBOX, self.onToggleShowAllH)

        # Радиокнопки для выбора небесного тела
        self.rb1 = wx.RadioButton(panel, -1, 'Sun', style=wx.RB_GROUP)
        self.rb2 = wx.RadioButton(panel, -1, 'Moon')
        self.rb3 = wx.RadioButton(panel, -1, 'Mercury')
        self.rb4 = wx.RadioButton(panel, -1, 'Venus')
        self.rb5 = wx.RadioButton(panel, -1, 'Mars')
        self.rb6 = wx.RadioButton(panel, -1, 'Jupiter')
        self.rb7 = wx.RadioButton(panel, -1, 'Saturn')
        self.rb8 = wx.RadioButton(panel, -1, 'Neptune')

        # Привязка событий к радиокнопкам
        radio_map = [
            ('Sun', self.rb1), ('Moon', self.rb2), ('Mercury', self.rb3),
            ('Venus', self.rb4), ('Mars', self.rb5), ('Jupiter', self.rb6),
            ('Saturn', self.rb7), ('Neptune', self.rb8)
        ]
        for body, rb in radio_map:
            rb.Bind(wx.EVT_RADIOBUTTON, lambda event, temp=body: self.doUpdateBody(event, temp))

        # Поля ввода и кнопка обновления
        self.text_ctrl_year = wx.TextCtrl(panel, -1, my_year)
        self.text_ctrl_lat = wx.TextCtrl(panel, -1, "{0:.3f}".format(float(observer.lat)*deg_per_rad))
        self.text_ctrl_lon = wx.TextCtrl(panel, -1, "{0:.3f}".format(float(observer.lon)*deg_per_rad))
        self.button_update = wx.Button(panel, -1, "Update Location/Year")
        wx.EVT_BUTTON(self, self.button_update.GetId(), self.doUpdateInfo)

        # Чекбоксы для часов (00–23)
        toggle = []
        mylabelH = ["{:02d}".format(i) for i in range(24)]

        for i in range(24):
            cb = wx.CheckBox(panel, label=mylabelH[i])
            if includeH[i] == 1 or show_allH == 1:
                cb.SetValue(True)
            cb.Bind(wx.EVT_CHECKBOX, lambda event, temp=mylabelH[i]: self.onToggleHour(event, temp))
            toggle.append(cb)

        # Компоновка элементов
        mainSizer.Add(self.canvas, 1, wx.EXPAND)

        checkSizer1.Add(self.text_ctrl_year, 0, wx.ALL, 5)
        checkSizer1.Add(self.text_ctrl_lat, 0, wx.ALL, 5)
        checkSizer1.Add(self.text_ctrl_lon, 0, wx.ALL, 5)
        checkSizer1.Add(self.button_update, 0, wx.ALL, 5)

        # Добавление радиокнопок в первый горизонтальный сайзер
        for rb in [self.rb1, self.rb2, self.rb3, self.rb4, self.rb5, self.rb6, self.rb7, self.rb8]:
            checkSizer1.Add(rb, 0, wx.ALL, 5)

        checkSizer2.Add(toggleShowAllD, 0, wx.ALL, 5)
        checkSizer3.Add(toggleShowAllH, 0, wx.ALL, 5)

        # Разделение чекбоксов часов на две строки (0–11 и 12–23)
        for i in range(0, 12):
            checkSizer2.Add(toggle[i], 0, wx.ALL, 5)
        for i in range(12, 24):
            checkSizer3.Add(toggle[i], 0, wx.ALL, 5)

        mainSizer.Add(checkSizer1)
        mainSizer.Add(checkSizer2)
        mainSizer.Add(checkSizer3)
        panel.SetSizer(mainSizer)

    def onToggleShowAllD(self, event):
        """Обработчик чекбокса «Показать все дни»."""
        global show_allD
        show_allD = 1 if show_allD == 0 else 0
        self.canvas.Clear()
        self.canvas.Draw(drawAnalemma(), xAxis=(0, 360), yAxis=(-90, 90))

    def onToggleShowAllH(self, event):
        """Обработчик чекбокса «Показать все часы»."""
        global show_allH
        show_allH = 1 if show_allH == 0 else 0
        self.canvas.Clear()
        self.canvas.Draw(drawAnalemma(), xAxis=(0, 360), yAxis=(-90, 90))

    def onToggleHour(self, event, hour):
        """Обработчик чекбокса выбора конкретного часа."""
        global includeH
        includeH[int(hour)] = 1 if includeH[int(hour)] == 0 else 0
        self.canvas.Clear()
        self.canvas.Draw(drawAnalemma(), xAxis=(0, 360), yAxis=(-90, 90))

    def doUpdateInfo(self, event):
        """Обработчик кнопки «Update Location/Year» — обновление года и координат."""
        global my_year, observer
        y = self.text_ctrl_year.GetValue()
        if is_int(y):
            # Ограничение диапазона вводимого года
            if int(y) < 1900:
                y = '1900'
            if int(y) > 2100:
                y = '2100'
            self.text_ctrl_year.SetValue(y)
            my_year = y

        lat = self.text_ctrl_lat.GetValue()
        if is_float(lat):
            if float(lat) < -90.0:
                lat = '-90.0'
            if float(lat) > 90.0:
                lat = '90.0'
            self.text_ctrl_lat.SetValue(lat)
            observer.lat = float(lat) / deg_per_rad

        lon = self.text_ctrl_lon.GetValue()
        if is_float(lon):
            if float(lon) < -180.0:
                lon = '-180.0'
            if float(lon) > 180.0:
                lon = '180.0'
            self.text_ctrl_lon.SetValue(lon)
            observer.lon = float(lon) / deg_per_rad

        self.canvas.Clear()
        self.canvas.Draw(drawAnalemma(), xAxis=(0, 360), yAxis=(-90, 90))

    def doUpdateBody(self, event, body):
        """Обработчик радиокнопок — смена небесного тела и перерисовка."""
        global astro_body, astro_str
        doUpdate = 0

        # Сопоставление имени тела с объектом PyEphem
        body_map = {
            "Sun":     ephem.Sun(),
            "Moon":    ephem.Moon(),
            "Mercury": ephem.Mercury(),
            "Venus":   ephem.Venus(),
            "Mars":    ephem.Mars(),
            "Jupiter": ephem.Jupiter(),
            "Saturn":  ephem.Saturn(),
            "Neptune": ephem.Neptune(),
        }

        if body in body_map and astro_str != body:
            astro_str = body
            astro_body = body_map[body]
            doUpdate = 1

        if doUpdate == 1:
            self.canvas.Clear()
            self.canvas.Draw(drawAnalemma(), xAxis=(0, 360), yAxis=(-90, 90))


# ------------------------------------------------------------------------------
# ТОЧКА ВХОДА
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app = wx.App(False)
    frame = MyGraph()
    frame.Show()
    app.MainLoop()

