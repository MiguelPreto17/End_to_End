import itertools
import logging
import matplotlib
import matplotlib.colors as clrs
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import warnings

from datetime import datetime
from matplotlib.lines import Line2D


warnings.filterwarnings("ignore")


def listify(value, length):
	return [value] * length


def divide(dividend, divisor):
	return dividend / divisor


def color_fader(c1, c2, mix=0):
	clr1 = np.array(clrs.to_rgb(c1))
	clr2 = np.array(clrs.to_rgb(c2))
	return clrs.to_hex((1-mix) * clr1 + mix * clr2)


def plot_results(obj):
	"""
	Function to plot the relevant results from the optimization problem resolution
	:param obj: Optimizer class instance resulting from the optimization procedure
	:type obj: flexergy.core.module.core.Optimizer.Optimizer
	:return: None
	:rtype: None
	"""
	# ******************************************************************************************************************
	#        INITIALIZE VARIABLES
	# ******************************************************************************************************************
	horizon = obj.time_intervals
	#all_days = obj.teste
	aux_bar_length = 0.5
	time_series = range(horizon)
	#time_series = range(all_days)


	offset_series = np.arange(0.5, horizon + 0.5, 1)
	expected_revenues = pd.DataFrame(obj.outputs['expectRevs'])['setpoint'].sum()
	e_deg2 = pd.DataFrame(obj.varis['e_deg2'])  # kWh
	pabs = pd.DataFrame(obj.varis['p_abs'])

	# -- BESS PLOT -----------------------------------------------------------------------------------------------------
	e_bess = pd.DataFrame(obj.varis['e_bess'])  # kWh
	e_bess2 = pd.DataFrame(obj.varis['e_bess2'])  # kWh
	e_deg = pd.DataFrame(obj.varis['e_deg']) * 1E3  # Wh
	total_deg = e_deg + e_deg2
	market = pd.Series(obj.market_prices)  # €/kWh
	feedin = pd.Series(obj.feedin_tariffs)  # €/kWh
	cost = market * pabs
	total_cost = cost + total_deg

	if obj.add_on_soc:
		max_e_bes = obj.varis['max_e_bes']  # kWh
		min_e_bes = obj.varis['min_e_bes']  # kWh
	else:
		max_e_bes = np.full(shape=horizon, fill_value=obj.bess.max_e_bess)  # kWh
		min_e_bes = np.full(shape=horizon, fill_value=obj.bess.min_e_bess)  # kWh

	# -- RENEWABLES PLOT -----------------------------------------------------------------------------------------------
	pv_generation = pd.DataFrame(obj.pv_forecasts)  # kW

	# -- INFLEXIBLE LOAD PLOT ------------------------------------------------------------------------------------------
	inflex_demand = pd.DataFrame(obj.load_forecasts)  # kW

	# -- PRICES AND TARIFFS PLOT ---------------------------------------------------------------------------------------
	"""market = pd.Series(obj.market_prices)  # €/kWh
	feedin = pd.Series(obj.feedin_tariffs)  # €/kWh
	cost = market * pabs
	total_cost = cost + total_deg"""

	# **************************************************************************************************************
	#        PLOTS
	# **************************************************************************************************************
	matplotlib.rcParams.update({'font.size': 15})
	nrows = 13
	fig, axes = plt.subplots(nrows=nrows, ncols=1, figsize=(30, 2.5*nrows), sharex=True)

	# --- Title definition -----------------------------------------------------------------------------------------
	title = f'Expected costs (+) / revenues (-): €{expected_revenues:.2f}'

	# **************************************************************************************************************
	#        PLOT 1 - Generation, load, prices and tariffs
	# **************************************************************************************************************
	vertical = 0  # Vertical relative position of the plot

	ax = axes[vertical]

	pv_generation.plot(title=title, kind='bar', width=aux_bar_length, align='edge', edgecolor='steelblue',
	                   color='teal', alpha=0.7, ax=ax)

	inflex_demand.plot(kind='bar', width=aux_bar_length, position=-1.0, edgecolor='maroon',
	                   color='indianred', alpha=0.7, ax=ax)

	# Create handles from scratch
	handles = list()
	handles.append(mpatches.Patch(color='teal', edgecolor='steelblue', alpha=0.7, label='Forecasted PV'))
	handles.append(mpatches.Patch(color='darkred', edgecolor='maroon', alpha=0.7, label='Forecasted demand'))

	# Second axis for prices and tariffs
	ax2 = ax.twinx()

	ax2.scatter(offset_series, market, label='Market prices', color='tomato', alpha=0.9, marker=7, s=100.0)

	ax2.scatter(offset_series, feedin, label='Feedin tariffs', color='forestgreen', alpha=0.9, marker=6, s=100.0)

	# Create handles
	fp_handles, _ = ax2.get_legend_handles_labels()
	handles.extend(fp_handles)

	# Tweak plot parameters
	ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1.03, 0.5), fancybox=True, shadow=True)
	ax.set_ylabel('kW')
	ax2.set_ylabel('€/kWh')

	ax.grid(which='major', axis='x', linestyle='--')

	box = ax.get_position()
	ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
	ax.xaxis.set_tick_params(labelbottom=True)

	vertical += 1

	# **************************************************************************************************************
	#        PLOT 2 - SOC and degradation
	# **************************************************************************************************************
	handles = []
	ax = axes[vertical]

	e_bess.plot(kind='bar', width=1.0, align='edge', edgecolor='steelblue', color='cornflowerblue', alpha=0.5,
	            ax=ax)

	for i in time_series:
		ax.hlines(y=max_e_bes[i], xmin=i, xmax=i+1, linewidth=2.0, color='darkslategrey', linestyle='--')
		ax.hlines(y=min_e_bes[i], xmin=i, xmax=i+1, linewidth=2.0, color='teal', linestyle='--')

	# Create handles from scratch
	handles.append(mpatches.Patch(edgecolor='steelblue', color='cornflowerblue', alpha=0.5, label=f'E content'))
	handles.append(Line2D([0], [0], color='darkslategrey', linestyle='dashed', lw=2.0, label=f'Maximum E content'))
	handles.append(Line2D([0], [0], color='teal', linestyle='dashed', lw=2.0, label=f'Minimum E content'))

	# Second axis for degradation
	ax2 = ax.twinx()

	e_deg.plot(kind='bar', width=0.05, color='maroon', alpha=0.5, ax=ax2)

	# Create handles from scratch
	handles.append(mpatches.Patch(color='maroon', alpha=0.5, label=f'Energy content degraded'))

	ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1.03, 0.5), fancybox=True, shadow=True)
	ax.set_ylabel(f'E content [kWh]')
	ax2.set_ylabel('E degraded [Wh]')
	ax.grid(which='major', axis='x', linestyle='--')

	box = ax.get_position()
	ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
	ax.xaxis.set_tick_params(labelbottom=True)

	vertical += 1

	plt.setp([a.get_xticklabels() for a in fig.axes[:-1]], visible=True, rotation=0)
	plt.xlim(0, horizon)
	for ax in fig.axes:
		plt.setp(ax.get_xticklabels(), visible=False)
		plt.setp(ax.get_xticklabels()[::4], visible=True)



	plt.savefig(rf'outputs/{obj.common_fname}.png')


	# **************************************************************************************************************
	#        PLOT 3 - BESS1
	# **************************************************************************************************************

	"""handles = []"""
	handles = []
	ax = axes[vertical]

	e_bess.plot(kind='bar', width=1.0, align='edge', edgecolor='steelblue', color='cornflowerblue', alpha=0.5,
				ax=ax)

	ax.set_ylabel(f'E content [kWh]')

	# Create handles from scratch
	handles.append(mpatches.Patch(edgecolor='steelblue', color='cornflowerblue', alpha=0.5, label=f'E content'))
	ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1.03, 0.5), fancybox=True, shadow=True)

	plt.savefig(rf'outputs/{obj.common_fname}.png')
	vertical += 1

	# **************************************************************************************************************
	#        PLOT 4 - BESS2
	# **************************************************************************************************************

	"""handles = []"""
	handles = []
	ax = axes[vertical]

	e_bess2.plot(kind='bar', width=1.0, align='edge', edgecolor='steelblue', color='cornflowerblue', alpha=0.5,
				ax=ax)

	ax.set_ylabel(f'E2 content [kWh]')

	# Create handles from scratch
	handles.append(mpatches.Patch(edgecolor='steelblue', color='cornflowerblue', alpha=0.5, label=f'E2 content'))
	ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1.03, 0.5), fancybox=True, shadow=True)

	plt.savefig(rf'outputs/{obj.common_fname}.png')
	vertical += 1

	# **************************************************************************************************************
	#        PLOT 5 - Degradation
	# **************************************************************************************************************

	handles = []
	ax = axes[vertical]

	e_deg.plot(kind='bar', width=1.0, align='edge', edgecolor='steelblue', color='maroon', alpha=0.5,
				ax=ax)

	ax.set_ylabel('E degraded [Wh]')

	# Create handles from scratch
	handles.append(mpatches.Patch(color='maroon', alpha=0.5, label=f'Energy degraded'))
	ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1.01, 0.5), fancybox=True, shadow=True)

	plt.savefig(rf'outputs/{obj.common_fname}.png')
	vertical += 1

	# **************************************************************************************************************
	#        PLOT 6 - Degradation2
	# **************************************************************************************************************

	handles = []
	ax = axes[vertical]

	e_deg2.plot(kind='bar', width=1.0, align='edge', edgecolor='steelblue', color='maroon', alpha=0.5,
				ax=ax)

	ax.set_ylabel('E2 degraded [Wh]')

	# Create handles from scratch
	handles.append(mpatches.Patch(color='maroon', alpha=0.5, label=f'Energy2 degraded'))
	ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1.01, 0.5), fancybox=True, shadow=True)

	plt.savefig(rf'outputs/{obj.common_fname}.png')
	vertical += 1

	# **************************************************************************************************************
	#        PLOT 7 - Total Degradation
	# **************************************************************************************************************

	handles = []
	ax = axes[vertical]

	total_deg.plot(kind='bar', width=1.0, align='edge', edgecolor='steelblue', color='maroon', alpha=0.5,
				ax=ax)

	ax.set_ylabel('Total E degraded [Wh]')

	# Create handles from scratch
	handles.append(mpatches.Patch(color='maroon', alpha=0.5, label=f'Total Energy degraded'))
	ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1.01, 0.5), fancybox=True, shadow=True)

	plt.savefig(rf'outputs/{obj.common_fname}.png')
	vertical += 1

	# **************************************************************************************************************
	#        PLOT 8 - Market
	# **************************************************************************************************************

	handles = []
	ax = axes[vertical]

	market.plot(kind='bar', width=1.0, align='edge', edgecolor='steelblue', color='forestgreen', alpha=0.5,
				ax=ax)

	ax.set_ylabel('Market [€]')

	# Create handles from scratch
	handles.append(mpatches.Patch(color='forestgreen', alpha=0.5, label=f'Price Market'))
	ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1.01, 0.5), fancybox=True, shadow=True)

	plt.savefig(rf'outputs/{obj.common_fname}.png')
	vertical += 1

	# **************************************************************************************************************
	#        PLOT 9 - Load
	# **************************************************************************************************************

	handles = []
	ax = axes[vertical]

	inflex_demand.plot(kind='bar', width=1.0, align='edge', edgecolor='maroon', color='forestgreen', alpha=0.5,
				ax=ax)

	ax.set_ylabel('Demand [kw]')

	# Create handles from scratch
	handles.append(mpatches.Patch(color='forestgreen', alpha=0.5, label=f'Load Demand'))
	ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1.01, 0.5), fancybox=True, shadow=True)

	plt.savefig(rf'outputs/{obj.common_fname}.png')
	vertical += 1

	# **************************************************************************************************************
	#        PLOT 10 - Pabs
	# **************************************************************************************************************

	handles = []
	ax = axes[vertical]

	pabs.plot(kind='bar', width=1.0, align='edge', edgecolor='maroon', color='forestgreen', alpha=0.5,
					   ax=ax)

	ax.set_ylabel('Pabs [kw]')

	# Create handles from scratch
	handles.append(mpatches.Patch(color='forestgreen', alpha=0.5, label=f'Pabs'))
	ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1.01, 0.5), fancybox=True, shadow=True)

	plt.savefig(rf'outputs/{obj.common_fname}.png')
	vertical += 1

	# **************************************************************************************************************
	#        PLOT 11 - Cost
	# **************************************************************************************************************

	handles = []
	ax = axes[vertical]

	cost.plot(kind='bar', width=1.0, align='edge', edgecolor='maroon', color='forestgreen', alpha=0.5,
			  ax=ax)

	ax.set_ylabel('Energy cost [kw]')

	# Create handles from scratch
	handles.append(mpatches.Patch(color='forestgreen', alpha=0.5, label=f'Energy cost'))
	ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1.01, 0.5), fancybox=True, shadow=True)

	plt.savefig(rf'outputs/{obj.common_fname}.png')
	vertical += 1

	# **************************************************************************************************************
	#        PLOT 12 - Total Cost
	# **************************************************************************************************************

	handles = []
	ax = axes[vertical]

	total_cost.plot(kind='bar', width=1.0, align='edge', edgecolor='maroon', color='forestgreen', alpha=0.5,
					   ax=ax)

	ax.set_ylabel('Total_Cost [$]')

	# Create handles from scratch
	handles.append(mpatches.Patch(color='forestgreen', alpha=0.5, label=f'Total_Cost'))
	ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1.01, 0.5), fancybox=True, shadow=True)

	plt.savefig(rf'outputs/{obj.common_fname}.png')
	vertical += 1