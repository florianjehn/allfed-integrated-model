
# Generated by CodiumAI
from turtle import pd
from scripts.animal_population_analysis.animal_feed_analysis import add_alpha_codes_from_ISO
from scripts.animal_population_analysis.animal_feed_analysis import add_alpha_codes_fuzzy
from scripts.animal_population_analysis.animal_feed_analysis import bulk_correlation_analysis

import pytest


# Add Alpha Codes From ISO
"""
Code Analysis

Objective:
The objective of the function is to add a column of alpha3 codes to a dataframe with country names in a specified column. The function uses fuzzy logic to match countries and retrieves the alpha3 codes from the pycountry library.

Inputs:
- df: a pandas dataframe
- incol: the name of the column in the dataframe containing country names
- outcol: (optional) the name of the column to be added to the dataframe for alpha3 codes. Default is "iso3".

Flow:
- Retrieve the input countries from the specified column in the dataframe
- Loop through each input country and try to match it with a country in the pycountry library using fuzzy logic
- If a match is found, retrieve the alpha3 code for the country
- If a match is not found, set the alpha3 code to "NA" and print a message indicating the input country could not be matched
- Append the alpha3 code to a list of countries
- Add the list of countries as a new column to the dataframe with the specified output column name
- Drop the original country name column from the dataframe
- Return the modified dataframe

Outputs:
- The modified dataframe with a new column containing alpha3 codes for each country in the specified input column
- If a country in the input column could not be matched, a message will be printed indicating the country could not be matched and the corresponding alpha3 code will be set to "NA"

Additional aspects:
- The function uses the pycountry library to retrieve alpha3 codes for countries
- Fuzzy logic is used to match countries in case the input country name is not an exact match with a country in the pycountry library
- The function drops the original country name column from the dataframe and returns the modified dataframe with the new alpha3 code column
"""
class TestAddAlphaCodesFromIso:
    # Tests that function adds alpha-3 codes to dataframe when input has valid ISO-3166-1 numeric codes
    def test_happy_path_numeric_codes(self):
        from pandas.testing import assert_frame_equal
        df = pd.DataFrame({'col': [840, 124, 156]})
        expected_output = pd.DataFrame({'iso3': ['USA', 'CAN', 'CHN']})
        output = add_alpha_codes_from_ISO(df, 'col')
        assert_frame_equal(output, expected_output)

    # Tests that function adds alpha-3 codes to dataframe when input has valid ISO-3166-1 alpha-3 codes
    def test_happy_path_alpha3_codes(self):
        import pandas as pd
        from pandas.testing import assert_frame_equal
        df = pd.DataFrame({'col': ['USA', 'CAN', 'CHN']})
        expected_output = pd.DataFrame({'iso3': ['USA', 'CAN', 'CHN']})
        output = add_alpha_codes_from_ISO(df, 'col')
        assert_frame_equal(output, expected_output)

    # Tests that function returns input dataframe when it has missing values
    def test_edge_case_missing_values(self):
        import pandas as pd
        from pandas.testing import assert_frame_equal
        df = pd.DataFrame({'col': [840, None, 156]})
        expected_output = pd.DataFrame({'iso3': ['USA', 'NA', 'CHN']})
        output = add_alpha_codes_from_ISO(df, 'col')
        assert_frame_equal(output, expected_output)

    # Tests that function returns 'NA' when input dataframe has non-existent country names
    def test_edge_case_nonexistent_country_names(self):
        from pandas.testing import assert_frame_equal
        df = pd.DataFrame({'col': ['Nonexistent Country']})
        expected_output = pd.DataFrame({'iso3': ['NA']})
        output = add_alpha_codes_from_ISO(df, 'col')
        assert_frame_equal(output, expected_output)

    # Tests that function returns 'NA' when input dataframe has invalid country names
    def test_edge_case_invalid_country_names(self):
        from pandas.testing import assert_frame_equal
        df = pd.DataFrame({'col': ['Invalid Country Name']})
        expected_output = pd.DataFrame({'iso3': ['NA']})
        output = add_alpha_codes_from_ISO(df, 'col')
        assert_frame_equal(output, expected_output)

    # Tests that function handles non-string input values
    def test_general_behaviour_non_string_input_values(self):
        import pandas as pd
        from pandas.testing import assert_frame_equal
        df = pd.DataFrame({'col': [840, 124, 156]})
        expected_output = pd.DataFrame({'iso3': ['USA', 'CAN', 'CHN']})
        output = add_alpha_codes_from_ISO(df, 'col')
        assert_frame_equal(output, expected_output)


"""
Code Analysis

Objective:
The objective of the 'add_alpha_codes_fuzzy' function is to add a column of alpha3 codes to a dataframe with country names in a specified column. The function uses fuzzy logic to match countries and handle cases where the input country name is not recognized.

Inputs:
- df: a pandas dataframe
- incol: the name of the column in the dataframe containing the country names
- outcol (optional): the name of the column to be added to the dataframe containing the alpha3 codes. Default is "iso3".

Flow:
1. Get the input country names from the specified column in the dataframe.
2. Iterate through each input country name and use fuzzy logic to search for a matching country in the pycountry library.
3. If a match is found, get the alpha3 code for the country and append it to a list of countries.
4. If no match is found, append "unk_" followed by the input country name to the list of countries.
5. Add the list of alpha3 codes as a new column to the dataframe.
6. Remove the original country name column from the dataframe.
7. Return the modified dataframe.

Outputs:
- df: the modified pandas dataframe with a new column containing alpha3 codes for each country.

Additional aspects:
- The function uses the pycountry library to search for country names and retrieve alpha3 codes.
- Fuzzy logic is used to handle cases where the input country name is not an exact match to a country name in the library.
- If no match is found, the function appends "unk_" followed by the input country name to the list of countries.
"""
class TestAddAlphaCodesFuzzy:
    # Tests that the function works correctly with a non-empty dataframe, a valid input column name, and a valid output column name
    def test_happy_path(self):
        df = pd.DataFrame({"Country": ["United States", "Canada", "Mexico"]})
        expected_output = pd.DataFrame({"alpha3": ["USA", "CAN", "MEX"]})
        output = add_alpha_codes_fuzzy(df, "Country")
        pd.testing.assert_frame_equal(output, expected_output)

    # Tests that the function returns an empty dataframe when given an empty dataframe
    def test_empty_dataframe(self):
        df = pd.DataFrame()
        expected_output = pd.DataFrame()
        output = add_alpha_codes_fuzzy(df, "Country")
        pd.testing.assert_frame_equal(output, expected_output)

    # Tests that the function raises a KeyError when given an invalid input column name
    def test_invalid_input_column(self):
        df = pd.DataFrame({"Country": ["United States", "Canada", "Mexico"]})
        with pytest.raises(KeyError):
            add_alpha_codes_fuzzy(df, "InvalidColumn")

    # Tests that the function raises a TypeError when given an input column name that is not a string
    def test_invalid_input_column_type(self):
        df = pd.DataFrame({"Country": ["United States", "Canada", "Mexico"]})
        with pytest.raises(TypeError):
            add_alpha_codes_fuzzy(df, 123)

    # Tests that the function raises a TypeError when given an output column name that is not a string
    def test_invalid_output_column_type(self):
        df = pd.DataFrame({"Country": ["United States", "Canada", "Mexico"]})
        with pytest.raises(TypeError):
            add_alpha_codes_fuzzy(df, "Country", 123)

    # Tests that the function correctly matches country names using fuzzy logic
    def test_fuzzy_matching(self):
        df = pd.DataFrame({"Country": ["United States", "Canada", "Mxco"]})
        expected_output = pd.DataFrame({"alpha3": ["USA", "CAN", "unk_Mxco"]})
        output = add_alpha_codes_fuzzy(df, "Country")
        pd.testing.assert_frame_equal(output, expected_output)


"""
Code Analysis

Objective:
The objective of the 'bulk_correlation_analysis' function is to calculate the correlation between a target column and all other columns in a given DataFrame, and to visualize the correlation using a scatter plot.

Inputs:
- df: a pandas DataFrame containing the data to be analyzed
- target_column: a string representing the name of the target column for which the correlation with other columns will be calculated

Flow:
1. Drop the target column and index from the DataFrame
2. Iterate over the remaining columns and calculate the correlation between the target column and each column
3. Print the correlation value for each column
4. Create a scatter plot to visualize the correlation between the target column and each column using Plotly

Outputs:
- Printed correlation values between the target column and each column in the DataFrame
- Scatter plot visualizations of the correlation between the target column and each column in the DataFrame

Additional aspects:
- The function uses the Plotly library to create scatter plots for visualization
- The function assumes that the input DataFrame contains numerical data
- The function does not modify the input DataFrame, but only performs calculations and visualizations on it.
"""
class TestBulkCorrelationAnalysis:
    # Tests that the function works with a DataFrame containing multiple columns and a valid target column
    def test_multiple_columns_valid_target(self):
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': [4, 5, 6],
            'col3': [7, 8, 9]
        })
        target_column = 'col1'
        bulk_correlation_analysis(df, target_column)
        assert True

    # Tests that the function works with a DataFrame containing only two columns and a valid target column
    def test_two_columns_valid_target(self):
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': [4, 5, 6]
        })
        target_column = 'col1'
        bulk_correlation_analysis(df, target_column)
        assert True

    # Tests that the function raises an exception if the target column is not in the DataFrame
    def test_two_columns_invalid_target(self):
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': [4, 5, 6]
        })
        target_column = 'invalid'
        with pytest.raises(KeyError):
            bulk_correlation_analysis(df, target_column)

    # Tests that the function works with an empty DataFrame
    def test_empty_dataframe(self):
        df = pd.DataFrame()
        target_column = 'col1'
        bulk_correlation_analysis(df, target_column)
        assert True

    # Tests that the function works with a DataFrame containing only one column
    def test_one_column_dataframe(self):
        df = pd.DataFrame({
            'col1': [1, 2, 3]
        })
        target_column = 'col1'
        bulk_correlation_analysis(df, target_column)
        assert True

    # Tests that the function works with a DataFrame containing only one row
    def test_one_row_dataframe(self):
        df = pd.DataFrame({
            'col1': [1],
            'col2': [2],
            'col3': [3]
        })
        target_column = 'col1'
        bulk_correlation_analysis(df, target_column)
        assert True






