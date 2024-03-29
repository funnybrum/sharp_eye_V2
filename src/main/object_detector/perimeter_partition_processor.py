import requests

class PerimeterPartitionProcessor(object):
    def process(self, video_file, scores, frames_with_objects):
        if 'person' in scores and scores['person'] > 0.75:
            requests.get("http://localhost:8080/hss/control/motion")
