import os
import sys
import shutil
import glob
import time
import datetime
from threading import Thread
import threading
import shutil
import queue
import concurrent.futures
import numpy as np
import pickle
import matplotlib.pyplot as plt
import multiprocessing as mp
import requests

from helpers.helpers import GetDataHeader, GetDataBody, plot_3D, plotHeatmap, test


checkingTime = datetime.datetime.fromtimestamp(0)

sourcePath = "C:\\Projects\\AI Modeling\Data\Sunsan\\void"
destPath = "C:\\Projects\\backGroundTask\\data"
AI_url = 'http://172.26.242.101:5001/data-portal-image-file'

lock = threading.Lock()


def scanFileToSend(path, destPath):
    # checkingTime = datetime.datetime.now()
    global checkingTime
    filesPath = path
    if not os.path.exists(filesPath):
        print("The source folder '" + filesPath +
              "' does not exist!!\n")
    else:
        # listOfFile = os.listdir(filesPath)
        # listOfFile.sort(key=os.path.getctime)

        list_of_files = filter(lambda x: os.path.isfile(os.path.join(filesPath, x)),
                               os.listdir(filesPath))
        # Sort list of files based on last modification time in ascending order
        list_of_files = sorted(list_of_files,
                               key=lambda x: os.path.getctime(
                                   os.path.join(filesPath, x)), reverse=True
                               )
        for file in list_of_files:
            _file = os.path.join(filesPath, file)
            fileCreationTime = datetime.datetime.fromtimestamp(
                os.path.getctime(_file))
            if (fileCreationTime > checkingTime):
                shutil.copy(_file, destPath)
            else:
                pass

    checkingTime = datetime.datetime.now()


def preprocessing():
    for fname in os.listdir(destPath):
        if (fname.endswith('.dat')):
            fpath = os.path.join(destPath, fname)
            fpath = fpath.replace('\\', '/')
            _f = open(fpath, 'rb')
            _f.close()
            _f = open(fpath, 'rb')
            _f.read(58)
            databody = GetDataBody(_f)

            result = []
            # converting databody into [60 seconds x 128 phases x 60 periods] format
            for point in databody:
                temp = [[point[i*128+j]
                         for j in range(128)] for i in range(60)]
                result.append(temp)

            picklefile = open(fpath.replace('.dat', '.p'), 'wb')
            pickle.dump(result, picklefile)

            picklefile.close()
            _f.close()
            os.remove(fpath)


def generatingImage():
    try:
        for fname in os.listdir(destPath):
            if (fname.endswith('.p')):
                fpath = os.path.join(destPath, fname)
                pfile = open(fpath, 'rb')

                datpfilePath = fpath.replace('.p', '.dat')

                datpfilePath = datpfilePath.replace('\\', '/')
                # os.remove(datpfilePath)
                datapoint = np.array(pickle.load(pfile))
                i = 0
                for i in range(60):  # Output per second graphs of the pickle files
                    # if pfilename.replace('.p', '_' + str(i) + '.png') not in png_files:
                    newFname = fname.replace(
                        '.p', '_' + str(i) + '.png')
                    plot_3D(datapoint[i], destPath + '\\' + newFname)
                    i += 1
                    # plotHeatmap(datapoint[i], destPath + '\\' + newFname)

                pfile.close()
                fpath = fpath.replace('\\', '/')
                os.remove(fpath)

    except ValueError:
        print(ValueError)


def sendFileToAI():
    print('send file')
    for fname in os.listdir(destPath):
        if (fname.endswith('.png')):
            fpath = os.path.join(destPath, fname)
            fpath = fpath.replace('\\', '/')
            files = {'file': open(fpath, 'rb')}
            r = requests.post(AI_url, files=files)
            files.clear()
            if (r.status_code == 200):
                os.remove(fpath)


def cleanFolder():
    pfiles = glob.glob('./*.p')
    dfiles = glob.glob('./*.dat')
    png_files = glob.glob('./*.png')
    fileList = pfiles + dfiles + png_files
    for f in fileList:
        try:
            os.remove(f)
        except OSError as e:
            print("Error: %s : %s" % (f, e.strerror))


def executeScanFile():
    while (True):
        scanFileToSend(sourcePath, destPath)
        time.sleep(5)


def executeProcessingFile():
    while (True):
        preprocessing()
        time.sleep(5)


def executeSendFileToAI():
    while (True):
        sendFileToAI()
        # cleanFolder()
        time.sleep(5)


def executeGeneratingImage():
    while (True):
        generatingImage()
        time.sleep(5)


def threadInit():
    print('thread start...')
    listfunc = [executeScanFile, executeProcessingFile, executeGeneratingImage,
                executeSendFileToAI]
    for func in listfunc:
        t = threading.Thread(target=func)
        t.start()


def main():
    print('start...')

    threadInit()
    # p1 = mp.Process(target=threadInit)
    # p1.start()
    # p = mp.Process(target=executeGeneratingImage)
    # p.start()

    '''

    pool = concurrent.futures.ThreadPoolExecutor(max_workers=16)
    pool.submit(executeScanFile)
    pool.submit(executeProcessingFile)
    pool.submit(executeGeneratingImage)
    pool.submit(executeSendFileToAI)
    pool.shutdown(wait=True)
    '''

    # scan = threading.Thread(target=executeScanFile)
    # send = threading.Thread(target=executeSendFileToAI)


if __name__ == "__main__":
    main()
