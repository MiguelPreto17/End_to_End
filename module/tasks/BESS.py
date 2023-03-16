"""
BESS class. This class encompasses all information regarding the BESS of the system.
"""
import math
import numpy as np
import pandas as pd

from helpers.dynamic_bess_helpers import *
from loguru import logger
from time import time


class BESS:

    def __init__(self):
        # Input data
        self.bess_asset = None  # Object to harbour the BESS's main characteristics
        self.bess_soc = None  # Object to harbour measured BESS SoC

        # BESS's data
        self.nominal_voltage = None  # Vdc
        self.initial_energy = None  # BESS initial energy capacity, before any degradation (kWh)
        self.nominal_energy = None  # kWh
        self.nominal_capacity = None  # kAh
        self.max_e_bess = None  # BES's maximum E content (kWh)
        self.min_e_bess = None  # BES's minimum E content (kWh) or BESS's reserve SoC (>= minimum SoC) (kWh)
        self.initial_e_bess = None  # BES's initial E content (kWh)
        self.p_dc_max_c = None  # Maximum power rate for charging the battery from DC view point (kW)
        self.p_dc_max_d = None  # Maximum power rate for discharging the battery from DC view point (kW)

    def configure(self, bess_asset, bess_soc):
        """
		Configure initialized BESS class with data from input JSON regarding the BES system
		:param bess_asset: main structure with BESS's characteristics ( = "bessAsset" structure)
		:type bess_asset: dict
		:param bess_soc: measured BESS SoC
		:type bess_soc: float
		:return: None
		:rtype: None
		"""

        logger.debug(f'Configuring BESS asset ...')
        self.bess_asset = bess_asset
        self.bess_soc = bess_soc

        # Assign batteries data (DC side)
        logger.debug(f' - parsing DC-side parameters')
        self.initial_energy = self.bess_asset.get('eNom')
        self.nominal_energy = self.bess_asset.get('actualENom')
        self.nominal_voltage = self.bess_asset.get('vNom')
        self.max_e_bess = self.bess_asset.get('maxSoc') / 100 * self.nominal_energy
        self.min_e_bess = self.bess_asset['minSoc'] / 100 * self.nominal_energy
        self.initial_e_bess = self.bess_soc / 100 * self.nominal_energy
        self.p_dc_max_c = self.bess_asset.get('bess_max_power_Ch')
        self.p_dc_max_d = self.bess_asset.get('bess_max_power_Disch')
