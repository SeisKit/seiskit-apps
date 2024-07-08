import pandas as pd
import re
import base64

class AT2:
    
    # init function
    def __init__(self, fileContents):
        
        # read file
        contentType, contentString = fileContents.split(',')
        decoded = base64.b64decode(contentString)
        self.lines = decoded.decode('utf-8').split('\n')
            
    def metadata(self):

        # extract metadata
        self.metadataLine = self.lines[1].strip().split(',')
        self.location = self.metadataLine[0].strip()
        self.date = self.metadataLine[1].strip()
        self.orientation = self.metadataLine[-1].strip()
        
        metadata = [self.location, self.date, self.orientation]
        
        return metadata
    
    def accdata(self):
        
        # extract npts and dt
        self.nptsdtLine = self.lines[3].strip()
        
        # Using regular expressions to extract NPTS and DT values
        self.nptsMatch = re.search(r'NPTS\s*=\s*(\d+)', self.nptsdtLine)
        self.dtMatch = re.search(r'DT\s*=\s*([.\d]+)\s*SEC', self.nptsdtLine)

        if self.nptsMatch and self.dtMatch:
            self.npts = int(self.nptsMatch.group(1))
            self.dt = float(self.dtMatch.group(1))
        else:
            raise ValueError("NPTS or DT information is missing or in an unexpected format.")
        
        # extract acceleration data
        self.accelerationData = []
        for line in self.lines[4:]:
            values = line.strip().split()
            for value in values:
                self.accelerationData.append(float(value))

        # check if the number of acceleration points matches NPTS
        if len(self.accelerationData) != self.npts:
            raise ValueError(f"Number of acceleration points ({len(self.accelerationData)}) does not match NPTS ({self.npts})")

        self.timeValues = [i * self.dt for i in range(self.npts)]

        accData = pd.DataFrame({
            'Time (s)': self.timeValues,
            'Acceleration (g)': self.accelerationData
        })
        
        return accData

class ASC:
    
    # init function
    def __init__(self, fileContents):
        
        # read file
        contentType, contentString = fileContents.split(',')
        decoded = base64.b64decode(contentString)
        self.lines = decoded.decode('utf-8').split('\n')
        
        # init metadata
        self.metadataDict = {}
    
    def metadata(self):
        
        # extract metadata
        metadataLines = []
        
        for line in self.lines:
            # check if the line contains a valid numerical value
            if re.match(r'^-?\d+(\.\d+)?$', line.strip()):
                break
            metadataLines.append(line.strip())
        
        for line in metadataLines:
            if ':' in line:
                key, value = line.split(':', 1)
                self.metadataDict[key.strip()] = value.strip()
        
        return self.metadataDict
    
    def accdata(self):
        # find where the acceleration data starts
        dataStartIndex = 0
        for i, line in enumerate(self.lines):
            # check if the line contains a valid numerical value
            if re.match(r'^-?\d+(\.\d+)?$', line.strip()):
                dataStartIndex = i
                break
        
        # extract acceleration data
        self.accelerationData = []
        for line in self.lines[dataStartIndex:]:
            line = line.strip().replace(',', '.')
            if line:  # Skip empty lines
                try:
                    self.accelerationData.append(float(line))
                except ValueError:
                    print(f"Skipping invalid line: {line}")
        
        # extract sampling interval and number of data points from metadata
        self.dt = float(self.metadataDict.get('SAMPLING_INTERVAL_S', 0.01))
        self.ndata = int(self.metadataDict.get('NDATA', len(self.accelerationData)))
        
        # check if the number of acceleration points matches NDATA
        if len(self.accelerationData) != self.ndata:
            raise ValueError(f"Number of acceleration points ({len(self.accelerationData)}) does not match NDATA ({self.ndata})")
        
        self.timeValues = [i * self.dt for i in range(self.ndata)]
        
        accData = pd.DataFrame({
            'Time (s)': self.timeValues,
            'Acceleration (cm/s^2)': self.accelerationData
        })
        
        return accData
    