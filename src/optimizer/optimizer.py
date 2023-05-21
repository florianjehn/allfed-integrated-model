"""
Optimizer Model
In this model, we estimate the macronutrient production allocated optimally
over time including models for traditional and resilient foods.
"""
from datetime import time
import pulp
import numpy as np
from pulp import LpMaximize, LpMinimize, LpProblem, LpVariable, LpConstraint


class Optimizer:
    def __init__(self):
        pass

    def optimize(self, single_valued_constants, time_consts):
        maximize_constraints = []  # used only for validation

        # Create the model to optimize
        model = LpProblem(name="optimization_nutrition", sense=LpMaximize)

        # make sure there's nothing fishy going on with the constants (no nan's)
        # (otherwise the linear optimizer will fail in a very mysterious way)

        # If having trouble with the optimization, here are a few parameters to reduce the number of variables
        # so you can print(model) to see what constraints are being added
        # single_valued_constants["NMONTHS"] = 1
        # single_valued_constants["ADD_SEAWEED"] = False
        # single_valued_constants["ADD_METHANE_SCP"] = False
        # single_valued_constants["ADD_CULLED_MEAT"] = False
        # single_valued_constants["inputs"]["OG_USE_BETTER_ROTATION"] = False

        self.single_valued_constants = single_valued_constants
        self.time_consts = time_consts

        self.time_months = []

        NMONTHS = single_valued_constants["NMONTHS"]

        variables = self.load_variable_names_and_prefixes(NMONTHS)
        # MODEL GENERATION LOOP #

        # TODO: it would be nice to not pass model or variables in, and instead to simply
        # get conditions as a dictionary, and add the conditions to the model in this function
        resource_constants = {
            "ADD_SEAWEED": {
                "prefixes": self.seaweed_prefixes,
                "function": self.add_seaweed_to_model,
            },
            "ADD_OUTDOOR_GROWING": {
                "prefixes": self.crops_food_prefixes,
                "function": self.add_outdoor_crops_to_model,
            },
            "ADD_STORED_FOOD": {
                "prefixes": self.stored_food_prefixes,
                "function": self.add_stored_food_to_model,
            },
            "ADD_CULLED_MEAT": {
                "prefixes": self.culled_meat_prefixes,
                "function": self.add_culled_meat_to_model,
            },
            "ADD_METHANE_SCP": {
                "prefixes": self.methane_scp_prefixes,
                "function": self.add_methane_scp_to_model,
            },
            "ADD_CELLULOSIC_SUGAR": {
                "prefixes": self.cell_sugar_prefixes,
                "function": self.add_cellulosic_sugar_to_model,
            },
        }

        for key, resource in resource_constants.items():
            if single_valued_constants[key]:
                prefixes = resource["prefixes"]
                func = resource["function"]
                variables = self.add_variable_from_prefixes(variables, prefixes)
                for month in range(0, NMONTHS):
                    conditions = func(month, variables)
                    model = self.add_conditions_to_model(model, month, conditions)

        for month in range(0, NMONTHS):
            [model, variables, maximize_constraints] = self.add_objectives_to_model(
                model, variables, month, maximize_constraints
            )
        PRINT_PULP_MESSAGES = False
        model += variables["objective_function"]

        status = model.solve(
            pulp.PULP_CBC_CMD(gapRel=0.0001, msg=PRINT_PULP_MESSAGES, fracGap=0.001)
        )
        ASSERT_SUCCESSFUL_OPTIMIZATION = True
        if ASSERT_SUCCESSFUL_OPTIMIZATION:
            assert status == 1, "ERROR: OPTIMIZATION FAILED!"

        model, variables = self.add_old_objective_as_constraint(
            model, variables, NMONTHS
        )

        if status == 1:
            model, variables = self.second_optimization_to_humans_maxed(
                model,
                variables,
                NMONTHS,
                ASSERT_SUCCESSFUL_OPTIMIZATION,
                single_valued_constants,
            )

        if status == 1 and self.single_valued_constants["STORE_FOOD_BETWEEN_YEARS"]:
            model, variables = self.third_optimization_smoothing(
                model,
                variables,
                NMONTHS,
                ASSERT_SUCCESSFUL_OPTIMIZATION,
                single_valued_constants,
            )
        return (
            model,
            variables,
            maximize_constraints,
            single_valued_constants,
            time_consts,
        )

    def add_conditions_to_model(self, model, month, conditions):
        for prefix, condition in conditions.items():
            constraint = (condition, f"{prefix}_{month}_Constraint")
            model += constraint

        return model

    def load_variable_names_and_prefixes(self, NMONTHS):
        variables = {}

        variables["objective_function"] = LpVariable(
            name="Least_Humans_Fed_Any_Month", lowBound=0
        )

        self.stored_food_prefixes = [
            "Stored_Food_Start",
            "Stored_Food_End",
            "Stored_Food_To_Humans",
            "Stored_Food_Feed",
            "Stored_Food_Biofuel",
        ]
        self.methane_scp_prefixes = [
            "Methane_SCP_To_Humans",
            "Methane_SCP_Feed",
            "Methane_SCP_Biofuel",
        ]
        self.cell_sugar_prefixes = [
            "Cellulosic_Sugar_To_Humans",
            "Cellulosic_Sugar_Feed",
            "Cellulosic_Sugar_Biofuel",
        ]
        self.culled_meat_prefixes = [
            "Culled_Meat_Start",
            "Culled_Meat_End",
            "Culled_Meat_Eaten",
        ]
        self.crops_food_prefixes = [
            "Crops_Food_Storage",
            "Crops_Food_Eaten",
            "Crops_Food_Eaten_Fat",
            "Crops_Food_Eaten_Protein",
            "Crops_Food_To_Humans",
            "Crops_Food_Feed",
            "Crops_Food_Biofuel",
            "Crops_Food_To_Humans_Fat",
            "Crops_Food_Feed_Fat",
            "Crops_Food_Biofuel_Fat",
            "Crops_Food_To_Humans_Protein",
            "Crops_Food_Feed_Protein",
            "Crops_Food_Biofuel_Protein",
        ]

        self.seaweed_prefixes = [
            "Seaweed_Wet_On_Farm",
            "Seaweed_To_Humans",
            "Seaweed_Feed",
            "Seaweed_Biofuel",
            "Used_Area",
        ]

        nested_list = [
            self.stored_food_prefixes,
            self.methane_scp_prefixes,
            self.cell_sugar_prefixes,
            self.culled_meat_prefixes,
            self.crops_food_prefixes,
            self.seaweed_prefixes,
        ]

        flattened_list = [item for sublist in nested_list for item in sublist]

        for camel_case_variable_name in flattened_list:
            # these will be overwritten if the variable is used
            variables[camel_case_variable_name.lower()] = [0] * NMONTHS

        variables["consumed_kcals"] = [0] * NMONTHS
        variables["consumed_fat"] = [0] * NMONTHS
        variables["consumed_protein"] = [0] * NMONTHS

        return variables

    def second_optimization_to_humans_maxed(
        self,
        model,
        variables,
        NMONTHS,
        ASSERT_SUCCESSFUL_OPTIMIZATION,
        single_valued_constants,
    ):
        """
        in this case we are trying to maximize the amount to humans, as long as feed and biofuel
        minimum demands are satisfied
        this allows the "best" food (stored food and outdoor growing) to go to humans if possible
        """
        model_max_to_humans = model

        # Create the model to optimize
        model_max_to_humans.sense = LpMaximize
        variables["objective_function_best_to_humans"] = LpVariable(
            name="TO_HUMANS_OBJECTIVE", lowBound=0
        )

        maximizer_string = "Crops_And_Stored_Food_Optimization_Averaged"
        total_feed_biofuel_variable = 0
        for month in range(0, NMONTHS):

            total_feed_biofuel_variable += (
                variables["methane_scp_feed"][month]
                + variables["methane_scp_biofuel"][month]
                + variables["cellulosic_sugar_feed"][month]
                + variables["cellulosic_sugar_biofuel"][month]
                + variables["seaweed_feed"][month]
                + variables["seaweed_biofuel"][month]
            ) / NMONTHS

        model_max_to_humans += (
            variables["objective_function_best_to_humans"]
            <= total_feed_biofuel_variable,
            maximizer_string,
        )

        model_max_to_humans.setObjective(variables["objective_function_best_to_humans"])

        status = model_max_to_humans.solve(
            pulp.PULP_CBC_CMD(gapRel=0.0001, msg=True, fracGap=0.001)
        )

        print("model_max_to_humans")
        print(model_max_to_humans)

        assert status == 1, "ERROR: OPTIMIZATION FAILED!"

        # here we're constraining the previous optimization to the previously determined optimal value
        total_feed_biofuel_variable = 0
        maximizer_string = "Crops_And_Stored_Food_Optimization_Averaged_Objective"
        for month in range(0, NMONTHS):
            total_feed_biofuel_variable += (
                variables["methane_scp_feed"][month]
                + variables["methane_scp_biofuel"][month]
                + variables["cellulosic_sugar_feed"][month]
                + variables["cellulosic_sugar_biofuel"][month]
                + variables["seaweed_feed"][month]
                + variables["seaweed_biofuel"][month]
            ) / NMONTHS >= (
                variables["methane_scp_feed"][month].varValue
                + variables["methane_scp_biofuel"][month].varValue
                + variables["cellulosic_sugar_feed"][month].varValue
                + variables["cellulosic_sugar_biofuel"][month].varValue
                + variables["seaweed_feed"][month].varValue
                + variables["seaweed_biofuel"][month].varValue
            ) / NMONTHS * 0.99999

        model_max_to_humans += (
            variables["objective_function_best_to_humans"]
            <= total_feed_biofuel_variable,
            maximizer_string,
        )

        return model_max_to_humans, variables

    def third_optimization_smoothing(
        self,
        model,
        variables,
        NMONTHS,
        ASSERT_SUCCESSFUL_OPTIMIZATION,
        single_valued_constants,
    ):
        """
        in this case we are trying to get the differences between all the variables
        to be the
        smallest, without causing the optimization to fail.
        """

        # Create the model to optimize
        model_smoothing = model
        model_smoothing.sense = LpMinimize
        variables["objective_function_smoothing"] = LpVariable(
            name="SMOOTHING_OBJECTIVE", lowBound=0
        )

        for month in range(0, NMONTHS):
            if single_valued_constants["ADD_CULLED_MEAT"]:
                maximizer_string = (
                    "Smoothing_Culled_Pos_Month" + str(month) + "_Objective_Constraint"
                )

                model_smoothing += (
                    variables["objective_function_smoothing"]
                    >= variables["culled_meat_eaten"][month] * 0.9999,
                    # - variables["culled_meat_eaten"][month - 1],
                    maximizer_string,
                )

                maximizer_string = (
                    "Smoothing_Culled_Neg_Month" + str(month) + "_Objective_Constraint"
                )
                model_smoothing += (
                    variables["objective_function_smoothing"]
                    >= -variables["culled_meat_eaten"][month] * 0.9999,
                    maximizer_string,
                )

        for month in range(3, NMONTHS):
            if single_valued_constants["ADD_STORED_FOOD"]:
                maximizer_string = (
                    "Smoothing_Stored_Pos_Month" + str(month) + "_Objective_Constraint"
                )

                model_smoothing += (
                    variables["objective_function_smoothing"]
                    >= variables["stored_food_to_humans"][month] * 0.99999,
                    maximizer_string,
                )
        print("model_smoothing")
        print(model_smoothing)

        model_smoothing.setObjective(variables["objective_function_smoothing"])

        status = model_smoothing.solve(
            pulp.PULP_CBC_CMD(gapRel=0.0001, msg=False, fracGap=0.001)
        )

        assert status == 1, "ERROR: OPTIMIZATION FAILED!"
        return model_smoothing, variables

    def add_old_objective_as_constraint(self, model, variables, NMONTHS):
        """
        we set min_value to the previous optimization value and make
        sure consumed_kcals meets this value each month
        """

        min_value = (
            model.objective.value() * 0.999999
        )  # reach almost the same as objective, but allow for small rounding error if needed

        # add the constraint for consumed_kcals each month

        for month in range(0, NMONTHS):
            maximizer_string = (
                "Old_Objective_Month_" + str(month) + "_Objective_Constraint"
            )

            model += (
                min_value <= variables["consumed_kcals"][month],
                maximizer_string,
            )

            if self.single_valued_constants["inputs"]["INCLUDE_FAT"]:
                maximizer_string = (
                    "Old_Fat_Objective_Month_" + str(month) + "_Objective_Constraint"
                )

                model += (
                    variables["objective_function"] <= variables["consumed_fat"][month],
                    maximizer_string,
                )

            if self.single_valued_constants["inputs"]["INCLUDE_PROTEIN"]:
                maximizer_string = (
                    "Old_Protein_Objective_Month_"
                    + str(month)
                    + "_Objective_Constraint"
                )

                model += (
                    variables["objective_function"]
                    <= variables["consumed_protein"][month],
                    maximizer_string,
                )
        return model, variables

    def create_lp_variables(self, prefix, month):
        """
        create a pulp variable, always positive
        """
        variable_name = f"{prefix}_Month_{month}_Variable"

        return LpVariable(variable_name, lowBound=0)

    def add_constraints(self, model, month, condition, prefix):
        constraint = (condition, f"{prefix}_{month}_Constraint")
        model += constraint
        return model

    def add_variable_from_prefixes(self, variables, prefixes):
        for month in range(0, self.single_valued_constants["NMONTHS"]):
            for prefix in prefixes:
                variable = self.create_lp_variables(prefix, month)
                variables[prefix.lower()][month] = variable
        return variables

    def add_seaweed_to_model(self, month, variables):
        conditions = {}

        initial_seaweed = self.single_valued_constants["INITIAL_SEAWEED"]
        max_density = self.single_valued_constants["MAXIMUM_DENSITY"]
        built_area = self.time_consts["built_area"][month]
        initial_built_area = self.single_valued_constants["INITIAL_BUILT_SEAWEED_AREA"]

        conditions["Seaweed_Wet_On_Farm_Lowerbound"] = (
            initial_seaweed <= variables["seaweed_wet_on_farm"][month]
        )
        conditions["Seaweed_Wet_On_Farm_Upperbound"] = (
            variables["seaweed_wet_on_farm"][month] <= max_density * built_area
        )
        conditions["Used_Area_Lowerbound"] = (
            variables["used_area"][month] >= initial_built_area
        )
        conditions["Used_Area_Upperbound"] = variables["used_area"][month] <= built_area

        # Additional conditions for the first month and later months
        if month == 0:
            conditions["Seaweed_Wet_On_Farm"] = (
                variables["seaweed_wet_on_farm"][0] == initial_seaweed
            )
            conditions["Used_Area"] = variables["used_area"][0] == initial_built_area
            conditions["Seaweed_To_Humans"] = variables["seaweed_to_humans"][0] == 0
            conditions["Seaweed_Feed"] = variables["seaweed_feed"][0] == 0
            conditions["Seaweed_Biofuel"] = variables["seaweed_biofuel"][0] == 0

        else:
            # Calculate intermediate values to simplify the condition
            prev_seaweed = variables["seaweed_wet_on_farm"][month - 1]
            growth_rate = self.time_consts["growth_rates_monthly"][month] / 100.0
            humans_consumed = variables["seaweed_to_humans"][month]
            feed_consumed = variables["seaweed_feed"][month]
            biofuel_consumed = variables["seaweed_biofuel"][month]
            prev_used_area = variables["used_area"][month - 1]
            curr_used_area = variables["used_area"][month]
            harvest_loss = self.single_valued_constants["HARVEST_LOSS"] / 100.0
            min_density = self.single_valued_constants["MINIMUM_DENSITY"]

            conditions["Seaweed_Wet_On_Farm"] = (
                variables["seaweed_wet_on_farm"][month]
                == prev_seaweed * (1 + growth_rate)
                - humans_consumed
                - feed_consumed
                - biofuel_consumed
                - (curr_used_area - prev_used_area) * min_density * harvest_loss
            )

        return conditions

    def add_stored_food_to_model_only_first_year(self, month, variables):
        conditions = {}

        max_kcals = self.single_valued_constants["stored_food"].initial_available.kcals

        if month == 0:  # first month
            conditions["Stored_Food_Start"] = (
                variables["stored_food_start"][0] == max_kcals
            )
            conditions["Stored_Food_Eaten"] = (
                variables["stored_food_end"][0]
                == variables["stored_food_start"][0]
                - variables["stored_food_to_humans"][0]
                - variables["stored_food_feed"][0]
                - variables["stored_food_biofuel"][0]
            )

        elif month > 12:  # after first year:
            for prefix in self.stored_food_prefixes[2:]:
                conditions[prefix] = variables[prefix][month] == 0

        else:
            conditions["Stored_Food_Eaten"] = (
                variables["stored_food_end"][month]
                == variables["stored_food_start"][month]
                - variables["stored_food_to_humans"][month]
                - variables["stored_food_feed"][month]
                - variables["stored_food_biofuel"][month]
            )

        return conditions

    def add_stored_food_to_model(self, month, variables):
        if not self.single_valued_constants["STORE_FOOD_BETWEEN_YEARS"]:
            return self.add_stored_food_to_model_only_first_year(month, variables)

        conditions = {}

        if month == 0:  # first Month
            conditions["Stored_Food_Start"] = (
                variables["stored_food_start"][0]
                == self.single_valued_constants["stored_food"].initial_available.kcals
            )

        elif month == self.single_valued_constants["NMONTHS"] - 1:  # last month
            conditions["Stored_Food_End"] = variables["stored_food_end"][month] == 0
            conditions["Stored_Food_Start"] = (
                variables["stored_food_start"][month]
                == variables["stored_food_end"][month - 1]
            )

        else:
            conditions["Stored_Food_Start"] = (
                variables["stored_food_start"][month]
                == variables["stored_food_end"][month - 1]
            )

        conditions["Stored_Food_Eaten_Feed_Biofuels"] = (
            variables["stored_food_end"][month]
            == variables["stored_food_start"][month]
            - variables["stored_food_to_humans"][month]
            - variables["stored_food_feed"][month]
            - variables["stored_food_biofuel"][month]
        )

        return conditions

    def add_culled_meat_to_model(self, month, variables):
        conditions = {}

        if month == 0:  # first Month
            conditions["Culled_Meat_Start"] = (
                variables["culled_meat_start"][0]
                == self.single_valued_constants["culled_meat"]
            )
        else:
            conditions["Culled_Meat_Start"] = (
                variables["culled_meat_start"][month]
                == variables["culled_meat_end"][month - 1]
            )

        conditions["Culled_Meat_Eaten"] = (
            variables["culled_meat_end"][month]
            == variables["culled_meat_start"][month]
            - variables["culled_meat_eaten"][month]
        )

        return conditions

    def add_outdoor_crops_to_model_no_storage(self, month, variables):
        conditions = {
            "Crops_Food_Storage_Zero": variables["crops_food_storage"][month] == 0
        }
        return conditions

    def handle_first_month(self, variables, month):
        conditions = {
            "Crops_Food_Storage": (
                variables["crops_food_storage"][month]
                == self.time_consts["outdoor_crops"].production.kcals[month]
                - variables["crops_food_eaten"][month]
            )
        }
        return conditions

    def handle_last_month(
        self, variables, month, use_relocated_crops, initial_harvest_duration
    ):
        if use_relocated_crops:
            assert (
                month > initial_harvest_duration
            ), """ERROR: In relocated case, you need to have a scenario at least 1 harvest duration long,
                right now it is this many months for harvest duration:""" + str(
                initial_harvest_duration
            )

        conditions = {
            "Crops_Food_None_Left": variables["crops_food_storage"][month] == 0,
            "Crops_Food_Storage": (
                variables["crops_food_storage"][month]
                == self.time_consts["outdoor_crops"].production.kcals[month]
                + variables["crops_food_storage"][month - 1]
                - variables["crops_food_eaten"][month]
            ),
        }
        return conditions

    def handle_other_months(self, variables, month, use_relocated_crops):
        conditions = {
            "Crops_Food_Storage": (
                variables["crops_food_storage"][month]
                == self.time_consts["outdoor_crops"].production.kcals[month]
                + variables["crops_food_storage"][month - 1]
                - variables["crops_food_eaten"][month]
            )
        }
        return conditions

    def add_crops_food_eaten_with_nutrient_name(
        self, variables, month, nutrient, lowercase_nutrient
    ):
        conditions = {
            "Crops_Food_Eaten"
            + nutrient: (
                variables["crops_food_eaten" + lowercase_nutrient][month]
                == variables["crops_food_to_humans" + lowercase_nutrient][month]
                + variables["crops_food_biofuel" + lowercase_nutrient][month]
                + variables["crops_food_feed" + lowercase_nutrient][month]
            )
        }
        return conditions

    def create_linear_constraints_for_fat_and_protein_crops_food(
        self, month, variables, fat_multiplier, protein_multiplier
    ):
        conditions = {}

        # for kcals case
        conditions.update(
            self.add_crops_food_eaten_with_nutrient_name(variables, month, "", "")
        )
        nutrient_multiplier_dictionary = {
            fat_multiplier: "_Fat",
            protein_multiplier: "_Protein",
        }
        for multiplier, nutrient in nutrient_multiplier_dictionary.items():
            lowercase_nutrient = nutrient.lower()

            conditions.update(
                self.add_crops_food_eaten_with_nutrient_name(
                    variables, month, nutrient, lowercase_nutrient
                )
            )

            for usage_type in ["_Feed", "_Biofuel"]:
                lowercase_usage_type = usage_type.lower()
                conditions["Crops_Food_Eaten_Conversion" + usage_type + nutrient] = (
                    variables["crops_food" + lowercase_usage_type + lowercase_nutrient][
                        month
                    ]
                    == variables["crops_food" + lowercase_usage_type][month]
                    * multiplier
                )

        return conditions

    def get_outdoor_crops_month_constants(self, use_relocated_crops, month):
        initial_harvest_duration = (
            self.single_valued_constants["INITIAL_HARVEST_DURATION_IN_MONTHS"]
            + self.single_valued_constants["DELAY"]["ROTATION_CHANGE_IN_MONTHS"]
        )
        if use_relocated_crops and month >= initial_harvest_duration:
            fat_multiplier = self.single_valued_constants["OG_ROTATION_FRACTION_FAT"]
            protein_multiplier = self.single_valued_constants[
                "OG_ROTATION_FRACTION_PROTEIN"
            ]
        else:
            fat_multiplier = self.single_valued_constants["OG_FRACTION_FAT"]
            protein_multiplier = self.single_valued_constants["OG_FRACTION_PROTEIN"]

        return (initial_harvest_duration, fat_multiplier, protein_multiplier)

    def add_outdoor_crops_to_model(self, month, variables):
        conditions = {}

        use_relocated_crops = self.single_valued_constants["inputs"][
            "OG_USE_BETTER_ROTATION"
        ]
        (
            initial_harvest_duration,
            fat_multiplier,
            protein_multiplier,
        ) = self.get_outdoor_crops_month_constants(use_relocated_crops, month)

        conditions.update(
            self.create_linear_constraints_for_fat_and_protein_crops_food(
                month, variables, fat_multiplier, protein_multiplier
            )
        )

        if month == 0:
            conditions.update(self.handle_first_month(variables, month))
        elif month == self.single_valued_constants["NMONTHS"] - 1:
            conditions.update(
                self.handle_last_month(
                    variables, month, use_relocated_crops, initial_harvest_duration
                )
            )
        else:
            conditions.update(
                self.handle_other_months(variables, month, initial_harvest_duration)
            )

        return conditions

    def add_methane_scp_to_model(self, month, variables):
        conditions = {
            "Methane_SCP": (
                variables["methane_scp_to_humans"][month]
                + variables["methane_scp_feed"][month]
                + variables["methane_scp_biofuel"][month]
                <= self.time_consts["methane_scp"].kcals[month]
            )
        }

        return conditions

    def add_cellulosic_sugar_to_model(self, month, variables):
        conditions = {
            "Cellulosic_Sugar": (
                variables["cellulosic_sugar_to_humans"][month]
                + variables["cellulosic_sugar_feed"][month]
                + variables["cellulosic_sugar_biofuel"][month]
                <= self.time_consts["cellulosic_sugar"].kcals[month]
            )
        }

        return conditions

    def add_percentage_intake_constraints(self, model, variables, month):
        """
        Percentage intake of the nonhuman and human diets, and the ratio of these resources used as biofuel
        """
        nutrient_ratios = {
            "Seaweed": self.single_valued_constants["SEAWEED_KCALS"],
            "Methane_SCP": 1,
            "Cellulosic_Sugar": 1,
        }

        for nutrient, nutrient_kcal_ratio in nutrient_ratios.items():
            if self.single_valued_constants["ADD_" + nutrient.upper()]:
                constraints_data = [
                    (
                        "HUMANS",
                        "MAX_" + nutrient.upper() + "_HUMANS_CAN_CONSUME_MONTHLY",
                        "to_humans",
                    ),
                    (
                        "FEED",
                        "MAX_" + nutrient.upper() + "_AS_PERCENT_KCALS_FEED",
                        "feed",
                    ),
                    (
                        "BIOFUEL",
                        "MAX_" + nutrient.upper() + "_AS_PERCENT_KCALS_BIOFUEL",
                        "biofuel",
                    ),
                ]
                for constraint_type, limit_key, usage in constraints_data:
                    condition = variables[nutrient.lower() + "_" + usage][
                        month
                    ] * nutrient_kcal_ratio <= (
                        self.single_valued_constants[limit_key]
                        if constraint_type == "HUMANS"
                        else self.single_valued_constants[limit_key]
                        / 100
                        * self.time_consts[usage.lower()].kcals[month]
                    )

                    model = self.add_constraints(
                        model,
                        month,
                        condition,
                        nutrient + "_Limit_" + constraint_type,
                    )

        return model

    def add_feed_biofuel_to_model(self, model, variables, month):
        feed_sum = (
            variables["stored_food_feed"][month]
            + variables["crops_food_feed"][month]
            + variables["seaweed_feed"][month]
            * self.single_valued_constants["SEAWEED_KCALS"]
            + variables["cellulosic_sugar_feed"][month]
            + variables["methane_scp_feed"][month]
        )
        biofuel_sum = (
            variables["stored_food_biofuel"][month]
            + variables["crops_food_biofuel"][month]
            + variables["seaweed_biofuel"][month]
            * self.single_valued_constants["SEAWEED_KCALS"]
            + variables["cellulosic_sugar_biofuel"][month]
            + variables["methane_scp_biofuel"][month]
        )

        conditions = {
            "Feed_Used": (
                feed_sum / self.single_valued_constants["BILLION_KCALS_NEEDED"] * 100
                == self.time_consts["feed"].kcals[month]
                / self.single_valued_constants["BILLION_KCALS_NEEDED"]
                * 100
            ),
            "Biofuel_Used": (
                biofuel_sum / self.single_valued_constants["BILLION_KCALS_NEEDED"] * 100
                == self.time_consts["biofuel"].kcals[month]
                / self.single_valued_constants["BILLION_KCALS_NEEDED"]
                * 100
            ),
        }
        model = self.add_conditions_to_model(model, month, conditions)
        return model

    # OBJECTIVE FUNCTIONS  #

    def add_objectives_to_model(self, model, variables, month, maximize_constraints):
        model = self.add_percentage_intake_constraints(model, variables, month)
        model = self.add_feed_biofuel_to_model(model, variables, month)

        variables["consumed_kcals"][month] = LpVariable(
            name="Humans_Fed_Kcals_" + str(month) + "_Variable", lowBound=0
        )
        variables["consumed_fat"][month] = LpVariable(
            name="Humans_Fed_Fat_" + str(month) + "_Variable", lowBound=0
        )
        variables["consumed_protein"][month] = LpVariable(
            name="Humans_Fed_Protein_" + str(month) + "_Variable", lowBound=0
        )

        model += (
            variables["consumed_kcals"][month]
            == (
                variables["stored_food_to_humans"][month]
                + variables["crops_food_to_humans"][month]
                # + variables["crops_food_eaten"][month]
                + variables["seaweed_to_humans"][month]
                * self.single_valued_constants["SEAWEED_KCALS"]
                # + variables["seaweed_feed"][month]
                # * self.single_valued_constants["SEAWEED_KCALS"]
                # + variables["seaweed_biofuel"][month]
                # * self.single_valued_constants["SEAWEED_KCALS"]
                + self.time_consts["grazing_milk_kcals"][month]
                + self.time_consts["cattle_grazing_maintained_kcals"][month]
                + variables["culled_meat_eaten"][month]
                + variables["cellulosic_sugar_to_humans"][month]
                # + variables["cellulosic_sugar_feed"][month]
                # + variables["cellulosic_sugar_biofuel"][month]
                + variables["methane_scp_to_humans"][month]
                # + variables["methane_scp_feed"][month]
                # + variables["methane_scp_biofuel"][month]
                + self.time_consts["greenhouse_area"][month]
                * self.time_consts["greenhouse_kcals_per_ha"][month]
                + self.time_consts["fish"].to_humans.kcals[month]
                + self.time_consts["grain_fed_created_kcals"][month]
            )
            / self.single_valued_constants["BILLION_KCALS_NEEDED"]
            * 100,
            "Kcals_Fed_Month_" + str(month) + "_Constraint",
        )
        # TODO: PUT BACK IN!
        # if self.single_valued_constants["inputs"]["INCLUDE_FAT"]:
        #     # fat monthly is in units thousand tons
        #     model += (
        #         variables["consumed_fat"][month]
        #         == (
        #             variables["stored_food_eaten"][month]
        #             * self.single_valued_constants["SF_FRACTION_FAT"]
        #             + variables["crops_food_eaten_fat"][month]
        #             + variables["seaweed_to_humans"][month]
        #             * self.single_valued_constants["SEAWEED_FAT"]
        #             + variables["seaweed_feed"][month]
        #             * self.single_valued_constants["SEAWEED_FAT"]
        #             + self.time_consts["grazing_milk_fat"][month]
        #             + self.time_consts["cattle_grazing_maintained_fat"][month]
        #             + variables["culled_meat_eaten"][month]
        #             * self.single_valued_constants["CULLED_MEAT_FRACTION_FAT"]
        #             + variables["methane_scp_to_humans"][month]
        #             * self.single_valued_constants["SCP_KCALS_TO_FAT_CONVERSION"]
        #             + variables["methane_scp_feed"][month]
        #             * self.single_valued_constants["SCP_KCALS_TO_FAT_CONVERSION"]
        #             + self.time_consts["greenhouse_area"][month]
        #             * self.time_consts["greenhouse_fat_per_ha"][month]
        #             + self.time_consts["fish"].to_humans.fat[month]
        #             + self.time_consts["grain_fed_created_fat"][month]
        #             - self.time_consts["nonhuman_consumption"].fat[month]
        #         )
        #         / self.single_valued_constants["THOU_TONS_FAT_NEEDED"]
        #         * 100,
        #         "Fat_Fed_Month_" + str(month) + "_Constraint",
        #     )

        # if self.single_valued_constants["inputs"]["INCLUDE_PROTEIN"]:
        #     model += (
        #         variables["consumed_protein"][month]
        #         == (
        #             variables["stored_food_eaten"][month]
        #             * self.single_valued_constants["SF_FRACTION_PROTEIN"]
        #             + variables["crops_food_eaten_protein"][month]
        #             + variables["seaweed_to_humans"][month]
        #             * self.single_valued_constants["SEAWEED_PROTEIN"]
        #             + variables["seaweed_feed"][month]
        #             * self.single_valued_constants["SEAWEED_PROTEIN"]
        #             + self.time_consts["grazing_milk_protein"][month]
        #             + self.time_consts["cattle_grazing_maintained_protein"][month]
        #             + variables["methane_scp_to_humans"][month]
        #             * self.single_valued_constants["SCP_KCALS_TO_PROTEIN_CONVERSION"]
        #             + variables["methane_scp_feed"][month]
        #             * self.single_valued_constants["SCP_KCALS_TO_PROTEIN_CONVERSION"]
        #             + variables["culled_meat_eaten"][month]
        #             * self.single_valued_constants["CULLED_MEAT_FRACTION_PROTEIN"]
        #             + self.time_consts["greenhouse_area"][month]
        #             * self.time_consts["greenhouse_protein_per_ha"][month]
        #             + self.time_consts["fish"].to_humans.kcals[month]
        #             + self.time_consts["grain_fed_created_protein"][month]
        #             - self.time_consts["nonhuman_consumption"].protein[month]
        #         )
        #         / self.single_valued_constants["THOU_TONS_PROTEIN_NEEDED"]
        #         * 100,
        #         "Protein_Fed_Month_" + str(month) + "_Constraint",
        #     )

        # no feeding human edible maintained meat or milk to animals or biofuels

        # maximizes the minimum objective_function value
        # We maximize the minimum humans fed from any month
        # We therefore maximize the minimum ratio of fat per human requirement,
        # protein per human requirement, or kcals per human requirement
        # for all months

        maximizer_string = "Kcals_Fed_Month_" + str(month) + "_Objective_Constraint"
        maximize_constraints.append(maximizer_string)
        model += (
            variables["objective_function"] <= variables["consumed_kcals"][month],
            maximizer_string,
        )

        if self.single_valued_constants["inputs"]["INCLUDE_FAT"]:
            maximizer_string = "Fat_Fed_Month_" + str(month) + "_Objective_Constraint"
            maximize_constraints.append(maximizer_string)
            model += (
                variables["objective_function"] <= variables["consumed_fat"][month],
                maximizer_string,
            )

        if self.single_valued_constants["inputs"]["INCLUDE_PROTEIN"]:
            maximizer_string = (
                "Protein_Fed_Month_" + str(month) + "_Objective_Constraint"
            )
            maximize_constraints.append(maximizer_string)
            model += (
                variables["objective_function"] <= variables["consumed_protein"][month],
                maximizer_string,
            )

        return [model, variables, maximize_constraints]
