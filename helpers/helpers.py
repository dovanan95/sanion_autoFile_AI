from matplotlib.backends.backend_agg import FigureCanvasAgg
import os
import sys
import struct
import pickle
import glob
# import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import time
import json
import ipaddress
import seaborn as sns
import pylab as plt
import psutil
plt.switch_backend('agg')

pactconversion = {"CHAR1": "<c", "INT4": "<i", "FLOAT4": "<f", "CHAR50": ""}
bytesizeconversion = {"FLOAT4": 4, "INT4": 4,
                      "CHAR1": 1, "CHAR50": 50, "FLOAT12": 48}
datatypes = ["FLOAT4", "INT4", "CHAR50", "INT4", "CHAR1", "FLOAT4", "CHAR1", "INT4", "INT4", "INT4", "CHAR1", "CHAR1", "CHAR1",
             "CHAR1", "CHAR1", "FLOAT12", "INT4", "INT4", "CHAR1", "FLOAT4", "FLOAT4", "FLOAT4", "FLOAT4", "CHAR1", "FLOAT4", "FLOAT4"]
datacolumns = ["File_Version", "Time_Of_Creation", "Sensor_Info", "IP_Address", "Target_Equipment", "Target_Voltage", "Sensor_Type", "Center_Frequency", "Bandwidth", "Channel_Codes", "Status_Of_Equipment", "Status_Of_Data", "Types_of_Discharge", "Alarm_Level", "Discharge_Type_Percentage_Flag",
               "Percantages_For_Discharges", "Number_Of_Phases", "Number_Of_Frequencies_Or_Periods", "Units_Of_Measurement", "Max_Intensity_Of_Discharge", "Average_Intensity_Of_Discharge", "Relativity_To_60hz", "Relativity_To_120hz", "Wave_Type", "Min_Range_Of_Frequency_Detection", "Max_Range_Of_Frequency_Detection"]


def GetDataHeader(file):
    '''
    Get the headers from an event file
    '''
#   file = open(FileName, 'rb')
    databuf = []
    output = []
    for type in datatypes:
        if type == "FLOAT12":
            for i in range(1, 13):
                bytes = file.read(4)
                trans = struct.unpack("<f", bytes)
                databuf.append(trans[0])
            output.append(databuf)
            continue
        elif type == "CHAR1":
            bytes = file.read(1)
            trans = struct.unpack("b", bytes)
            output.append(trans[0])
            continue
        bytes = file.read(bytesizeconversion[type])
        format = pactconversion[type]
        if format:
            trans = struct.unpack(format, bytes)
            # print("type : {}, Big Endian : {} --> Little Endian : {}".format(type, bytes, trans[0]))
            output.append(trans[0])
        else:
            output.append(-1)
    return output


def GetDataBody(file):
    '''
    Processes the .dat and extracts the requisite data
    '''
    # print("length of a data is {}" .format(len(file)))

    phases = 128
    periods = 60
    prpschunk = phases * periods
    totalbuf = []
    min = 60
    _data = file.read(1)
    # trans = struct.unpack("B", data)
    for i in range(min):
        databuf = []
        for j in range(prpschunk):
            data = file.read(1)
            trans = struct.unpack("B", data)
            # print('trans', i, j, trans, data)
            if trans[0] != 0:
                databuf.append(float(trans[0]*55/(-255)))
            else:
                databuf.append(0)
        totalbuf.append(databuf)
    return totalbuf


def plot_3D(data, name):
    # Set up grid and test data
    nx, ny = 60, 128
    x = range(nx)
    y = range(ny)

    data = np.array(-1*data)

    hf = plt.figure(figsize=(10, 10))
    ha = hf.add_subplot(111, projection='3d')
    ha.set_axis_off()

    # `plot_surface` expects `x` and `y` data to be 2D
    X, Y = np.meshgrid(x, y)
    ha.plot_surface(X.T, Y.T, data)

    plt.savefig(name)  # Save the plots
    plt.close()


def plotHeatmap(data, name):
    graph = sns.heatmap(data, cbar=False, xticklabels=False, yticklabels=False)
    fig = graph.get_figure()
    fig.savefig(name)


def scatter_density(packets, name):
    print("Data is being plotted...")
    x_coor = []
    y_coor = []
    for i in range(len(packets)):
        sec_result = packets[i]
        for pe in range(len(packets)):
            for ph in range(128):
                dbm = sec_result[pe][ph]
                x_coor.append(ph)
                y_coor.append(dbm)

    y_coor = [i*25/51 for i in y_coor]
    px = 1/plt.rcParams['figure.dpi']  # pixel in inches
    plt.subplots(figsize=(224*px, 224*px))

    plt.plot(x_coor, y_coor, '.', color='grey', alpha=.5, markersize=2)
    plt.axis([-10, 365, -55, 0])
    # 0 : With scale, 1: Without Scale
    if 1:
        # Selecting the axis-X making the bottom and top axes False.
        plt.tick_params(axis='x', which='both', bottom=False,
                        top=False, labelbottom=False)

        # Selecting the axis-Y making the right and left axes False
        plt.tick_params(axis='y', which='both', right=False,
                        left=False, labelleft=False)

        # Iterating over all the axes in the figure
        # and make the Spines Visibility as False
        for pos in ['right', 'top', 'bottom', 'left']:
            plt.gca().spines[pos].set_visible(False)

    plt.savefig(name.replace('.p', '.png'))
    plt.close()


def test():
    print('test')
