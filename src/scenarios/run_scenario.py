"""

This function runs a single optimization by computing the parameters,
running the parameters onto the optimizer, extracting the results, and interpreting the
results into more useful values for plotting and scenario evaluation

Created on Tue Jul 19

@author: morgan
"""

import sys

from src.optimizer.optimizer import Optimizer
from src.optimizer.interpret_results import Interpreter
from src.optimizer.extract_results import Extractor
from src.scenarios.scenarios import Scenarios
from src.optimizer.validate_results import Validator
from src.optimizer.parameters import Parameters


class ScenarioRunner:
    def __init__(self):
        pass

    def run_and_analyze_scenario(self, constants_for_params, scenarios_loader):
        """
        computes params, Runs the optimizer, extracts data from optimizer, interprets
        the results, validates the results, and optionally prints an output with people
        fed.

        arguments: constants from the scenario, scenario loader (to print the aspects
        of the scenario and check no scenario parameter has been set twice or left
        unset)

        returns: the interpreted results
        """
        interpreter = Interpreter()
        # take the variables defining the scenario and compute the resulting needed
        # values as inputs to the optimizer

        constants_loader = Parameters()

        (
            single_valued_constants,
            time_consts,
            feed_and_biofuels,
            meat_dictionary,
        ) = constants_loader.compute_parameters_first_round(
            constants_for_params, scenarios_loader
        )
        interpreter.set_feed(feed_and_biofuels)
        interpreter.set_meat_dictionary(meat_dictionary)

        # actually make PuLP optimize effective people fed based on all the constants
        # we've determined
        (
            model,
            variables,
            percent_fed_from_model,
            time_consts,
        ) = self.run_optimizer(single_valued_constants, time_consts)

        interpreted_results = self.interpret_optimizer_results(
            single_valued_constants,
            model,
            variables,
            time_consts,
            interpreter,
            percent_fed_from_model,
        )

        # (
        #     # single_valued_constants,
        #     # time_consts,
        #     # feed_and_biofuels,
        # ) =
        min_human_food_consumption = constants_loader.compute_parameters_second_round(
            constants_for_params,
            time_consts,
            interpreted_results,
            percent_fed_from_model,
        )

        optimizer = Optimizer(single_valued_constants, time_consts)

        (
            model,
            variables,
            # percent_fed_from_model_round2,
            time_consts,
        ) = optimizer.optimize_feed_to_animals(
            single_valued_constants, time_consts, min_human_food_consumption
        )

        # print("interpreted_results")
        # print(interpreted_results)
        # breakpoint()
        # quit()

        PRINT_NEEDS_RATIO = False
        if PRINT_NEEDS_RATIO:
            interpreter.print_kcals_per_capita_per_day(interpreted_results)

        return interpreted_results

    def interpret_optimizer_results(
        self,
        single_valued_constants,
        model,
        variables,
        time_consts,
        interpreter,
        percent_fed_from_model,
    ):
        validator = Validator()

        extractor = Extractor(single_valued_constants)
        #  get values from all the optimizer in list and integer formats
        extracted_results = extractor.extract_results(model, variables, time_consts)

        # TODO: eventually all the values not directly solved by the optimizer should
        # be removed from extracted_results

        #  interpret the results, nicer for plotting, reporting, and printing results
        interpreted_results = interpreter.interpret_results(extracted_results)

        # ensure no errors were made in the extraction and interpretation, or if the
        # optimizer did not correctly satisfy constraints within a reasonable margin
        # of error
        validator.validate_results(
            extracted_results,
            interpreted_results,
            time_consts,
            percent_fed_from_model,
        )

        return interpreted_results

    def run_optimizer(self, single_valued_constants, time_consts):
        """
        Runs the optimizer and returns the model, variables, and constants
        """
        optimizer = Optimizer(single_valued_constants, time_consts)
        validator = Validator()

        (
            model,
            variables,
            maximize_constraints,
            percent_fed_from_model,
            time_consts,
        ) = optimizer.optimize_to_humans(single_valued_constants, time_consts)

        CHECK_CONSTRAINTS = False
        if CHECK_CONSTRAINTS:
            print("")
            print("VALIDATION")
            print("")
            print("")
            # check all the mathematically defined constraints in the optimizer are
            # satisfied within reasonable rounding errors
            validator.check_constraints_satisfied(
                model,
                maximize_constraints,
                model.variables(),
            )

        return (model, variables, percent_fed_from_model, time_consts)

    def set_depending_on_option(self, country_data, scenario_option):
        scenario_loader = Scenarios()
        # SCALE

        if scenario_option["scale"] == "global":
            constants_for_params = scenario_loader.init_global_food_system_properties()
            constants_for_params["COUNTRY_CODE"] = "global"
        elif scenario_option["scale"] == "country":
            constants_for_params = scenario_loader.init_country_food_system_properties(
                country_data
            )

            constants_for_params["COUNTRY_CODE"] = country_data["iso3"]
        else:
            scenario_is_correct = False
            constants_for_params["COUNTRY_CODE"] = "global"

            assert (
                scenario_is_correct
            ), "You must specify 'scale' key as global,or country"

        constants_for_params["NMONTHS"] = scenario_option["NMONTHS"]

        # EXCESS
        constants_for_params = scenario_loader.set_excess_to_zero(constants_for_params)

        # STORED FOOD

        if scenario_option["stored_food"] == "zero":
            constants_for_params = scenario_loader.set_no_stored_food(
                constants_for_params
            )
        elif scenario_option["stored_food"] == "baseline":
            constants_for_params = scenario_loader.set_baseline_stored_food(
                constants_for_params
            )
        else:
            scenario_is_correct = False

            assert (
                scenario_is_correct
            ), "You must specify 'stored_food_at_start' key as zero, or baseline"

        # END_SIMULATION_STOCKS_RATIO

        if scenario_option["end_simulation_stocks_ratio"] == "zero":
            constants_for_params = scenario_loader.set_stored_food_buffer_zero(
                constants_for_params
            )
        elif (
            scenario_option["end_simulation_stocks_ratio"]
            == "no_stored_food_between_years"
        ):
            constants_for_params = scenario_loader.set_no_stored_food_between_years(
                constants_for_params
            )
        elif scenario_option["end_simulation_stocks_ratio"] == "baseline":
            constants_for_params = scenario_loader.set_stored_food_buffer_as_baseline(
                constants_for_params
            )
        else:
            scenario_is_correct = False

            assert (
                scenario_is_correct
            ), "You must specify 'end_simulation_stocks_ratio' key as zero, no_stored_between_years, or baseline"

        # SHUTOFF
        if scenario_option["shutoff"] == "immediate":
            constants_for_params = scenario_loader.set_immediate_shutoff(
                constants_for_params
            )
        elif scenario_option["shutoff"] == "one_month_delayed_shutoff":
            constants_for_params = scenario_loader.set_one_month_delayed_shutoff(
                constants_for_params
            )

        elif scenario_option["shutoff"] == "short_delayed_shutoff":
            constants_for_params = scenario_loader.set_short_delayed_shutoff(
                constants_for_params
            )
        elif scenario_option["shutoff"] == "long_delayed_shutoff":
            constants_for_params = scenario_loader.set_long_delayed_shutoff(
                constants_for_params
            )
        elif scenario_option["shutoff"] == "continued":
            constants_for_params = scenario_loader.set_continued_feed_biofuels(
                constants_for_params
            )
        else:
            scenario_is_correct = False

            assert scenario_is_correct, """You must specify 'shutoff' key as immediate,short_delayed_shutoff,one_month_delayed_shutoff,
            long_delayed_shutoff, or continued"""

        # WASTE

        if scenario_option["waste"] == "zero":
            constants_for_params = scenario_loader.set_waste_to_zero(
                constants_for_params
            )
        elif scenario_option["waste"] == "tripled_prices_in_country":
            constants_for_params = scenario_loader.set_country_waste_to_tripled_prices(
                constants_for_params, country_data
            )
        elif scenario_option["waste"] == "doubled_prices_in_country":
            constants_for_params = scenario_loader.set_country_waste_to_doubled_prices(
                constants_for_params, country_data
            )
        elif scenario_option["waste"] == "baseline_in_country":
            constants_for_params = scenario_loader.set_country_waste_to_baseline_prices(
                constants_for_params, country_data
            )
        elif scenario_option["waste"] == "tripled_prices_globally":
            constants_for_params = scenario_loader.set_global_waste_to_tripled_prices(
                constants_for_params
            )
        elif scenario_option["waste"] == "doubled_prices_globally":
            constants_for_params = scenario_loader.set_global_waste_to_doubled_prices(
                constants_for_params
            )
        elif scenario_option["waste"] == "baseline_globally":
            constants_for_params = scenario_loader.set_global_waste_to_baseline_prices(
                constants_for_params
            )
        else:
            scenario_is_correct = False

            assert scenario_is_correct, """You must specify 'waste' key as zero,tripled_prices_in_country,
            doubled_prices_in_country,baseline_in_country,tripled_prices_globally,
            doubled_prices_globally,or baseline_globally"""

        # NUTRITION

        if scenario_option["nutrition"] == "baseline":
            constants_for_params = scenario_loader.set_baseline_nutrition_profile(
                constants_for_params
            )
        elif scenario_option["nutrition"] == "catastrophe":
            constants_for_params = scenario_loader.set_catastrophe_nutrition_profile(
                constants_for_params
            )
        else:
            scenario_is_correct = False

            assert (
                scenario_is_correct
            ), "You must specify 'nutrition' key as baseline, or catastrophe"

        # INTAKE CONSTRAINTS

        if scenario_option["intake_constraints"] == "enabled":
            constants_for_params = scenario_loader.set_intake_constraints_to_enabled(
                constants_for_params
            )
        elif scenario_option["intake_constraints"] == "disabled_for_humans":
            constants_for_params = (
                scenario_loader.set_intake_constraints_to_disabled_for_humans(
                    constants_for_params
                )
            )
        else:
            scenario_is_correct = False

            assert (
                scenario_is_correct
            ), "You must specify 'intake_constraints' key as enabled, or disabled_for_humans"

        # SEASONALITY

        # SEASONALITY

        if scenario_option["seasonality"] == "no_seasonality":
            constants_for_params = scenario_loader.set_no_seasonality(
                constants_for_params
            )
        elif scenario_option["seasonality"] == "country":
            constants_for_params = scenario_loader.set_country_seasonality(
                constants_for_params, country_data
            )
        elif scenario_option["seasonality"] == "baseline_globally":
            constants_for_params = scenario_loader.set_global_seasonality_baseline(
                constants_for_params
            )
        elif scenario_option["seasonality"] == "nuclear_winter_globally":
            constants_for_params = (
                scenario_loader.set_global_seasonality_nuclear_winter(
                    constants_for_params
                )
            )
        else:
            scenario_is_correct = False

            assert scenario_is_correct, """You must specify 'seasonality' key as no_seasonality, country,
             baseline_globally,or nuclear_winter_globally"""

        # GRASSES
        if scenario_option["grasses"] == "baseline":
            constants_for_params = scenario_loader.set_grasses_baseline(
                constants_for_params
            )
        elif scenario_option["grasses"] == "global_nuclear_winter":
            constants_for_params = scenario_loader.set_global_grasses_nuclear_winter(
                constants_for_params
            )
        elif scenario_option["grasses"] == "country_nuclear_winter":
            constants_for_params = scenario_loader.set_country_grasses_nuclear_winter(
                constants_for_params, country_data
            )
        elif scenario_option["grasses"] == "all_crops_die_instantly":
            constants_for_params = scenario_loader.set_country_grasses_to_zero(
                constants_for_params
            )
        else:
            scenario_is_correct = False

            assert scenario_is_correct, """You must specify 'grasses' key as baseline,
            global_nuclear_winter,all_crops_die_instantly, or country_nuclear_winter"""

        # FISH

        if scenario_option["fish"] == "zero":
            constants_for_params = scenario_loader.set_fish_zero(constants_for_params)
        elif scenario_option["fish"] == "nuclear_winter":
            constants_for_params = scenario_loader.set_fish_nuclear_winter_reduction(
                constants_for_params
            )
        elif scenario_option["fish"] == "baseline":
            constants_for_params = scenario_loader.set_fish_baseline(
                constants_for_params
            )
        else:
            scenario_is_correct = False

            assert (
                scenario_is_correct
            ), "You must specify 'fish' key as either zero, nuclear_winter,or baseline"

        # CROPS

        if scenario_option["crop_disruption"] == "zero":
            constants_for_params = scenario_loader.set_disruption_to_crops_to_zero(
                constants_for_params
            )
        elif scenario_option["crop_disruption"] == "global_nuclear_winter":
            constants_for_params = (
                scenario_loader.set_nuclear_winter_global_disruption_to_crops(
                    constants_for_params
                )
            )
        elif scenario_option["crop_disruption"] == "country_nuclear_winter":
            constants_for_params = (
                scenario_loader.set_nuclear_winter_country_disruption_to_crops(
                    constants_for_params, country_data
                )
            )
        elif scenario_option["crop_disruption"] == "all_crops_die_instantly":
            constants_for_params = scenario_loader.set_zero_crops(constants_for_params)
        else:
            scenario_is_correct = False

            assert scenario_is_correct, """You must specify 'crop_disruption' key as either zero,
            global_nuclear_winter, all_crops_die_instantly, or country_nuclear_winter"""

        # PROTEIN

        if scenario_option["protein"] == "required":
            print("ERROR: fat and protein not working in this version of the model")
            print("(compute parameters in the second round would need to be modified)")
            sys.exit()
            constants_for_params = scenario_loader.include_protein(constants_for_params)
        elif scenario_option["protein"] == "not_required":
            constants_for_params = scenario_loader.dont_include_protein(
                constants_for_params
            )
        else:
            scenario_is_correct = False

            assert (
                scenario_is_correct
            ), "You must specify 'protein' key as either required, or not_required"

        # FAT

        if scenario_option["fat"] == "required":
            print("ERROR: fat and protein not working in this version of the model")
            print("(compute parameters in the second round would need to be modified)")
            sys.exit()
            constants_for_params = scenario_loader.include_fat(constants_for_params)
        elif scenario_option["fat"] == "not_required":
            constants_for_params = scenario_loader.dont_include_fat(
                constants_for_params
            )
        else:
            scenario_is_correct = False

            assert (
                scenario_is_correct
            ), "You must specify 'fat' key as either required, or not_required"

        # CULLING

        if scenario_option["cull"] == "do_eat_culled":
            constants_for_params = scenario_loader.cull_animals(constants_for_params)
        elif scenario_option["cull"] == "dont_eat_culled":
            constants_for_params = scenario_loader.dont_cull_animals(
                constants_for_params
            )
        else:
            scenario_is_correct = False

            assert (
                scenario_is_correct
            ), "You must specify 'cull' key as either do_eat_culled, or dont_eat_culled"

        # SCENARIO

        if scenario_option["scenario"] == "all_resilient_foods":
            constants_for_params = scenario_loader.get_all_resilient_foods_scenario(
                constants_for_params
            )
        elif scenario_option["scenario"] == "all_resilient_foods_and_more_area":
            constants_for_params = (
                scenario_loader.get_all_resilient_foods_and_more_area_scenario(
                    constants_for_params
                )
            )
        elif scenario_option["scenario"] == "no_resilient_foods":
            constants_for_params = scenario_loader.get_no_resilient_food_scenario(
                constants_for_params
            )
        elif scenario_option["scenario"] == "seaweed":
            constants_for_params = scenario_loader.get_seaweed_scenario(
                constants_for_params
            )
        elif scenario_option["scenario"] == "methane_scp":
            constants_for_params = scenario_loader.get_methane_scp_scenario(
                constants_for_params
            )
        elif scenario_option["scenario"] == "cellulosic_sugar":
            constants_for_params = scenario_loader.get_cellulosic_sugar_scenario(
                constants_for_params
            )
        elif scenario_option["scenario"] == "relocated_crops":
            constants_for_params = scenario_loader.get_relocated_crops_scenario(
                constants_for_params
            )
        elif scenario_option["scenario"] == "greenhouse":
            constants_for_params = scenario_loader.get_greenhouse_scenario(
                constants_for_params
            )
        elif scenario_option["scenario"] == "industrial_foods":
            constants_for_params = scenario_loader.get_industrial_foods_scenario(
                constants_for_params
            )
        else:
            scenario_is_correct = False

            assert scenario_is_correct, """You must specify 'scenario' key as either baseline_climate,
            all_resilient_foods,all_resilient_foods_and_more_area,no_resilient_foods,seaweed,methane_scp,
            cellulosic_sugar,relocated_crops or greenhouse"""

        if scenario_option["meat_strategy"] == "reduce_breeding_USA":
            constants_for_params = scenario_loader.set_breeding_to_greatly_reduced(
                constants_for_params
            )
        elif scenario_option["meat_strategy"] == "baseline_breeding":
            constants_for_params = scenario_loader.set_to_baseline_breeding(
                constants_for_params
            )
        else:
            scenario_is_correct = False

            assert scenario_is_correct, """You must specify 'meat_strategy' key as either ,
            reduce_breeding_USA or baseline_breeding"""

        return constants_for_params, scenario_loader
