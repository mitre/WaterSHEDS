'''
Multiprocessing approach to calculating all of the downstream flow lines. Please note that you need AMPLE storage on your system to run this.
'''

import arcpy
import shutil 
import os 
from multiprocessing import Pool, Manager,cpu_count
from datetime import datetime 
import uuid
import time 
import stat 
import logging

ws = input("What is the file path of your File Geodatabase workspace: ")

tmp_dir = os.path.join(os.path.dirname(ws),"temp_dir")

output_trace_dir = os.path.join(os.path.join(os.path.dirname(ws), "trace_outputs"))
arcpy.env.workspace=ws
arcpy.env.overwriteOutput=True

## USER INPUT -- Specify the AOI HUC boundary, located in the FGDB workspace, 
## for clipping data and setting extent:
AOI = input('Please enter the name of your AOI HUC boundary that is located in your FGDB workspace: ')

## USER INPUT -- Specify the file path of the NHDPlus Hydro Geometric Network:
in_geometric_network=input("Please enter the path to the NHDPlus Hydro Geometric Network file: ")

## User Input -- Specify the number of processors to use (will adivse if it's greater than cpu_count)
print(f'Your machine has {cpu_count()} processors available.  How many do you wish to use? ')
process_count_to_use = input()

##USER INPUT -- Specify the UTM Zone for your AOI -- Used when converting Vectors to Raster Output 
## Please see the README for a listing of acceptable codes.
utm_output_coordinate_system_number=32618
logFile = os.path.join(os.getcwd(), os.path.basename(ws)+ f"_{datetime.now().strftime('%Y%m%d%H%M%S')}.log")
logging.basicConfig(filename = logFile, filemode = 'a', format='%(asctime)s - %(message)s', level = logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

def create_fgdb(directory:str, name:str):
    ''' If one does not already exist, this will create the FGDB to store the results 

    Parameters
    ----------
        directory: str
            name of the base directory to create the FGDB
        name: str 
            the name of the output FGDB
    Returns
    ----------    
    str
        Full path to the created, or already existing FGDB
    '''

    outName = f"{name}.gdb"

    outPath = os.path.join(directory, outName)
    if os.path.exists(outPath):
        return outPath
    else:
        try:
            # print(f"Creating File GeoDatabase Named {name} ")

            arcpy.CreateFileGDB_management(directory, outName, "CURRENT")
        except Exception as e:
            print(f"[!!!!!!!!!!!!!!!!!!!!!!!!!! Error creating FileGeoDatabase ---> {e} -> !!!!!!!!!!!!!!!!!!!!!!!!!!]")
        #else:
        #    print(f"File GeoDatabase created and is available at {outPath}")

    return outPath

def change_file_times(in_dir):
    current_time = time.time()

    os.utime(in_dir,(current_time,current_time))
    for x in os.listdir(in_dir): 
        os.utime(os.path.join(in_dir,x),(current_time,current_time))

def delete(in_dir):
    '''
    Will loop through the temporary geodatabase and attempt to delete any files that were created. 

    '''
    for x in os.listdir(in_dir): 
        if ".sr.lock" not in x: 
            try:
                os.remove(os.path.join(in_dir,x))  
            # shutil.rmtree(in_dir, onerror=on_rm_error)
            except Exception as e: 
                pass   

def preform_hazard_trace(inputs):
    '''
    Preforms the downstream traces
    inputs: list 
        Index 0: original directory containing the hydronet files
        Index 1: input feature class to use in the calculation 
        Index 2: Current workspace (what `arcpy.env.workspace` is set to)
        Index 3: 
    
    '''
    
    run_uuid = uuid.uuid4().hex
    og_hydronet_dir = os.path.dirname(os.path.dirname(inputs[0]))

    new_hydronet_dir = os.path.join(tmp_dir,f'{os.path.basename(og_hydronet_dir).split(".gdb")[0]}_{run_uuid}.gdb')

    shutil.copytree(og_hydronet_dir, new_hydronet_dir)
    os.chmod(new_hydronet_dir,stat.S_IWRITE)
    change_file_times(new_hydronet_dir)

    HYDRO_NET_TRACE_Network = os.path.join(f'{new_hydronet_dir}','Hydrography','HydroNet_Trace')
    fcLine = inputs[1]
    # print(fcLine)
    ws = inputs[2]
    try: 
        print(f'Processing {datetime.now()} - {fcLine} ')
        trace_output_gdb = create_fgdb(output_trace_dir, f'trace_{run_uuid}')

    #     ## Copying the input fcLine file so we hopefully don't get any error messages
        arcpy.management.CopyFeatures(fcLine, os.path.join(trace_output_gdb, fcLine), '', None, None, None)
        
        fcLine = os.path.join(trace_output_gdb, fcLine)

        field_names_fcLine = []
        field_names = []
        field_names_fcLine = [f.name for f in arcpy.ListFields(fcLine, "Starting_NHDPlusID")]
            
        traceGroupName = fcLine+"_TraceGroup"
        outName="tempTrace_"+os.path.basename(fcLine)
        output_file = os.path.join(trace_output_gdb, outName) 
        
        # Compute Trace without aggregation, which results in a selection. 
        arcpy.tn.Trace(HYDRO_NET_TRACE_Network, "DOWNSTREAM", fcLine, 
                    '', "NO_DIRECTION", '', "EXCLUDE_BARRIERS", "DO_NOT_VALIDATE_CONSISTENCY", 
                    "DO_NOT_IGNORE_BARRIERS_AT_STARTING_POINTS", "IGNORE_INDETERMINATE_FLOW", None, None, 
                    "BOTH_JUNCTIONS_AND_EDGES", None, None, "NETWORK_LAYERS;SELECTION", "NEW_SELECTION", 
                    "CLEAR_ALL_PREVIOUS_TRACE_RESULTS", '', "Trace_Results_Aggregated_Points", 
                    "Trace_Results_Aggregated_Lines", traceGroupName, "DO_NOT_USE_TRACE_CONFIGURATION", '', None)
        
        copyTraceGroupNameFlowline = traceGroupName+"\\"+"NHDFlowline"

        # Copy/save the selected trace to the output file location and join the 
        # Starting_NHDPlusID field to each output.
        try: 
            arcpy.management.CopyFeatures(copyTraceGroupNameFlowline, output_file, '', None, None, None)  
        except Exception as e: 
            print('exception on copy features', e)

        arcpy.JoinField_management(output_file,"NHDPlusID", fcLine, "Starting_NHDPlusID", field_names_fcLine)
        
        field_names = [f.name for f in arcpy.ListFields(fcLine, "Starting_NHDPlusID")]
        # Create a list with tuples where each tuple contains the attribute values
        # to pass onto the update cursor to populate fields.
        # The Starting_NHDPlusID source attribute values are copied to all rows in the downstream trace.  

        def rows_as_dicts(cursor):
            colnames = cursor.fields
            for row in cursor:
                yield dict(zip(colnames, row))

        fc_dict = {}
        with arcpy.da.SearchCursor(fcLine, list(field_names)) as sc:
            for row in rows_as_dicts(sc):
                fc_dict.update(row)

        field_range = range(len(field_names))

        # Use an insert cursor to populate Starting_NHDPlusID for each row in downstream trace.
        with arcpy.da.UpdateCursor(output_file, list(field_names)) as cursor:
            fRange = range(len(fc_dict))
            fVals = list(fc_dict.values())
            for row in cursor:
                for Index in fRange:
                    row[Index] = fVals[Index]   
                    cursor.updateRow(row)    
            del cursor

            
        print("FinishedTrace "+traceGroupName)
        
        ## attempt to delete files in the new hydronet directory that we temporarilly added
        delete(new_hydronet_dir)
    except Exception as e: 
        print(f'[!!!!!!!!! Issue processing {fcLine} --> {e} !!!!!!!!!]')
        logger.error(f'[!!!!!!!!! Issue processing {fcLine} --> {e} !!!!!!!!!]')

if __name__ == '__main__': 

    print(logFile)
    strt = datetime.now()
    print('Starting everything now')

    if os.path.exists(output_trace_dir): 
        pass
    else: 
        os.makedirs(output_trace_dir)
        os.chmod(output_trace_dir, stat.S_IWRITE)

    if os.path.exists(tmp_dir): 
        pass
    else: 
        os.makedirs(tmp_dir)
    os.chmod(tmp_dir,stat.S_IWRITE)

    HYDRO_NET_TRACE_Network=os.path.join(os.path.dirname(in_geometric_network), 'HydroNet_Trace')
    

    og_hydronet_dir = os.path.dirname(os.path.dirname(HYDRO_NET_TRACE_Network))

    ## load in already processed

    print('Grabbing all of the split flowlines')
    ## Loop through all split flowlines.
    fcListLines = arcpy.ListFeatureClasses("*_0",feature_type="line")
    mappings = []
    for fcListLine in fcListLines: 
        mappings.append([HYDRO_NET_TRACE_Network,fcListLine,ws])
    
    print(f'There are {len(mappings)} split flowlines to process')
    logger.info(f'There are {len(mappings)} split flowlines to process')

    # ## Create the pool and specify the number of CPUs to use 
    process_count = process_count_to_use
    pool = Pool(processes=int(process_count))
    ## Map the items in the feature_data_set dictionary to the inFDS_processing function and process
    pool.map(preform_hazard_trace, mappings)
    ## close the pool when finished
    pool.close()
    ## bring it all back together
    pool.join()
    
    
    print(f'Finished processing all hazzard layers at {datetime.now()}. Taking a break for 1 minute before moving all output generated into 1 FGDB')
    
    time.sleep(60)
    # output_fgdb = create_fgdb(os.path.dirname(ws), 'AllTraceOutputs_BCM_July26_v2')
    output_trace_files = []
    failed_files = []
    print(f'Moving {len(os.listdir(output_trace_dir))} files to {ws}')
    for x in os.listdir(output_trace_dir):
        ## Temporarily set that as the workspace
        arcpy.env.workspace=os.path.join(output_trace_dir,x)        
        try: 
            to_copy=arcpy.ListFeatureClasses(wild_card = 'tempTrace_*')[0]
            arcpy.management.CopyFeatures(to_copy, os.path.join(ws, to_copy))
        except Exception as e: 
            print(f'Failed to copy data in {os.path.join(output_trace_dir,x)} --> error is {e}')
            failed_files.append(os.path.join(output_trace_dir,x))
            pass
        else: 
            print(f'Moved {to_copy}')

    print(f'Finished iterating all generated file geodatabases. The total number of failed copies was {len(failed_files)}')
    for failed in failed_files: 
        print(f'The failed files were {failed}')

    end = datetime.now()
    print(f'Total time in main is: {end-strt}')

