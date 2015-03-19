# Stephen Wood
# Written January 29, 2015
# This file is designed to plot chemical space partitioning maps
# given: X, Y, and a set of phi values. (usually a set of 3)

import numpy as np
from pylab import *

class SWChemicalSpaceMap(object):
	"""docstring for SWChemicalSpaceMap"""
	def __init__(self, x, y, phi, phase_names):
		super(SWChemicalSpaceMap, self).__init__()
		self.y = y
		self.x = x
		self.phi = phi
		self.phase_names = phase_names

		# Various properties
		self.xmin = min(x)
		self.xmax = max(x)
		self.ymin = min(y)
		self.ymax = max(y)
		self.scale = False
		self.alpha = 1.0
		self.levels = (50, 90, 200)
		self.linewidth = 2
		self.line_levels = (50, 90)
		self.plot_lines = False

		self.colors = [('aqua', 'deepskyblue'), ('crimson', 'maroon'), ('yellow', 'gold'), ('orange', 'coral')]

		self.check_lengths()
		self.plot()
	
	def check_lengths(self):
			if not len(self.phi) == len(self.phase_names):
				raise Exception('Error, number of phase names does not match number of phis provided')

	def plot(self):
		for i in range(len(self.phi)):
			contourf(self.x, self.y, self.phi[i], 8, levels = self.levels, alpha = self.alpha, colors = self.colors[i])
			if self.plot_lines:
				contour(self.x, self.y, self.phi[i], self.line_levels, alpha = 1.0, colors = self.colors[i][1], linewidths = self.linewidth)