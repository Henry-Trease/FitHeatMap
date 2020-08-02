#!/usr/bin/env python
import os,sys
import math
from fitparse import FitFile

## Global var
ESP = 0.00001
POINT_LIMIT = 3


if len(sys.argv) <= 1:
    print("Error: Please provide a file to process")
    exit()
#filename = sys.argv[1]
path = sys.argv[1]

################ Functions ################

def writeLayer(htmlFile, layerFormArray, coordArray, routeID, color):
    #color is an array: [r,g,b,t]
    for i in layerFormArray:

        i = i.replace("<r>", str(color[0]))
        i = i.replace('<g>', str(color[1]))
        i = i.replace('<b>', str(color[2]))
        i = i.replace('<t>', str(color[3]))
        i = i.replace('<ID>', str(routeID))

        if i.find("<<< Place Coords Here >>>") == -1:
            htmlFile.write(i)
        else:
            for j in coordArray:
                if not j == "Break":
                    htmlFile.write("[" + str(j[1]) + ", " + str(j[0]) + "],\n")

### Returns the places new layers should be created and the hits per segment
def searchSplit(arr):
    splitArr = [[0,arr[0][2]]]
    key = arr[0][2]
    count = 0
    for i in arr:
        if i == "Break":
            splitArr.append([count, key])
        else:
            if not i[2] == key:
                splitArr.append([arr.index(i)-1,key])
                key = i[2]
        count += 1
    splitArr.append([len(arr), arr[-2][2]])
    return splitArr

### finds an array of the indexes of every item in arr that match the key. Can select which column in 2d array to search
def finder(arr, key, index):
    retIndex = []
    for i in arr:
        if not i == "Break":
            if abs(i[index] - key) < ESP:
              retIndex.append(arr.index(i))
    return retIndex

### Returns a color array, moved to lookup table because it was faster
def colorFinder(index, trans):
    if str(index).isdigit():
        if index < 2:
            return [0, 0, 255, trans]
        elif index < 3:
            return [0, 255, 0, trans]
        else:
            return [255, 0, 0, trans]
    else:
        return [0, 255, 255, trans]   

    '''if index < 2:
        return [153, 204, 255, trans]
    elif index < 3:
        return [102, 178, 255, trans]
    elif index < 4:
        return [51, 153, 255, trans]
    elif index < 5:
        return [0, 126, 255, trans]
    elif index < 6:
        return [0, 102, 204, trans]
    else:
        return [0, 76, 153, trans]'''

### Looks for points that are close to eacheother and combines them
def condenser(arr):
    length = len(arr)
    tempArr = []
    for i in arr:
        if len(tempArr) == 0:
            tempArr.append(i)
            continue
        if not i == 'Break':
            tempBool = 0
            for j in tempArr:
                if not j == 'Break':
                    dist = math.hypot(i[1]-j[1], i[0]-j[0])
                    if dist < 0.0001:
                        j[2]+=1
                        tempBool = 1
                        continue
            if tempBool == 0:
                tempArr.append(i)
        else:
            print("Condensed another file. Up to " + str(len(tempArr)) + " points")
            tempArr.append(i)
    return tempArr

################ Main ################

htmlFile = open("heatMapDisplay.html", 'w')

coordArray = []
numPoints = 0

lat = 0.0
lon = 0.0

count = 0

files = os.listdir(path)
#for filename in files:

for filename in files:
    if filename[0] == '.': ## ignore hidden files
        continue
    print("Processing file: "+ filename)
    fitfile = FitFile(path + filename)
    #fitfile = FitFile(filename)
    for record in fitfile.get_messages('record'):
        for record_data in record:
            #print(record_data)
            if record_data.units:
                if(record_data.name == "position_lat" and record_data.value != None):
                    lat = record_data.value*(180.0/2.0**31)
                if(record_data.name == "position_long" and record_data.value != None):
                    lon = record_data.value*(180.0/2.0**31)
                if(lat != 0.0 and lon != 0.0):
                    pointArray = [lat, lon, 1]
                    if count > POINT_LIMIT: ## cuts down the number of points
                        coordArray.append(pointArray)
                        numPoints += 1
                        count = 0
                    count += 1

                    lat = 0.0 # reset lat, long values
                    lon = 0.0
    coordArray.append("Break")
#for i in coordArray:
#    print i
#print("\n\n")
#print("Condensing array. There are " + str(len(coordArray))+ " points")
coordArray = condenser(coordArray)
#print("Condensing array. There are " + str(len(coordArray))+ " points")
#print("\n\n")
#for i in coordArray:
#    print i
#print("\n\n")

# Finish writing the html 
print("Writing to file")
lineNum = 0
layerFormArray = []

# Add the template lines to setup mapbox
with open("jsTemplates/layerTemplate.html", 'r') as layerForm:
    layerLine = layerForm.readline()
    while layerLine:
        layerFormArray.append(layerLine)
        layerLine = layerForm.readline()

with open("jsTemplates/mapTemplate.html", 'r') as htmlForm:
    line = htmlForm.readline()
    while line:
        if not line.find("<<< Add layer here >>>") == -1:
            line = htmlForm.readline() # read another line to skip the '<<< Place Coords Here >>>' key
            
            splitArr = searchSplit(coordArray) ## splitArr[x][0] = place in coordArray to create new layer, splitArr[x][1] = number of hits on that segment 

            for i in range(1, len(splitArr)):
                #color = colorFinder(i, 0.5)
                color = colorFinder(splitArr[i][1], 0.5)
                print("Route"+str(i), color, splitArr[i-1][0], splitArr[i][0], splitArr[i][1])
                writeLayer(htmlFile, layerFormArray, coordArray[splitArr[i-1][0]:splitArr[i][0]], "Route"+str(i), color)

        htmlFile.write(line)
        line = htmlForm.readline()
        lineNum+=1

print("Finished processing " + str(numPoints) + " points. Created heatMapDisplay.html")
htmlFile.close()        
