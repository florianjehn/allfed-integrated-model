############################### Parameters ####################################
##                                                                            #
##           Calculates all the parameters that feed into the optimizer       #
##                                                                            #
###############################################################################

# TODO: make a couple sub functions that deal with the different parts, where
#      it assigns the returned values to the constants.

import os
import sys
import numpy as np
from pandas.core import window

module_path = os.path.abspath(os.path.join("../.."))
if module_path not in sys.path:
    sys.path.append(module_path)

from src.food_system.meat_and_dairy import MeatAndDairy
from src.food_system.outdoor_crops import OutdoorCrops
from src.food_system.seafood import Seafood
from src.food_system.stored_food import StoredFood
from src.food_system.cellulosic_sugar import CellulosicSugar
from src.food_system.greenhouses import Greenhouses
from src.food_system.methane_scp import MethaneSCP
from src.food_system.seaweed import Seaweed
from src.food_system.feed_and_biofuels import FeedAndBiofuels

from src.food_system.food import Food
from src.food_system.unit_conversions import UnitConversions


class Parameters:
    def __init__(self):
        self.FIRST_TIME_RUN = True
        self.SIMULATION_STARTING_MONTH = "MAY"
        # Dictionary of the months to set the starting point of the model to
        # the months specified in parameters.py
        months_dict = {
            "JAN": 1,
            "FEB": 2,
            "MAR": 3,
            "APR": 4,
            "MAY": 5,
            "JUN": 6,
            "JUL": 7,
            "AUG": 8,
            "SEP": 9,
            "OCT": 10,
            "NOV": 11,
            "DEC": 12,
        }
        self.SIMULATION_STARTING_MONTH_NUM = months_dict[self.SIMULATION_STARTING_MONTH]

    def computeParameters(self, constants, scenarios_loader):

        assert self.FIRST_TIME_RUN
        self.FIRST_TIME_RUN = False

        PRINT_SCENARIO_PROPERTIES = True
        if PRINT_SCENARIO_PROPERTIES:
            print(scenarios_loader.scenario_description)

        # ensure every parameter has been initialized for the scenarios_loader
        scenarios_loader.check_all_set()

        constants_for_params = constants["inputs"]

        # time dependent constants as inputs to the optimizer
        time_consts = {}
        constants = {}

        constants = self.init_scenario(constants, constants_for_params)

        #### NUTRITION PER MONTH ####

        # https://docs.google.com/spreadsheets/d / 1RZqSrHNiIEuPQLtx1ebCd_kUcFvEF6Ea46xyzA5wU0s/edit#gid=1516287804

        constants = self.set_nutrition_per_month(constants, constants_for_params)

        ####SEAWEED INITIAL VARIABLES####

        constants, built_area = self.set_seaweed_params(constants, constants_for_params)
        time_consts["built_area"] = built_area

        #### FISH ####
        time_consts, constants = self.init_fish_params(
            constants, time_consts, constants_for_params
        )

        #### CROP PRODUCTION VARIABLES ####

        constants, outdoor_crops = self.init_outdoor_crops(
            constants, constants_for_params
        )

        #### CONSTANTS FOR GREENHOUSES ####

        time_consts = self.init_greenhouse_params(
            time_consts, constants_for_params, outdoor_crops
        )

        #### STORED FOOD VARIABLES ####

        stored_food = StoredFood(constants_for_params, outdoor_crops)
        stored_food.calculate_stored_food_to_use(self.SIMULATION_STARTING_MONTH_NUM)

        constants["SF_FRACTION_FAT"] = stored_food.SF_FRACTION_FAT
        constants["SF_FRACTION_PROTEIN"] = stored_food.SF_FRACTION_PROTEIN
        constants["stored_food"] = stored_food

        #### FEED AND BIOFUEL VARIABLES ####

        time_consts, feed_and_biofuels = self.init_feed_and_biofuels(
            time_consts, constants_for_params, outdoor_crops, stored_food
        )

        ####LIVESTOCK, MILK INITIAL VARIABLES####

        meat_and_dairy, constants, time_consts = self.init_meat_and_dairy_params(
            constants, time_consts, constants_for_params, feed_and_biofuels
        )

        #### CONSTANTS FOR METHANE SINGLE CELL PROTEIN ####

        time_consts, methane_scp = self.init_scp_params(
            time_consts, constants_for_params
        )

        #### CONSTANTS FOR CELLULOSIC SUGAR ####

        time_consts = self.init_cs_params(time_consts, constants_for_params)

        #### OTHER VARIABLES ####

        constants["inputs"] = constants_for_params

        PRINT_FIRST_MONTH_CONSTANTS = True

        if PRINT_FIRST_MONTH_CONSTANTS:
            self.print_constants(
                constants,
                time_consts,
                feed_and_biofuels,
                stored_food,
                methane_scp,
                meat_and_dairy,
            )

        return (constants, time_consts)

    def init_scenario(self, constants, constants_for_params):
        """
        Initialize the scenario for some constants used for the optimizer.
        """

        # population
        self.POP = constants_for_params["POP"]
        # population in units of millions of people
        self.POP_BILLIONS = constants_for_params["POP"] / 1e9
        constants = {}
        constants["POP"] = self.POP
        constants["POP_BILLIONS"] = self.POP_BILLIONS

        # full months duration of simulation

        # single valued inputs to optimizer
        constants["NMONTHS"] = constants_for_params["NMONTHS"]
        constants["ADD_FISH"] = constants_for_params["ADD_FISH"]
        constants["ADD_SEAWEED"] = constants_for_params["ADD_SEAWEED"]
        constants["ADD_MEAT"] = constants_for_params["ADD_MEAT"]
        constants["ADD_MILK"] = constants_for_params["ADD_MILK"]
        constants["ADD_STORED_FOOD"] = constants_for_params["ADD_STORED_FOOD"]
        constants["ADD_METHANE_SCP"] = constants_for_params["ADD_METHANE_SCP"]
        constants["ADD_CELLULOSIC_SUGAR"] = constants_for_params["ADD_CELLULOSIC_SUGAR"]
        constants["ADD_GREENHOUSES"] = constants_for_params["ADD_GREENHOUSES"]
        constants["ADD_OUTDOOR_GROWING"] = constants_for_params["ADD_OUTDOOR_GROWING"]

        return constants

    def set_nutrition_per_month(self, constants, constants_for_params):
        """
        Set the nutrition per month for the simulation.
        """

        # we will assume a 2100 kcals diet, and scale the "upper safe" nutrition
        # from the spreadsheet down to this "standard" level.
        # we also add 20% loss, according to the sorts of loss seen in this spreadsheet
        KCALS_DAILY = constants_for_params["NUTRITION"]["KCALS_DAILY"]
        FAT_DAILY = constants_for_params["NUTRITION"]["FAT_DAILY"]
        PROTEIN_DAILY = constants_for_params["NUTRITION"]["PROTEIN_DAILY"]
        constants["KCALS_DAILY"] = KCALS_DAILY
        constants["FAT_DAILY"] = FAT_DAILY
        constants["PROTEIN_DAILY"] = PROTEIN_DAILY

        Food.conversions.set_nutrition_requirements(
            kcals_daily=KCALS_DAILY,
            fat_daily=FAT_DAILY,
            protein_daily=PROTEIN_DAILY,
            population=self.POP,
        )

        constants["BILLION_KCALS_NEEDED"] = Food.conversions.billion_kcals_needed
        constants["THOU_TONS_FAT_NEEDED"] = Food.conversions.thou_tons_fat_needed
        constants[
            "THOU_TONS_PROTEIN_NEEDED"
        ] = Food.conversions.thou_tons_protein_needed

        constants["KCALS_MONTHLY"] = Food.conversions.kcals_monthly
        constants["PROTEIN_MONTHLY"] = Food.conversions.protein_monthly
        constants["FAT_MONTHLY"] = Food.conversions.fat_monthly

        CONVERSION_TO_KCALS = self.POP / 1e9 / KCALS_DAILY
        CONVERSION_TO_FAT = self.POP / 1e9 / FAT_DAILY
        CONVERSION_TO_PROTEIN = self.POP / 1e9 / PROTEIN_DAILY

        constants["CONVERSION_TO_KCALS"] = CONVERSION_TO_KCALS
        constants["CONVERSION_TO_FAT"] = CONVERSION_TO_FAT
        constants["CONVERSION_TO_PROTEIN"] = CONVERSION_TO_PROTEIN

        return constants

    def set_seaweed_params(self, constants, constants_for_params):
        """
        Set the seaweed parameters.
        """
        seaweed = Seaweed(constants_for_params)

        # determine area built to enable seaweed to grow there
        built_area = seaweed.get_built_area(constants_for_params)

        constants["INITIAL_SEAWEED"] = seaweed.INITIAL_SEAWEED
        constants["SEAWEED_KCALS"] = seaweed.SEAWEED_KCALS
        constants["HARVEST_LOSS"] = seaweed.HARVEST_LOSS
        constants["SEAWEED_FAT"] = seaweed.SEAWEED_FAT
        constants["SEAWEED_PROTEIN"] = seaweed.SEAWEED_PROTEIN

        constants["MINIMUM_DENSITY"] = seaweed.MINIMUM_DENSITY
        constants["MAXIMUM_DENSITY"] = seaweed.MAXIMUM_DENSITY
        constants["MAXIMUM_AREA"] = seaweed.MAXIMUM_AREA
        constants["INITIAL_AREA"] = seaweed.INITIAL_AREA

        return constants, built_area

    def init_outdoor_crops(self, constants, constants_for_params):
        """
        initialize the outdoor crops parameters
        """
        constants_for_params["STARTING_MONTH_NUM"] = self.SIMULATION_STARTING_MONTH_NUM

        outdoor_crops = OutdoorCrops(constants_for_params)
        outdoor_crops.calculate_rotation_ratios(constants_for_params)
        outdoor_crops.calculate_monthly_production(constants_for_params)

        constants["OG_FRACTION_FAT"] = outdoor_crops.OG_FRACTION_FAT
        constants["OG_FRACTION_PROTEIN"] = outdoor_crops.OG_FRACTION_PROTEIN

        constants[
            "OG_ROTATION_FRACTION_KCALS"
        ] = outdoor_crops.OG_ROTATION_FRACTION_KCALS
        constants["OG_ROTATION_FRACTION_FAT"] = outdoor_crops.OG_ROTATION_FRACTION_FAT
        constants[
            "OG_ROTATION_FRACTION_PROTEIN"
        ] = outdoor_crops.OG_ROTATION_FRACTION_PROTEIN

        return constants, outdoor_crops

    def init_fish_params(self, constants, time_consts, constants_for_params):
        """
        Initialize seafood parameters, not including seaweed
        """
        seafood = Seafood(constants_for_params)

        (
            production_kcals_fish_per_month,
            production_fat_fish_per_month,
            production_protein_fish_per_month,
        ) = seafood.get_seafood_production(constants_for_params)

        time_consts["production_kcals_fish_per_month"] = production_kcals_fish_per_month
        time_consts[
            "production_protein_fish_per_month"
        ] = production_protein_fish_per_month
        time_consts["production_fat_fish_per_month"] = production_fat_fish_per_month

        constants["FISH_KCALS"] = seafood.FISH_KCALS
        constants["FISH_FAT"] = seafood.FISH_FAT
        constants["FISH_PROTEIN"] = seafood.FISH_PROTEIN

        return time_consts, constants

    def init_greenhouse_params(self, time_consts, constants_for_params, outdoor_crops):
        """
        Initialize the greenhouse parameters.
        """

        greenhouses = Greenhouses(constants_for_params)

        greenhouse_area = greenhouses.get_greenhouse_area(
            constants_for_params, outdoor_crops
        )
        time_consts["greenhouse_area"] = greenhouse_area

        (
            greenhouse_kcals_per_ha,
            greenhouse_fat_per_ha,
            greenhouse_protein_per_ha,
        ) = greenhouses.get_greenhouse_yield_per_ha(constants_for_params, outdoor_crops)

        crops_food_produced = outdoor_crops.get_crop_production_minus_greenhouse_area(
            constants_for_params, greenhouses.greenhouse_fraction_area
        )
        time_consts["crops_food_produced"] = crops_food_produced
        time_consts["greenhouse_kcals_per_ha"] = greenhouse_kcals_per_ha
        time_consts["greenhouse_fat_per_ha"] = greenhouse_fat_per_ha
        time_consts["greenhouse_protein_per_ha"] = greenhouse_protein_per_ha

        return time_consts

    def init_cs_params(self, time_consts, constants_for_params):
        """
        Initialize the parameters for the cellulosic sugar model
        """

        cellulosic_sugar = CellulosicSugar(constants_for_params)
        cellulosic_sugar.calculate_monthly_cs_production(constants_for_params)

        production_kcals_cell_sugar_per_month = (
            cellulosic_sugar.get_monthly_cs_production()
        )
        time_consts[
            "production_kcals_cell_sugar_per_month"
        ] = production_kcals_cell_sugar_per_month

        return time_consts

    def init_scp_params(self, time_consts, constants_for_params):
        """
        Initialize the parameters for single cell protein
        """

        methane_scp = MethaneSCP(constants_for_params)
        methane_scp.calculate_monthly_scp_production(constants_for_params)

        (
            production_kcals_scp_per_month,
            production_fat_scp_per_month,
            production_protein_scp_per_month,
        ) = methane_scp.get_scp_production()
        time_consts["production_kcals_scp_per_month"] = production_kcals_scp_per_month
        time_consts["production_fat_scp_per_month"] = production_fat_scp_per_month
        time_consts[
            "production_protein_scp_per_month"
        ] = production_protein_scp_per_month

        return time_consts, methane_scp

    def init_feed_and_biofuels(
        self, time_consts, constants_for_params, outdoor_crops, stored_food
    ):
        """
        Initialize feed and biofuels parameters.
        """

        feed_and_biofuels = FeedAndBiofuels(constants_for_params)

        # make sure nonhuman consumption is always less than or equal to outdoor crops+stored food for all nutrients, pre-waste
        feed_and_biofuels.set_nonhuman_consumption_with_cap(
            constants_for_params, outdoor_crops, stored_food
        )

        nonhuman_consumption = feed_and_biofuels.nonhuman_consumption

        # post waste
        time_consts["nonhuman_consumption"] = nonhuman_consumption

        return time_consts, feed_and_biofuels

    def init_meat_and_dairy_params(
        self, constants, time_consts, constants_for_params, feed_and_biofuels
    ):
        """
        Meat and dairy are initialized here.
        NOTE: Important convention: anything pre-waste is marked so. Everything else
              that could include waste should be assumed to be post-waste if not marked

        """

        meat_and_dairy = MeatAndDairy(constants_for_params)

        time_consts, meat_and_dairy = self.init_grazing_params(
            constants_for_params, time_consts, meat_and_dairy
        )

        time_consts, meat_and_dairy = self.init_grain_fed_meat_params(
            time_consts, meat_and_dairy, feed_and_biofuels, constants_for_params
        )

        (constants, meat_culled, meat_and_dairy) = self.init_culled_meat_params(
            constants_for_params, constants, meat_and_dairy
        )

        time_consts["meat_culled"] = meat_culled

        # TODO: DELETE ME!
        # print("grain_fed_created_fat.in_units_percent_fed()")
        # print(grain_fed_balance.in_units_percent_fed())

        # store variables useful for extractor

        return meat_and_dairy, constants, time_consts

    def init_grazing_params(self, constants_for_params, time_consts, meat_and_dairy):

        meat_and_dairy.calculate_meat_milk_from_human_inedible_feed(
            constants_for_params
        )
        (
            grazing_milk_kcals,
            grazing_milk_fat,
            grazing_milk_protein,
        ) = meat_and_dairy.get_grazing_milk_produced_postwaste()
        time_consts["grazing_milk_kcals"] = grazing_milk_kcals
        time_consts["grazing_milk_fat"] = grazing_milk_fat
        time_consts["grazing_milk_protein"] = grazing_milk_protein

        # Post-waste cattle ongoing meat production from grazing
        (
            cattle_grazing_maintained_kcals,
            cattle_grazing_maintained_fat,
            cattle_grazing_maintained_protein,
        ) = meat_and_dairy.get_cattle_grazing_maintained()
        time_consts["cattle_grazing_maintained_kcals"] = cattle_grazing_maintained_kcals
        time_consts["cattle_grazing_maintained_fat"] = cattle_grazing_maintained_fat
        time_consts[
            "cattle_grazing_maintained_protein"
        ] = cattle_grazing_maintained_protein

        return time_consts, meat_and_dairy

    def init_grain_fed_meat_params(
        self, time_consts, meat_and_dairy, feed_and_biofuels, constants_for_params
    ):

        # APPLY FEED+BIOFUEL WASTE here
        # this is because the total contributed by feed and biofuels is actually applied to
        # the crops and stored food before waste, which means the subtraction of waste happens
        # to the feed and biofuels before subtracting from stored food and crops.
        # any reasonable cap of production should reflect a cap on the actual amount available
        # to humans.
        CROP_WASTE = 1 - constants_for_params["WASTE"]["CROPS"] / 100

        feed_post_waste = feed_and_biofuels.get_feed_post_waste(CROP_WASTE)

        nonhuman_consumption = feed_and_biofuels.get_nonhuman_consumption_post_waste(
            CROP_WASTE
        )

        # "grain" in all cases just means the stored food + outdoor crop production that is human edible and used for feed
        # this calculation is pre-waste for meat and feed
        # Chicken and pork only ever use "grain" as defined above in this model, not grasses
        meat_and_dairy.calculate_meat_and_dairy_from_grain(
            feed_and_biofuels.fed_to_animals_prewaste
        )
        # this calculation is pre-waste for the feed
        # no waste is applied for the grasses either.
        # the milk has had waste applied
        (
            grain_fed_milk_kcals,
            grain_fed_milk_fat,
            grain_fed_milk_protein,
        ) = meat_and_dairy.get_milk_from_human_edible_feed(constants_for_params)

        # post waste
        (
            grain_fed_meat_kcals,
            grain_fed_meat_fat,
            grain_fed_meat_protein,
        ) = meat_and_dairy.get_meat_from_human_edible_feed()

        # Cap the max created by the amount used, as conversion can't be > 1,
        # but the actual conversion only uses kcals
        (
            grain_fed_meat_fat_capped,
            grain_fed_meat_protein_capped,
            grain_fed_milk_fat_capped,
            grain_fed_milk_protein_capped,
        ) = meat_and_dairy.cap_fat_protein_to_amount_used(
            feed_and_biofuels.get_feed_post_waste(CROP_WASTE),
            grain_fed_meat_fat,
            grain_fed_meat_protein,
            grain_fed_milk_fat,
            grain_fed_milk_protein,
        )

        time_consts["grain_fed_meat_kcals"] = grain_fed_meat_kcals
        time_consts["grain_fed_meat_fat"] = grain_fed_meat_fat_capped
        time_consts["grain_fed_meat_protein"] = grain_fed_meat_protein_capped
        time_consts["grain_fed_milk_kcals"] = grain_fed_milk_kcals
        time_consts["grain_fed_milk_fat"] = grain_fed_milk_fat_capped
        time_consts["grain_fed_milk_protein"] = grain_fed_milk_protein_capped

        # print("meat fat")
        # print(grain_fed_meat_fat)
        # print("milk fat")
        # print(grain_fed_milk_fat)

        grain_fed_created_kcals = grain_fed_meat_kcals + grain_fed_milk_kcals
        grain_fed_created_fat = grain_fed_meat_fat_capped + grain_fed_milk_fat_capped
        grain_fed_created_protein = (
            grain_fed_meat_protein_capped + grain_fed_milk_protein_capped
        )
        time_consts["grain_fed_created_kcals"] = grain_fed_created_kcals
        time_consts["grain_fed_created_fat"] = grain_fed_created_fat
        time_consts["grain_fed_created_protein"] = grain_fed_created_protein

        assert (feed_post_waste.kcals >= grain_fed_created_kcals).all()

        return time_consts, meat_and_dairy

    def init_culled_meat_params(self, constants_for_params, constants, meat_and_dairy):

        # culled meat is based on the amount that wouldn't be maintained (excluding
        # maintained cattle as well as maintained chicken and pork)
        # this calculation is pre-waste for the meat maintained of course (no waste
        # applied to livestock maintained counts from which we determined the amount
        # of meat which can be culled)
        # the actual culled meat returned is post waste
        # NOTE: in the future, the extra caloric gain in reducing livestock populations
        #       slowly and caloric loss from increasing livestock populations slowly
        #       should also be calculated
        meat_and_dairy.calculate_animals_culled(constants_for_params)
        meat_and_dairy.calculated_culled_meat()

        feed_shutoff_delay_months = constants_for_params["DELAY"]["FEED_SHUTOFF_MONTHS"]
        meat_culled = meat_and_dairy.get_culled_meat_post_waste(
            constants_for_params, feed_shutoff_delay_months
        )

        constants["MEAT_CULLED_FRACTION_FAT"] = meat_and_dairy.meat_culled_fraction_fat
        constants[
            "MEAT_CULLED_FRACTION_PROTEIN"
        ] = meat_and_dairy.meat_culled_fraction_protein

        constants["CULL_DURATION_MONTHS"] = meat_and_dairy.CULL_DURATION_MONTHS

        constants["KG_PER_SMALL_ANIMAL"] = meat_and_dairy.KG_PER_SMALL_ANIMAL
        constants["KG_PER_MEDIUM_ANIMAL"] = meat_and_dairy.KG_PER_MEDIUM_ANIMAL
        constants["KG_PER_LARGE_ANIMAL"] = meat_and_dairy.KG_PER_LARGE_ANIMAL

        constants[
            "LARGE_ANIMAL_KCALS_PER_KG"
        ] = meat_and_dairy.LARGE_ANIMAL_KCALS_PER_KG
        constants["LARGE_ANIMAL_FAT_PER_KG"] = meat_and_dairy.LARGE_ANIMAL_FAT_PER_KG
        constants[
            "LARGE_ANIMAL_PROTEIN_PER_KG"
        ] = meat_and_dairy.LARGE_ANIMAL_PROTEIN_PER_KG

        constants[
            "MEDIUM_ANIMAL_KCALS_PER_KG"
        ] = meat_and_dairy.MEDIUM_ANIMAL_KCALS_PER_KG
        constants["MEDIUM_ANIMAL_FAT_PER_KG"] = meat_and_dairy.MEDIUM_ANIMAL_FAT_PER_KG
        constants[
            "MEDIUM_ANIMAL_PROTEIN_PER_KG"
        ] = meat_and_dairy.MEDIUM_ANIMAL_PROTEIN_PER_KG

        constants[
            "SMALL_ANIMAL_KCALS_PER_KG"
        ] = meat_and_dairy.SMALL_ANIMAL_KCALS_PER_KG
        constants["SMALL_ANIMAL_FAT_PER_KG"] = meat_and_dairy.SMALL_ANIMAL_FAT_PER_KG
        constants[
            "SMALL_ANIMAL_PROTEIN_PER_KG"
        ] = meat_and_dairy.SMALL_ANIMAL_PROTEIN_PER_KG
        return (constants, meat_culled, meat_and_dairy)

    def print_constants(
        self,
        constants,
        time_consts,
        feed_and_biofuels,
        stored_food,
        methane_scp,
        meat_and_dairy,
    ):
        print(
            """
            conversion to kcals/person/day:
            million dry caloric tons monthly * 12 = millon dry caloric tons annually
            million dry caloric tons annually * 1e6 = dry caloric tons annually
            dry caloric tons annually * 1e3 = dry caloric kg annually
            dry caloric kg annually * 4e3 = calories annually (1 kg dry caloric just means the equivalent of 1 kg of sugar)
            calories annually  / 365 = calories per day
            calories per day / 7.8e9 = calories per person per day globally
            therefore:
            calories per person per day globally = million tons dry caloric monthly * 12 * 1e6 * 4e6 / 365 / 7.8e9
            
            conversion to months worth of food:
            million tons dry caloric * 1e6 = tons dry caloric
            tons dry caloric * 1e3 = kg dry caloric
            kg dry caloric * 4e3 = calories
            calories / 2100 = people fed per day
            people fed per day / 30 = people fed per month
            people fed per month / 7.8e9 = fraction of global population fed for a month 
            fraction of global population fed for a month = months global population is fed from this food source
            therefore:
            months global population fed = million tons dry caloric *1e6*4e6 /2100/30/7.8e9

            NOTE: WASTE IS CONSIDERED IN THE FOLLOWING OUTPUTS at the following levels:
        """
        )
        print(constants["inputs"]["WASTE"])
        # used by world population
        print("")
        print("calories consumed per day")
        print(constants["KCALS_DAILY"])
        print("fat consumed per day grams")
        print(constants["FAT_DAILY"])
        print("protein consumed per day grams")
        print(constants["PROTEIN_DAILY"])
        print("")
        print(
            "INITIAL_HUMANS_KCALS "
            + str(self.POP)
            + " people consumed million tons dry caloric monthly"
        )
        print(-self.POP * constants["KCALS_MONTHLY"] / 4e6 / 1e6)
        print(
            "INITIAL_HUMANS_FAT "
            + str(self.POP)
            + " people consumed million tons monthly"
        )
        print(-self.POP * constants["FAT_MONTHLY"] / 1e3)
        print(
            "INITIAL_HUMANS_PROTEIN "
            + str(self.POP)
            + " people consumed million tons monthly"
        )
        print(-self.POP * constants["PROTEIN_MONTHLY"] / 1e3)
        print("")
        # 1000 tons protein or fat per dry caloric ton
        print("INITIAL_HUMANS_FAT consumed percentage")
        print(
            100
            * self.POP
            * constants["FAT_MONTHLY"]
            / 1e3
            / (self.POP * constants["KCALS_MONTHLY"] / 4e6 / 1e6)
        )
        print("INITIAL_HUMANS_PROTEIN consumed percentage")
        print(
            100
            * self.POP
            * constants["PROTEIN_MONTHLY"]
            / 1e3
            / (self.POP * constants["KCALS_MONTHLY"] / 4e6 / 1e6)
        )

        CROP_WASTE = constants["inputs"]["WASTE"]["CROPS"]

        amount_to_cancel_waste = 1 / (1 - CROP_WASTE / 100)

        CFP = time_consts["crops_food_produced"][0] * amount_to_cancel_waste

        outdoor_crops_RF_KCALS = constants["OG_ROTATION_FRACTION_KCALS"]
        outdoor_crops_RF_FAT = constants["OG_ROTATION_FRACTION_FAT"]
        outdoor_crops_RF_PROTEIN = constants["OG_ROTATION_FRACTION_PROTEIN"]

        # 1000 tons protein or fat per dry caloric ton
        print("")
        print("INITIAL_OG_KCALS million tons dry caloric monthly")
        print(CFP * 1e9 / 4e6 / 1e6)
        print("INITIAL_OG_FAT million tons monthly")
        print(CFP * constants["OG_FRACTION_FAT"] / 1e3)
        print("INITIAL_OG_PROTEIN million tons monthly")
        print(CFP * constants["OG_FRACTION_PROTEIN"] / 1e3)
        print("")
        print("INITIAL_OG_FAT percentage")
        print(100 * CFP * constants["OG_FRACTION_FAT"] / 1e3 / (CFP * 1e9 / 4e6 / 1e6))
        print("INITIAL_OG_PROTEIN percentage")
        print(
            100 * CFP * constants["OG_FRACTION_PROTEIN"] / 1e3 / (CFP * 1e9 / 4e6 / 1e6)
        )
        print("")
        print("INITIAL_OG_ROTATION_KCALS million tons dry caloric monthly")
        print(CFP * outdoor_crops_RF_KCALS * 1e9 / 4e6 / 1e6)
        print("INITIAL_OG_ROTATION_FAT million tons monthly")
        print(CFP * outdoor_crops_RF_FAT / 1e3)
        print("INITIAL_OG_ROTATION_PROTEIN million tons monthly")
        print(CFP * outdoor_crops_RF_PROTEIN / 1e3)
        print("")
        print("INITIAL_OG_ROTATION_FAT percentage")
        print(
            100
            * CFP
            * outdoor_crops_RF_FAT
            / 1e3
            / (CFP * outdoor_crops_RF_KCALS * 1e9 / 4e6 / 1e6)
        )
        print("INITIAL_OG_ROTATION_PROTEIN percentage")
        print(100 * outdoor_crops_RF_PROTEIN)
        INITIAL_SF_KCALS = constants["stored_food"].kcals * amount_to_cancel_waste
        SF_FRACTION_FAT = constants["SF_FRACTION_FAT"]
        SF_FRACTION_PROTEIN = constants["SF_FRACTION_PROTEIN"]

        print("")
        print("INITIAL_SF_KCALS million tons dry caloric")
        print(INITIAL_SF_KCALS * 1e9 / 4e6 / 1e6)
        print("INITIAL_SF_FAT million tons")

        print(INITIAL_SF_KCALS * SF_FRACTION_FAT / 1e3)
        print("INITIAL_SF_PROTEIN million tons")
        print(INITIAL_SF_KCALS * SF_FRACTION_PROTEIN / 1e3)
        print("")
        print("INITIAL_SF_FAT percentage")
        print(100 * SF_FRACTION_FAT)
        print("INITIAL_SF_PROTEIN percentage")
        print(100 * SF_FRACTION_PROTEIN)
        if feed_and_biofuels.FEED_MONTHLY_USAGE.kcals > 0:
            print("")
            print("INITIAL_FEED_KCALS million tons dry caloric monthly")
            print(-feed_and_biofuels.FEED_MONTHLY_USAGE.kcals * 1e9 / 4e6 / 1e6)
            print("INITIAL_FEED_FAT million tons monthly")
            print(-feed_and_biofuels.FEED_MONTHLY_USAGE.fat / 1e3)
            print("INITIAL_FEED_PROTEIN million tons monthly")
            print(-feed_and_biofuels.FEED_MONTHLY_USAGE.protein / 1e3)
            print("")
            print("INITIAL_FEED_fat percentage")
            print(
                100
                * feed_and_biofuels.FEED_MONTHLY_USAGE.fat
                / 1e3
                / (feed_and_biofuels.FEED_MONTHLY_USAGE.kcals * 1e9 / 4e6 / 1e6)
            )
            print("INITIAL_FEED_PROTEIN percentage")
            print(
                100
                * feed_and_biofuels.FEED_MONTHLY_USAGE.protein
                / 1e3
                / (feed_and_biofuels.FEED_MONTHLY_USAGE.kcals * 1e9 / 4e6 / 1e6)
            )
            print("")

            CPM = np.array(meat_and_dairy.chicken_pork_kcals)[0]
            LARGE_ANIMAL_KCALS_PER_KG = constants["LARGE_ANIMAL_KCALS_PER_KG"]
            LARGE_ANIMAL_FAT_PER_KG = constants["LARGE_ANIMAL_FAT_PER_KG"]
            LARGE_ANIMAL_PROTEIN_PER_KG = constants["LARGE_ANIMAL_PROTEIN_PER_KG"]
            grazing_maintained = meat_and_dairy.get_cattle_grazing_maintained()[0]
            CM = (
                grazing_maintained[0]
                + meat_and_dairy.cattle_grain_fed_maintained_kcals[0]
            )
            if CPM > 0:
                print("INITIAL_CH_PK_KCALS million tons dry caloric monthly")
                print(CPM * 1e9 / 4e6 / 1e6)
                print("INITIAL_CH_PK_FAT million tons monthly")
                print(meat_and_dairy.chicken_pork_fat[0] / 1e3)
                print("INITIAL_CH_PK_PROTEIN million tons monthly")
                print(meat_and_dairy.chicken_pork_protein[0] / 1e3)
                print("")
                print("INITIAL_CH_PK_FAT percentage")
                print(
                    100
                    * meat_and_dairy.chicken_pork_fat[0]
                    / 1e3
                    / (CPM * 1e9 / 4e6 / 1e6)
                )
                print("INITIAL_CH_PK_PROTEIN percentage")
                print(
                    100
                    * meat_and_dairy.chicken_pork_protein[0]
                    / 1e3
                    / (CPM * 1e9 / 4e6 / 1e6)
                )
                print("")
            else:
                print("(no chicken pork maintained considered yet)")
                print("")
            if CM > 0:
                print("INITIAL_CM_KCALS million tons dry caloric monthly")
                print(CM * 1e9 / 4e6 / 1e6)

                print("INITIAL_CM_FAT million tons monthly")
                print(
                    CM
                    * 1e9
                    / LARGE_ANIMAL_KCALS_PER_KG
                    * LARGE_ANIMAL_FAT_PER_KG
                    / 1e6
                    / 1e3
                )
                print("INITIAL_CM_PROTEIN million tons monthly")
                print(
                    CM
                    * 1e9
                    / LARGE_ANIMAL_KCALS_PER_KG
                    * LARGE_ANIMAL_PROTEIN_PER_KG
                    / 1e6
                    / 1e3
                )
                print("")
                print("INITIAL_CM_FAT percentage")
                print(
                    100
                    * CM
                    * 1e9
                    / LARGE_ANIMAL_KCALS_PER_KG
                    * LARGE_ANIMAL_FAT_PER_KG
                    / 1e6
                    / 1e3
                    / (CM * 1e9 / 4e6 / 1e6)
                )
                print("INITIAL_CM_PROTEIN percentage")
                print(
                    100
                    * CM
                    * 1e9
                    / LARGE_ANIMAL_KCALS_PER_KG
                    * LARGE_ANIMAL_PROTEIN_PER_KG
                    / 1e6
                    / 1e3
                    / (CM * 1e9 / 4e6 / 1e6)
                )
                print("")
                print("culled chicken, pork, and cattle per month.")
                print(
                    "reaches minimum after "
                    + str(constants["CULL_DURATION_MONTHS"])
                    + " months"
                )
            else:
                print("(no cattle maintained from human edible considered yet)")
                print("")

            MEAT_WASTE = constants["inputs"]["WASTE"]["MEAT"]

            CM_IN_KCALS = time_consts["cattle_grazing_maintained_kcals"][0] / (
                1 - MEAT_WASTE / 100
            )
            CM_IN_FAT = time_consts["cattle_grazing_maintained_fat"][0] / (
                1 - MEAT_WASTE / 100
            )
            CM_IN_PROTEIN = time_consts["cattle_grazing_maintained_protein"][0] / (
                1 - MEAT_WASTE / 100
            )

            if CM_IN_KCALS > 0:
                print(
                    "INITIAL_CM_IN_KCALS million tons dry caloric monthly (cattle meat produced in 2020 monthly)"
                )
                print(CM_IN_KCALS * 1e9 / 4e6 / 1e6)

                print("INITIAL_CM_IN_FAT million tons monthly")
                print(CM_IN_FAT / 1e3)
                print("INITIAL_CM_IN_PROTEIN million tons monthly")
                print(CM_IN_PROTEIN / 1e3)
                print("")
                print("INITIAL_CM_IN_FAT percentage")
                print(100 * CM_IN_FAT / 1e3 / (CM_IN_KCALS * 1e9 / 4e6 / 1e6))
                print("INITIAL_CM_IN_PROTEIN percentage")
                print(100 * CM_IN_PROTEIN / 1e3 / (CM_IN_KCALS * 1e9 / 4e6 / 1e6))
                print("")
            else:
                print("No meat (would be cattle) from inedible sources")
                print("")

            print("")
            if constants["inputs"]["CULL_ANIMALS"]:
                print("INITIAL_CULLED_KCALS million tons dry caloric monthly")
                print("INITIAL_CULLED_FAT million tons monthly")
                print("INITIAL_CULLED_PROTEIN million tons monthly")
                print("")
                print("INITIAL_CULLED_FAT percentage")
                print("INITIAL_CULLED_PROTEIN percentage")
                print("")
        else:
            print("No Feed Usage")

        if constants["ADD_MILK"]:
            grazing_milk_kcals = time_consts["grazing_milk_kcals"][0]
            grazing_milk_fat = time_consts["grazing_milk_fat"][0]
            grazing_milk_protein = time_consts["grazing_milk_protein"][0]
            MILK_WASTE = constants["inputs"]["WASTE"]["MILK"]
            print("INITIAL_MILK_KCALS million tons dry caloric monthly")
            print(grazing_milk_kcals / (1 - MILK_WASTE / 100) * 1e9 / 4e6 / 1e6)

            print("INITIAL_MILK_FAT million tons monthly")
            print(grazing_milk_fat / (1 - MILK_WASTE / 100) / 1e3)
            print("INITIAL_MILK_PROTEIN million tons monthly")
            print(grazing_milk_protein / (1 - MILK_WASTE / 100) / 1e3)
            print("")
            print("INITIAL_MILK_FAT percentage")
            print(
                100
                * grazing_milk_fat
                / (1 - MILK_WASTE / 100)
                / 1e3
                / (grazing_milk_kcals / (1 - MILK_WASTE / 100) * 1e9 / 4e6 / 1e6)
            )
            print("INITIAL_MILK_PROTEIN percentage")
            print(
                100
                * grazing_milk_protein
                / (1 - MILK_WASTE / 100)
                / 1e3
                / (grazing_milk_kcals / (1 - MILK_WASTE / 100) * 1e9 / 4e6 / 1e6)
            )
            print("")
        if constants["ADD_FISH"]:
            FISH_WASTE = constants["inputs"]["WASTE"]["SEAFOOD"]
            production_kcals_fish_per_month = time_consts[
                "production_kcals_fish_per_month"
            ][0]
            production_fat_fish_per_month = time_consts[
                "production_fat_fish_per_month"
            ][0]
            production_protein_fish_per_month = time_consts[
                "production_protein_fish_per_month"
            ][0]

            print("INITIAL_FISH_KCALS million tons dry caloric monthly")
            print(
                production_kcals_fish_per_month
                / (1 - FISH_WASTE / 100)
                * 1e9
                / 4e6
                / 1e6
            )

            print("INITIAL_FISH_PROTEIN million tons monthly")
            print(production_protein_fish_per_month / (1 - FISH_WASTE / 100) / 1e3)
            print("INITIAL_FISH_FAT million tons monthly")
            print(production_fat_fish_per_month / (1 - FISH_WASTE / 100) / 1e3)
            print("")
            print("INITIAL_FISH_FAT percentage")
            print(
                100
                * production_fat_fish_per_month
                / (1 - FISH_WASTE / 100)
                / 1e3
                / (
                    production_kcals_fish_per_month
                    / (1 - FISH_WASTE / 100)
                    * 1e9
                    / 4e6
                    / 1e6
                )
            )
            print("INITIAL_FISH_PROTEIN percentage")
            print(
                100
                * production_protein_fish_per_month
                / (1 - FISH_WASTE / 100)
                / 1e3
                / (
                    production_kcals_fish_per_month
                    / (1 - FISH_WASTE / 100)
                    * 1e9
                    / 4e6
                    / 1e6
                )
            )
            print("")
            print("")
        if feed_and_biofuels.biofuels.any_greater_than_zero():
            # 1000 tons protein/fat per dry caloric ton
            print("INITIAL_BIOFUEL_KCALS million tons dry caloric monthly")
            print(-feed_and_biofuels.biofuel_monthly_usage.kcals * 1e9 / 4e6 / 1e6)
            print("INITIAL_BIOFUEL_FAT million tons monthly")
            print(-feed_and_biofuels.biofuel_monthly_usage.fat / 1e3)
            print("INITIAL_BIOFUEL_PROTEIN million tons monthly")
            print(-feed_and_biofuels.biofuel_monthly_usage.protein / 1e3)
            print("INITIAL_BIOFUEL_FAT percentage")
            print(
                100
                * feed_and_biofuels.biofuel_monthly_usage.fat
                / 1e3
                / (feed_and_biofuels.biofuel_monthly_usage.kcals * 1e9 / 4e6 / 1e6)
            )
            print("INITIAL_BIOFUEL_PROTEIN percentage")
            print(
                100
                * feed_and_biofuels.biofuel_monthly_usage.protein
                / 1e3
                / (feed_and_biofuels.biofuel_monthly_usage.kcals * 1e9 / 4e6 / 1e6)
            )
        else:
            print("No biofuel usage")
            print("")

        if constants["ADD_METHANE_SCP"]:
            production_kcals_scp_per_month = time_consts[
                "production_kcals_scp_per_month"
            ]
            production_fat_scp_per_month = time_consts["production_fat_scp_per_month"]
            production_protein_scp_per_month = time_consts[
                "production_protein_scp_per_month"
            ]

            production_scp = Food(
                kcals=production_kcals_scp_per_month,
                fat=production_fat_scp_per_month,
                protein=production_protein_scp_per_month,
                kcals_units="billion kcals each month",
                fat_units="thousand tons each month",
                protein_units="thousand tons each month",
            )

            production_scp.in_units_kcals_grams_grams_per_capita_from_ratio(
                methane_scp.SCP_KCALS_PER_KG,
                methane_scp.SCP_FRAC_PROTEIN,
                methane_scp.SCP_FRAC_FAT,
            )
            print("production scp")
            print(production_scp)
