# %%
from os import mkdir, remove, sendfile
from os.path import exists
from numpy import NaN
import pandas as pd
from urllib.request import urlopen
import json

# %%
language = 'en'


def get_dhs_ids():
    df = pd.read_excel(
        'controls/LOOKUP_TABLE_CONTROL.xlsx',
        sheet_name='DHS_SDG')
    return df['IndicatorId'].to_list()

# get the data for each id and country from the indicator data api


def update_data(agg, id, country_code, survey_id, language):
    data = json.loads(urlopen(
        f'http://api.dhsprogram.com/rest/dhs/data?breakdown=all&indicatorIds={id}&countryIds={country_code}&surveyIds={survey_id}&lang={language}&f=json').read())
    return agg + data['Data']

# combine all of the indiacator data


def aggrigate_data(ids, country_code, survey_id, language):
    agg = []
    for id in ids:
        agg = update_data(agg, id, country_code, survey_id, language)
    return agg

# run to gather each measurement


def update_measurement(agg, id):
    try:
        data = json.loads(
            urlopen(f'http://api.dhsprogram.com/rest/dhs/indicators/{id}').read())
        return agg + data['Data']
    except BaseException:
        print(f'missing {id}')
        return agg

# combine measurement metadata


def aggrigate_measurement(ids):
    agg = []
    for id in ids:
        agg = update_measurement(agg, id)
    return agg

# loops through indicator id's and adds all data to a large dict object


def merge_to_df(ids, country_code, survey_id, language):
    indicator_ids_dict = aggrigate_data(ids, country_code, survey_id, language)
    indicator_ids_df = pd.json_normalize(indicator_ids_dict)
    DHS_indicator_SDG_series = pd.read_excel(
        'controls/LOOKUP_TABLE_CONTROL.xlsx',
        sheet_name='DHS_SDG')
    # add in SDG Series Demensions
    return indicator_ids_df.merge(
        DHS_indicator_SDG_series,
        right_on="IndicatorId",
        left_on="IndicatorId").reset_index()

# combeine the series list


def aggrigated_indicator_list(df):
    sdg_series_df = df[['SDG_Series']].groupby(
        ['SDG_Series']).first().reset_index()
    return sdg_series_df['SDG_Series'].to_list()

# get the survey measurement metadata for each IndicatorId


def measurements_df(ids):
    measurements = aggrigate_measurement(ids)
    return pd.json_normalize(measurements)

# run for each survey with each survey id and gets all the data from the
# id's list from the top of the sheet


def run_for_survey(ids, country_code, survey_id, language):
    indicators_with_sdg_dimensions = merge_to_df(
        ids, country_code, survey_id, language)
    aggrigated_indicator_ids_df = indicators_with_sdg_dimensions[['IndicatorId',
                                                                  'RegionId',
                                                                  'Indicator',
                                                                  'SDG_Series',
                                                                  'CharacteristicCategory',
                                                                  'CharacteristicLabel',
                                                                  'SDG_Goal_ID',
                                                                  'SDG_Goal_Desc']].groupby(['IndicatorId',
                                                                                             'SDG_Series',
                                                                                             'CharacteristicCategory',
                                                                                             'RegionId',
                                                                                             'CharacteristicLabel',
                                                                                             'SDG_Goal_ID',
                                                                                             'SDG_Goal_Desc']).first().reset_index()
    sdg_series_list = aggrigated_indicator_list(aggrigated_indicator_ids_df)

    measurements = measurements_df(ids)
    measurements.to_excel(
        f'outputs/{country_code}/{survey_id}/measurements.xlsx',
        index=False)

    # TODO: for performance filter all_sdg_goal dataframe to only include
    # selected goals
    all_sdg_goals = pd.read_excel(
        'controls/LOOKUP_TABLE_CONTROL.xlsx',
        sheet_name='All_SDG_Goals')
    dimensions = pd.read_excel(
        'controls/LOOKUP_TABLE_CONTROL.xlsx',
        sheet_name='characteristic_to_dimension')

    all_sdg_goals.insert(8, 'CharacteristicIndicator', '')
    all_sdg_goals.insert(15, 'Value', '')
    all_sdg_goals.insert(16, 'MeasurementType', '')
    all_sdg_goals.insert(16, 'RegionId', '')

    # %%
    # Iterate through sdg goal sheet
    for series_index, series_row in all_sdg_goals.iterrows():
        if series_row['Series Code'] not in sdg_series_list:
            continue

        for dim_index, dim_row in dimensions.iterrows():
            # skip if NaN
            if type(dim_row['Dimension Code']) == float:
                continue
            value = ''
            if dim_row['Dimension Code'] == series_row['Dimension Code']:
                for dhs_index, dhs_row in indicators_with_sdg_dimensions.iterrows():
                    if dhs_row['SDG_Series'] == series_row['Series Code']:
                        measurements_row = measurements[['MeasurementType', 'DenominatorWeightedId',
                                                         'DenominatorUnweightedId']][measurements['IndicatorId'] == dhs_row['IndicatorId']]
                        all_sdg_goals['CharacteristicIndicator'].iloc[series_index] = str(
                            dhs_row['IndicatorId']) + ',' + str(
                            dim_row['CharacteristicCategory']) + ',' + str(
                            dim_row['CharacteristicLabel'])  # + ',' + str(dhs_row['MeasurementType']) + ',' + str(dhs_row['DenominatorWeightedId'])
                        all_sdg_goals['IndicatorId'].iloc[series_index] = str(
                            dhs_row['IndicatorId'])
                        value = indicators_with_sdg_dimensions['Value'][
                            (indicators_with_sdg_dimensions['IsPreferred'] == 1) & (
                                indicators_with_sdg_dimensions['IndicatorId'] == dhs_row['IndicatorId']) & (
                                indicators_with_sdg_dimensions['SDG_Series'] == dhs_row['SDG_Series']) & (
                                indicators_with_sdg_dimensions['CharacteristicCategory'] == dim_row['CharacteristicCategory']) & (
                                indicators_with_sdg_dimensions['CharacteristicLabel'] == dim_row['CharacteristicLabel'])].to_list()
                        region_id = indicators_with_sdg_dimensions['RegionId'][
                            (indicators_with_sdg_dimensions['IsPreferred'] == 1) & (
                                indicators_with_sdg_dimensions['IndicatorId'] == dhs_row['IndicatorId']) & (
                                indicators_with_sdg_dimensions['SDG_Series'] == dhs_row['SDG_Series']) & (
                                indicators_with_sdg_dimensions['CharacteristicCategory'] == dim_row['CharacteristicCategory']) & (
                                indicators_with_sdg_dimensions['CharacteristicLabel'] == dim_row['CharacteristicLabel'])].to_list()
                        if len(value) == 0:
                            continue

                        all_sdg_goals['Value'].iloc[series_index] = value[0]
                        all_sdg_goals['MeasurementType'].iloc[series_index] = measurements_row['MeasurementType'].to_list()[
                            0]
                        all_sdg_goals['RegionId'] = region_id[0]

    # # get totals and file under series code for each Series Code
    i = 0
    series_index_rows = []
    for id in sdg_series_list:
        row = {'Series Code': id, 'Value': NaN, 'Attribute Name': id}
        matching_row = all_sdg_goals[['Series Code', 'Attribute Name', 'Value']][(
            all_sdg_goals['CharacteristicIndicator'].str.contains(',Total,Total')) & (all_sdg_goals['Attribute Name'].str.contains(id))]

        valueList = matching_row['Value'].tolist()
        attribute_list = matching_row['Attribute Name'].tolist()
        if len(valueList) > 0:
            row['Value'] = valueList[0]
            series_index_rows.append(row)
        i = i + 1

    # create series code totals dataframe
    series_index_rows = pd.DataFrame(series_index_rows)

    regional_df = indicators_with_sdg_dimensions[(indicators_with_sdg_dimensions['RegionId'] != '') & (
        indicators_with_sdg_dimensions['SDG_Series'] != '')]

    updated_columns = {
        "RegionId": "Nation",
        "Indicator": "Target Description",
        "SDG_Goal_ID": "Indicator",
        "SDG_Series": "Series Code",
        "SDG_Goal_Desc": "Goal Description",
        "SurveyYear": "Year",
        "SurveyId": "Survey"
    }

    regional_df = regional_df.merge(
        measurements[['IndicatorId', 'MeasurementType']], on="IndicatorId").reset_index()
    regional_df['Target'] = regional_df['SDG_Goal_ID'].str.slice(0, 3)
    regional_df['Goal'] = regional_df['SDG_Goal_ID'].str.slice(0, 1)

    regional_df = regional_df.rename(columns=updated_columns)
    regional_df = regional_df[['Goal',
                               'Goal Description',
                               "Target",
                               "Target Description",
                               "Indicator",
                               "IndicatorId",
                               "Nation",
                               "Value",
                               "MeasurementType",
                               "Year",
                               "Survey"]]
    regional_df.to_excel(
        f'outputs/{country_code}/{survey_id}/regional_data.xlsx',
        index=False)

    # append series code totals table to all_sdg_goals dataframe
    all_sdg_goals = all_sdg_goals.append(series_index_rows)

    # filter out all rows with missing values
    all_sdg_goals = all_sdg_goals[all_sdg_goals['Value'] != '']

    # add in characteristics true for all
    all_sdg_goals['Nation'] = country_code
    all_sdg_goals['Survey'] = survey_id
    all_sdg_goals['Year'] = survey_id[2:6]

    # export national data
    all_sdg_goals.to_excel(
        f'outputs/{country_code}/{survey_id}/national_data.xlsx',
        index=False)
    print(f'done with {country_code} - {survey_id}')

# take parameters in from the command line with dynamic country and survey
# information


def get_user_parameters():
    def select_country():
        countries = json.loads(
            urlopen('http://api.dhsprogram.com/rest/dhs/countries?f=json').read())

        id = 0
        for country in countries['Data']:
            print(f'{id} {country["CountryName"]}')
            id = id + 1

        print('Select a country Id from the list above ^')
        country_id = input("Country ID: ")
        selected_country = countries['Data'][int(country_id)]
        print(f'Selected Country: {selected_country["CountryName"]}')
        # add in the next country code list with blank survey list
        tool_inputs.append([selected_country["DHS_CountryCode"], []])

        def select_survey(country_code):
            surveys = json.loads(urlopen(
                f'https://previewapi.dhsprogram.com/rest/dhs/surveys/{country_code}').read())
            id = 0
            for survey in surveys['Data']:
                print(f'{id} {survey["SurveyId"]}')
                id = id + 1
            print('Select a survey Id from the list above ^')
            survey_id = input("Survey ID: ")
            selected_survey = surveys['Data'][int(survey_id)]

            print()
            tool_inputs[len(tool_inputs) -
                        1][1].append(selected_survey['SurveyId'])
            add_another = input(
                'Would you like to add another survey? (y/n): ')
            print()
            if add_another == 'y':
                select_survey(country_code)
            else:
                return

        select_survey(selected_country["DHS_CountryCode"])
        add_another = input('Would you like to add another country? (y/n): ')
        if add_another == 'y':
            select_country()
        else:
            return

    tool_inputs = []  # [[country_code1, [survey_id1, survey_id2]], [country_code2,[survey_id1]]]

    select_country()
    print(tool_inputs)
    return tool_inputs

# for managing the cleanup of the outputs directory


def clear_and_make_dir(path):
    if exists(path):
        from shutil import rmtree
        rmtree(path)
    mkdir(path)

# get all the geomtries from the dhs api


def get_geometry(country):

    # TODO: Request geojson with '?f=geojson'
    url = f'https://api.dhsprogram.com/rest/dhs/geometry/{country}'
    json_array = json.loads(urlopen(url).read())['Data']

    # update items to have a country code as a region id if missing
    for item in json_array:
        if item['RegionID'] == "":
            item['RegionID'] = item["CountryCode"]

    df = pd.json_normalize(json_array)
    df.to_excel(f'outputs/{country}/geometry.xlsx')

# ! FAILS TO GET DATA
def get_geojson(country):

    # TODO: Request geojson with '?f=geojson'
    url = f'https://api.dhsprogram.com/rest/dhs/geometry/{country}?f=geojson'
    json_array = json.loads(urlopen(url).read())['Data']

    # update items to have a country code as a region id if missing
    for item in json_array.features:
        if item.properties['RegionID'] == "":
            item.properties['RegionID'] = item.properties["CountryCode"]

    f = open(f'outputs/geojson/{country}.json', "w")
    f.write(json.dumps(json_array))
    f.close()

# get and combine all of the user input into xlsx files for countries and surveys
# TODO add in 3rd arguement for list of goals and set to default to all


def get_all_data(ids, user_input):
    clear_and_make_dir('outputs')
    clear_and_make_dir('outputs/geojson')

    # # loop through country and survey from user inputs to generate xlsx files by survey
    for input_list in user_input:
        country = input_list[0]
        surveys = input_list[1]
        clear_and_make_dir(f'outputs/{country}')
        get_geometry(country)

        for survey in surveys:
            clear_and_make_dir(f'outputs/{country}/{survey}')
            clear_and_make_dir(f'outputs/{country}/{survey}/multivalues')
            print(f'Start of: {country} - {survey}')
            run_for_survey(ids, country, survey, language)
        if exists('outputs/table.xlsx'):
            remove('outputs/table.xlsx')
        
        # ! FAILS TO GET DATA
        # get_geojson(country)


    # # loop through country and survey from user inputs and combine xlsx files
    for input_list in user_input:
        country = input_list[0]
        surveys = input_list[1]

        # combine geometry
        df = pd.read_excel(f'outputs/{country}/geometry.xlsx')
        if exists('outputs/geometry.xlsx'):
            geometry = pd.read_excel('outputs/geometry.xlsx')
            geometry = pd.concat([geometry, df], ignore_index=True)
            geometry.to_excel('outputs/geometry.xlsx', index=False)
        else:
            df.to_excel('outputs/geometry.xlsx', index=False)

        # combine all of the survey and geometry infomation in the outputs root
        # folder
        for survey in surveys:
            df = pd.read_excel(
                f'outputs/{country}/{survey}/national_data.xlsx')
            if exists('outputs/national_data.xlsx'):
                national_data = pd.read_excel('outputs/national_data.xlsx')
                national_data = pd.concat(
                    [national_data, df], ignore_index=True)
                national_data.to_excel(
                    'outputs/national_data.xlsx', index=False)
            else:
                df.to_excel('outputs/national_data.xlsx', index=False)

            df = pd.read_excel(
                f'outputs/{country}/{survey}/regional_data.xlsx')
            if exists('outputs/regional_data.xlsx'):
                regional_data = pd.read_excel('outputs/regional_data.xlsx')
                regional_data = pd.concat(
                    [regional_data, df], ignore_index=True)
                regional_data.to_excel(
                    'outputs/regional_data.xlsx', index=False)
            else:
                df.to_excel('outputs/regional_data.xlsx', index=False)

    regional_df = pd.read_excel('outputs/regional_data.xlsx')
    national_df = pd.read_excel('outputs/national_data.xlsx')

    # merge attribute name to regional_df
    df = pd.read_excel(
        'controls/LOOKUP_TABLE_CONTROL.xlsx',
        sheet_name='DHS_SDG')
    regional_df = regional_df.merge(
        df,
        left_on="IndicatorId",
        right_on="IndicatorId").reset_index()
    all_df = pd.concat([national_df, regional_df])

    # TODO filter out goal export
    # region, year, ...
    # List of GOALS in all_df
    goals = all_df[["Goal"]].groupby(
        ["Goal"], as_index=False).first().reset_index()
    goals["Goal"].astype('int')
    goals = goals['Goal'].to_list()  # ! filter goals here

    # Create for loop that serates all_df by GOAL and export each xlxs by goal
    for goal in goals:
        series_code_columns = all_df[["Series Code"]][all_df['Goal'] == goal].groupby(
            ["Series Code"], as_index=False).first()
        attribute_ids_columns = all_df[["Attribute Name"]][all_df['Goal'] == goal].groupby(
            ["Attribute Name"], as_index=False).first()

        sdg_columns = series_code_columns['Series Code'].to_list(
        ) + attribute_ids_columns['Attribute Name'].to_list()
        sdg_columns.sort()
        sdg_columns = ['GEO_ID', 'YEAR', 'SURVEY'] + sdg_columns

        # combine all regional and national data
        dfinal_list = []
        for all_index, all_row in all_df.iterrows():
            series_code = all_row[['SDG_Series']][0]
            attribute_name = all_row[['Attribute Name']][0]
            nation = all_row[['Nation']][0]
            year = all_row[['Year']][0]
            value = all_row[['Value']][0]
            survey = all_row[['Survey']][0]

            # if national
            if len(nation) == 2:
                data = {"GEO_ID": nation, "YEAR": year, "SURVEY": survey}
                data[attribute_name] = value
                dfinal_list.append(data)
            # if regional
            else:
                data = {"GEO_ID": nation, "YEAR": year, "SURVEY": survey}
                data[series_code] = value
                dfinal_list.append(data)

        dfinal = pd.DataFrame(columns=sdg_columns, data=dfinal_list)
        dfinal = dfinal.groupby(['GEO_ID', 'YEAR'], as_index=False).first()
        dfinal = dfinal.loc[:, ~dfinal.columns.duplicated()]
        dfinal.to_excel(f'outputs/final_{goal}.xlsx')

    series_code_columns = all_df[["Series Code"]].groupby(
        ["Series Code"], as_index=False).first()
    attribute_ids_columns = all_df[["Attribute Name"]].groupby(
        ["Attribute Name"], as_index=False).first()
    sdg_columns = series_code_columns['Series Code'].to_list(
    ) + attribute_ids_columns['Attribute Name'].to_list()
    sdg_columns.sort()
    sdg_columns = ['GEO_ID', 'YEAR', 'SURVEY'] + sdg_columns

    # combine all regional and national data
    dfinal_list = []
    for all_index, all_row in all_df.iterrows():
        series_code = all_row[['SDG_Series']][0]
        attribute_name = all_row[['Attribute Name']][0]
        nation = all_row[['Nation']][0]
        year = all_row[['Year']][0]
        value = all_row[['Value']][0]
        survey = all_row[['Survey']][0]

        # if national
        if len(nation) == 2:
            data = {"GEO_ID": nation, "YEAR": year, "SURVEY": survey}
            data[attribute_name] = value
            dfinal_list.append(data)
        # if regional
        else:
            data = {"GEO_ID": nation, "YEAR": year, "SURVEY": survey}
            data[series_code] = value
            dfinal_list.append(data)

    dfinal = pd.DataFrame(columns=sdg_columns, data=dfinal_list)
    dfinal = dfinal.groupby(['GEO_ID', 'YEAR'], as_index=False).first()
    dfinal = dfinal.loc[:, ~dfinal.columns.duplicated()]
    dfinal.to_excel('outputs/final.xlsx')


ids = get_dhs_ids()

# # FOR TESTING
# add in list of subnational totals that match up to the series_id
# get_all_data(ids, [['AM', ['AM2000DHS', 'AM2010DHS']], [
#              'VN', ['VN1997DHS', 'VN2002DHS', 'VN2005AIS']]])

# # FOR PRODUCTION
user_input = get_user_parameters()
get_all_data(ids, user_input)
