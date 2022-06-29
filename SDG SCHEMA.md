## SDG Schema

The SDG Solution Schema attempts to define the structure where SDG Indicators are represented as columns in a table. Addtionally, each dis-aggregation of an indicator is represented in its own column.

Here is a quick example:

Output Table:
| Geography ID | Reporting Year | SI_POV_DAY1 | SI_POV_DAY1_AGE_T_P | SI_POV_DAY1_EDUCATION_LEV_T_P |
|-------------- |---------------- |------------- |--------------------- |------------------------------- |
| 1 | 2021 | 13.70 | 9.5 | 11.43 |

## Column Descriptions

#### Geography Fields

| Column         | Description                                                                                                                     |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Geography ID   | The ID of the geography that the indicator is reported on. This will be used to join to a spatial layer containing the same ID. |
| Reporting Year | The year that the indicator is reported on.                                                                                     |

#### Indicator Fields

For each SDG Indicator, we will follow the same pattern of

[INDICATOR CODE]\_[DIMENSION NAME]\_[DIMENSION VALUE]\_[PERCENTAGE OR RATIO]

| Column                        | Description                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SI_POV_DAY1                   | This is the overall (total) percentage of people in poverty.                                                                                                                                                                                                                                                                                                                                                                                |
| SI_POV_DAY1_AGE_T_P           | The percentage of people who are in poverty by age. We break down this field name as follows: <ul><li>**SI_POV_DAY1** : Indicator Code </li><li> **AGE** : The Age dimension of the Indicator </li><li> **T** stands for "Total". In this example for the "Age" dimension, another possible value here could be "G25" for "Greater than 25". Or simply "M" or "F" for "Male" or "Female" </li><li> **P** stands for "Percentage" </li></ul> |
| SI_POV_DAY1_EDUCATION_LEV_T_P | The total percentage of people who are in poverty by education level. We break down this field name as follows: <ul><li>**SI_POV_DAY1** : Indicator Code </li><li> **EDUCATION_LEV** : The Education Level dimension of the Indicator </li><li> **T** stands for "Total" </li><li> **P** stands for "Percentage" </li></ul>                                                                                                                 |

**Note**

> For each SDG Indicator Code, you can retrieve all potential Codes and Values via an API call to the SDG API. For example for `SI_POV_DAY1`, you can use this URL: https://unstats.un.org/SDGAPI/v1/sdg/Series/SI_POV_DAY1/Dimensions
