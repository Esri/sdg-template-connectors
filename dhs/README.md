## DHS SDG Solution Connector

This script will allow the user to select mulitple countries and surveys from the DHS api and map those indicators over the SDG Schema.

The output will be put in the `outputs` folder in the root directory.

The script is to be run in a terminal and the user will be prompted to select the countries and surveys they would like to create excel files from.

## python installation

This environment uses `venv`. Install venv with `python3 install venv`

make a new environment with `python3 -m venv venv`

activate with `source venv/bin/activate`

install the libraries `pip3 install -r requirements.txt`

run the script `python3 DHS_field_mappings.py`

follow the prompts and select the desired countries and surveys

the results will be placed in the `outputs` folder of the project

**_ALL FILES AND FOLDERS WILL BE DELETED UPON THE NEXT RUN OF THE SCRIPT_**

## Controls file

All of the information is dependent on the `controls/LOOKUP_TABLE_CONTROL.xlsx` file. Each of the tables plays a role in the script to run this script. If you need to update the information on this script you should do so there first.

- `DHS_SDG` - a sheet that allows you to map the dhs indicator api to the sdg series indicator `Source: DHS and Walter`
- `characteristic_to_dimension` - a mapping feature that allows the user to map the dhs CharacteristicCategory and CharacteristicLabel to the sdg Dimension Code `Source: Walter`
- `All_SDG_Goals` - a full list of sdg information that allows the user to connect the dhs information to the sdg information. `Source: Esri`
