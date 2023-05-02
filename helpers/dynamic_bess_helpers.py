import functools
import math
import pandas as pd
import numpy as np

from loguru import logger
from scipy.optimize import curve_fit


def deg_curve_linearization(deg_curve_data, capacity_loss):
	"""
	2 -step function that: 1) converts a degradation curve from "Depth of Discharge (DOD) (%) vs. Number of cycles until
	end-of-life (EOL) criterion is achieved" to "DOD (%) vs. Cycle life loss (%)" based on the capacity_loss criterion
	and 2) linearizes the curve and returns the slope (with the line always intersecting the origin x=0, y=0)
	:param deg_curve_data: dataframe with DOD(%) and respective number of cycles until EOL is achieved
	:type deg_curve_data: pandas.core.frame.DataFrame
	:param capacity_loss: (100 - EOL criterion (%)) for the BESS asset considered
	:type capacity_loss: Union[int, float]
	:return: slope of the linearized "DOD vs. Cycle life loss" curve
	:rtype: float
	"""
	# Get columns of interest and convert the y-axis from nr of cycles to cycle life loss (cll)
	clean_df = deg_curve_data.loc[:, ('dod', 'nrCycles')].copy()
	clean_df['nrCycles'] = capacity_loss / clean_df['nrCycles']
	clean_df.columns = ['dod', 'cll']

	# Model to point the linear solution to pass on the origin, xf=0 and yf=0
	def model(x, m, xf, yf):
		return m*(x-xf)+yf

	# The curve_fit function uses "model" to fit the x and y data
	partial_model = functools.partial(model, xf=0, yf=0)

	# Curve fitting using scipy.optimize.curve_fit()
	best_fit, _ = curve_fit(partial_model, xdata=clean_df.dod.values, ydata=clean_df.cll.values)
	return best_fit[0]


def c_rate_limits(max_c_rate, nom_capacity, inv_max_idc):
	"""
	Checks if BES's maximum C-rate current is higher than the inverter's nominal current and,
	 if it is, substitute it by the inverter's nominal current corresponding C-rate
	:param max_c_rate: input maximum C-rate
	:type max_c_rate: float
	:param nom_capacity: nominal capacity in Ah
	:type nom_capacity: float
	:param inv_max_idc: inverter's maximum Idc current
	:type inv_max_idc: float
	:return: effective maximum C-rate
	:rtype: float
	"""

	# At first, the maximum c-rate is assumed as inputted
	max_c_rate_edited = max_c_rate

	# Through the BESS capacity, the current for maximum C-rate is calculated
	bess_current = nom_capacity * max_c_rate_edited

	# Substitute the C-rate by the C-rate corresponding to the inverter nominal current if needed
	if bess_current > inv_max_idc:
		max_c_rate_edited = inv_max_idc / bess_current

	return max_c_rate_edited


def average_c_rates_dups(bess_test_data, key2test_value):
	"""
	Function to convert test data into a pandas.core.frame.DataFrame and average equal c-rates tested per test set
	:param bess_test_data: "testData structure of a BESS asset configured
	:type bess_test_data: dict
	:param key2test_value: checkup dictionary relating the keys of a test set structure and the corresponding value key
	:type key2test_value: dict of string
	:return: dictionary with test data converted from a dict to a dataframe
	:rtype: dict
	"""
	# For each test set available:
	# 1) Convert list values with structure {'cRate': float, 'value_name': float, 'trial': float} to dataframe
	# 2) Average equal c-rates
	for key, values in bess_test_data.items():
		if key in ['addOnSoc', 'betterEffApprox', 'roundEffApprox']:
			continue

		bess_test_data[key] = pd.DataFrame(values).groupby('cRate', as_index=False)[key2test_value.get(key)].mean()

	return bess_test_data


def power_rate_limits(nom_cap, max_c_rate, data, action):
	"""
	Returns the limit power rates for charging or discharging the BESS.
	First the function tries to retrieve the nominal voltage observed for a given (dis)charge C-rate;
	It is assumed that the C-rate is the maximum C-rate that can be applied under the current conditions.
	If the maximum C-rate was not tested (plausible when it is constrained not by the BESS itself but by the
	inverter's nominal current, then a least squares linearization is applied to the nominal voltage values
	retrieved for several C-rates and the nominal (dis)charge voltage for the maximum C-rate is calculated.
	The function returns the product between the calculated voltage and the amp rate that generated that voltage.
	:param nom_cap: BESS's nominal capacity in Ah
	:type nom_cap: float
	:param max_c_rate: BESS's actual maximum C-rate
	:type max_c_rate: float
	:param data: dataframe of "vNomC" or "vNomD" structure
	:type data: pandas.DataFrame of float
	:param action: if power rate limit was assessed for 'charging' or for 'discharging'
	:type action: str
	:return: BESS's power rate limit for charging or discharging in W
	:rtype: float
	"""
	# Parse input data
	c_rates = data.get('cRate').round(2)
	v_avgs = data.get('vAvg')
	_max_c_rate = round(max_c_rate, 2)

	# Convert the maximum C-rate to current in A
	max_amp_rate = max_c_rate * nom_cap

	# Check if the max C-rate was tested
	max_in_set = data[v_avgs.name].loc[c_rates == _max_c_rate]

	# Obtain the voltage measured/expected at maximum C-rate
	if not max_in_set.empty:
		# Get the measured voltage at maximum C-rate and calculate the corresponding power rate
		max_c_rate_voltage = max_in_set.sum()

	else:
		logger.debug(f' ... c-rate {_max_c_rate} was not tested; '
		             f'{action} power rate limit being approximated by least squares...')
		# Linearly approach, through least squares over the tested set points, the power limit
		amp_rates = c_rates * nom_cap
		m, i = __least_squares(amp_rates, v_avgs)
		max_c_rate_voltage = m * max_amp_rate + i

	# Check if the power rate calculated is higher than the inverter's nominal power and return the minimum
	power_limit = max_amp_rate * max_c_rate_voltage

	return power_limit


def __least_squares(x_set, y_set):
	"""
	Function to approach a set of 2D coordinates through the least squares method
	:type x_set: pandas.core.series.Series of floats
	:type y_set: pandas.core.series.Series of floats
	:rtype: (float, float)
	"""
	aux = np.vstack([x_set.values, np.ones(len(x_set))]).T
	m, i = np.linalg.lstsq(aux, y_set.values, rcond=None)[0]

	return m, i


def linearize(data, x_col='cRate', y_col='eRemain'):
	"""
	Returns the line parameters for calculating the energy limits of the BESS as a function of its (dis)charging
	power. The function applies a least squares approximation in order to linearize the relationship between an
	applied C-rate (afterwards converted to power rate) and the corresponding maximum energy fraction.
	The energy fraction represents maximum SoC or minimum SoC that can be achieved for a given charge/discharge
	current. Naturally, for higher currents, the fractions will be more restrictive, i.e. the battery will be
	considered to be fully charged/discharged, with a lower/higher energy content.
	:param data: dataframe of "cLim" or "dLim" structure
	:type data: pandas.core.frame.DataFrame
	:param x_col: name of column in dataframe to be considered as the x-axis
	:type x_col: str
	:param y_col: name of column in dataframe to be considered as the y-axis
	:type y_col: str
	:return: line parameters (slope and origin) resulting from the 2D linearization
	:rtype: (float, float)
	"""
	x_set = data.get(x_col)
	y_set = data.get(y_col)

	return __least_squares(x_set, y_set)


def efficiencies(df, cut_value, constant_eff):
	"""
	Returns the line parameters for calculating the (dis)charge efficiency of the BESS as a function of its
	(dis)charging power. The function applies a least squares approximation in order to linearize the relationship
	between an applied C-rate (afterwards converted to power rate) and the corresponding efficiency observed.
	The function also checks if the minimum C-rate tested is greater than the defined cut-value. If so, the slope
	for the linearization before the cut-value becomes the constant efficiency value provided.
	:param df: dataframe with the pwoer rates and the corresponding measured values
	:type df: pandas.core.frame.DataFrame
	:param cut_value: power rate after which the efficiency is considered constant
	:type cut_value: float
	:param constant_eff: constant efficiency value to be considered
	:type constant_eff: float
	:return: slope and origin, parameters of the linearization performed for efficiency before cut-value
	:rtype: (float, float)
	"""

	if df.get('x').min() < cut_value:
		sub_df = df.loc[df.get('x') < cut_value]
		sub_df.append({sub_df.columns[0]: cut_value, sub_df.columns[1]: constant_eff*cut_value}, ignore_index=True)
		slope, origin = linearize(sub_df, x_col='x', y_col='y')
	else:
		slope, origin = constant_eff, 0.0

	return slope, origin
