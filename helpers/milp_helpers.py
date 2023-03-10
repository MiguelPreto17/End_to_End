import functools
import itertools
import math
import numpy as np
import operator
import pandas as pd


def create_strftime_list(horizon, step, init):
	"""
	Returns a list of strings representing datetime values in ISO 8601 format.
	The first datetime value matches "init" and extends for the number of hours provided in "horizon",
	with the values distancing one from the other the number of minutes specified in "step".
	:param horizon: horizon configured in hours
	:type horizon: int
	:param step: time step configured in hours
	:type step: int
	:param init: datetime value of the first time step to be considered in the optimization horizon (timezone = 'UTC')
	:type init: pandas._libs.tslibs.timestamps.Timestamp
	:return: list of datetime values in ISO 8061 string format
	:rtype: list of str
	"""
	# Create list of all time steps as "pandas._libs.tslibs.timestamps.Timestamp" values
	nr_time_steps = int(horizon/step)
	frequency = f'{int(step*60)}T'
	dt_list = pd.date_range(init, periods=nr_time_steps, freq=frequency).to_list()

	# Convert values to string in ISO 8601 format
	iso_8601_format = "%Y-%m-%dT%H:%M:%SZ"

	return [dt.strftime(iso_8601_format) for dt in dt_list]
