#


## Validator
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/optimizer/validate_results.py/#L15)
```python 
Validator()
```




**Methods:**


### .validate_results
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/optimizer/validate_results.py/#L16)
```python
.validate_results(
   extracted_results, interpreted_results, time_consts, percent_fed_from_model,
   optimization_type, country_code
)
```

---
Validates the results of the model by ensuring that the optimizer returns the same as the sum of nutrients,
that zero kcals have zero fat and protein, that there are no NaN values, and that all values are greater than or
equal to zero.


**Args**

* **model** (Model) : The model to validate the results of.
* **extracted_results** (ExtractedResults) : The extracted results from the model.
* **interpreted_results** (InterpretedResults) : The interpreted results from the model.


**Returns**

None

### .ensure_all_time_constants_units_are_billion_kcals
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/optimizer/validate_results.py/#L61)
```python
.ensure_all_time_constants_units_are_billion_kcals(
   time_consts
)
```


### .check_constraints_satisfied
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/optimizer/validate_results.py/#L74)
```python
.check_constraints_satisfied(
   model, maximize_constraints, variables
)
```

---
This function checks if all constraints are satisfied by the final values of the variables.
It takes a really long time to run, so it's run infrequently.


**Args**

* **model** (pulp.LpProblem) : The optimization model
* **maximize_constraints** (list) : A list of constraints to maximize
* **variables** (list) : A list of variables to check constraints against


**Returns**

None


**Raises**

* **AssertionError**  : If a constraint is not satisfied


### .ensure_optimizer_returns_same_as_sum_nutrients
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/optimizer/validate_results.py/#L161)
```python
.ensure_optimizer_returns_same_as_sum_nutrients(
   percent_fed_from_model, interpreted_results, INCLUDE_FAT, INCLUDE_PROTEIN,
   country_code
)
```

---
ensure there was no major error in the optimizer or in analysis which caused
the sums reported to differ between adding up all the extracted variables and
just look at the reported result of the objective of the optimizer

### .ensure_zero_kcals_have_zero_fat_and_protein
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/optimizer/validate_results.py/#L224)
```python
.ensure_zero_kcals_have_zero_fat_and_protein(
   interpreted_results
)
```

---
Checks that for any month where kcals is zero for any of the foods,
then fat and protein must also be zero.


**Args**

* **interpreted_results** (InterpretedResults) : An instance of the InterpretedResults class


**Returns**

None

---
Notes:
    This function is called to ensure that the kcals, fat and protein values are consistent
    for each food source, feed and biofuels independently.


**Raises**

* **AssertionError**  : If the kcals value is zero but the fat or protein value is non-zero.


### .ensure_never_nan
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/optimizer/validate_results.py/#L272)
```python
.ensure_never_nan(
   interpreted_results
)
```

---
This function checks that the interpreter results are always defined as a real number.
It does this by calling the make_sure_not_nan() method on each of the interpreted_results attributes.
If any of the attributes contain NaN values, an exception will be raised.


**Args**

* **interpreted_results** (InterpretedResults) : An instance of the InterpretedResults class.


**Raises**

* **ValueError**  : If any of the interpreted_results attributes contain NaN values.


**Returns**

None

### .ensure_all_greater_than_or_equal_to_zero
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/optimizer/validate_results.py/#L301)
```python
.ensure_all_greater_than_or_equal_to_zero(
   interpreted_results
)
```

---
Checks that all the results variables are greater than or equal to zero.

**Args**

* **interpreted_results** (InterpretedResults) : An instance of the InterpretedResults class


**Raises**

* **AssertionError**  : If any of the results variables are less than zero


### .assert_feed_and_biofuel_used_is_zero_if_humans_are_starving
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/optimizer/validate_results.py/#L781)
```python
.assert_feed_and_biofuel_used_is_zero_if_humans_are_starving(
   interpreted_results, epsilon = 0.001
)
```

