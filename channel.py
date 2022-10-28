class IptvChannel:
    def __init__(self,url,fileName):
        self.url = url 
        self.fileName = fileName
        self.counter = 0

    def get_next_file_name(self):
        self.counter += 1
        return f"{self.fileName}_{self.counter}.mp4"