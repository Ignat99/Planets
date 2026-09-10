import wx
from wx.lib.plot import PlotCanvas, PlotGraphics, PolyLine, PolyMarker
import math
import ephem
import datetime

astro_str = "Sun"
astro_body = ephem.Sun()
observer = ephem.Observer()
observer.name = "Wichita Mountains"
observer.lon = '-98:31.92'
observer.lat = '34:44.64'
my_year = str(datetime.datetime.now().year) # current year...

# this array determines which hours to show by default at start-up
includeH = [0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0] # 12 noon (local) on by default...
show_allH = 0 # this is an override to the above and will show all hours...
includeD = [0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0] # 1, 11, and 21 on by default...
show_allD = 0 # this is an override to the above and will show all days...
deg_per_rad = 57.2957795

# Calculate the requested geometric properties

# 1. Edges on a Penteract (5-cube)
# Formula for k-faces of n-cube: 2^(n-k) * binom(n, k)
# For edges (k=1) on a 5-cube (n=5):
edges_penteract = (2**(5-1)) * (5) # 16 * 5 = 80

# 2. Volumes (3-faces) on a 5-orthoplex (5-cross-polytope)
# Formula for k-faces of n-orthoplex: 2^(k+1) * binom(n, k+1)
# For volumes (3-faces, meaning k=3) on a 5-orthoplex (n=5):
# Note: k here is dimension of the face. Volumes are 3D faces.
# k=3 -> 2^(3+1) * binom(5, 3+1) = 2^4 * binom(5, 4) = 16 * 5 = 80
volumes_orthoplex = (2**4) * 5

# 3. Two-dimensional faces (k=2) on both:
# For Penteract (5-cube): k=2 -> 2^(5-2) * binom(5, 2) = 2^3 * 10 = 80
faces2d_penteract = (2**3) * 10

# For 5-orthoplex: k=2 -> 2^(2+1) * binom(5, 2+1) = 2^3 * binom(5, 3) = 8 * 10 = 80
faces2d_orthoplex = (2**3) * 10

print(f"Edges on Penteract: {edges_penteract}")
print(f"Volumes on 5-orthoplex: {volumes_orthoplex}")
print(f"2D faces on Penteract: {faces2d_penteract}")
print(f"2D faces on 5-orthoplex: {faces2d_orthoplex}")
print(f"Days in two sorokovniks: {2 * 40}")


def is_int(s):
  try:
    int(s)
    return True
  except ValueError:
    return False

def is_float(s):
  try:
    float(s)
    return True
  except ValueError:
    return False

def is_valid_date(y,m,d):
  try:
    newDate = datetime.datetime(y,m,d)
    return True
  except ValueError:
    return False

def analemma_xy_cable(date):
    # 1. Базовый астрономический расчет
    adjtime = ephem.date(ephem.date(date) - float(observer.lon)*(12.0/math.pi)*ephem.hour)
    observer.date = adjtime
    astro_body.compute(observer)
    
    base_x = deg_per_rad * float(astro_body.az)
    base_y = deg_per_rad * float(astro_body.alt)
    
    # 2. Внедрение вашей эвристики: Коаксиальный волновой пробой
    # Переводим дату в условную фазу (t) для вычисления пульсаций
    t = float(ephem.date(date)) 
    
    # Эвристическая стоячая волна: имитация пи-мезонного резонанса и пьезо-сдвига ядра
    # Частоты подобраны так, чтобы создавать фрактальные "зубцы" на аналемме
    wave_core = math.sin(t * 2 * math.pi / 365.25) * 5.0 # Годовое сжатие конденсатора
    wave_jet = math.sin(t * 2 * math.pi * 12.0) * math.cos(t * 2 * math.pi) * 2.0 # Коронарный джет
    
    # 3. Модификация траектории пересечения торического многообразия
    # Разворачиваем координаты на условный угол модуляции (эффект шахматного разворота Юпаны)
    mod_x = base_x + wave_core
    mod_y = base_y + wave_jet
    
    return (mod_x, mod_y)


# return the altitude and azimuth in degrees in an x,y tuple
def analemma_xy(date):
  adjtime = ephem.date(ephem.date(date) - float(observer.lon)*(12.0/math.pi)*ephem.hour)
  observer.date = adjtime
  astro_body.compute(observer)
  #print astro_body.alt, astro_body.az
  x = deg_per_rad * float(astro_body.az)
  y = deg_per_rad * float(astro_body.alt)
  return (x,y)
 
def drawAnalemma():
  global my_year
  analemma_group = []
  data = []
  for i in xrange(25):
    data.append([])

  for m in xrange(1,13):
    for d in xrange(1,len(includeD)):
      if includeD[d] == 1 or show_allD == 1:
        if is_valid_date(int(my_year), m, d):
          for h in xrange(len(includeH)):
            if includeH[h] == 1 or show_allH == 1:
              date = '{0:s}/{1:d}/{2:d} {3:d}:00'.format(my_year, m, d, h)
              data[h].append(analemma_xy(date))

  for h in xrange(len(includeH)):
    if includeH[h] == 1 or show_allH == 1:
      for j in xrange(len(data[h])):
        if data[h][j][1] > 0:
          mycolor = "yellow"
        else:
          mycolor = "blue"
        analemma_pts = PolyMarker(data[h][j], legend="{0:d}:00".format(h), colour=mycolor, marker='circle',size=1)
        analemma_group.append(analemma_pts)

  line = PolyLine([(270,-90), (270,90)], colour='black', width=1)
  analemma_group.append(line)
  line = PolyLine([(180,-90), (180,90)], colour='black', width=1)
  analemma_group.append(line)
  line = PolyLine([(90,-90), (90,90)], colour='black', width=1)
  analemma_group.append(line)
  line = PolyLine([(0,45), (360,45)], colour='black', width=1)
  analemma_group.append(line)
  line = PolyLine([(0,0), (360,0)], colour='black', width=3)
  analemma_group.append(line)
  line = PolyLine([(0,-45), (360,-45)], colour='black', width=1)
  analemma_group.append(line)

  mylon = deg_per_rad * float(observer.lon)
  mylat = deg_per_rad * float(observer.lat)
  my_ns = "N" if mylat > 0 else "S"
  my_we = "W" if mylon < 0 else "E"
  mytitle = "{0:s} Analemma Plot for  {1:.3f}{2:s}  {3:.3f}{4:s}".format(my_year, abs(mylat), my_ns, abs(mylon), my_we)
  xDesc = "Direction [N=0, E=90, S=180, W=270] [Yellow = {0:s} above horizon, Blue = {0:s} below horizon]".format(astro_str)
  return PlotGraphics(analemma_group, mytitle, xDesc, "Elevation")
 
########################################################################
class MyGraph(wx.Frame):
 
    #----------------------------------------------------------------------
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Analemma Plot', size=(1024,768))
 
        # Add a panel so it looks the correct on all platforms
        panel = wx.Panel(self, wx.ID_ANY)
 
        # create some sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        checkSizer1 = wx.BoxSizer(wx.HORIZONTAL)
        checkSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        checkSizer3 = wx.BoxSizer(wx.HORIZONTAL)
 
        # create the widgets
        self.canvas = PlotCanvas(panel)
        self.canvas.SetBackgroundColour("GRAY")
        self.canvas.Draw(drawAnalemma(), xAxis=(0,360), yAxis=(-90,90))
        toggleShowAllD = wx.CheckBox(panel, label="Show All Days ")
        toggleShowAllD.Bind(wx.EVT_CHECKBOX, self.onToggleShowAllD)
        toggleShowAllH = wx.CheckBox(panel, label="Show All Hours")
        toggleShowAllH.Bind(wx.EVT_CHECKBOX, self.onToggleShowAllH)

        self.rb1 = wx.RadioButton(panel, -1, 'Sun', style=wx.RB_GROUP)
        self.rb2 = wx.RadioButton(panel, -1, 'Moon')
        self.rb3 = wx.RadioButton(panel, -1, 'Mercury')
        self.rb4 = wx.RadioButton(panel, -1, 'Venus')
        self.rb5 = wx.RadioButton(panel, -1, 'Mars')
        self.rb6 = wx.RadioButton(panel, -1, 'Jupiter')
        self.rb7 = wx.RadioButton(panel, -1, 'Saturn')
        self.rb8 = wx.RadioButton(panel, -1, 'Neptune')
        self.rb1.Bind(wx.EVT_RADIOBUTTON, lambda event, temp="Sun": self.doUpdateBody(event, temp))
        self.rb2.Bind(wx.EVT_RADIOBUTTON, lambda event, temp="Moon": self.doUpdateBody(event, temp))
        self.rb3.Bind(wx.EVT_RADIOBUTTON, lambda event, temp="Mercury": self.doUpdateBody(event, temp))
        self.rb4.Bind(wx.EVT_RADIOBUTTON, lambda event, temp="Venus": self.doUpdateBody(event, temp))
        self.rb5.Bind(wx.EVT_RADIOBUTTON, lambda event, temp="Mars": self.doUpdateBody(event, temp))
        self.rb6.Bind(wx.EVT_RADIOBUTTON, lambda event, temp="Jupiter": self.doUpdateBody(event, temp))
        self.rb7.Bind(wx.EVT_RADIOBUTTON, lambda event, temp="Saturn": self.doUpdateBody(event, temp))
        self.rb8.Bind(wx.EVT_RADIOBUTTON, lambda event, temp="Neptune": self.doUpdateBody(event, temp))


        self.text_ctrl_year = wx.TextCtrl(panel, -1, my_year)
        self.text_ctrl_lat = wx.TextCtrl(panel, -1, "{0:.3f}".format(float(observer.lat)*deg_per_rad))
        self.text_ctrl_lon = wx.TextCtrl(panel, -1, "{0:.3f}".format(float(observer.lon)*deg_per_rad))
        self.button_update = wx.Button(panel, -1, "Update Location/Year")
        wx.EVT_BUTTON(self,self.button_update.GetId(), self.doUpdateInfo)

        toggle = []
        mylabelH = ["00","01","02","03","04","05","06","07","08","09","10","11",\
                    "12","13","14","15","16","17","18","19","20","21","22","23"]

        for i in xrange(24):
          toggle.append(wx.CheckBox(panel, label=mylabelH[i]))
          if includeH[i] == 1 or show_allH == 1:
            toggle[i].SetValue(True)
          toggle[i].Bind(wx.EVT_CHECKBOX, lambda event, temp=mylabelH[i]: self.onToggleHour(event, temp))

        # layout the widgets
        mainSizer.Add(self.canvas, 1, wx.EXPAND)
        checkSizer1.Add(self.text_ctrl_year, 0, wx.ALL, 5)
        checkSizer1.Add(self.text_ctrl_lat, 0, wx.ALL, 5)
        checkSizer1.Add(self.text_ctrl_lon, 0, wx.ALL, 5)
        checkSizer1.Add(self.button_update, 0, wx.ALL, 5)
        checkSizer2.Add(toggleShowAllD, 0, wx.ALL, 5)
        checkSizer3.Add(toggleShowAllH, 0, wx.ALL, 5)

        for i in xrange(0,12):
          checkSizer2.Add(toggle[i], 0, wx.ALL, 5)
        for i in xrange(12,24):
          checkSizer3.Add(toggle[i], 0, wx.ALL, 5)

        checkSizer1.Add(self.rb1, 0, 0, 5)
        checkSizer1.Add(self.rb2, 0, 0, 5)
        checkSizer1.Add(self.rb3, 0, 0, 5)
        checkSizer1.Add(self.rb4, 0, 0, 5)
        checkSizer1.Add(self.rb5, 0, 0, 5)
        checkSizer1.Add(self.rb6, 0, 0, 5)
        checkSizer1.Add(self.rb7, 0, 0, 5)
        checkSizer1.Add(self.rb8, 0, 0, 5)

        mainSizer.Add(checkSizer1)
        mainSizer.Add(checkSizer2)
        mainSizer.Add(checkSizer3)
        panel.SetSizer(mainSizer)
 
    #----------------------------------------------------------------------
    def onToggleShowAllD(self, event):
        """"""
        global show_allD
        show_allD = 1 if show_allD == 0 else 0
        self.canvas.Clear()
        self.canvas.Draw(drawAnalemma(), xAxis=(0,360), yAxis=(-90,90))

    #----------------------------------------------------------------------
    def onToggleShowAllH(self, event):
        """"""
        global show_allH
        show_allH = 1 if show_allH == 0 else 0
        self.canvas.Clear()
        self.canvas.Draw(drawAnalemma(), xAxis=(0,360), yAxis=(-90,90))

    #----------------------------------------------------------------------
    def onToggleHour(self, event, hour):
        """"""
        global includeH
        includeH[int(hour)] = 1 if includeH[int(hour)] == 0 else 0
        self.canvas.Clear()
        self.canvas.Draw(drawAnalemma(), xAxis=(0,360), yAxis=(-90,90))

    #----------------------------------------------------------------------
    def doUpdateInfo(self, event):
        """"""
        global my_year, observer
        y = self.text_ctrl_year.GetValue()
        if is_int(y):
          # I'm going to limit what users can input here...
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
          observer.lat = float(lat)/deg_per_rad

        lon = self.text_ctrl_lon.GetValue()
        if is_float(lon):
          if float(lon) < -180.0:
            lon = '-180.0'
          if float(lon) > 180.0:
            lon = '180.0'
          self.text_ctrl_lon.SetValue(lon)
          observer.lon = float(lon)/deg_per_rad

        self.canvas.Clear()
        self.canvas.Draw(drawAnalemma(), xAxis=(0,360), yAxis=(-90,90))

    #----------------------------------------------------------------------
    def doUpdateBody(self, event, body):
        """"""
        global astro_body, astro_str
        doUpdate = 0

        if body == "Sun" and astro_str != "Sun":
          astro_str = "Sun"
          astro_body = ephem.Sun()
          doUpdate = 1
        if body == "Moon" and astro_str != "Moon":
          astro_str = "Moon"
          astro_body = ephem.Moon()
          doUpdate = 1
        if body == "Mercury" and astro_str != "Mercury":
          astro_str = "Mercury"
          astro_body = ephem.Mercury()
          doUpdate = 1
        if body == "Venus" and astro_str != "Venus":
          astro_str = "Venus"
          astro_body = ephem.Venus()
          doUpdate = 1
        if body == "Mars" and astro_str != "Mars":
          astro_str = "Mars"
          astro_body = ephem.Mars()
          doUpdate = 1
        if body == "Jupiter" and astro_str != "Jupiter":
          astro_str = "Jupiter"
          astro_body = ephem.Jupiter()
          doUpdate = 1
        if body == "Saturn" and astro_str != "Saturn":
          astro_str = "Saturn"
          astro_body = ephem.Saturn()
          doUpdate = 1
        if body == "Neptune" and astro_str != "Neptune":
          astro_str = "Neptune"
          astro_body = ephem.Neptune()
          doUpdate = 1

        if doUpdate == 1:
          self.canvas.Clear()
          self.canvas.Draw(drawAnalemma(), xAxis=(0,360), yAxis=(-90,90))

if __name__ == '__main__':
    app = wx.App(False)
    frame = MyGraph()
    frame.Show()
    app.MainLoop()