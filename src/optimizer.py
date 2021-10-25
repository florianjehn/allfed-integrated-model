import os
import sys
module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
	sys.path.append(module_path)

import numpy as np
from src.analysis import Analyzer
from src.plotter import Plotter
from src.validate import Validator

import pulp
from pulp import LpMaximize, LpProblem, LpVariable

####### TO DO ###
##  Crops
##		nonrelocated: we're closer to an answer here. Open phil: 
##			total production year 1, war happens month 5: 40%
##			already 20% harvested, remaining 20% (of ~5gtons annualized) after month 5 (7 months).
##			year 2: 10% of normal (but let's assume year 2, assume 20% rather than 10%)
##			year 2 would have ~1 gton dry carb equivalent, 20% of normal year
##			
##		relocated: 60% reduction plucked out of thin air (for later)
##		crop relocation within countries (for later)
##		
##  Assume food availability increases, increasing human food to chickens (for later)
## 	Assume different times till standard agriculture supplants resilient foods (12 months baseline). Not having resilient foods would extend.
## 	For small animals, should be able to slaughter them in less than a month (1 month baseline)
##  Cattle currently take a year to slaughter normally
##		Rate limit: all cattle in 3 months. (baseline)
##  Assume biofuel takes a month (baseline)
##		find biofuel values for total production, tons dry food, ask mike
##		roughly currently 60% sugarcane, 40% maize
## 	Assume waste drops
##		assume global average is waste from household from poor countries in one month (baseline)
##		waste from distribution doesn't change (baseline)
##		seaweed as 30% (baseline)
##   MULTIPLIER ON CS 

class Optimizer:

	def __init__(self):
		pass



	def optimize(self,constants):

		#full months duration of simulation
		NMONTHS=constants['inputs']['NMONTHS']
		# print("NMONTHS: "+str(NMONTHS))
		DAYS_IN_MONTH=30
		NDAYS=NMONTHS*DAYS_IN_MONTH
		ADD_FISH = constants['inputs']['ADD_FISH']
		ADD_SEAWEED=constants['inputs']['ADD_SEAWEED']
		# print("ADD_SEAWEED: "+str(ADD_SEAWEED))
		ADD_NONEGG_NONDAIRY_MEAT=constants['inputs']['ADD_NONEGG_NONDAIRY_MEAT']
		# print("ADD_NONEGG_NONDAIRY_MEAT: "+str(ADD_NONEGG_NONDAIRY_MEAT))
		ADD_DAIRY=constants['inputs']['ADD_DAIRY']
		# print("ADD_DAIRY: "+str(ADD_DAIRY))

		# eggs are lower priority than milk, so we're waiting till later to fill in data
		ADD_EGGS=False 
		# print("ADD_EGGS: "+str(ADD_EGGS))

		ADD_STORED_FOOD=constants['inputs']['ADD_STORED_FOOD']
		# print("ADD_STORED_FOOD: "+str(ADD_STORED_FOOD))
		ADD_METHANE_SCP = constants['inputs']['ADD_METHANE_SCP']
		# print("ADD_METHANE_SCP: "+str(ADD_METHANE_SCP))
		ADD_CELLULOSIC_SUGAR = constants['inputs']['ADD_CELLULOSIC_SUGAR']
		# print("ADD_CELLULOSIC_SUGAR: "+str(ADD_CELLULOSIC_SUGAR))
		ADD_GREENHOUSES = constants['inputs']['ADD_GREENHOUSES']
		# print("ADD_GREENHOUSES: "+str(ADD_GREENHOUSES))
		ADD_OUTDOOR_GROWING = constants['inputs']['ADD_OUTDOOR_GROWING']
		# print("ADD_OUTDOOR_GROWING: "+str(ADD_OUTDOOR_GROWING))
		MAXIMIZE_ONLY_FOOD_AFTER_DAY_150=False
		# print("MAXIMIZE_ONLY_FOOD_AFTER_DAY_150: "
			# + str(MAXIMIZE_ONLY_FOOD_AFTER_DAY_150))
		LIMIT_SEAWEED_AS_PERCENT_KCALS=constants['inputs']['LIMIT_SEAWEED_AS_PERCENT_KCALS']
		# print("LIMIT_SEAWEED_AS_PERCENT_KCALS: "+str(LIMIT_SEAWEED_AS_PERCENT_KCALS))
		MAX_SEAWEED_AS_PERCENT_KCALS=constants['inputs']['MAX_SEAWEED_AS_PERCENT_KCALS']#max percent of kcals from seaweed  per person

		VERBOSE = False
		# print("VERBOSE: "+str(VERBOSE))

		# Create the model to optimize
		model = LpProblem(name="optimization_nutrition", sense=LpMaximize)

		# Initialize the variable to maximize
		z = LpVariable(name="Least_Humans_Fed_Any_Month", lowBound=0)

		#### NUTRITION PER MONTH ####

		#https://docs.google.com/spreadsheets/d/1RZqSrHNiIEuPQLtx1ebCd_kUcFvEF6Ea46xyzA5wU0s/edit#gid=1516287804

		#we will assume a 2100 kcals diet, and scale the "upper safe" nutrients
		#from the spreadsheet down to this "standard" level.
		#we also add 20% loss, according to the sorts of loss seen in this spreadsheet
		KCALS_DAILY = constants['inputs']['NUTRITION']['KCALS_DAILY']
		PROTEIN_DAILY = constants['inputs']['NUTRITION']['PROTEIN_DAILY']
		FAT_DAILY = constants['inputs']['NUTRITION']['FAT_DAILY']

		# INTAKES={}
		# INTAKES['lower_severe']={}
		# INTAKES['lower_severe']['fat'] = 20 #grams per day
		# INTAKES['lower_severe']['protein'] = 46 #grams per day
		# INTAKES['lower_severe']['kcals'] = 1039 #per day
		# INTAKES['lower_moderate']={}
		# INTAKES['lower_moderate']['fat'] = 35 #grams per day
		# INTAKES['lower_moderate']['protein'] = 51 #grams per day
		# INTAKES['lower_moderate']['kcals'] = 1039 #per day
		KCALS_MONTHLY=KCALS_DAILY*DAYS_IN_MONTH#in kcals per person
		PROTEIN_MONTHLY=PROTEIN_DAILY*DAYS_IN_MONTH/1e9# in thousands of tons
		FAT_MONTHLY=FAT_DAILY*DAYS_IN_MONTH/1e9# in thousands of tons

		WORLD_POP=7.8e9
		KCAL_REQ_PER_MONTH = WORLD_POP * KCALS_MONTHLY/1e9

		KG_TO_1000_TONS=1/(1e6)

		# MILK_INIT_TONS_ANNUAL=constants['inputs']['MILK_INIT_TONS_ANNUAL']
		# MILK_INIT_TONS_DRY_CALORIC_EQIVALENT=MILK_INIT_TONS_ANNUAL*1e6/12 #first month
		KCALS_PER_DRY_CALORIC_TONS=4e6

		#https://www.ciwf.org.uk/media/5235182/Statistics-Dairy-cows.pdf
		ANNUAL_LITERS_PER_COW=2200
		KCALS_PER_LITER=609 #kcals for 1 liter whole milk, googled it

		# billion kcals per unit mass initial (first month)
		INITIAL_MILK_COWS = constants['inputs']['INITIAL_MILK_COWS']
		INITIAL_MILK_COWS_THOUSANDS = INITIAL_MILK_COWS/1000

		INIT_SMALL_ANIMALS=constants['inputs']['INIT_SMALL_ANIMALS']
		INIT_SMALL_NONEGG_ANIMALS=INIT_SMALL_ANIMALS
		INIT_MEDIUM_ANIMALS=constants['inputs']['INIT_MEDIUM_ANIMALS']
		INIT_LARGE_ANIMALS = constants['inputs']['INIT_LARGE_ANIMALS']

		INIT_LARGE_NONDAIRY_ANIMALS=INIT_LARGE_ANIMALS-INITIAL_MILK_COWS_THOUSANDS*1e3




		####SEAWEED INITIAL VARIABLES####

		#use "laver" variety for now from nutrition calculator
		#https://docs.google.com/spreadsheets/d/1RZqSrHNiIEuPQLtx1ebCd_kUcFvEF6Ea46xyzA5wU0s/edit#gid=1516287804
		WET_TO_DRY_MASS_CONVERSION=1/6
		
		#in order, in equal parts by mass:
		# Emi-tsunomata dry
		# Irish Moss dry
		# Kelp dry
		# Laver dry
		# Wakame dry
		# Fucus vesiculosus dry
		# Fucus spiralis dry

		#kcals per kg dry
		KCALS_PER_KG = \
			(2590
			+2940
			+2580
			+2100
			+2700
			+2520
			+3100)/7

		# dry fraction mass fat		
		MASS_FRACTION_FAT_DRY = \
			(.014
			+.010
			+.034
			+.017
			+.038
			+.031
			+.020)/7
	
		# dry fraction mass digestible protein		
		MASS_FRACTION_PROTEIN_DRY = (\
			0.770 * 0.153
			+ 0.770 * 0.091
			+ 0.768 * 0.101
			+ 0.862 * 0.349
			+ 0.700 * 0.182
			+ 0.147 * 0.060
			+ 0.147 * 0.100)/7

		SEAWEED_WASTE = constants['inputs']['WASTE']['SEAWEED']

		## seaweed billion kcals per 1000 tons wet
		# convert 1000 tons to kg 
		# convert kg to kcals
		# convert kcals to billions of kcals
		# convert wet mass seaweed to dry mass seaweed
		SEAWEED_KCALS = 1e6 * KCALS_PER_KG / 1e9 \
			* WET_TO_DRY_MASS_CONVERSION \
			* (1-SEAWEED_WASTE/100)

		## seaweed fraction digestible protein per 1000 ton wet
		SEAWEED_PROTEIN = MASS_FRACTION_PROTEIN_DRY \
			* WET_TO_DRY_MASS_CONVERSION \
			* (1-SEAWEED_WASTE/100)


		## seaweed fraction fat per 1000 tons wet
		SEAWEED_FAT = MASS_FRACTION_FAT_DRY \
			* WET_TO_DRY_MASS_CONVERSION \
			* (1-SEAWEED_WASTE/100)

		HARVEST_LOSS=constants['inputs']['HARVEST_LOSS']
		INITIAL_SEAWEED=constants['inputs']['INITIAL_SEAWEED']
		INITIAL_AREA=constants['inputs']['INITIAL_AREA']
		NEW_AREA_PER_DAY=constants['inputs']['NEW_AREA_PER_DAY']
		MINIMUM_DENSITY=constants['inputs']['MINIMUM_DENSITY']
		MAXIMUM_DENSITY=constants['inputs']['MAXIMUM_DENSITY']
		MAXIMUM_AREA=constants['inputs']['MAXIMUM_AREA']
		SEAWEED_PRODUCTION_RATE=constants['inputs']['SEAWEED_PRODUCTION_RATE']


		built_area=np.linspace(INITIAL_AREA,(NDAYS-1)*NEW_AREA_PER_DAY+INITIAL_AREA,NDAYS)
		built_area[built_area>MAXIMUM_AREA]=MAXIMUM_AREA
		seaweed_food_produced=[0]*NDAYS
		seaweed_food_produced_monthly=[0]*NMONTHS
		seaweed_wet_on_farm=[0]*NDAYS
		density=[0]*NDAYS
		used_area=[0]*NDAYS


		#### STORED FOOD VARIABLES ####

		# (nuclear event in mid-may)
		#mike's spreadsheet: https://docs.google.com/spreadsheets/d/19kzHpux690JTCo2IX2UA1faAd7R1QcBK/edit#gid=806987252

		TONS_DRY_CALORIC_EQIVALENT_SF=constants['inputs']['TONS_DRY_CALORIC_EQIVALENT_SF']
		INITIAL_SF_KCALS = KCALS_PER_DRY_CALORIC_TONS*TONS_DRY_CALORIC_EQIVALENT_SF/1e9 # billion kcals per unit mass initial

		INITIAL_SF_PROTEIN = constants['inputs']['INITIAL_SF_PROTEIN'] 
		INITIAL_SF_FAT = constants['inputs']['INITIAL_SF_FAT'] 

		print('INITIAL_SF_KCALS')
		print(INITIAL_SF_KCALS)
		print('INITIAL_SF_PROTEIN')
		print(INITIAL_SF_PROTEIN)
		print('INITIAL_SF_FAT')
		print(INITIAL_SF_FAT)


		#we need kcals from a unit of mass of stored food.
		#if the unit is mass, we know initial_sf_kcals/initial_sf_kcals is unitless 1

		SF_FRACTION_KCALS =	INITIAL_SF_KCALS \
			/ (INITIAL_SF_KCALS
				+ INITIAL_SF_PROTEIN
				+ INITIAL_SF_FAT)
		SF_FRACTION_FAT =	INITIAL_SF_FAT \
			/ (INITIAL_SF_KCALS
				+ INITIAL_SF_PROTEIN
				+ INITIAL_SF_FAT)
		SF_FRACTION_PROTEIN = INITIAL_SF_PROTEIN \
			/ (INITIAL_SF_KCALS
				+ INITIAL_SF_PROTEIN
				+ INITIAL_SF_FAT)


		SF_WASTE = constants['inputs']['WASTE']['CEREALS']
		#mass initial, units don't matter, we only need to ensure we use the correct 
		#fraction of kcals, fat, and protein per unit initial stored food.
		INITIAL_SF=INITIAL_SF_KCALS/SF_FRACTION_KCALS * (1-SF_WASTE/100)
		# so INITIAL_SF = INITIAL_SF_KCALS+ INITIAL_SF_PROTEIN+ INITIAL_SF_FAT
		# and we find:  INITIAL_SF*SF_FRACTION_FAT =INITIAL_SF_FAT
		# 

		stored_food_start=[0]*NMONTHS
		stored_food_end=[0]*NMONTHS
		stored_food_eaten=[0]*NMONTHS # if stored food isn't modeled, this stays zero

		#### FISH ####


		FISH_TONS_WET_2018 = 168936.71*1e3
		FISH_KCALS_PER_TON = 1310*1e3
		FISH_PROTEIN_PER_KG = 0.0204
		FISH_FAT_PER_KG = 0.0048
		
		FISH_WASTE = constants['inputs']['WASTE']['SEAFOOD']
		FISH_ESTIMATE = FISH_TONS_WET_2018 * (1-FISH_WASTE/100)
		#billions of kcals per month
		FISH_KCALS = FISH_ESTIMATE/12*FISH_KCALS_PER_TON/1e9
		FISH_KG_MONTHLY=FISH_ESTIMATE/12*1e3

		FISH_PROTEIN = FISH_KG_MONTHLY * FISH_PROTEIN_PER_KG / 1e6 #units of 1000s tons protein (so, value is in the hundreds of thousands of tons)
		FISH_FAT = FISH_KG_MONTHLY * FISH_FAT_PER_KG / 1e6#units of 1000s tons fat (so, value is in the tens of thousands of tons)
		

		#### NON EGG NONDAIRY MEAT ####

		#time from slaughter livestock to it turning into food
		#not functional yet
		# MEAT_DELAY = 1 #months

		#we use this spreadsheeet https://docs.google.com/spreadsheets/d/1ZyDrGI84TwhXj_QNicwjj9EPWLJ-r3xnAYMzKSAfWc0/edit#gid=824870019

		#edible meat, organs, and fat added

		KG_PER_SMALL_ANIMAL=2.36
		KG_PER_MEDIUM_ANIMAL=24.6
		KG_PER_LARGE_ANIMAL=269.7

		# see comparison between row https://docs.google.com/spreadsheets/d/1RZqSrHNiIEuPQLtx1ebCd_kUcFvEF6Ea46xyzA5wU0s/edit#gid=1516287804
		#kcal ratio:
		# compared to livestock meat stats here: https://docs.google.com/spreadsheets/d/1-upBP5-iPtBzyjm5zbeGlfuE4FwqLUyR/edit#gid=1495649381

		#this helps with fat vs other meat https://extension.tennessee.edu/publications/documents/pb1822.pdf
		#that's how we get 237 kg meat but not separable fat, and 91kg separable fat+bone
		#then, we use this spreadsheeet https://docs.google.com/spreadsheets/d/1ZyDrGI84TwhXj_QNicwjj9EPWLJ-r3xnAYMzKSAfWc0/edit#gid=824870019
		# to estimate 13% organ to meat ratio.


		#billions of kcals, 1000s of tons fat, 1000s of tons protein
		#includes organs, fat, and meat

		LARGE_ANIMAL_KCALS_PER_KG = 2750
		LARGE_ANIMAL_FAT_PER_KG = .182
		LARGE_ANIMAL_PROTEIN_PER_KG = .257

		MEDIUM_ANIMAL_KCALS_PER_KG = 3375
		MEDIUM_ANIMAL_FAT_PER_KG = .247
		MEDIUM_ANIMAL_PROTEIN_PER_KG = .129

		SMALL_ANIMAL_KCALS_PER_KG = 1525
		SMALL_ANIMAL_FAT_PER_KG = 0.076
		SMALL_ANIMAL_PROTEIN_PER_KG = .196



		KCALS_PER_SMALL_ANIMAL=SMALL_ANIMAL_KCALS_PER_KG*KG_PER_SMALL_ANIMAL/1e9
		FAT_PER_SMALL_ANIMAL=SMALL_ANIMAL_FAT_PER_KG*KG_PER_SMALL_ANIMAL*KG_TO_1000_TONS
		PROTEIN_PER_SMALL_ANIMAL=SMALL_ANIMAL_PROTEIN_PER_KG*KG_PER_SMALL_ANIMAL*KG_TO_1000_TONS

		KCALS_PER_MEDIUM_ANIMAL=MEDIUM_ANIMAL_KCALS_PER_KG*KG_PER_MEDIUM_ANIMAL/1e9
		FAT_PER_MEDIUM_ANIMAL=MEDIUM_ANIMAL_FAT_PER_KG*KG_PER_MEDIUM_ANIMAL*KG_TO_1000_TONS
		PROTEIN_PER_MEDIUM_ANIMAL=MEDIUM_ANIMAL_PROTEIN_PER_KG*KG_PER_MEDIUM_ANIMAL*KG_TO_1000_TONS

		KCALS_PER_LARGE_ANIMAL=LARGE_ANIMAL_KCALS_PER_KG*KG_PER_LARGE_ANIMAL/1e9
		FAT_PER_LARGE_ANIMAL=LARGE_ANIMAL_FAT_PER_KG*KG_PER_LARGE_ANIMAL*KG_TO_1000_TONS
		PROTEIN_PER_LARGE_ANIMAL=LARGE_ANIMAL_PROTEIN_PER_KG*KG_PER_LARGE_ANIMAL*KG_TO_1000_TONS

		KCALS_PER_1000_LARGE_ANIMALS=KCALS_PER_LARGE_ANIMAL * 1000
		FAT_PER_1000_LARGE_ANIMALS=FAT_PER_LARGE_ANIMAL * 1000
		PROTEIN_PER_1000_LARGE_ANIMALS=PROTEIN_PER_LARGE_ANIMAL * 1000

		INIT_NONEGG_NONDAIRY_MEAT_KCALS = \
			INIT_SMALL_NONEGG_ANIMALS*KCALS_PER_SMALL_ANIMAL \
			+ INIT_MEDIUM_ANIMALS*KCALS_PER_MEDIUM_ANIMAL \
			+ INIT_LARGE_NONDAIRY_ANIMALS*KCALS_PER_LARGE_ANIMAL 
		INIT_NONEGG_NONDAIRY_MEAT_FAT = \
			INIT_SMALL_NONEGG_ANIMALS*FAT_PER_SMALL_ANIMAL \
			+ INIT_MEDIUM_ANIMALS*FAT_PER_MEDIUM_ANIMAL \
			+ INIT_LARGE_NONDAIRY_ANIMALS*FAT_PER_LARGE_ANIMAL
		INIT_NONEGG_NONDAIRY_MEAT_PROTEIN = \
			INIT_SMALL_NONEGG_ANIMALS*PROTEIN_PER_SMALL_ANIMAL \
			+ INIT_MEDIUM_ANIMALS*PROTEIN_PER_MEDIUM_ANIMAL \
			+ INIT_LARGE_NONDAIRY_ANIMALS*PROTEIN_PER_LARGE_ANIMAL


		MEAT_FRACTION_KCALS = INIT_NONEGG_NONDAIRY_MEAT_KCALS \
			/ (INIT_NONEGG_NONDAIRY_MEAT_KCALS
				+ INIT_NONEGG_NONDAIRY_MEAT_PROTEIN
				+ INIT_NONEGG_NONDAIRY_MEAT_FAT)
		MEAT_FRACTION_FAT =	INIT_NONEGG_NONDAIRY_MEAT_FAT \
			/ (INIT_NONEGG_NONDAIRY_MEAT_KCALS
				+ INIT_NONEGG_NONDAIRY_MEAT_PROTEIN
				+ INIT_NONEGG_NONDAIRY_MEAT_FAT)
		MEAT_FRACTION_PROTEIN = INIT_NONEGG_NONDAIRY_MEAT_PROTEIN \
			/ (INIT_NONEGG_NONDAIRY_MEAT_KCALS
				+ INIT_NONEGG_NONDAIRY_MEAT_PROTEIN
				+ INIT_NONEGG_NONDAIRY_MEAT_FAT)

		MEAT_WASTE = constants['inputs']['WASTE']['MEAT']
		print(INIT_NONEGG_NONDAIRY_MEAT_KCALS)
		print("days")
		print(INIT_NONEGG_NONDAIRY_MEAT_KCALS/(7.8*2100))
		print("dry caloric")
		print(INIT_NONEGG_NONDAIRY_MEAT_KCALS*1e9/4e6/1e6)
		#arbitrary mass units


		if(constants['inputs']['INCLUDE_ECONOMICS']):
			# if we assume the rich serve the remaining food to animals and 
			# eating the animals
			
			#billions kcals
			MEAT_CURRENT_YIELD_PER_YEAR = 158 #million tons dry caloric
			MEAT_SUSTAINABLE_YIELD_PER_YEAR = 100.4 #million tons dry caloric

			FRACTION_TO_SLAUGHTER = 1-MEAT_SUSTAINABLE_YIELD_PER_YEAR/MEAT_CURRENT_YIELD_PER_YEAR

			MEAT_SUSTAINABLE_YIELD_PER_MONTH = \
				MEAT_SUSTAINABLE_YIELD_PER_YEAR/12*4e12/1e9
			
			SUSTAINED_MEAT_MONTHLY = MEAT_SUSTAINABLE_YIELD_PER_YEAR

			print("SUSTAINED_MEAT_MONTHLY")
			print(SUSTAINED_MEAT_MONTHLY)

		else:
			SUSTAINED_MEAT_MONTHLY = 0
			FRACTION_TO_SLAUGHTER = 1

		print('SUSTAINED_MEAT_MONTHLY')
		print(SUSTAINED_MEAT_MONTHLY)
		print('FRACTION_TO_SLAUGHTER')
		print(FRACTION_TO_SLAUGHTER)
		INITIAL_NONEGG_NONDAIRY_MEAT=INIT_NONEGG_NONDAIRY_MEAT_KCALS \
			/ MEAT_FRACTION_KCALS \
			* (1-MEAT_WASTE/100) \
			* FRACTION_TO_SLAUGHTER

		print("INITIAL_NONEGG_NONDAIRY_MEAT")
		print(INITIAL_NONEGG_NONDAIRY_MEAT)

		nonegg_nondairy_meat_start=[0]*NMONTHS
		nonegg_nondairy_meat_end=[0]*NMONTHS
		nonegg_nondairy_meat_eaten=[0]*NMONTHS


		#### CROP PRODUCTION VARIABLES ####
		#assumption: outdoor crop production is very similar in nutritional
		# profile to stored food
		#reference: row 58, 'area and scaling by month' tab  https://docs.google.com/spreadsheets/d/1-upBP5-iPtBzyjm5zbeGlfuE4FwqLUyR/edit#gid=642022040
		JAN_YIELD = 543e6 #tonnes dry carb equivalent
		FEB_YIELD = 86e6 #tonnes dry carb equivalent
		MAR_YIELD = 117e6 #tonnes dry carb equivalent
		APR_YIELD = 167e6 #tonnes dry carb equivalent
		MAY_YIELD = 164e6 #tonnes dry carb equivalent
		JUN_YIELD = 199e6 #tonnes dry carb equivalent
		JUL_YIELD = 427e6 #tonnes dry carb equivalent
		AUG_YIELD = 383e6 #tonnes dry carb equivalent
		SEP_YIELD = 505e6 #tonnes dry carb equivalent
		OCT_YIELD = 926e6 #tonnes dry carb equivalent
		NOV_YIELD = 667e6 #tonnes dry carb equivalent
		DEC_YIELD = 661e6 #tonnes dry carb equivalent

		# print('tons per hectare per year')
		# print(np.sum(np.array([JAN_YIELD, FEB_YIELD, MAR_YIELD, APR_YIELD, MAY_YIELD, JUN_YIELD, JUL_YIELD, AUG_YIELD, SEP_YIELD, OCT_YIELD, NOV_YIELD, DEC_YIELD]))/500e6)
		# quit()
			#billions of kcals
		JAN_KCALS_OG=JAN_YIELD*KCALS_PER_DRY_CALORIC_TONS / 1e9
		FEB_KCALS_OG=FEB_YIELD*KCALS_PER_DRY_CALORIC_TONS / 1e9
		MAR_KCALS_OG=MAR_YIELD*KCALS_PER_DRY_CALORIC_TONS / 1e9
		APR_KCALS_OG=APR_YIELD*KCALS_PER_DRY_CALORIC_TONS / 1e9
		MAY_KCALS_OG=MAY_YIELD*KCALS_PER_DRY_CALORIC_TONS / 1e9
		JUN_KCALS_OG=JUN_YIELD*KCALS_PER_DRY_CALORIC_TONS / 1e9
		JUL_KCALS_OG=JUL_YIELD*KCALS_PER_DRY_CALORIC_TONS / 1e9
		AUG_KCALS_OG=AUG_YIELD*KCALS_PER_DRY_CALORIC_TONS / 1e9
		SEP_KCALS_OG=SEP_YIELD*KCALS_PER_DRY_CALORIC_TONS / 1e9
		OCT_KCALS_OG=OCT_YIELD*KCALS_PER_DRY_CALORIC_TONS / 1e9
		NOV_KCALS_OG=NOV_YIELD*KCALS_PER_DRY_CALORIC_TONS / 1e9
		DEC_KCALS_OG=DEC_YIELD*KCALS_PER_DRY_CALORIC_TONS / 1e9

		KCALS_PREDISASTER_BEFORE_MAY = JAN_KCALS_OG+FEB_KCALS_OG+MAR_KCALS_OG+APR_KCALS_OG+MAY_KCALS_OG
		KCALS_PREDISASTER_AFTER_MAY = JUN_KCALS_OG+JUL_KCALS_OG+AUG_KCALS_OG+SEP_KCALS_OG+OCT_KCALS_OG+NOV_KCALS_OG+DEC_KCALS_OG

		KCALS_PREDISASTER_ANNUAL=JAN_KCALS_OG+FEB_KCALS_OG+MAR_KCALS_OG+APR_KCALS_OG+MAY_KCALS_OG+JUN_KCALS_OG+JUL_KCALS_OG+AUG_KCALS_OG+SEP_KCALS_OG+OCT_KCALS_OG+NOV_KCALS_OG+DEC_KCALS_OG


		# year 1: post disaster yield annual = 40% of predisaster yields, with war in mid-may
		RATIO_KCALS_POSTDISASTER_Y1 = constants['inputs']['RATIO_KCALS_POSTDISASTER']['Y1']

		RATIO_KCALS_POSTDISASTER_AFTER_MAY_Y1 = (RATIO_KCALS_POSTDISASTER_Y1
			* KCALS_PREDISASTER_ANNUAL
			- KCALS_PREDISASTER_BEFORE_MAY) \
			/ KCALS_PREDISASTER_AFTER_MAY

		# year 2: 20% of normal year
		RATIO_KCALS_POSTDISASTER_Y2 = constants['inputs']['RATIO_KCALS_POSTDISASTER']['Y2']
		RATIO_KCALS_POSTDISASTER_Y3 = constants['inputs']['RATIO_KCALS_POSTDISASTER']['Y3']
		RATIO_KCALS_POSTDISASTER_Y4 = constants['inputs']['RATIO_KCALS_POSTDISASTER']['Y4']

		KCALS_GROWN=[\
			MAY_KCALS_OG * RATIO_KCALS_POSTDISASTER_AFTER_MAY_Y1,
			JUN_KCALS_OG * RATIO_KCALS_POSTDISASTER_AFTER_MAY_Y1,
			JUL_KCALS_OG * RATIO_KCALS_POSTDISASTER_AFTER_MAY_Y1,
			AUG_KCALS_OG * RATIO_KCALS_POSTDISASTER_AFTER_MAY_Y1,
			SEP_KCALS_OG * RATIO_KCALS_POSTDISASTER_AFTER_MAY_Y1,
			OCT_KCALS_OG * RATIO_KCALS_POSTDISASTER_AFTER_MAY_Y1,
			NOV_KCALS_OG * RATIO_KCALS_POSTDISASTER_AFTER_MAY_Y1,
			DEC_KCALS_OG * RATIO_KCALS_POSTDISASTER_AFTER_MAY_Y1,
			JAN_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y2,
			FEB_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y2,
			MAR_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y2,
			APR_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y2,
			MAY_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y2,
			JUN_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y2,
			JUL_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y2,
			AUG_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y2,
			SEP_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y2,
			OCT_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y2,
			NOV_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y2,
			DEC_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y2,
			JAN_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y3,
			FEB_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y3,
			MAR_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y3,
			APR_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y3,
			MAY_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y3,
			JUN_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y3,
			JUL_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y3,
			AUG_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y3,
			SEP_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y3,
			OCT_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y3,
			NOV_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y3,
			DEC_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y3,
			JAN_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y4,
			FEB_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y4,
			MAR_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y4,
			APR_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y4,
			MAY_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y4,
			JUN_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y4,
			JUL_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y4,
			AUG_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y4,
			SEP_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y4,
			OCT_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y4,
			NOV_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y4,
			DEC_KCALS_OG * RATIO_KCALS_POSTDISASTER_Y4]

		CROP_WASTE = constants['inputs']['WASTE']['CROPS']

		TOTAL_CROP_AREA = 500e6 #500 million hectares in tropics

		GH_DRY_TONS_PER_HECTARE_PER_YEAR = 6.4 #tons/ha/yr, NOT multiplied by 80% of area used
		GH_KCALS_PER_HECTARE_PER_MONTH =  GH_DRY_TONS_PER_HECTARE_PER_YEAR*KCALS_PER_DRY_CALORIC_TONS/12




		# we know:
		# 	units_sf_mass*SF_FRACTION_KCALS=sf_kcals
		# and
		# 	units_sf_mass*SF_FRACTION_PROTEIN=sf_protein
		# so
		# 	units_sf_mass = sf_kcals/SF_FRACTION_KCALS
		# => assumption listed previously =>
		# 	units_og_mass = og_kcals/SF_FRACTION_KCALS
		# 	units_og_mass = og_protein/SF_FRACTION_PROTEIN
		# therefore
		# 	og_protein = og_kcals*SF_FRACTION_PROTEIN/SF_FRACTION_KCALS

		
		#see z152 on 'FAOSTAT food balance' tab https://docs.google.com/spreadsheets/d/1-upBP5-iPtBzyjm5zbeGlfuE4FwqLUyR/edit#gid=102948593
		OG_PROTEIN_PER_KCALS = 0.00946373696 #1000 tons protein per billion kcals
		OG_FAT_PER_KCALS = 0.01361071549 #1000 tons fat per billion kcals
		

		#### CONSTANTS FOR GREENHOUSES ####
		#greenhouses tab
		#assumption: greenhouse crop production is very similar in nutritional
		# profile to stored food
		# reference: see https://docs.google.com/spreadsheets/d/1f9eVD14Y2d9vmLFP3OsJPFA5d2JXBU-63MTz8MlB1rY/edit#gid=756212200
		GREENHOUSE_SLOPE_MULTIPLIER = constants['inputs']['GREENHOUSE_SLOPE_MULTIPLIER']
		GREENHOUSE_PERCENT_KCALS=list(np.array([0,0,0,0,0,11.60,11.60,11.60,23.21,23.21,23.21,34.81,34.81,34.81,46.41,46.41,46.41,58.01,58.01,58.01,69.62,69.62,69.62,81.22,81.22,81.22,92.82,92.82,92.82,104.43,104.43,104.43,116.03,116.03,116.03,127.63,127.63,127.63,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24,139.24])*GREENHOUSE_SLOPE_MULTIPLIER*(1-CROP_WASTE/100))

		import matplotlib.pyplot as plt
		if(ADD_GREENHOUSES):
			production_kcals_greenhouses_per_month = []
			for x in GREENHOUSE_PERCENT_KCALS:
				production_kcals_greenhouses_per_month.append(x / 100 * KCAL_REQ_PER_MONTH)
		else:
			production_kcals_greenhouses_per_month=[0]*len(GREENHOUSE_PERCENT_KCALS)

		greenhouse_area = list(np.array(production_kcals_greenhouses_per_month)*1e9/GH_KCALS_PER_HECTARE_PER_MONTH)
		KCALS_GROWN_MINUS_GREENHOUSE = []
		for i in range(0,len(KCALS_GROWN)):
			KCALS_GROWN_MINUS_GREENHOUSE.append(\
				KCALS_GROWN[i]*(1-greenhouse_area[i]/TOTAL_CROP_AREA)\
			)
			print((1-greenhouse_area[i]/TOTAL_CROP_AREA))
		# quit()
		# GH_DRY_TONS_PER_HECTARE_PER_YEAR*4e6/1e9
		
		# print("GH_DRY_TONS_PER_HECTARE_PER_YEAR*4e6/1e9")
		# print(GH_DRY_TONS_PER_HECTARE_PER_YEAR*4e6/1e9)
		# print("POTATO_CALORIES")
		# print(POTATO_CALORIES)

		SPRING_WHEAT_FRACTION_OF_ROTATION = 0.20
		SPRING_BARLEY_FRACTION_OF_ROTATION = 0.25
		POTATO_FRACTION_OF_ROTATION = 0.22
		RAPESEED_FRACTION_OF_ROTATION = 0.33

		#billion kcals per hectare per year
		SPRING_WHEAT_CALORIES = 21056*1e3/1e9 * SPRING_WHEAT_FRACTION_OF_ROTATION
		SPRING_BARLEY_CALORIES = 22528*1e3/1e9 * SPRING_BARLEY_FRACTION_OF_ROTATION
		POTATO_CALORIES = 37410*1e3/1e9 * POTATO_FRACTION_OF_ROTATION
		RAPESEED_CALORIES = 10670*1e3/1e9 * RAPESEED_FRACTION_OF_ROTATION

		SUM_CALORIES = SPRING_WHEAT_CALORIES \
			+ SPRING_BARLEY_CALORIES \
			+ POTATO_CALORIES \
			+ RAPESEED_CALORIES

		# SUM_CALORIES_PER_HECTARE = 0.0237337
		SUM_CALORIES_PER_HECTARE = 9.69/5*1.4*4e6/1e9 # 0.010853 

		# GREENHOUSE_YIELD_MULTIPLIER = \
			# (GH_DRY_TONS_PER_HECTARE_PER_YEAR*4e6/1e9)/SUM_CALORIES
		GREENHOUSE_YIELD_MULTIPLIER = 1
		print(GREENHOUSE_YIELD_MULTIPLIER)

		GREENHOUSE_CALORIES = SUM_CALORIES_PER_HECTARE/12#SUM_CALORIES*GREENHOUSE_YIELD_MULTIPLIER

		#billion kcals per hectare per year
		ADJUSTED_POTATO_CALORIES = POTATO_CALORIES*GREENHOUSE_YIELD_MULTIPLIER 

		#thousand tons protein per hectare per year
		ADJUSTED_POTATO_PROTEIN = 0.804/1e3 * \
			GREENHOUSE_YIELD_MULTIPLIER * POTATO_FRACTION_OF_ROTATION

		#thousand tons protein per hectare per year
		ADJUSTED_SPRING_BARLEY_PROTEIN = 0.634/1e3 * \
			GREENHOUSE_YIELD_MULTIPLIER * SPRING_BARLEY_FRACTION_OF_ROTATION

		#thousand tons protein per hectare per year
		ADJUSTED_SPRING_WHEAT_PROTEIN = 0.634/1e3 * \
			GREENHOUSE_YIELD_MULTIPLIER * SPRING_WHEAT_FRACTION_OF_ROTATION

		#thousand tons protein per hectare per year
		ADJUSTED_RAPESEED_PROTEIN = 0/1e3 * \
			GREENHOUSE_YIELD_MULTIPLIER * RAPESEED_FRACTION_OF_ROTATION

		#thousand tons fat per hectare per year
		ADJUSTED_POTATO_FAT = 0.043/1e3 * \
			GREENHOUSE_YIELD_MULTIPLIER * POTATO_FRACTION_OF_ROTATION

		#thousand tons fat per hectare per year
		ADJUSTED_SPRING_WHEAT_FAT = 0.074/1e3 * \
			GREENHOUSE_YIELD_MULTIPLIER * SPRING_WHEAT_FRACTION_OF_ROTATION


		#thousand tons fat per hectare per year
		ADJUSTED_SPRING_BARLEY_FAT = 0.074/1e3 * \
			GREENHOUSE_YIELD_MULTIPLIER * SPRING_BARLEY_FRACTION_OF_ROTATION

		#thousand tons fat per hectare per year
		ADJUSTED_RAPESEED_FAT = 1.195/1e3 * \
			GREENHOUSE_YIELD_MULTIPLIER * RAPESEED_FRACTION_OF_ROTATION

		GREENHOUSE_PROTEIN = (ADJUSTED_POTATO_PROTEIN \
			+ ADJUSTED_SPRING_BARLEY_PROTEIN\
			+ ADJUSTED_SPRING_WHEAT_PROTEIN\
			+ ADJUSTED_RAPESEED_PROTEIN) \
			/12

		GREENHOUSE_FAT = (ADJUSTED_POTATO_FAT \
			+ ADJUSTED_SPRING_WHEAT_FAT \
			+ ADJUSTED_SPRING_BARLEY_FAT \
			+ ADJUSTED_RAPESEED_FAT) \
			/12

		if(ADD_OUTDOOR_GROWING):
			production_kcals_outdoor_growing_per_month = \
				list(np.array(KCALS_GROWN_MINUS_GREENHOUSE) \
					* (1 - CROP_WASTE/100) )
		else:
			production_kcals_outdoor_growing_per_month=[0]*len(KCALS_GROWN)
		# we know:
		# 	units_sf_mass*SF_FRACTION_KCALS=sf_kcals
		# and
		# 	units_sf_mass*SF_FRACTION_PROTEIN=sf_protein
		# so
		# 	units_sf_mass = sf_kcals/SF_FRACTION_KCALS
		# => assumption listed previously =>
		# 	units_gh_mass = gh_kcals/SF_FRACTION_KCALS
		# 	units_gh_mass = gh_protein/SF_FRACTION_PROTEIN
		# therefore
		# 	gh_protein = gh_kcals*SF_FRACTION_PROTEIN/SF_FRACTION_KCALS
		#mass initial, units don't matter, we only need to ensure we use the correct 
		#fraction of kcals, fat, and protein per unit initial stored food.
		
		greenhouse_start=[0]*NMONTHS
		greenhouse_end=[0]*NMONTHS
		greenhouse_eaten=[0]*NMONTHS

		GREENHOUSE_FAT_MULTIPLIER = \
			constants['inputs']['GREENHOUSE_FAT_MULTIPLIER']


		production_protein_greenhouses_per_month = \
			list(np.array(production_kcals_greenhouses_per_month) \
			* OG_PROTEIN_PER_KCALS )

		production_fat_greenhouses_per_month = \
			list(np.array(production_kcals_greenhouses_per_month) \
			* OG_FAT_PER_KCALS * GREENHOUSE_FAT_MULTIPLIER )


		production_protein_outdoor_growing_per_month = \
			list(np.array(production_kcals_outdoor_growing_per_month) \
			* OG_PROTEIN_PER_KCALS  )
		
		production_fat_outdoor_growing_per_month = \
			list(np.array(production_kcals_outdoor_growing_per_month) \
			* OG_FAT_PER_KCALS)

		INITIAL_OG_KCALS = production_kcals_outdoor_growing_per_month[0]
		INITIAL_OG_FAT = production_fat_outdoor_growing_per_month[0]
		INITIAL_OG_PROTEIN = production_protein_outdoor_growing_per_month[0] 

		OG_FRACTION_KCALS =	INITIAL_OG_KCALS \
			/ (INITIAL_OG_KCALS
				+ INITIAL_OG_PROTEIN
				+ INITIAL_OG_FAT)
		OG_FRACTION_FAT =	INITIAL_OG_FAT \
			/ (INITIAL_OG_KCALS
				+ INITIAL_OG_PROTEIN
				+ INITIAL_OG_FAT)
		OG_FRACTION_PROTEIN = INITIAL_OG_PROTEIN \
			/ (INITIAL_OG_KCALS
				+ INITIAL_OG_PROTEIN
				+ INITIAL_OG_FAT)


		crops_food_start=[0]*NMONTHS
		crops_food_end=[0]*NMONTHS
		crops_food_produced=list(np.array(production_kcals_outdoor_growing_per_month)/OG_FRACTION_KCALS)
		crops_food_eaten=[0]*NMONTHS


		if(VERBOSE):
			print("production_kcals_outdoor_growing_per_month0")
			print(production_kcals_outdoor_growing_per_month[0])
			print("production_protein_outdoor_growing_per_month[0]")
			print(production_protein_outdoor_growing_per_month[0])
			print("production_fat_outdoor_growing_per_month[0]")
			print(production_fat_outdoor_growing_per_month[0])

			print("production_protein_outdoor_growing_per_month per b kcals[0]")
			print(production_protein_outdoor_growing_per_month[0]/production_kcals_outdoor_growing_per_month[0])
			print("production_fat_outdoor_growing_per_monthper b kcals[0]")
			print(production_fat_outdoor_growing_per_month[0]/production_kcals_outdoor_growing_per_month[0])
			
			print("production_protein_sf_per_month per b kcals[0]")
			print(INITIAL_SF_PROTEIN/INITIAL_SF_KCALS)
			print("production_fat_stored_food_per_monthper b kcals[0]")
			print(INITIAL_SF_FAT/INITIAL_SF_KCALS)
		# quit()		


		# quit()
		# plt.plot(GREENHOUSE_PERCENT_KCALS)

		# plt.show()

		# plt.plot(greenhouse_area)
		# plt.show()
		# quit()
		####LIVESTOCK, EGG, DAIRY INITIAL VARIABLES####

		DAIRY_PRODUCTION = constants['inputs']['DAIRY_PRODUCTION']
		DAIRY_WASTE = constants['inputs']['WASTE']['DAIRY']
		#billions of kcals
		MILK_KCALS_PER_1000_COWS_PER_MONTH = ANNUAL_LITERS_PER_COW \
			* KCALS_PER_LITER \
			/ 12 \
			/ 1e9 \
			* 1000 \
			* DAIRY_PRODUCTION \
			* (1-DAIRY_WASTE/100)


		#https://docs.google.com/spreadsheets/d/1-upBP5-iPtBzyjm5zbeGlfuE4FwqLUyR/edit#gid=2007828143
		#per kg, whole milk, per nutrition calculator
		MILK_KCALS = 610
		MILK_FAT = .032 #kg
		MILK_PROTEIN = .033 #kg

		#1000 tons to billions of kcals = grams/kcals
		MILK_FAT_TO_KCAL_RATIO = MILK_FAT/MILK_KCALS
		MILK_PROTEIN_TO_KCAL_RATIO = MILK_PROTEIN/MILK_KCALS

		# "FAOSTAT Food Balances", cell z 148
		#https://docs.google.com/spreadsheets/d/1-upBP5-iPtBzyjm5zbeGlfuE4FwqLUyR/edit#gid=102948593 

		# !!!assume all dairy from large animals!!!

		#!!!THESE NUMBERS ARE PRELIMINARY, NEED FUTURE ADJUSTMENT!!! (I googled these numbers)

		#1000s of Tons
		MILK_FAT_PER_1000_COWS_PER_MONTH= MILK_FAT/MILK_KCALS \
			* (MILK_KCALS_PER_1000_COWS_PER_MONTH / 1000) \
			* KG_TO_1000_TONS \
			* 1000

		#1000s of Tons
		MILK_PROTEIN_PER_1000_COWS_PER_MONTH=MILK_PROTEIN/MILK_KCALS \
			* (MILK_KCALS_PER_1000_COWS_PER_MONTH / 1000) \
			* KG_TO_1000_TONS \
			* 1000

		#mike's spreadsheet "area and scaling by month"
		#https://docs.google.com/spreadsheets/d/1-upBP5-iPtBzyjm5zbeGlfuE4FwqLUyR/edit#gid=642022040


		dairy_animals_1000s_start=[0]*NMONTHS
		dairy_animals_1000s_end=[0]*NMONTHS
		dairy_animals_1000s_eaten=[0]*NMONTHS

		#### CONSTANTS FOR METHANE SINGLE CELL PROTEIN ####
		SUGAR_WASTE = constants['inputs']['WASTE']['SUGAR']

		#apply sugar waste also to methane scp, for lack of better baseline

		#in billions of calories
		INDUSTRIAL_FOODS_SLOPE_MULTIPLIER = \
			constants['inputs']['INDUSTRIAL_FOODS_SLOPE_MULTIPLIER']
		#billion calories a month for 100% population.
		INDUSTRIAL_FOODS_MONTHLY_KCAL_MULTIPLIER = 6793977/12 
		METHANE_SCP_PERCENT_KCALS = list(np.array([0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2,2,4,7,7,7,7,7,9,11,11,11,11,11,11,13,15,15,15,15,15,17,20,20,20,20,20,22,22,24,24,24,24,24,26,28,28,28,28,28,30,30,33,33,33,33,33,35,37,37,37,37,37,39,39,41,41])/(1-0.12)*INDUSTRIAL_FOODS_SLOPE_MULTIPLIER)

		if(ADD_METHANE_SCP):
			production_kcals_scp_per_month = []
			for x in METHANE_SCP_PERCENT_KCALS:
				production_kcals_scp_per_month.append(x / 100 * INDUSTRIAL_FOODS_MONTHLY_KCAL_MULTIPLIER*(1-SUGAR_WASTE/100))
		else:
			production_kcals_scp_per_month=[0]*len(METHANE_SCP_PERCENT_KCALS)


		SCP_KCALS_PER_KG = 5350
		SCP_FRAC_PROTEIN=0.650
		SCP_FRAC_FAT=0.09

		production_protein_scp_per_month = \
			list(np.array(production_kcals_scp_per_month) \
			* SCP_FRAC_PROTEIN / SCP_KCALS_PER_KG )

		production_fat_scp_per_month = \
			list(np.array(production_kcals_scp_per_month) \
			* SCP_FRAC_FAT / SCP_KCALS_PER_KG )



		#### CONSTANTS FOR CELLULOSIC SUGAR ####

		#in billions of calories
		# CELL_SUGAR_PERCENT_KCALS = list(np.array([0.00, 0.00, 0.00, 0.00, 0.00, 9.79, 9.79, 9.79, 19.57, 23.48, 24.58, 28.49, 28.49,29.59,31.64, 31.64, 31.64, 31.64, 33.69, 35.74, 35.74, 35.74, 35.74, 37.78, 38.70, 39.61,40.53,41.44, 42.35, 43.27, 44.18, 45.10, 46.01, 46.93, 47.84, 48.76, 49.67, 50.58, 51.50,52.41,53.33, 54.24, 55.16, 56.07, 56.99, 57.90, 58.81, 59.73, 60.64, 61.56, 62.47, 63.39,64.30,65.21, 66.13, 67.04, 67.96, 68.87, 69.79, 70.70, 71.62, 72.53, 73.44, 74.36, 75.27,76.19,77.10, 78.02, 78.93, 79.85, 80.76, 81.67]) * CELLULOSIC_SUGAR_SLOPE_MULTIPLIER*(1-12/100))
		CELL_SUGAR_PERCENT_KCALS = list(np.array([0.00, 0.00, 0.00, 0.00, 0.00, 9.79, 9.79, 9.79, 20, 20, 20, 20, 20,20,20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20,20,20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20,20,20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20,20,20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20,20,20, 20, 20, 20, 20, 20]) *1/(1-0.12)* INDUSTRIAL_FOODS_SLOPE_MULTIPLIER)


		# print(np.array(CELL_SUGAR_PERCENT_KCALS)+np.array(METHANE_SCP_PERCENT_KCALS))
		# years = np.linspace(0,len(CELL_SUGAR_PERCENT_KCALS)-1,len(CELL_SUGAR_PERCENT_KCALS))/12
		# plt.plot(years,np.array(CELL_SUGAR_PERCENT_KCALS)+np.array(METHANE_SCP_PERCENT_KCALS))
		# plt.xlabel('years from may event')
		# plt.ylabel('percent human kcal requirement')
		# plt.show()
		# quit()
		if(ADD_CELLULOSIC_SUGAR):
			production_kcals_cell_sugar_per_month = []
			for x in CELL_SUGAR_PERCENT_KCALS:
				production_kcals_cell_sugar_per_month.append(x / 100 * INDUSTRIAL_FOODS_MONTHLY_KCAL_MULTIPLIER*(1-SUGAR_WASTE/100))
		else:
			production_kcals_cell_sugar_per_month = \
				[0]*len(CELL_SUGAR_PERCENT_KCALS)

		if(VERBOSE):
			print("INITIAL_MILK_COWS_THOUSANDS, billions")
			print(INITIAL_MILK_COWS_THOUSANDS/1e9)
			print("Number of large animals, billions")
			print((INIT_LARGE_NONDAIRY_ANIMALS+INITIAL_MILK_COWS_THOUSANDS)/1e9)
			print("Percent Dairy Animals of large animals")
			print(INITIAL_MILK_COWS_THOUSANDS/(INIT_LARGE_NONDAIRY_ANIMALS+INITIAL_MILK_COWS_THOUSANDS)*100)

			print('millions of people fed for a year from eating milk cows')
			print(INITIAL_MILK_COWS_THOUSANDS*1000*FAT_PER_LARGE_ANIMAL/(12*FAT_MONTHLY)/1e6)

			print("billions of people fed for a year from eating all livestock minus dairy cows and egg laying hens")
			print(INIT_NONEGG_NONDAIRY_MEAT_FAT/(12*FAT_MONTHLY)/1e9)


		#### BIOFUELS ####
		#see 'biofuels' tab https://docs.google.com/spreadsheets/d/1-upBP5-iPtBzyjm5zbeGlfuE4FwqLUyR/edit#gid=2030318378
		BIOFUEL_KCALS_PER_YEAR = 8.3e5 #billions of kcals
		BIOFUEL_KCALS_PER_MONTH = BIOFUEL_KCALS_PER_YEAR/12
		BIOFUEL_PROTEIN_PER_YEAR = 1.45e4 #1000s of tons
		BIOFUEL_PROTEIN_PER_MONTH = BIOFUEL_PROTEIN_PER_YEAR/12
		BIOFUEL_FAT_PER_YEAR = 0.522e4 #1000s of tons
		BIOFUEL_FAT_PER_MONTH = BIOFUEL_FAT_PER_YEAR/12#1000s of tons
		biofuels_fat = [BIOFUEL_FAT_PER_MONTH]*NMONTHS
		biofuels_kcals = [BIOFUEL_KCALS_PER_MONTH]*NMONTHS
		biofuels_protein = [BIOFUEL_PROTEIN_PER_MONTH]*NMONTHS

		biofuel_delay = constants['inputs']['BIOFUEL_SHUTOFF_DELAY']
		biofuels_fat = [BIOFUEL_FAT_PER_MONTH]*biofuel_delay + [0]*(NMONTHS-biofuel_delay)
		biofuels_protein = [BIOFUEL_PROTEIN_PER_MONTH]*biofuel_delay + [0]*(NMONTHS-biofuel_delay)
		biofuels_kcals = [BIOFUEL_KCALS_PER_MONTH]*biofuel_delay + [0]*(NMONTHS-biofuel_delay)


		#### OTHER VARIABLES ####

		humans_fed_fat = [0]*NMONTHS
		humans_fed_protein = [0]*NMONTHS
		humans_fed_kcals = [0]*NMONTHS
		maximize_constraints=[] #used only for validation
		allvariables=[z] #used only for validation

		#store variables useful for analysis
		# constants={}
		constants['NMONTHS']=NMONTHS
		constants['NDAYS']=NDAYS
		constants['ADD_STORED_FOOD']=ADD_STORED_FOOD
		constants['ADD_FISH']=ADD_FISH
		constants['ADD_SEAWEED']=ADD_SEAWEED
		constants['ADD_GREENHOUSES']=ADD_GREENHOUSES
		constants['ADD_NONEGG_NONDAIRY_MEAT']=ADD_NONEGG_NONDAIRY_MEAT
		constants['ADD_DAIRY']=ADD_DAIRY
		constants['ADD_OUTDOOR_GROWING']=ADD_OUTDOOR_GROWING
		constants['MAXIMIZE_ONLY_FOOD_AFTER_DAY_150']= \
			MAXIMIZE_ONLY_FOOD_AFTER_DAY_150
		constants['LIMIT_SEAWEED_AS_PERCENT_KCALS']=\
			LIMIT_SEAWEED_AS_PERCENT_KCALS
		constants['VERBOSE']=VERBOSE
		constants['KCALS_MONTHLY']=KCALS_MONTHLY
		constants['PROTEIN_MONTHLY']=PROTEIN_MONTHLY
		constants['FAT_MONTHLY']=FAT_MONTHLY
		constants['MINIMUM_DENSITY']=MINIMUM_DENSITY
		constants['HARVEST_LOSS']=HARVEST_LOSS
		constants['MAXIMUM_AREA']=MAXIMUM_AREA
		constants['MAXIMUM_DENSITY']=MAXIMUM_DENSITY
		constants['SF_FRACTION_KCALS']=SF_FRACTION_KCALS
		constants['SF_FRACTION_FAT']=SF_FRACTION_FAT
		constants['SF_FRACTION_PROTEIN']=SF_FRACTION_PROTEIN
		constants['OG_FRACTION_KCALS']=OG_FRACTION_KCALS
		constants['OG_FRACTION_FAT']=OG_FRACTION_FAT
		constants['OG_FRACTION_PROTEIN']=OG_FRACTION_PROTEIN
		constants['MEAT_FRACTION_KCALS']=MEAT_FRACTION_KCALS
		constants['MEAT_FRACTION_FAT']=MEAT_FRACTION_FAT
		constants['MEAT_FRACTION_PROTEIN']=MEAT_FRACTION_PROTEIN
		constants['MILK_KCALS_PER_1000_COWS_PER_MONTH']=MILK_KCALS_PER_1000_COWS_PER_MONTH
		constants['MILK_FAT_PER_1000_COWS_PER_MONTH']=MILK_FAT_PER_1000_COWS_PER_MONTH
		constants['MILK_PROTEIN_PER_1000_COWS_PER_MONTH']=MILK_PROTEIN_PER_1000_COWS_PER_MONTH
		constants['KCALS_PER_1000_LARGE_ANIMALS']=KCALS_PER_1000_LARGE_ANIMALS
		constants['FAT_PER_1000_LARGE_ANIMALS']=FAT_PER_1000_LARGE_ANIMALS
		constants['PROTEIN_PER_1000_LARGE_ANIMALS']=PROTEIN_PER_1000_LARGE_ANIMALS
		constants['SEAWEED_KCALS']=SEAWEED_KCALS
		constants['SEAWEED_FAT']=SEAWEED_FAT
		constants['SEAWEED_PROTEIN']=SEAWEED_PROTEIN
		constants['INITIAL_SF']=INITIAL_SF
		constants['INITIAL_NONEGG_NONDAIRY_MEAT']=INITIAL_NONEGG_NONDAIRY_MEAT
		constants['WORLD_POP'] = WORLD_POP
		constants['ADD_CELLULOSIC_SUGAR'] = ADD_CELLULOSIC_SUGAR
		constants['ADD_METHANE_SCP'] = ADD_METHANE_SCP
		constants['FISH_FAT'] = FISH_FAT
		constants['FISH_PROTEIN'] = FISH_PROTEIN
		constants['FISH_KCALS'] = FISH_KCALS
		constants['GREENHOUSE_CALORIES'] = GREENHOUSE_CALORIES
		constants['GREENHOUSE_PROTEIN'] = GREENHOUSE_PROTEIN
		constants['GREENHOUSE_FAT'] = GREENHOUSE_FAT

		#### FUNCTIONS FOR EACH FOOD TYPE ####


		def add_seaweed_to_model(model, m):
			sum_food_this_month=[]
			for d in np.arange(m*DAYS_IN_MONTH,(m+1)*DAYS_IN_MONTH):
				time_days_daily.append(d)
				seaweed_wet_on_farm[d] = LpVariable("Seaweed_Wet_On_Farm_"+str(d)+"_Variable", INITIAL_SEAWEED, MAXIMUM_DENSITY*built_area[d])
				# food production (using resources)
				seaweed_food_produced[d] = LpVariable(name="Seaweed_Food_Produced_During_Day_"+str(d)+"_Variable", lowBound=0)

				used_area[d] = LpVariable("Used_Area_"+str(d)+"_Variable", INITIAL_AREA,built_area[d])

				if(d==0): #first Day
					model += (seaweed_wet_on_farm[0] == INITIAL_SEAWEED,
						"Seaweed_Wet_On_Farm_0_Constraint")
					model += (used_area[0] == INITIAL_AREA,
						"Used_Area_Day_0_Constraint")
					model += (seaweed_food_produced[0] == 0,
						"Seaweed_Food_Produced_Day_0_Constraint")

				else: #later Days
					model += (seaweed_wet_on_farm[d] <= used_area[d]*MAXIMUM_DENSITY)

					model += (seaweed_wet_on_farm[d] == 
						seaweed_wet_on_farm[d-1]*(1+SEAWEED_PRODUCTION_RATE/100.)
						- seaweed_food_produced[d]
						- (used_area[d]-used_area[d-1])*MINIMUM_DENSITY*(HARVEST_LOSS/100),
						"Seaweed_Wet_On_Farm_"+str(d)+"_Constraint")

				allvariables.append(used_area[d])
				allvariables.append(seaweed_wet_on_farm[d])

				allvariables.append(seaweed_food_produced[d])
				sum_food_this_month.append(seaweed_food_produced[d])

			seaweed_food_produced_monthly[m] = LpVariable(name="Seaweed_Food_Produced_Monthly_"+str(m)+"_Variable", lowBound=0)
			

			model += (seaweed_food_produced_monthly[m] == np.sum(sum_food_this_month),
				"Seaweed_Food_Produced_Monthly_"+str(m)+"_Constraint")


			allvariables.append(seaweed_food_produced_monthly[m])

			return model


		#incorporate linear constraints for stored food consumption each month
		def add_stored_food_to_model(model, m):
			stored_food_start[m] = LpVariable("Stored_Food_Start_Month_"+str(m)+"_Variable", 0,INITIAL_SF)
			stored_food_end[m] = LpVariable("Stored_Food_End_Month_"+str(m)+"_Variable", 0,INITIAL_SF)
			stored_food_eaten[m] = LpVariable("Stored_Food_Eaten_During_Month_"+str(m)+"_Variable",0,INITIAL_SF)
			
			if(m==0): #first Month
				model += (stored_food_start[0] <= INITIAL_SF, "Stored_Food_Start_Month_0_Constraint")
			else:
				model += (stored_food_start[m] <= stored_food_end[m-1], "Stored_Food_Start_Month_"+str(m)+"_Constraint")

			model += (stored_food_end[m] <= stored_food_start[m] - stored_food_eaten[m], "Stored_Food_End_Month_"+str(m)+"_Constraint")

			allvariables.append(stored_food_start[m])
			allvariables.append(stored_food_end[m])
			allvariables.append(stored_food_eaten[m])

			return model

		#incorporate linear constraints for stored food consumption each month
		def add_outdoor_crops_to_model(model, m):
			crops_food_start[m] = LpVariable("Crops_Food_Start_Month_"+str(m)+"_Variable", lowBound=0)
			crops_food_end[m] = LpVariable("Crops_Food_End_Month_"+str(m)+"_Variable", lowBound=0)
			crops_food_eaten[m] = LpVariable("Crops_Food_Eaten_During_Month_"+str(m)+"_Variable",lowBound=0)
			
			if(m==0): #first Month
				model += (crops_food_start[m] <= 0, "Crops_Food_Start_Month_0_Constraint")
			else:
				model += (crops_food_start[m] <= crops_food_end[m-1], "Crops_Food_Start_Month_"+str(m)+"_Constraint")

			model += (crops_food_end[m] <= crops_food_start[m]-crops_food_eaten[m]+crops_food_produced[m], "Crops_Food_End_Month_"+str(m)+"_Constraint")

			allvariables.append(crops_food_start[m])
			allvariables.append(crops_food_end[m])
			allvariables.append(crops_food_eaten[m])

			return model

		# #incorporate greenhouse planted food tradeoff to address calories and
		# #protein requirements
		# #we already have the area for growing total food, and the productivity
		# # in terms of calories, fat, and protein per hectare
		# def add_greenhouses_to_model(model, m):
			
		# 	#Spring wheat
		# 	#Spring barley
		# 	#Potato
		# 	#Rapeseed (oil only)
		# 	# greenhouse_area

		# 	if(m==0): #first Month
		# 		model += (area_spring_wheat[m] <= 0, \
		# 			"Area_Spring_Wheat_Month_0_Constraint")
		# 		model += (area_spring_barley[m] <= 0, \
		# 			"Area_Spring_Barley_Month_0_Constraint")
		# 		model += (area_potato[m] <= 0, \
		# 			"Area_Potato_Month_0_Constraint")
		# 		model += (area_rapeseed[m] <= 0, \
		# 			"Area_Rapeseed_Month_0_Constraint")
				
		# 	else:
		# 		model += (greenhouse_food_start[m] <= greenhouse_food_end[m-1],
		# 			"Crops_Food_Start_Month_"+str(m)+"_Constraint")
		# 		model += (greenhouse_area[m] == \
		# 			area_spring_barley[m] + \
		# 			area_rapeseed[m] + \
		# 			area_potato[m] + \
		# 			area_spring_wheat[m],\
		# 			"Area_Spring_Wheat_Month_"+str(m)+"_Constraint")
		# 		model += (area_spring_barley[m] <= 0, \
		# 			"Area_Spring_Barley_Month_"+str(m)+"_Constraint")
		# 		model += (area_potato[m] <= 0, \
		# 			"Area_Potato_Month_"+str(m)+"_Constraint")
		# 		model += (area_rapeseed[m] <= 0, \
		# 			"Area_Rapeseed_Month_"+str(m)+"_Constraint")

		# 	return model

		#### LIVESTOCK: NONDAIRY MEAT, NON EGGS ####

		#assumes all meat is fed using grasslands
		#no difference in waste between carcass meat and other food sources yet
		#dairy cows and egg-laying chickens are modeled separately
		#this can be treated essentially as stored food
		#assume there's no population growth of cows

		#incorporate linear constraints for nonegg_nondairy meat consumption each month
		def add_nonegg_nondairy_meat_to_model(model, m):
			nonegg_nondairy_meat_start[m] = LpVariable("Non_Egg_Nondairy_Meat_Start_"+str(m)+"_Variable", 0,INITIAL_NONEGG_NONDAIRY_MEAT)
			nonegg_nondairy_meat_end[m] = LpVariable("Non_Egg_Nondairy_Meat_End_"+str(m)+"_Variable", 0,INITIAL_NONEGG_NONDAIRY_MEAT)
			nonegg_nondairy_meat_eaten[m] = LpVariable("Non_Egg_Nondairy_Meat_Eaten_During_Month_"+str(m)+"_Variable",0,INITIAL_NONEGG_NONDAIRY_MEAT)
			
			if(m==0): #first Month
				model += (nonegg_nondairy_meat_start[0] <= INITIAL_NONEGG_NONDAIRY_MEAT, "Non_Egg_Nondairy_Meat_Start_Month_0_Constraint")
			else:
				model += (nonegg_nondairy_meat_start[m] <= nonegg_nondairy_meat_end[m-1], "Non_Egg_Nondairy_Meat_Start_Month_"+str(m)+"_Constraint")

			model += (nonegg_nondairy_meat_end[m] <= nonegg_nondairy_meat_start[m] - nonegg_nondairy_meat_eaten[m], "Non_Egg_Nondairy_Meat_End_Month_"+str(m)+"_Constraint")

			allvariables.append(nonegg_nondairy_meat_start[m])
			allvariables.append(nonegg_nondairy_meat_end[m])
			allvariables.append(nonegg_nondairy_meat_eaten[m])

			return model

		#### LIVESTOCK: MILK, EGGS ####
		#no resources currently are used by dairy cows or chickens
		#the only trade-off is between eating their meat vs eating their milk or eggs  

		def add_eggs_to_model(model, m):
			pass
			#small_nonegg_animals_start

		#dairy animals are all assumed to be large animals
		def add_dairy_to_model(model, m):
			# print(INITIAL_MILK_COWS_THOUSANDS)
			dairy_animals_1000s_start[m] = LpVariable("Dairy_Animals_Start_"+str(m)+"_Variable", 0,INITIAL_MILK_COWS_THOUSANDS)
			dairy_animals_1000s_end[m] = LpVariable("Dairy_Animals_End_"+str(m)+"_Variable", 0,INITIAL_MILK_COWS_THOUSANDS)
			dairy_animals_1000s_eaten[m] = LpVariable("Dairy_Animals_Eaten_During_Month_"+str(m)+"_Variable",0,INITIAL_MILK_COWS_THOUSANDS)
			
			if(m==0): #first Month
				model += (dairy_animals_1000s_start[0] <= INITIAL_MILK_COWS_THOUSANDS, "Dairy_Animals_Start_Month_0_Constraint")
			else:
				model += (dairy_animals_1000s_start[m] <= dairy_animals_1000s_end[m-1], 
					"Dairy_Animals_Start_Month_"+str(m)+"_Constraint")

			model += (dairy_animals_1000s_end[m] <= dairy_animals_1000s_start[m] \
				- dairy_animals_1000s_eaten[m],
				"Dairy_Animals_Eaten_Month_"+str(m)+"_Constraint")

			allvariables.append(dairy_animals_1000s_start[m])
			allvariables.append(dairy_animals_1000s_end[m])
			allvariables.append(dairy_animals_1000s_eaten[m])

			return model

		#### OBJECTIVE FUNCTIONS ####


		def add_objectives_to_model(model, m, maximize_constraints):
			#total eaten
			humans_fed_fat[m] = \
				LpVariable(name="Humans_Fed_Fat_"+str(m)+"_Variable",lowBound=0)
			humans_fed_protein[m] = \
				LpVariable(name="Humans_Fed_Protein_"+str(m)+"_Variable",lowBound=0)
			humans_fed_kcals[m] = \
				LpVariable(name="Humans_Fed_Kcals_"+str(m)+"_Variable",lowBound=0)

			allvariables.append(humans_fed_fat[m])
			allvariables.append(humans_fed_protein[m])
			allvariables.append(humans_fed_kcals[m])


			if(ADD_SEAWEED and LIMIT_SEAWEED_AS_PERCENT_KCALS):
				model += (seaweed_food_produced_monthly[m]*SEAWEED_KCALS <= 
					(MAX_SEAWEED_AS_PERCENT_KCALS/100)*(humans_fed_kcals[m]*KCALS_MONTHLY),
					"Seaweed_Limit_Kcals_"+str(m)+"_Constraint")

				# allvariables.append(humans_fed_fat[m])

			#finds billions of people fed that month per nutrient

			#stored food eaten*sf_fraction_kcals is in units billions kcals monthly
			#seaweed_food_produced_monthly*seaweed_kcals is in units billions kcals
			#kcals monthly is in units kcals
			model += (humans_fed_kcals[m] == 
				(stored_food_eaten[m]*SF_FRACTION_KCALS
				+ crops_food_eaten[m]*OG_FRACTION_KCALS
				+ seaweed_food_produced_monthly[m]*SEAWEED_KCALS
				# + dairy_animals_1000s_eaten[m]*KCALS_PER_1000_LARGE_ANIMALS
				+ (dairy_animals_1000s_start[m]+dairy_animals_1000s_end[m])/2 \
					* MILK_KCALS_PER_1000_COWS_PER_MONTH
				+ nonegg_nondairy_meat_eaten[m]*MEAT_FRACTION_KCALS
				- biofuels_kcals[m]
				+ production_kcals_cell_sugar_per_month[m]
				+ production_kcals_scp_per_month[m]
				# + production_kcals_greenhouses_per_month[m]
				+ greenhouse_area[m]*GREENHOUSE_CALORIES
				+FISH_KCALS)/KCALS_MONTHLY,
				"Kcals_Fed_Month_"+str(m)+"_Constraint")

			#stored_food_eaten*sf_fraction_fat is in units thousand tons monthly
			#seaweed_food_produced_monthly*seaweed_fat is in units thousand tons monthly
			#fat monthly is in units thousand tons
			# quit()
			model += (humans_fed_fat[m] == 
				(stored_food_eaten[m]*SF_FRACTION_FAT 
				+ crops_food_eaten[m]*OG_FRACTION_FAT
				+ seaweed_food_produced_monthly[m]*SEAWEED_FAT
				# + dairy_animals_1000s_eaten[m]*FAT_PER_1000_LARGE_ANIMALS
				+ (dairy_animals_1000s_start[m]+dairy_animals_1000s_end[m])/2 \
					* MILK_FAT_PER_1000_COWS_PER_MONTH*1e9
				- biofuels_fat[m]
				# + production_fat_greenhouses_per_month[m]
				+ production_fat_scp_per_month[m]
				+ nonegg_nondairy_meat_eaten[m]*MEAT_FRACTION_FAT
				+ greenhouse_area[m]*GREENHOUSE_FAT
				+ FISH_FAT)/FAT_MONTHLY/1e9,
				"Fat_Fed_Month_"+str(m)+"_Constraint")
			
			#stored_food_eaten*sf_fraction_protein is in units thousand tons monthly
			#seaweed_food_produced_monthly*seaweed_protein is in units thousand tons monthly
			#fat monthly is in units thousand tons
			# 	+ seaweed_food_produced_monthly[m]*SEAWEED_PROTEIN
			# 	+ dairy_animals_1000s_eaten[m]*PROTEIN_PER_1000_LARGE_ANIMALS
			# 	+ (dairy_animals_1000s_start[m]+dairy_animals_1000s_end[m])/2 \
			# 		* MILK_PROTEIN_PER_1000_COWS_PER_MONTH
			# 	+ production_protein_greenhouses_per_month[m]
			# 	+ nonegg_nondairy_meat_eaten[m]*MEAT_FRACTION_PROTEIN)/PROTEIN_MONTHLY/1e9)
			model += (humans_fed_protein[m] == 
				(stored_food_eaten[m]*SF_FRACTION_PROTEIN
				+ crops_food_eaten[m]*OG_FRACTION_PROTEIN
				+ seaweed_food_produced_monthly[m]*SEAWEED_PROTEIN
				# + dairy_animals_1000s_eaten[m]*PROTEIN_PER_1000_LARGE_ANIMALS
				+ (dairy_animals_1000s_start[m]+dairy_animals_1000s_end[m])/2 \
					* MILK_PROTEIN_PER_1000_COWS_PER_MONTH*1e9
				- biofuels_protein
				# + production_protein_greenhouses_per_month[m]
				+ production_protein_scp_per_month[m]
				+ nonegg_nondairy_meat_eaten[m]*MEAT_FRACTION_PROTEIN
				+ greenhouse_area[m]*GREENHOUSE_PROTEIN
				+ FISH_PROTEIN)/PROTEIN_MONTHLY/1e9,
				"Protein_Fed_Month_"+str(m)+"_Constraint")

			# maximizes the minimum z value
			# We maximize the minimum humans fed from any month 
			# We therefore maximize the minimum ratio of fat per human requirement, 
			# protein per human requirement, or kcals per human requirement
			# for all months
			maximizer_string="Kcals_Fed_Month_"+str(m)+"_Objective_Constraint"
			maximize_constraints.append(maximizer_string)
			model += (z <= humans_fed_kcals[m], maximizer_string)

			maximizer_string="Fat_Fed_Month_"+str(m)+"_Objective_Constraint"
			maximize_constraints.append(maximizer_string)
			model += (z <= humans_fed_fat[m], maximizer_string)

			maximizer_string="Protein_Fed_Month_"+str(m)+"_Objective_Constraint"
			maximize_constraints.append(maximizer_string)
			model += (z <= humans_fed_protein[m], maximizer_string)

			return [model, maximize_constraints]



		#### MODEL GENERATION LOOP ####
		
		time_days_monthly=[]
		time_days_daily=[]
		time_months=[]
		time_days_middle=[]
		time_months_middle=[]
		for m in range(0,NMONTHS):
			time_days_middle.append(DAYS_IN_MONTH*(m+0.5))
			time_days_monthly.append(DAYS_IN_MONTH*m)
			time_days_monthly.append(DAYS_IN_MONTH*(m+1))
			time_months.append(m)
			time_months.append(m+1)
			time_months_middle.append(m+0.5)

			if(ADD_SEAWEED):
				model = add_seaweed_to_model(model,m)

			if(ADD_OUTDOOR_GROWING):
				model = add_outdoor_crops_to_model(model,m)

			# if(ADD_GREENHOUSES):
			# 	model = add_greenhouses_to_model(model,m)

			if(ADD_STORED_FOOD):
				model = add_stored_food_to_model(model,m)

			if(ADD_NONEGG_NONDAIRY_MEAT):
				model = add_nonegg_nondairy_meat_to_model(model,m)

			if(ADD_DAIRY):
				model = add_dairy_to_model(model,m)

			if(ADD_EGGS):
				model = add_eggs_to_model(model,m)

			if(
				(not MAXIMIZE_ONLY_FOOD_AFTER_DAY_150)
				or 
				(MAXIMIZE_ONLY_FOOD_AFTER_DAY_150 and (m >= 5))#start month 5 is day 150
			):
				[model,maximize_constraints] = \
					add_objectives_to_model(model, m,maximize_constraints)
			
		obj_func = z
		model += obj_func

		status = model.solve(pulp.PULP_CBC_CMD(fracGap=0.0001,msg=VERBOSE))
		assert(status==1)
		print('')	
		print('VALIDATION')	
		print('')	
		print('')


		#double check it worked

		print('pulp reports successful optimization')
		if(constants['CHECK_CONSTRAINTS']):
			Validator.checkConstraintsSatisfied(
				model,
				status,
				maximize_constraints,
				allvariables,
				VERBOSE)


		if(VERBOSE):
			for var in model.variables():
				print(f"{var.name}: {var.value()}")

		print('')

		analysis = Analyzer(constants)

		show_output=False


		# if no stored food, will be zero
		analysis.analyze_SF_results(
			stored_food_eaten,
			stored_food_start,
			stored_food_end,
			show_output
		)
		# print(analysis.st)
		#extract numeric seaweed results in terms of people fed and raw tons wet
		#if seaweed not added to model, will be zero
		analysis.analyze_seaweed_results(
			seaweed_wet_on_farm,
			used_area,
			built_area,
			seaweed_food_produced,#daily
			seaweed_food_produced_monthly,
			show_output
		)

		# if no cellulosic sugar, will be zero
		analysis.analyze_CS_results(
			production_kcals_cell_sugar_per_month,
			show_output
		)

		# if no scp, will be zero
		analysis.analyze_SCP_results(
			production_kcals_scp_per_month,
			production_protein_scp_per_month,
			production_fat_scp_per_month,
			show_output
		)
		# if no cellulosic sugar, will be zero
		analysis.analyze_fish_results(time_months_middle)

		# if no greenhouses, will be zero
		analysis.analyze_GH_results(
			greenhouse_area,
			show_output
		)

		# if no outdoor food, will be zero
		analysis.analyze_OG_results(
			crops_food_eaten,
			crops_food_start,
			crops_food_end,
			crops_food_produced,
			greenhouse_area,
			show_output
		)

		#if nonegg nondairy meat isn't included, these results will be zero
		analysis.analyze_nonegg_nondairy_results(
			nonegg_nondairy_meat_start,
			nonegg_nondairy_meat_end,
			nonegg_nondairy_meat_eaten,
			show_output
		)

		#if dairy isn't included, these results will be zero
		analysis.analyze_dairy_results(
			dairy_animals_1000s_start,
			dairy_animals_1000s_end,
			dairy_animals_1000s_eaten,
			show_output
		)

		analysis.analyze_results(model,time_months_middle)
		return [time_months,time_months_middle,analysis]


