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

        # Inverter's data
        self.inverter_nominal_power = None  # kVA
        self.inverter_nominal_current = None  # kA
        self.inverter_nominal_voltage = None  # Vac
        self.inverter_max_idc = None  # Inverter's maximum admissible current on DC side (A)
        self.p_ac_max_c = None  # Maximum power rate for charging (kVA)
        self.p_ac_max_d = None  # Maximum power rate for discharging (kVA)

        # BES's data
        self.nominal_voltage = None  # Vdc
        self.initial_energy = None  # BESS initial energy capacity, before any degradation (kWh)
        self.nominal_energy = None  # kWh
        self.nominal_capacity = None  # kAh
        self.max_e_bess = None  # BES's maximum E content (kWh)
        self.min_e_bess = None  # BES's minimum E content (kWh) or BESS's reserve SoC (>= minimum SoC) (kWh)
        self.initial_e_bess = None  # BES's initial E content (kWh)
        self.c_rate_max_ch = None  # Maximum charging c-rate
        self.c_rate_max_disch = None  # Maximum discharging c-rate
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

        # Assign inverters data (AC side)
        logger.debug(f' - parsing AC-side parameters')
        self.inverter_nominal_power = self.bess_asset.get('invSNom')
        self.inverter_nominal_voltage = self.bess_asset.get('invVNom')
        self.inverter_nominal_current = self.inverter_nominal_power / (math.sqrt(3) * self.inverter_nominal_voltage)
        self.p_ac_max_c = self.inverter_nominal_power
        self.p_ac_max_d = self.inverter_nominal_power

        # Assign batteries data (DC side)
        logger.debug(f' - parsing DC-side parameters')
        self.initial_energy = self.bess_asset.get('eNom')
        self.nominal_energy = self.bess_asset.get('actualENom')
        self.nominal_voltage = self.bess_asset.get('vNom')
        self.nominal_capacity = self.nominal_energy / self.nominal_voltage
        self.max_e_bess = self.bess_asset.get('maxSoc') / 100 * self.nominal_energy
        self.min_e_bess = self.bess_asset['minSoc'] / 100 * self.nominal_energy
        self.initial_e_bess = self.bess_soc / 100 * self.nominal_energy
        self.inverter_max_idc = self.bess_asset.get('invMaxIDC')
        self.c_rate_max_ch = c_rate_limits(self.bess_asset.get('maxCCh'), self.nominal_capacity,
                                           self.inverter_max_idc)
        self.c_rate_max_disch = c_rate_limits(self.bess_asset.get('maxCDch'), self.nominal_capacity,
                                              self.inverter_max_idc)
        self.p_dc_max_c = self.c_rate_max_ch * self.nominal_capacity * self.nominal_voltage
        self.p_dc_max_d = self.c_rate_max_disch * self.nominal_capacity * self.nominal_voltage
