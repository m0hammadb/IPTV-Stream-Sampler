from errno import EROFS
from fileinput import filename
import requests
import shutil
import datetime
from typing import *
from channel import *
import os
import re
from datetime import *

def add_log(text:str) -> None:
    with open("log.txt","a",encoding="utf-8") as writer:
        writer.write(text + "\n")

def download_stream_url(url,timeToDownload,fileName):
    try:
        local_filename = fileName
        
        with requests.get(url, stream=True,verify=False,timeout=20) as streamReader:
            startTime = datetime.now()
            with open(local_filename, 'wb') as fileWriter:
                for s in streamReader.iter_content(chunk_size=128):
                    
                    fileWriter.write(s)
                    currentTime = datetime.now()
                    passedTime = (currentTime - startTime).seconds
                    if(passedTime >= timeToDownload):
                        break
        
        if(os.stat(fileName).st_size <= 512000):
            os.remove(fileName)
            return False                
    except Exception as ex:
        add_log(f"Error on {fileName}, Text: {ex}, URL: {url}")
        return False
            

    return True
checkUrlDict={}
def check_url(url):
    global checkUrlDict
    if(get_iptv_base_address(url) in checkUrlDict):
        if checkUrlDict[get_iptv_base_address(url)] == 1:
            return True
        
        if checkUrlDict[get_iptv_base_address(url)] <= -10:
            return False
    else:
        checkUrlDict[get_iptv_base_address(url)] = 0
    print("Checking: " + url)
    try:
        with requests.get(url, stream=True,verify=False,timeout=10) as streamReader:
            for s in streamReader.iter_content(chunk_size=128):
                print("PASSED!")
                checkUrlDict[get_iptv_base_address(url)] = 1
                return True
        print("FAILED")
        checkUrlDict[get_iptv_base_address(url)] -= 1
        return False
    except Exception as ex:
        print("FAILED")
        checkUrlDict[get_iptv_base_address(url)] -= 1
        return False

def read_all_channels(inputFile:str,searchQueryList:List[str],noDupes = False,dupeDict={}) -> List[IptvChannel]:
    
    lst = []
    with open(inputFile,encoding="utf-8") as reader:
        fileContent = reader.read()
        lines = fileContent.split("\n")
        startLine = -1
        while True:
            startLine += 1
            if(startLine >= len(lines)):
                return []
            if(lines[startLine].startswith("#EXTINF")):
                break
        
        for i in range(startLine,len(lines)-1,2):
            fileUrl = lines[i+1]
            nameLine = lines[i]
            nameO = re.search(r'#EXTINF:-1,(.*)', nameLine)
            nameO2 = re.search(r'tvg-name="(.*?)"',nameLine)
            if(nameO == None and nameO2 == None):
                continue
            if(nameO):
                name = nameO.group(1)
            if(nameO2):
                name = nameO2.group(1)
            nameSplitter = fileUrl.split("/")
            if(nameSplitter[-1].find(".mp4") != -1 or nameSplitter[-1].find(".mkv") != -1 ):
                continue
            name = name.replace(":","").replace("|","")
            for searchQuery in searchQueryList:
                if(name.lower().find(searchQuery.lower()) > -1):
                    if(noDupes):
                        if(name.lower() in dupeDict):
                            break
                    if(check_url(fileUrl)):
                        dupeDict[name.lower()] = 1
                        channel = IptvChannel(fileUrl,name)
                        lst.append(channel)
                        break
    
    return lst

def get_new_folder():
    currentFolder = 1
    while True:
        if(os.path.exists(str(currentFolder))):
            files = os.listdir(str(currentFolder))
            if(files):
                currentFolder += 1
            else:
                break
        else:
            os.mkdir(str(currentFolder))
            break
    
    return str(currentFolder)

def move_mp4_files(toDirectory):
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for f in files:
        if(f.lower().endswith(".mp4")):
            shutil.move(f,f"{toDirectory}/{f}")

def get_search_queries():
    lst = []
    with open("search.txt") as reader:
        for line in reader:
            lst.append(line.replace("\n",""))
    return lst


def read_all_m3u_channels(queries,noDupes=False):
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    dupeDict = {}
    lst = []
    for f in files:
        if(f.lower().endswith(".m3u")):
            lst.extend(read_all_channels(f,queries,noDupes,dupeDict))
    return lst
def get_iptv_base_address(fullAddress:str):
    spl = fullAddress.split("/")
    r = "" 
    for i in range(len(spl) - 1):
        r += spl[i] + "/"
    return r
def main():  
    newFolder = get_new_folder()
    move_mp4_files(newFolder)
    #channels = read_all_channels("channels5.m3u",get_search_queries())
    channels = read_all_m3u_channels(get_search_queries(),True)
    print(channels)
    errorDict = {}

    while True:
        i = 0
        errorCount = 0
        from time import sleep
        for channel in channels:
            sleep(1)
            i += 1
            baseAddress = get_iptv_base_address(channel.url)
            if(baseAddress not in errorDict):
                errorDict[baseAddress] = {"error":0,"total":0,"average_error":0}
            else:
                if(errorDict[baseAddress]["average_error"] >= 0.5):
                    errorCount += 1
                    continue

            
                    
            os.system("cls")
            
            print("Base Address: " + baseAddress)
            print("Full Address: " + channel.url)
            print("Error Count: " + str(errorDict[baseAddress]))
            print(f"[{i}/{len(channels)}]Recording: " + channel.fileName)
            startTime = datetime.now()
            nextFile = ""

            while True:
                nextFile = channel.get_next_file_name()
                if(not os.path.exists(nextFile)):
                    break
            
            result = download_stream_url(channel.url,20,nextFile)

            passedTime = datetime.now() - startTime

            if result == False or passedTime.seconds >= 60:
                errorDict[baseAddress]["error"] += 1
            errorDict[baseAddress]["total"] += 1
            if(errorDict[baseAddress]["total"] >= 10):
                errorDict[baseAddress]["average_error"] = errorDict[baseAddress]["error"] / errorDict[baseAddress]["total"]
        if errorCount == len(channels):
            errorDict = {}
    add_log("while true broken!")
main()
#add_log("Main broken")

