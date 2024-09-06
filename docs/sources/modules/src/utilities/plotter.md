#


## Plotter
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/utilities/plotter.py/#L38)
```python 

```




**Methods:**


### .helper_for_plotting_fig_3abcde
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/utilities/plotter.py/#L791)
```python
.helper_for_plotting_fig_3abcde(
   interpreter, xlim, gs, row, fig, max_y_percent, ADD_SECOND_COLUMN,
   split_legend = True
)
```


### .helper_for_plotting_fig_2abcde
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/utilities/plotter.py/#L971)
```python
.helper_for_plotting_fig_2abcde(
   ax, interpreter, xlim, title, add_ylabel = True, add_xlabel = True,
   ylim_constraint = 100000, split_legend = True
)
```


### .plot_fig_3abcde_updated
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/utilities/plotter.py/#L1279)
```python
.plot_fig_3abcde_updated(
   results, xlim, ADD_SECOND_COLUMN = False
)
```


### .plot_fig_3ab
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/utilities/plotter.py/#L1363)
```python
.plot_fig_3ab(
   monte_carlo_data, food_names, removed, added
)
```


### .plot_fig_s2abcd
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/utilities/plotter.py/#L1460)
```python
.plot_fig_s2abcd(
   interpreter1, interpreter2, xlim1, xlim2
)
```


### .getylim_nutrients
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/utilities/plotter.py/#L1823)
```python
.getylim_nutrients(
   interpreter, xlim
)
```


### .plot_histogram
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/utilities/plotter.py/#L1846)
```python
.plot_histogram(
   ax, data, N, xlabel, ylabel, title
)
```

---
Plots a histogram of the given data on the given axis with the given labels and title.


**Args**

* **ax** (matplotlib.axes.Axes) : The axis to plot the histogram on.
* **data** (list) : The data to plot.
* **N** (int) : The number of data points.
* **xlabel** (str) : The label for the x-axis.
* **ylabel** (str) : The label for the y-axis.
* **title** (str) : The title for the plot.


**Returns**

None


**Example**


```python

>>> data = [1, 2, 3, 4, 5]
>>> N = 5
>>> xlabel = "X Label"
>>> ylabel = "Y Label"
>>> title = "Title"
>>> plot_histogram(ax, data, N, xlabel, ylabel, title)
```

### .plot_histogram_with_boxplot
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/utilities/plotter.py/#L1876)
```python
.plot_histogram_with_boxplot(
   data, xlabel, title
)
```


### .get_people_fed_legend
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/utilities/plotter.py/#L1901)
```python
.get_people_fed_legend(
   interpreter, is_nuclear_winter, split_legend = False
)
```


### .get_feed_biofuels_legend
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/utilities/plotter.py/#L1974)
```python
.get_feed_biofuels_legend(
   interpreter
)
```


### .plot_monthly_reductions_seasonally
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/utilities/plotter.py/#L2030)
```python
.plot_monthly_reductions_seasonally(
   ratios
)
```


### .plot_monthly_reductions_no_seasonality
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/utilities/plotter.py/#L2042)
```python
.plot_monthly_reductions_no_seasonality(
   all_months_reductions
)
```

---
Plot the reduction each month, showing the seasonal variability.

### .plot_food
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/utilities/plotter.py/#L2057)
```python
.plot_food(
   food, title
)
```

---
Plot the food generically with the 3 macronutrients.

### .plot_food_alternative
[source](https://github.com/allfed/allfed-integrated-model/blob/master/src/utilities/plotter.py/#L2121)
```python
.plot_food_alternative(
   food, title
)
```

---
Plot the food generically with the 3 macronutrients (alternative layout).
