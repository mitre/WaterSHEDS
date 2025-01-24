## WaterSHEDs

### Modeling Surface Water PFAS Vulnerability 
##
#### NOTICE: © 2024 The MITRE Corporation. All Rights Reserved. Approved for Public Release; Distribution Unlimited. Public Release Case Number 24-3501.
 
#### NOTICE: MITRE hereby grants express written permission to use, reproduce, distribute, modify, and otherwise leverage this software to the extent permitted by the licensed terms provided in the LICENSE.md file included with this project.

#### ACKNOWLEDGEMENT

The MITRE WaterSHEDS model was created in collaboration with the U.S. Geological Survey. Major thanks to Larry Barber and Brianna Williams from the USGS Water Mission Area - Proxies Project team for their invaluable input and suggestions in model development, application, and collaboration.

##

### Requirements to Run 
1. The Esri provided Python Environment 
2. A jupyter notebook server 
3. A single directory that contains: 
   1. The WaterSHEDs notebook
   2. All data required to run (more information below)
4. An EPSG code corresponding to the UTM Zone for your AOI 
   - This is used in the code to convert Vector Outputs to a Raster
   - A supported list of EPSG codes can be found [here](https://pro.arcgis.com/en/pro-app/latest/arcpy/classes/pdf/projected_coordinate_systems.pdf)
5. A File Geodatabase Workspace
   - This geodatabase will be where your 1) base data is stored and 2) your results are written to
   - Note: The geodatabase should to include all of the data referenced in this section. 

### Data
6. A polygon denoting your Area of Interest (AOI) 
   - This polygon should be included in your File Geodatabase Workspace
7. Data for your AOI from the National Hydrography Dataset 
   - This dataset is used to identify potential downstream vulnerabilities from hazard sources. The [NHDPlus HR](https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer) is a national, geospatial model of the flow of water across the landscape and through the stream network. The NHDPlus HR is built using the National Hydrography Dataset High Resolution data at 1:24,000 scale or better, the 1/3 arc-second (10 meter ground spacing) 3D Elevation Program data, and the nationally complete Watershed Boundary Dataset.  
       - [Access data from the USGS National Map here](https://www.epa.gov/waterdata/get-nhdplus-national-hydrography-dataset-plus-data#NHDPlusV2Map)
       - [Access data from staged ftp site here](https://prd-tnm.s3.amazonaws.com/index.html?prefix=StagedProducts/Hydrography/NHDPlusHR/Beta/GDB/)

8.  A copy of the EPA's Facility Registry System (FRS). This data contains a file that has all of the NAICS codes for facilities within the system.  It can be downloaded here:  [EPA State Combined CSV Download Files](https://ordsext.epa.gov/FLA/www3/state_files/national_combined.zip). 
    -  This data is used to calculte a preliminary vulnerability based on teh industry type. 
    -  The file you want to extract from this ZIP is the`"NATIONAL_NAICS_File.csv`

9.  A copy of the NHDPlusV21 catchment data from the EPA to include: 
   -  Download Option: [NHPPlusV2](https://www.epa.gov/waterdata/get-nhdplus-national-hydrography-dataset-plus-data#v2datamap) 
      - You will need to identify your region and download the `NHDPlusV21_{RegionName}_NHDPlusCatchment.7z` file
      - These files are needed to aggregate the results and configure summary attributes. 
   - There is also an [ArcGIS Feature Server](https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/NHDPlusV21/FeatureServer) that contains the data. 
   - The shapefile denoting the catchment region will need to be imported into the File Geodatabase specified in requirement 4

10. PFAS Hazard Source Data
    - This notebook will download this data for you and you and you do not need to indvidually download them. That said, for awareness, the layers are listed below.
    1.  [DoD Site Boundaries](https://services7.arcgis.com/n1YM8pTrFmm7L4hs/arcgis/rest/services/mirta/FeatureServer/1)
    2.  [Fire Stations](https://carto.nationalmap.gov/arcgis/rest/services/structures/MapServer/51)
    3.  [Oil and Natural Gas Wells](https://services7.arcgis.com/FGr1D95XCGALKXqM/ArcGIS/rest/services/Oil_Wells/FeatureServer/0)
    4.  [Solid Waste Landfill Facilities](https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/EPA_Disaster_Debris_Recovery_Data/FeatureServer/0)
    5.  [Runways](https://services6.arcgis.com/ssFJjBXIUyZDrSYZ/arcgis/rest/services/Runways/FeatureServer/0)
    6.  [NPDES Facilities](https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/oeca__echo__npdes_facilities_outfalls/FeatureServer/0)
    7.  [Facilities of Interest](https://services.arcgis.com/cJ9YHowT8TU7DUyn/ArcGIS/rest/services/FRS_INTERESTS/FeatureServer/0)
    8.  [DoD Formerly Used Defense Sites](https://services7.arcgis.com/n1YM8pTrFmm7L4hs/ArcGIS/rest/services/FUDS_property_areas/FeatureServer/0)
    - **Note**: This notebook was written with these as the input layers.  With that in mind, many of the layer names in the notebook refer to the above. If you have additional layers you wish to download, or different layers all together, you will need to identify and update those references below. 

##
### Steps to Run 
**Note**: It is reccomended that you do NOT run this notebook from within ArcGIS Pro. 
1. In order to run the code, first open the python command prompt that comes with ArcGIS Pro
   1. In the Windows start menu, navigate to the ArcGIS folder and selct the "Python Command Prompt" option

2. One the command prompt is open, type the following: `jupyter notebook` 
   - Note: If this is your first time running the command, you will not have a `jupyter_notebook_config.py` file.  This means your notebook will default to and display all files in the ArcGIS Pro python directory.  To change this behavior: 
     -  Shut down the existing jupyter notebook by pressing `CTRL + c` and select `y` when prompted
     -  In the same terminal, type `jupyter notebook --generate-config` 
        -  This will create a config file for you
     -  Navigate to the directory where the config file was created and open the `jupyter_notebook_config.py` file
     -  Search for and update the following to your desired directory: `c.NotebookApp.notebook_dir`
     -  Save the file and re-run the `jupyter notebook` command

3. In the resulting notebook server, navigate to where your copy of the WaterSHEDs notebook and all data exists
   
4. Run the initial import steps and, when prompted, answer the following: 
   1. What is the file path of your File Geodatabase workspace? 
   2. Please enter the name of your AOI HUC boundary that is located in your FGDB workspace
   3. Please enter the path to the input NHD Flowline Flie
   4. Please enter the path to the NHDPlus Flowline VAA table
   5. Please enter the path to the NHDPlus EROMMA file
   6. Please enter the path to the NHDPlus Catchment layer
   7. Please enter the path to the NHDPlus Hydro Geometric Network file
      1. **Note**: This is used to create and enable the trace network. The tool used in ArcPy to preform this PERMANENTLY MODIFIES the input data. The cell, named "Create and Enable Trace Network", can only be run ONCE with the HYDRO NET input layer. 
   8. Please enter the EPSG code that corresponds to the UTM Zone for your AOI
      1. Please see the following for reference [here](https://pro.arcgis.com/en/pro-app/latest/arcpy/classes/pdf/projected_coordinate_systems.pdf)
         - It is reccomended you use a NAD_1983_11 based projection. These can be found starting at the bottom of Page 78
   9.  Please enter the full path to the CSV that contains the NAICS codes for facilities in the FRS
   10. Specify a short name to differentiate between outputs 
##
### While Running the Notebook
- There are instances where user input will still be required to help differentiate outputs. These occur: 
  - Under Vulnerability Modeling when calulating Distance Decay, users will be required to specify a unique File Geodatabase Table name to store results.
  - When calculating the weighted sum, users will be required to enter weights for the various layers.  The default values used by the MITRE team are: 
  
     -    DoD Facilities: 0.17
     -    Facilities of Interest (FOI) - 100 = 0.15
     -    Facilities of Interest (FOI) - 75 = 0.13
     -    Facilities of Interest (FOI) - 50 = 0.11
     -    Formerly Used Defense Sites (FUDS) = 0.08
     -    Runways = 0.08
     -    Landfills = 0.08 
     -    Facilities of Interest (FOI) - 25 = 0.06 
     -    NPDES Permitted Facilities = 0.06 
     -    Firestations = 0.03
     -    Oiland Gas Facilities = 0.03
     -    Facilities of Interest (FOI) - 1 = 0.02
     
     
