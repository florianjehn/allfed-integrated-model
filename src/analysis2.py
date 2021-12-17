import os
import sys
module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
	sys.path.append(module_path)
import numpy as np

class Analyzer:
	def __init__(self,constants):
		self.c=constants



	#order the variables that occur mid-month into a list of numeric values
	def makeMidMonthlyVars(self,variables,conversion,show_output):
		variable_output=[]
		#if the variable was not modeled
		if(type(variables[0])==type(0)):
			return np.array([0]*len(variables))  #return initial value

		if(show_output):
			print("Monthly Output for "+str(variables[0]))

		for m in range(0,self.c['NMONTHS']):
			val=variables[m]
			# if(val==0)

			#if the variable was not modeled
			if(type(val)==type(0)):
				variable_output.append(val*conversion)
			else:
				variable_output.append(val.varValue*conversion)
			if(show_output):
				print("    Month "+str(m)+": "+str(variable_output[m]))
		return np.array(variable_output)


	#order the variables that occur mid-month into a list of numeric values
	def makeMidMonthlyOGKcals(self,
		crops_food_eaten_no_rot,
		crops_food_eaten_rot,
		crops_kcals_produced,
		conversion,
		show_output):
		
		immediately_eaten_output=[]
		new_stored_eaten_output=[]
		cf_eaten_output = []
		cf_produced_output = []

		#if the variable was not modeled
		if(type(crops_food_eaten_no_rot[0])==type(0)):
			return [[0]*len(crops_food_eaten_no_rot),\
				[0]*len(crops_food_eaten_no_rot)]  #return initial value

		if(show_output):
			print("Monthly Output for "+str(variables[0]))

		for m in range(0,self.c['NMONTHS']):
			cf_produced = crops_kcals_produced[m]
			cf_produced_output.append(cf_produced)
			
			cf_eaten = crops_food_eaten_no_rot[m].varValue + \
				crops_food_eaten_rot[m].varValue*self.c["OG_ROTATION_FRACTION_KCALS"]
			cf_eaten_output.append(cf_eaten)

			if(cf_produced <= cf_eaten):
				immediately_eaten = cf_produced
				new_stored_crops_eaten = cf_eaten - cf_produced
			else: #crops_food_eaten < crops_kcals_produced
				immediately_eaten = cf_eaten
				new_stored_crops_eaten = 0

			immediately_eaten_output.append(immediately_eaten*conversion)
			new_stored_eaten_output.append(new_stored_crops_eaten*conversion)
			if(show_output):
				print("    Month "+str(m)+": imm eaten: "
					+ str(immediately_eaten_output[m])
					+' new stored eaten: '
					+str(new_stored_eaten_output[m]))


		# import matplotlib.pyplot as plt
		# plt.plot(cf_produced_output)
		# plt.title("cfpo")
		# plt.show()

		# plt.plot(cf_eaten_output)
		# plt.title("cfeo")
		# plt.show()
		# plt.plot(new_stored_eaten_output)
		# plt.title("nseo")
		# plt.show()
		# plt.plot(immediately_eaten_output)
		# plt.title("ieo")
		# plt.show()
		# quit()
		return [immediately_eaten_output,new_stored_eaten_output]

	#order the variables that occur start and end month into list of numeric values
	def makeStartEndMonthlyVars(
		self,
		variable_start,
		variable_end,
		conversion,
		show_output):

		#if the variable was not modeled
		if(type(variable_start[0])==type(0)):
			#return initial value, all zeros
			return [0]*len(variable_start)*2 

		variable_output=[]
		if(show_output):
			print("Monthly Output for "+str(variable_start[0]))

		for m in range(0,self.c['NMONTHS']):
			val=variable_start[m]
			variable_output.append(val.varValue*conversion)
			val=variable_end[m]
			variable_output.append(val.varValue*conversion)
			if(show_output):
				print("    End Month "+str(m)+": "+str(variable_output[m]))
		return variable_output

	def makeDailyVars(self,variables,conversion,show_output):
		variable_output=[]
		#if the variable was not modeled
		if(type(variables[0])==type(0)):
			return variables #return initial value

		if(show_output):
			print("Daily Output for "+str(variables[0]))
		for d in range(0,self.c['NDAYS']):
			val=variables[d]
			# if(val==0)
			variable_output.append(val.varValue*conversion)
			if(show_output):
				print("    Day "+str(d)+": "+str(variable_output[d]))
		return variable_output


	#if greenhouses aren't included, these results will be zero
	def analyze_GH_results(
		self,
		greenhouse_kcals_per_ha,
		greenhouse_fat_per_ha,
		greenhouse_protein_per_ha,
		greenhouse_area,
		show_output
		):

		# self.greenhouse_kcals_per_ha = self.makeMidMonthlyVars(
		# 	greenhouse_kcals_per_ha,
		# 	1,
		# 	show_output)
		# self.greenhouse_fat_per_ha = self.makeMidMonthlyVars(
		# 	greenhouse_fat_per_ha,
		# 	1,
		# 	show_output)
		# self.greenhouse_protein_per_ha = self.makeMidMonthlyVars(
		# 	greenhouse_protein_per_ha,
		# 	1,
		# 	show_output)
		self.billions_fed_GH_kcals = \
			np.multiply(\
				np.array(greenhouse_area),\
				np.array(greenhouse_kcals_per_ha) \
				* 1/self.c["KCALS_MONTHLY"]
			)

		self.billions_fed_GH_fat= \
			np.multiply(
				np.array(greenhouse_area),\
				np.array(greenhouse_fat_per_ha) \
				*1/self.c["FAT_MONTHLY"]/1e9
			)

		self.billions_fed_GH_protein = \
			np.multiply(
				np.array(greenhouse_area),\
				np.array(greenhouse_protein_per_ha)
				* 1/self.c["PROTEIN_MONTHLY"]/1e9
			)

	# #if greenhouses aren't included, these results will be zero
	# def analyze_GH_results(
	# 	self,
	# 	production_kcals_greenhouses_per_m,
	# 	production_fat_greenhouses_per_m,
	# 	production_protein_greenhouses_per_m,
	# 	show_output
	# 	):

	# 	self.billions_fed_GH_kcals = \
	# 		np.array(production_kcals_greenhouses_per_m) \
	# 		/ self.c["KCALS_MONTHLY"]
	# 	self.billions_fed_GH_fat= \
	# 		np.array(production_fat_greenhouses_per_m) \
	# 		/ self.c["FAT_MONTHLY"]/1e9
	# 	self.billions_fed_GH_protein = \
	# 		np.array(production_protein_greenhouses_per_m) \
	# 		/ self.c["PROTEIN_MONTHLY"]/1e9


	#if fish aren't included, these results will be zero
	def analyze_fish_results(
		self,
		production_kcals_fish_per_m,
		production_fat_fish_per_m,
		production_protein_fish_per_m,
		show_output
		):


		self.billions_fed_fish_kcals = \
			np.array(production_kcals_fish_per_m) \
			/ self.c["KCALS_MONTHLY"]

		self.billions_fed_fish_protein = \
			np.array(production_protein_fish_per_m) \
			/ self.c["PROTEIN_MONTHLY"]/1e9

		self.billions_fed_fish_fat = \
			np.array(production_fat_fish_per_m) \
			/ self.c["FAT_MONTHLY"]/1e9
		
	#if outdoor growing isn't included, these results will be zero
	def analyze_OG_results(
		self,
		crops_food_eaten_no_rot,
		crops_food_eaten_rot,
		crops_food_storage_no_rot,
		crops_food_storage_rot,
		crops_food_produced,
		show_output
		):
		CROPS_WASTE = 1-self.c["inputs"]["WASTE"]["CROPS"]/100
		self.billions_fed_OG_storage_no_rot = self.makeMidMonthlyVars(
			crops_food_storage_no_rot,
			CROPS_WASTE/self.c["KCALS_MONTHLY"],\
			show_output)

		self.billions_fed_OG_storage_rot = self.makeMidMonthlyVars(
			crops_food_storage_rot,
			CROPS_WASTE\
			* self.c["OG_ROTATION_FRACTION_KCALS"]/self.c["KCALS_MONTHLY"],\
			show_output)

		#immediate from produced and storage changes account for all eaten
		# but storage can come from produced!
		#we know storage_change + all_eaten = produced
		# if(storage_change>=0):
		# 	assert(all_eaten >= storage_change)
		# 	eaten_from_stored = storage_change
		# 	immediately_eaten = all_eaten - eaten_from_stored
		# else:
		# 	eaten_from_stored = 0

		og_produced_kcals = \
			np.concatenate([
				np.array(crops_food_produced[0:self.c['inputs']["INITIAL_HARVEST_DURATION"]]),\
				np.array(crops_food_produced[self.c['inputs']["INITIAL_HARVEST_DURATION"]:])\
				 * self.c["OG_ROTATION_FRACTION_KCALS"],
			])* CROPS_WASTE


		[self.billions_fed_immediate_OG_kcals_tmp,\
		self.billions_fed_new_stored_OG_kcals_tmp]\
		 = self.makeMidMonthlyOGKcals(
			crops_food_eaten_no_rot,
			crops_food_eaten_rot,
			og_produced_kcals,
			CROPS_WASTE / self.c["KCALS_MONTHLY"],
			show_output
			)


		self.billions_fed_immediate_OG_kcals = \
			np.multiply(
				np.array(self.billions_fed_immediate_OG_kcals_tmp),
				self.OG_SF_fraction_kcals_to_humans
			)

		self.billions_fed_new_stored_OG_kcals = \
			np.multiply(
				np.array(self.billions_fed_new_stored_OG_kcals_tmp),
				self.OG_SF_fraction_kcals_to_humans
			)

		self.billions_fed_OG_kcals = np.multiply(
			np.array(self.makeMidMonthlyVars(
				crops_food_eaten_no_rot,
				CROPS_WASTE/self.c["KCALS_MONTHLY"],
				show_output))
			+ np.array(self.makeMidMonthlyVars(
				crops_food_eaten_rot,
				CROPS_WASTE \
				 * self.c["OG_ROTATION_FRACTION_KCALS"]/self.c["KCALS_MONTHLY"],
				show_output)),
			self.OG_SF_fraction_kcals_to_humans\
		)

		self.billions_fed_OG_fat = np.multiply(
			np.array(self.makeMidMonthlyVars(
				crops_food_eaten_no_rot,
				CROPS_WASTE\
				 * self.c["OG_FRACTION_FAT"]/self.c["FAT_MONTHLY"]/1e9,
				show_output))
			+ np.array(self.makeMidMonthlyVars(
				crops_food_eaten_rot,
				CROPS_WASTE\
				 * self.c["OG_ROTATION_FRACTION_FAT"]/self.c["FAT_MONTHLY"]/1e9,
				show_output)),
			self.OG_SF_fraction_fat_to_humans\
		)

		self.billions_fed_OG_protein = np.multiply(
			np.array(self.makeMidMonthlyVars(
				crops_food_eaten_no_rot,
				CROPS_WASTE
				* self.c["OG_FRACTION_PROTEIN"]\
				/self.c["PROTEIN_MONTHLY"]/1e9,
				show_output))
			+ np.array(self.makeMidMonthlyVars(
				crops_food_eaten_rot,
				CROPS_WASTE\
				 * self.c["OG_ROTATION_FRACTION_PROTEIN"]\
				/self.c["PROTEIN_MONTHLY"]/1e9,
				show_output)),
			self.OG_SF_fraction_protein_to_humans\
		)

		self.billions_fed_OG_produced_kcals = \
			np.multiply(
				CROPS_WASTE\
				* og_produced_kcals / self.c["KCALS_MONTHLY"],
				self.OG_SF_fraction_kcals_to_humans
			)

		self.billions_fed_OG_produced_fat = \
			np.multiply(
				np.concatenate([
					np.array(crops_food_produced[0:self.c['inputs']["INITIAL_HARVEST_DURATION"]])
					* self.c["OG_FRACTION_FAT"],\
					np.array(crops_food_produced[self.c['inputs']["INITIAL_HARVEST_DURATION"]:])\
					 * self.c["OG_ROTATION_FRACTION_FAT"],
				]) / self.c["FAT_MONTHLY"]/1e9,
				self.OG_SF_fraction_fat_to_humans
			) * CROPS_WASTE

		self.billions_fed_OG_produced_protein = \
			np.multiply(
				np.concatenate([
					np.array(crops_food_produced[0:self.c['inputs']["INITIAL_HARVEST_DURATION"]])
					* self.c["OG_FRACTION_PROTEIN"],\
					np.array(crops_food_produced[self.c['inputs']["INITIAL_HARVEST_DURATION"]:])\
					 * self.c["OG_ROTATION_FRACTION_PROTEIN"],
				]) / self.c["PROTEIN_MONTHLY"]/1e9,
				self.OG_SF_fraction_protein_to_humans
			) * CROPS_WASTE
		# print("self.billions_fed_OG_produced_kcals")
		# print(self.billions_fed_OG_produced_kcals)
		# print("self.billions_fed_OG_produced_fat")
		# print(self.billions_fed_OG_produced_fat)
		# print("self.billions_fed_OG_produced_protein")
		# print(self.billions_fed_OG_produced_protein)
		# print("self.billions_fed_OG_kcals")
		# print(self.billions_fed_OG_kcals)
		# print("self.billions_fed_OG_fat")
		# print(self.billions_fed_OG_fat)
		# print("self.billions_fed_OG_protein")
		# print(self.billions_fed_OG_protein)
		# print("self.billions_fed_GH_fat")
		# print(self.billions_fed_GH_fat)
		# quit()
	#if cellulosic sugar isn't included, these results will be zero
	def analyze_CS_results(
		self,
		production_kcals_CS_per_m,
		show_output
		):

		self.billions_fed_CS_kcals = \
			np.array(production_kcals_CS_per_m) \
			/ self.c["KCALS_MONTHLY"]


	#if methane scp isn't included, these results will be zero
	def analyze_SCP_results(
		self,
		production_kcals_scp_per_m,
		production_fat_scp_per_m,
		production_protein_scp_per_m,
		show_output
		):

		self.billions_fed_SCP_kcals = \
			np.array(production_kcals_scp_per_m) \
			/ self.c["KCALS_MONTHLY"]

		self.billions_fed_SCP_fat = \
			np.array(production_fat_scp_per_m) \
			/ self.c["FAT_MONTHLY"]/1e9

		self.billions_fed_SCP_protein = \
			np.array(production_protein_scp_per_m) \
			/ self.c["PROTEIN_MONTHLY"]/1e9

	#if stored food isn't included, these results will be zero
	def analyze_meat_dairy_results(
		self,
		meat_start,
		meat_end,
		meat_eaten,
		dairy_milk_kcals,
		dairy_milk_fat,
		dairy_milk_protein,
		cattle_maintained_kcals,
		cattle_maintained_fat,
		cattle_maintained_protein,
		h_e_meat_kcals,
		h_e_meat_fat,
		h_e_meat_protein,
		h_e_milk_kcals,
		h_e_milk_fat,
		h_e_milk_protein,
		h_e_balance_kcals,
		h_e_balance_fat,
		h_e_balance_protein,
		show_output
		):

		self.billions_fed_meat_kcals_tmp = np.array(self.makeMidMonthlyVars(
			meat_eaten,
			1/self.c["KCALS_MONTHLY"],
			show_output))


		self.billions_fed_meat_kcals = \
			self.billions_fed_meat_kcals_tmp \
		 + np.array(cattle_maintained_kcals)\
			 / self.c["KCALS_MONTHLY"]

		if(self.c["VERBOSE"]):
			print("expected culled meat kcals month 0 to 8ish")
			# print(self.c["MEAT_FRACTION_KCALS"]*self.c["LIMIT_PER_MONTH_CULLED"])
			print(self.c["LIMIT_PER_MONTH_CULLED"])
			print("actual culled meat")
			print(self.billions_fed_meat_kcals_tmp*self.c["KCALS_MONTHLY"])
			# print(np.divide(self.billions_fed_meat_kcals_tmp,self.OG_SF_fraction_kcals_to_humans)*self.c["KCALS_MONTHLY"])

		self.billions_fed_meat_fat_tmp = np.array(self.makeMidMonthlyVars(
			meat_eaten,
			self.c["MEAT_FRACTION_FAT"]/self.c["FAT_MONTHLY"]/1e9,
			show_output))

		self.billions_fed_meat_fat = self.billions_fed_meat_fat_tmp\
		 + np.array(cattle_maintained_fat) / self.c["FAT_MONTHLY"]/1e9


		self.billions_fed_meat_protein_tmp = np.array(self.makeMidMonthlyVars(
			meat_eaten,
			self.c["MEAT_FRACTION_PROTEIN"]\
			/self.c["PROTEIN_MONTHLY"]/1e9,
			show_output))

		self.billions_fed_meat_protein = self.billions_fed_meat_protein_tmp\
		 + np.array(cattle_maintained_protein) / self.c["PROTEIN_MONTHLY"]/1e9


		self.billions_fed_milk_kcals = np.array(dairy_milk_kcals) \
			/ self.c["KCALS_MONTHLY"]

		self.billions_fed_milk_fat = np.array(dairy_milk_fat)\
			/ self.c["FAT_MONTHLY"] / 1e9

		self.billions_fed_milk_protein = np.array(dairy_milk_protein)\
			/ self.c["PROTEIN_MONTHLY"] / 1e9

		self.billions_fed_h_e_meat_kcals = \
			h_e_meat_kcals / self.c["KCALS_MONTHLY"]

		self.billions_fed_h_e_meat_fat = \
			h_e_meat_fat / self.c["FAT_MONTHLY"]/1e9

		self.billions_fed_h_e_meat_protein = \
			h_e_meat_protein / self.c["PROTEIN_MONTHLY"]/1e9


		self.billions_fed_h_e_milk_kcals = \
			h_e_milk_kcals / self.c["KCALS_MONTHLY"]

		self.billions_fed_h_e_milk_fat = \
			h_e_milk_fat / self.c["FAT_MONTHLY"]/1e9

		self.billions_fed_h_e_milk_protein = \
			h_e_milk_protein / self.c["PROTEIN_MONTHLY"]/1e9


		self.billions_fed_h_e_balance_kcals = \
			h_e_balance_kcals / self.c["KCALS_MONTHLY"]

		self.billions_fed_h_e_balance_fat = \
			h_e_balance_fat / self.c["FAT_MONTHLY"]/1e9

		self.billions_fed_h_e_balance_protein = \
			h_e_balance_protein / self.c["PROTEIN_MONTHLY"]/1e9
		

		#useful for plotting meat and dairy

		# import matplotlib.pyplot as plt
		# cm = np.multiply(np.array(cattle_maintained_kcals)\
		# 			 / self.c["KCALS_MONTHLY"],self.OG_SF_fraction_kcals_to_humans)
		# plt.plot(cm,label = "cattle meat")
		# m=np.multiply(self.billions_fed_meat_kcals_tmp,self.OG_SF_fraction_kcals_to_humans)
		# plt.plot(m,label = "non cattle meat")
		# plt.plot(self.billions_fed_milk_kcals,label = "milk")
		# plt.title("milk and meat")
		# lim = np.array(879e6/12)*1e3* 610/1e9*(1-self.c['inputs']['WASTE']['DAIRY']/100)/self.c["KCALS_MONTHLY"]
		# plt.plot(np.array([lim]*self.c["inputs"]["NMONTHS"]),label = "lim dairy")
		# plt.plot(self.billions_fed_h_e_meat_kcals,label = "h e meat")
		# plt.plot(self.billions_fed_h_e_milk_kcals,label = "h e milk")
		# plt.plot(cm + m +self.billions_fed_h_e_meat_kcals + self.billions_fed_h_e_milk_kcals + self.billions_fed_milk_kcals,label = "sum")
		# plt.legend()
		# plt.show()


		if(self.c['ADD_MEAT'] and self.c['VERBOSE']):
			print('Days non egg, non dairy meat global at start, by kcals')
			print(360*self.c['INITIAL_MEAT'] 
				/ (12*self.c['KCALS_MONTHLY']))

	#if stored food isn't included, these results will be zero
	def analyze_SF_results(
		self,
		stored_food_eaten,
		stored_food_start,
		stored_food_end,
		show_output
		):


		CROPS_WASTE = 1-self.c["inputs"]["WASTE"]["CROPS"]/100

		self.billions_fed_SF_kcals = np.multiply(self.makeMidMonthlyVars(
			stored_food_eaten,
			CROPS_WASTE\
			 * self.c["SF_FRACTION_KCALS"]/self.c["KCALS_MONTHLY"],
			show_output),self.OG_SF_fraction_kcals_to_humans)


		# self.billion_person_years_SF_kcals = self.makeStartEndMonthlyVars(
		# 	stored_food_start,
		# 	stored_food_end,
		# 	self.c["SF_FRACTION_KCALS"]/(self.c["KCALS_MONTHLY"]*12)*(1-self.c["inputs"]["H_E_FRACTION_USED_FOR_FEED"]),
		# 	show_output)

		self.billions_fed_SF_fat = np.multiply(self.makeMidMonthlyVars(
			stored_food_eaten,
			CROPS_WASTE\
			 * self.c["SF_FRACTION_FAT"]/self.c["FAT_MONTHLY"]/1e9,
			show_output),self.OG_SF_fraction_fat_to_humans)

		# self.billion_person_years_SF_fat = self.makeStartEndMonthlyVars(
		# 	stored_food_start,
		# 	stored_food_end,
		# 	self.c["SF_FRACTION_FAT"]/(self.c["FAT_MONTHLY"]*12)/1e9*(1-self.c["inputs"]["H_E_FRACTION_USED_FOR_FEED"]),
		# 	show_output)
	
		self.billions_fed_SF_protein = np.multiply(self.makeMidMonthlyVars(
			stored_food_eaten,
			CROPS_WASTE\
			 * self.c["SF_FRACTION_PROTEIN"]/self.c["PROTEIN_MONTHLY"]/1e9,
			show_output),self.OG_SF_fraction_protein_to_humans)

		# self.billion_person_years_SF_protein = self.makeStartEndMonthlyVars(
		# 	stored_food_start,
		# 	stored_food_end,
		# 	self.c["SF_FRACTION_PROTEIN"]/(self.c["PROTEIN_MONTHLY"]*12)/1e9*(1-self.c["inputs"]["H_E_FRACTION_USED_FOR_FEED"],
		# 	show_output)

		if(self.c['ADD_STORED_FOOD'] and self.c['VERBOSE']):
			print('Days stored food global at start, by kcals')
			print(360*self.c['INITIAL_SF'] 
				* self.c['SF_FRACTION_KCALS']
				/ (12*self.c["KCALS_MONTHLY"]))
			print('Days stored food global at start, by fat')
			print(360*self.c['INITIAL_SF'] 
				* self.c['SF_FRACTION_FAT']
				/ (12*self.c['FAT_MONTHLY']*7.9e9))
			print('Days stored food global at start, by protein')
			print(360*self.c['INITIAL_SF'] 
				* self.c['SF_FRACTION_PROTEIN']
				/ (12*self.c['PROTEIN_MONTHLY']*7.9e9))

	def analyze_seaweed_results(
		self,
		seaweed_wet_on_farm,
		used_area,
		built_area,
		seaweed_food_produced,
		seaweed_food_produced_monthly,
		show_output
		):

		# self.seaweed_wet_on_farm = self.makeDailyVars(
		# 	seaweed_wet_on_farm,
		# 	1,
		# 	show_output)

		# self.seaweed_used_area = self.makeDailyVars(
		# 	used_area,
		# 	1,
		# 	show_output)

		self.seaweed_built_area = built_area
		self.seaweed_built_area_max_density = np.array(built_area)*self.c['MAXIMUM_DENSITY']

		# self.seaweed_loss = np.append([0],
		# 		np.diff(self.seaweed_used_area)
		# 		* self.c["MINIMUM_DENSITY"]
		# 		* (self.c["HARVEST_LOSS"]/100))
		# self.seaweed_food_produced_daily = self.makeDailyVars(
		# 	seaweed_food_produced,
		# 	1,
		# 	show_output)

		self.seaweed_food_produced_monthly = self.makeMidMonthlyVars(
			seaweed_food_produced_monthly,
			1,
			show_output)

		self.billions_fed_seaweed_kcals = self.makeMidMonthlyVars(
			seaweed_food_produced_monthly,
			self.c["SEAWEED_KCALS"]/self.c["KCALS_MONTHLY"],
			show_output)

		self.billions_fed_seaweed_fat = self.makeMidMonthlyVars(
			seaweed_food_produced_monthly,
			self.c["SEAWEED_FAT"]/self.c["FAT_MONTHLY"]/1e9,
			show_output)

		self.billions_fed_seaweed_protein = self.makeMidMonthlyVars(
			seaweed_food_produced_monthly,
			self.c["SEAWEED_PROTEIN"]/self.c["PROTEIN_MONTHLY"]/1e9,
			show_output)


		# self.max_seaweed = self.c['MAXIMUM_AREA'] * self.c['MAXIMUM_DENSITY']
		# self.seaweed_used_area_max_density = np.array(self.seaweed_used_area) * self.c['MAXIMUM_DENSITY']


	# The optimizer will maximize minimum fat, calories, and protein over any month, but it does not care which sources these come from. The point of this function is to determine the probable contributions to excess calories used for feed and biofuel from appropriate sources (unless this has been updated, it takes it exclusively from outdoor growing and stored food). 
	# there is also a constraint to make sure the sources which can be used for feed are not exhausted, and the model will not be able to solve if the usage from biofuels and feed are more than the available stored food and outdoor crop production.
	def compute_excess_after_run(self,model):

		# I spent like five hours trying to figure out why the answer was wrong 
		# until I finally found an issue with string ordering, fixed it below

		humans_fed_kcals = []
		humans_fed_fat = []
		humans_fed_protein = []
		order_kcals = []
		order_fat = []
		order_protein = []
		for var in model.variables():
			if("Humans_Fed_Kcals_" in var.name):
				humans_fed_kcals.append(var.value())
				order_kcals.append(\
					int(var.name[len("Humans_Fed_Kcals_"):].split("_")[0])\
				)
			if("Humans_Fed_Fat_" in var.name):
				order_fat.append(\
					int(var.name[len("Humans_Fed_Fat_"):].split("_")[0])\
				)
				humans_fed_fat.append(var.value())
			if("Humans_Fed_Protein_" in var.name):
				order_protein.append(\
					int(var.name[len("Humans_Fed_Protein_"):].split("_")[0])\
				)
				humans_fed_protein.append(var.value())

		zipped_lists = zip(order_kcals, humans_fed_kcals)
		sorted_zipped_lists = sorted(zipped_lists)
		self.humans_fed_kcals_optimizer = [element for _, element in sorted_zipped_lists]

		zipped_lists = zip(order_fat, humans_fed_fat)
		sorted_zipped_lists = sorted(zipped_lists)
		self.humans_fed_fat_optimizer = [element for _, element in sorted_zipped_lists]
		
		zipped_lists = zip(order_protein, humans_fed_protein)
		sorted_zipped_lists = sorted(zipped_lists)
		self.humans_fed_protein_optimizer = [element for _, element in sorted_zipped_lists]

		feed_delay = self.c['inputs']['FEED_SHUTOFF_DELAY']
		sum_before = np.sum((np.array(self.humans_fed_kcals_optimizer)[:feed_delay] - self.c["WORLD_POP"]/1e9))

		if(feed_delay == self.c["NMONTHS"]):
			self.excess_after_run = (np.array(self.humans_fed_kcals_optimizer) - self.c["WORLD_POP"]/1e9)*self.c["KCALS_MONTHLY"]
		else:		
			# any consistent monthly excess is subtracted
			# also spread out excess calories in pre-"feed shutoff" months
			# to be used in months after feed is shutoff 
			self.excess_after_run = \
				(\
					np.array(self.humans_fed_kcals_optimizer) \
					- self.c["WORLD_POP"]/1e9 \
					+ (sum_before)/(self.c["NMONTHS"]-feed_delay)
				)*self.c["KCALS_MONTHLY"]
	
	def calc_fraction_OG_SF_to_humans(\
		self,
		model,
		crops_food_eaten_no_rot,
		crops_food_eaten_rot,
		stored_food_eaten,
		excess_calories,
		excess_fat_used,
		excess_protein_used
		):
		
		"""
		each month:
			(all the sources except using human edible fed food) + (-excess provided) + (meat and dairy from human edible sources)
			=
			(all the sources except using human edible fed food)*(fraction fed to humans) + (meat and dairy from human edible sources) 
		because each month:
			1 + (-excess provided)/(all the sources except using human edible fed food)
			=
			(fraction fed to humans)
		
		so then we let

		(all the sources except using human edible fed food)*(fraction fed to humans)
		==
		(all the sources except using human edible fed food) + (-excess provided)

		let:
		a = all the sources except using human edible fed food
		b = excess
		c = fraction fed to humans
		d = meat and dairy from human edible sources
		e = humans actually fed from everything together

		Perhaps this (inscrutible?) algebra will be helpful to you

		a-b = a*c => c = (a-b)/a = 1-b/a

		and if:
		a+d-b=e
		a=b-d+e

		then we have

		c = 1 - b/(b-d+e)
		
		"""
		SF_kcals = self.makeMidMonthlyVars(
			stored_food_eaten,
			self.c["SF_FRACTION_KCALS"]/self.c["KCALS_MONTHLY"],
			False)


		# self.billion_person_years_SF_kcals = self.makeStartEndMonthlyVars(
		# 	stored_food_start,
		# 	stored_food_end,
		# 	self.c["SF_FRACTION_KCALS"]/(self.c["KCALS_MONTHLY"]*12)*(1-self.c["inputs"]["H_E_FRACTION_USED_FOR_FEED"]),
		# 	show_output)

		SF_fat = self.makeMidMonthlyVars(
			stored_food_eaten,
			self.c["SF_FRACTION_FAT"]/self.c["FAT_MONTHLY"]/1e9,
			False)

		# self.billion_person_years_SF_fat = self.makeStartEndMonthlyVars(
		# 	stored_food_start,
		# 	stored_food_end,
		# 	self.c["SF_FRACTION_FAT"]/(self.c["FAT_MONTHLY"]*12)/1e9*(1-self.c["inputs"]["H_E_FRACTION_USED_FOR_FEED"]),
		# 	show_output)
		
		SF_protein = self.makeMidMonthlyVars(
			stored_food_eaten,
			self.c["SF_FRACTION_PROTEIN"]/self.c["PROTEIN_MONTHLY"]/1e9,
			False)

		OG_kcals = \
			np.array(self.makeMidMonthlyVars(
				crops_food_eaten_no_rot,
				1/self.c["KCALS_MONTHLY"],
				False))\
			+ np.array(self.makeMidMonthlyVars(
				crops_food_eaten_rot,
				self.c["OG_ROTATION_FRACTION_KCALS"]/self.c["KCALS_MONTHLY"],
				False))\

		OG_fat = \
			np.array(self.makeMidMonthlyVars(
				crops_food_eaten_no_rot,
				self.c["OG_FRACTION_FAT"]/self.c["FAT_MONTHLY"]/1e9,
				False))\
			+ np.array(self.makeMidMonthlyVars(
				crops_food_eaten_rot,
				self.c["OG_ROTATION_FRACTION_FAT"]/self.c["FAT_MONTHLY"]/1e9,
				False))

		OG_protein = \
			np.array(self.makeMidMonthlyVars(
				crops_food_eaten_no_rot,
				self.c["OG_FRACTION_PROTEIN"]\
				/self.c["PROTEIN_MONTHLY"]/1e9,
				False))\
			+ np.array(self.makeMidMonthlyVars(
				crops_food_eaten_rot,
				self.c["OG_ROTATION_FRACTION_PROTEIN"]\
				/self.c["PROTEIN_MONTHLY"]/1e9,
				False))


		print(excess_calories)
		print(np.array(OG_kcals))
		print(np.array(SF_kcals))
		OG_SF_fraction_kcals_to_feed =\
			np.divide(\
				excess_calories,\
				(np.array(OG_kcals) + np.array(SF_kcals)) \
				 * self.c["KCALS_MONTHLY"]\
			)


		OG_SF_fraction_kcals_to_humans = 1 - OG_SF_fraction_kcals_to_feed

		# it seems impossible for there to be more fat used for feed than actually produced from all the sources, if the optimizer spits out a positive number of people fed in terms of fat.
		# The estimate for amount used for feed divides the excess by all the sources (except human edible feed). If the excess is greater than the sources, we have a problem.
		# The sources actually added to get humans_fed_fat, does however include the excess as a negative number. The excess is added to humans_fat_fed to cancel this. Also, humans_fed_fat includes meat and milk from human edible.
		# So the only reason it doesnt actually go negative is because the optimizer takes an optimization including the human edible fat which pushes it to some positive balance of people fed in terms of fat.
		# So its not impossible, it just means that the part of the excess which required more fat had to come from the animal outputs themselves.
		# By adding a requirement that the fat, calories and protein need to be satisfied before human edible produce meat is taken into account we will have 100% of resources spent on meeting these requirements and 0% going to humans. The optimizer will still 

		# print("h_e_meat_fat + h_e_milk_fat")
		# print(h_e_meat_fat + h_e_milk_fat)

		# print("np.array(humans_fed_fat)")
		# print(np.array(humans_fed_fat)\
		# 			 * self.c["FAT_MONTHLY"]\
		# 			 * 1e9)

		OG_SF_fraction_fat_to_feed = \
			np.divide(\
				excess_fat_used,\
				(np.array(OG_fat) + np.array(SF_fat))\
				 * self.c["FAT_MONTHLY"] * 1e9
			)

		OG_SF_fraction_fat_to_humans = 1 - OG_SF_fraction_fat_to_feed
			
		OG_SF_fraction_protein_to_feed = \
			np.divide(\
				excess_protein_used,\
				(np.array(OG_protein) + np.array(SF_protein))\
				 * self.c["PROTEIN_MONTHLY"] * 1e9
			)

		OG_SF_fraction_protein_to_humans = 1 - OG_SF_fraction_protein_to_feed
		
		# print("OG_SF_fraction_fat_to_feed")
		# print(OG_SF_fraction_fat_to_feed)

		print("OG_SF_fraction_kcals_to_feed")
		print(OG_SF_fraction_kcals_to_feed)
		# print(OG_SF_fraction_fat_to_feed<=1)
		assert((OG_SF_fraction_kcals_to_feed <= 1+ 1e-5).all())
		assert((OG_SF_fraction_kcals_to_feed >= 0).all())
		if(self.c["inputs"]["INCLUDE_FAT"]):
			assert((OG_SF_fraction_fat_to_feed <= 1 + 1e-5).all())
			assert((OG_SF_fraction_fat_to_feed >= 0).all())
		if(self.c["inputs"]["INCLUDE_PROTEIN"]):
			assert((OG_SF_fraction_protein_to_feed <= 1+ 1e-5).all())
			assert((OG_SF_fraction_protein_to_feed >= 0).all())


		self.OG_SF_fraction_kcals_to_humans = OG_SF_fraction_kcals_to_humans
		self.OG_SF_fraction_fat_to_humans = OG_SF_fraction_fat_to_humans
		self.OG_SF_fraction_protein_to_humans = OG_SF_fraction_protein_to_humans

	def analyze_results(self,model,time_months_middle):
		self.kcals_fed = (np.array(self.billions_fed_SF_kcals)\
			+np.array(self.billions_fed_meat_kcals)\
			+np.array(self.billions_fed_seaweed_kcals)\
			+np.array(self.billions_fed_milk_kcals)\
			+np.array(self.billions_fed_CS_kcals)\
			+np.array(self.billions_fed_SCP_kcals)\
			+np.array(self.billions_fed_GH_kcals)\
			+np.array(self.billions_fed_OG_kcals)\
			+np.array(self.billions_fed_fish_kcals)\
			+ self.billions_fed_h_e_meat_kcals\
			+ self.billions_fed_h_e_milk_kcals)


		self.fat_fed = np.array(self.billions_fed_SF_fat)\
			+np.array(self.billions_fed_meat_fat)\
			+np.array(self.billions_fed_seaweed_fat)\
			+np.array(self.billions_fed_milk_fat)\
			+np.array(self.billions_fed_SCP_fat)\
			+np.array(self.billions_fed_GH_fat)\
			+np.array(self.billions_fed_OG_fat)\
			+np.array(self.billions_fed_fish_fat)\
			+ self.billions_fed_h_e_meat_fat\
			+ self.billions_fed_h_e_milk_fat

		self.protein_fed = (np.array(self.billions_fed_SF_protein)\
			+np.array(self.billions_fed_meat_protein)\
			+np.array(self.billions_fed_seaweed_protein)\
			+np.array(self.billions_fed_milk_protein)\
			+np.array(self.billions_fed_GH_protein)\
			+np.array(self.billions_fed_SCP_protein)\
			+np.array(self.billions_fed_OG_protein)\
			+np.array(self.billions_fed_fish_protein))\
			+ self.billions_fed_h_e_meat_protein\
			+ self.billions_fed_h_e_milk_protein

		print(abs(np.divide(self.kcals_fed - np.array(self.humans_fed_kcals_optimizer),self.kcals_fed)))
		assert((abs(np.divide(self.kcals_fed \
			- np.array(self.humans_fed_kcals_optimizer),self.kcals_fed)) < 1e-6).all())
		if(self.c["inputs"]["INCLUDE_FAT"]):
			# print(abs(np.divide(self.fat_fed - np.array(self.humans_fed_fat_optimizer),self.fat_fed)))
			assert((abs(np.divide(self.fat_fed \
				- np.array(self.humans_fed_fat_optimizer),self.fat_fed)) < 1e-6).all())
		if(self.c["inputs"]["INCLUDE_PROTEIN"]):
			assert((abs(np.divide(self.protein_fed \
				- np.array(self.humans_fed_protein_optimizer),self.protein_fed)) < 1e-6).all())
		

		SF_OG_kcals = (np.array(self.billions_fed_SF_kcals)\
			+np.array(self.billions_fed_OG_kcals)\
			)
		SF_OG_fat = (np.array(self.billions_fed_SF_fat)\
			+np.array(self.billions_fed_OG_fat)\
			)
		SF_OG_protein = (np.array(self.billions_fed_SF_protein)\
			+np.array(self.billions_fed_OG_protein)\
			)
		
			
		#if it takes all the available ag production to produce minimum for biofuel and animal feed demands
		division = []
		print("SF_OG_kcals")
		print(SF_OG_kcals)
		print("OG_SF_fraction_kcals_to_humans")
		print(self.OG_SF_fraction_kcals_to_humans)
		#divide off the reduction to get
		for zipped_lists in zip(SF_OG_kcals,self.OG_SF_fraction_kcals_to_humans):
			
			if(zipped_lists[1] <= 0):
				assert(zipped_lists[0] >= -1e-5)
				division.append(0)
			else:
				division.append(zipped_lists[0]/zipped_lists[1])
		

		print("SF_OG_kcals")
		print(SF_OG_kcals)
		print("self.billions_fed_h_e_meat_kcals")
		print(self.billions_fed_h_e_meat_kcals)
		print("self.billions_fed_h_e_milk_kcals")
		print(self.billions_fed_h_e_milk_kcals)
		print("np.array(division)")
		print(np.array(division))
		print("self.billions_fed_h_e_balance_kcals")
		print(self.billions_fed_h_e_balance_kcals)
		fractional_difference = \
			np.divide(\
				(\
					SF_OG_kcals \
					+ self.billions_fed_h_e_meat_kcals\
					+ self.billions_fed_h_e_milk_kcals\
				)\
				-\
				(\
					np.array(division)+self.billions_fed_h_e_balance_kcals\
				),\
				SF_OG_kcals \
				+ self.billions_fed_h_e_meat_kcals\
				+ self.billions_fed_h_e_milk_kcals\
			)
		print(abs(fractional_difference))
		assert((abs(fractional_difference)<1e-6).all())

		if(self.c['inputs']['INCLUDE_FAT'] == True):
			division = []
			for zipped_lists in zip(SF_OG_fat,self.OG_SF_fraction_fat_to_humans):
				
				if(zipped_lists[1] <= 0):
					assert(zipped_lists[0] >= -1e-5)
					division.append(0)
				else:
					division.append(zipped_lists[0]/zipped_lists[1])

			fractional_difference = \
				np.divide(\
					(\
						SF_OG_fat \
						+ self.billions_fed_h_e_meat_fat\
						+ self.billions_fed_h_e_milk_fat\
					)\
					-\
					(\
						np.array(division)\
						+self.billions_fed_h_e_balance_fat\
					),\
					SF_OG_fat \
					+ self.billions_fed_h_e_meat_fat\
					+ self.billions_fed_h_e_milk_fat\
				)

			# print(fractional_difference)
			assert((abs(fractional_difference)<1e-6).all())
		

		if(self.c['inputs']['INCLUDE_PROTEIN'] == True):

			division = []
			for zipped_lists in zip(SF_OG_protein,self.OG_SF_fraction_protein_to_humans):			
				
				if(zipped_lists[1] <= 0):
					assert(zipped_lists[0] >= -1e-5)
					division.append(0)
				else:
					division.append(zipped_lists[0]/zipped_lists[1])
			
			fractional_difference = \
				np.divide(\
					(\
						SF_OG_protein \
						+ self.billions_fed_h_e_meat_protein\
						+ self.billions_fed_h_e_milk_protein\
					)\
					-\
					(\
						np.array(division)\
						+self.billions_fed_h_e_balance_protein\
					),\
					SF_OG_protein \
					+ self.billions_fed_h_e_meat_protein\
					+ self.billions_fed_h_e_milk_protein\
				)

			assert((abs(fractional_difference)<1e-6).all())
		

		self.people_fed_billions=model.objective.value()

		fed = {'fat':np.round(np.min(self.fat_fed),2),'kcals':np.round(np.min(self.kcals_fed),2),'protein':np.round(np.min(self.protein_fed),2)}
		mins =  [key for key in fed if 
				all(fed[temp] >= fed[key]
				for temp in fed)]
		print(fed)

		print("Nutrients with constraining values are: " + str(mins))
		print('Estimated people fed is '+ str(self.people_fed_billions)+' billion')
		return [self.people_fed_billions,mins]
		

	#billions of kcals
	def countProduction(self,months):
		
		kcals = self.kcals_fed*self.c['KCALS_MONTHLY']

		kcals_sum = 0
		for m in months:
			kcals_sum = kcals_sum + kcals[m-1]

		return kcals_sum