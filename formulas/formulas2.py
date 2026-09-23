#! /usr/bin/env python
# Check the plot docstring

from sympy import Symbol, exp, sin, cos, pi, cot, sqrt
from sympy.plotting import (plot, plot_parametric,
                            plot3d_parametric_surface, plot3d_parametric_line,
                            plot3d)


x = Symbol('x')
y = Symbol('y')
u = Symbol('u')
v = Symbol('v')
theta = Symbol('theta')
epsilon = 2
epsilon_z = 1.5
mu = 0.2
mu_z = 1.9
omega = 40*pi 
# -sqrt(epsilon*epsilon_z*mu/(-epsilon*cos(theta)**2 + epsilon + epsilon_z*cos(theta)**2))*Abs(omega)
expr = -sqrt(epsilon*epsilon_z*mu/(-epsilon*cos(theta)**2 + epsilon + epsilon_z*cos(theta)**2))*omega

#param_line_3d = plot3d_parametric_line((x*cos(x), x*sin(x), x, (x, 0, 15)),(1.5*x*cos(x), 1.5*x*sin(x), x, (x, 0, 15)),(2*x*cos(x), 2*x*sin(x), x, (x, 0, 15)), show=False)
param_line_3d = plot3d_parametric_line((epsilon_z*cos(expr)*cos(theta)*cos(omega*theta)/sin(theta)/epsilon -omega*mu_z*cos(expr)*cos(omega*theta)/sin(theta)/expr,\
				       -epsilon_z*cos(expr)*cos(theta)*sin(omega*theta)/sin(theta)/epsilon*expr + omega*epsilon_z*cos(expr)*sin(omega*theta)/sin(theta)/expr,\
				        exp(theta), (theta, 0.1, 3)),\
#				       (-omega*mu_z*exp(expr)*cos(omega*theta)/sin(theta)/expr,\
#				       omega*epsilon_z*exp(expr)*sin(omega*theta)/sin(theta)/expr,\
#				        exp(expr), (theta, 0.1, 3)),\
#				        (-omega*mu_z*cos(theta)/sin(theta)**2 /expr,\
#				        omega*epsilon_z*cos(theta)/sin(theta)**2 *cos(omega*theta+pi/2)**2 * expr,\
#				        theta, (theta, 0.1, 20)),\
				        show=False)
param_line_3d[0].line_color = lambda u: u  # parametric
#param_line_3d[1].line_color = lambda u, v: u*v  # first and second coordinates
#param_line_3d[2].line_color = lambda u, v, w: u*v*w  # all coordinates


if __name__ == '__main__':
    for p in [param_line_3d]:
        p.show()

