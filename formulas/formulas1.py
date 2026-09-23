from sympy.abc import x, y, z
from sympy.abc import i, j, k
#from sympy.abc import rho, phi, theta
from sympy.abc import r, n
from sympy.abc import alpha, beta, gamma
from sympy.abc import omega, mu, epsilon

# Из sympy импортируем все необходимые функции, включая solve
from sympy import var, symbols, sin, cos, exp, zeros, Matrix, Symbol, Function, I, eye, simplify, latex, expand, solve

# Импортируем Mv вместо MV, а также Format и xpdf из модуля printer
from galgebra.printer import Format, xpdf
from galgebra.mv import Mv
from galgebra.ga import Ga

############### Geometric Algebra & Format of out pdf file ##############
# Инициализация принтера формул
Format()
########################################################################

F, Psi = symbols('F, Psi', cls=Function)
G = symbols('G', integer=True)
var("rho theta phi")
var("t")

n = i * sin(theta) * cos(phi) + j * sin(theta) * sin (phi) + k * cos (theta)
r = i * x + j * y + k * z

g1 = expand(n * r)

# Square is equal to one unit vectors and the product of pairs of unit vectors is zero
oneii = i * i
onejj = j * j
onekk = k * k
oneij = i * j
oneik = i * k
onejk = j * k

# Simplifying
g1=g1.subs(oneii,1).expand().simplify()
g1=g1.subs(onejj,1).expand().simplify()
g1=g1.subs(onekk,1).expand().simplify()
g1=g1.subs(oneij,0).expand().simplify()
g1=g1.subs(oneik,0).expand().simplify()
g1=g1.subs(onejk,0).expand().simplify()

# Multiply by the propagation constant in the direction of wave
g2 = expand(G * g1)
g2 = expand(g2)

# Propagation constants along the axes
alpha1 = G * sin(theta) * cos(phi)
beta1 = G * sin(theta) * sin(phi)
gamma1 = G * cos(theta)

# Simplifying
g2=g2.subs(alpha1,alpha).expand().simplify()
g2=g2.subs(beta1,beta).expand().simplify()
g2=g2.subs(gamma1,gamma).expand().simplify()

print ("r =", g2)

#Propagation constants along the axes are related
g3 = alpha1**2 + beta1**2 + gamma1**2

# Simplifying
g3=g3.subs(sin(phi)**2, 1-cos(phi)**2).expand().simplify()

print (r'%\alpha^{2} + \beta^{2} + \gamma^{2} = ', latex(g3))

x_hat = Matrix([
    rho * sin(theta) * cos(phi),
    rho * sin(theta) * sin(phi),
    rho * cos(theta)])

psi = Function("psi")

psi =exp(I*omega*t) * exp(-I*g2)
print ("\Psi =", latex(psi))

#Derivatives of the wave function of the coordinates
dpsidx=psi.diff(x)
dpsidx=dpsidx.subs(psi,'Psi').expand().simplify()
print ("d \Psi / dx =", latex(dpsidx))

dpsidy=psi.diff(y)
dpsidy=dpsidy.subs(psi,'Psi').expand().simplify()
print ("d \Psi / dy =", latex(dpsidy))

dpsidz=psi.diff(z)
dpsidz=dpsidz.subs(psi,'Psi').expand().simplify()
print ("d \Psi / dz =", latex(dpsidz))

########### Maxwell's  Equations ###################
omega, mu, epsilon, muz, epsilonz = symbols('omega mu epsilon mu_z epsilon_z', integer=True)
Z = Matrix(([omega*mu,0,0,0,0,0],[0,omega*mu,0,0,0,0],[0,0,omega*muz,0,0,0],[0,0,0,omega*epsilon,0,0],[0,0,0,0,omega*epsilon,0],[0,0,0,0,0,omega*epsilonz]))

C = Matrix((\
	[0, 0, 0, 0, gamma1, -beta1],\
	[0, 0, 0, -gamma1, 0, alpha1],\
	[0, 0, 0, beta1, -alpha1, 0],\
	[0, -gamma1, beta1, 0, 0, 0],\
	[gamma1,0, -alpha1, 0, 0, 0],\
	[-beta1, alpha1, 0, 0, 0, 0],\
	))

Z1=Z + C.transpose()
Z2=Z1.det()
Z3=Z2.simplify()
Z3=Z3/omega**2/mu/epsilon
Z4=solve(Z3,G)
for id in range(len(Z4)):
	Z4[id]=Z4[id].subs(sin(theta)**2, 1-cos(theta)**2).expand().simplify()
	
print("Z4 =", Z4)

# Переменные пространства-времени
vars = symbols('t x y z')

# Создаем ортогональную диагональную метрику Минковского
xyz_space, *basis = Ga.build('gamma*t|x|y|z', g=[1, -1, -1, -1], coords=vars)

# ИСПРАВЛЕНО: Извлекаем первый элемент (индекс 0) из списка basis, это вектор gamma_t
g0_vector = basis[0]
I_mv = xyz_space.i

# ИСПРАВЛЕНО: Аргумент fct=True заменен на f=True согласно спецификации новой galgebra
E = xyz_space.mv('E', 'vector', f=True) 
H = xyz_space.mv('H', 'vector', f=True)

# Задаем начальные компоненты векторов
E.set_coef(1, 0, 0)
H.set_coef(1, 0, 0)

# Домножаем векторы на временную компоненту
E = E * g0_vector 
H = H * g0_vector 

# Складываем электромагнитное поле
F_field = E + I_mv * H

print ('E = \\bm{E\\gamma_{t}} =', E)
print ('H = \\bm{H\\gamma_{t}} =', H)
print ('F = E+IH =', F_field) 

# Генерация итогового PDF/TeX документа
xpdf(paper=(6,7))
