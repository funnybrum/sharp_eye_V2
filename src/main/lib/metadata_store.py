import glob
import os
import yaml

from lib import config


class MetadataStore(object):
    """
    Metadata storage. Exposes the following methods:
      1) Load all metadata
      2) Store metadata for a video file
      3) Get metadata for a video file

    Metadata is loaded when the storage is created. The metadata is not refreshed. If it needs to be refresh a new
    object must be created.

    Metadata is stored in YAML files in the snapshot folder. Each file contains metadata only for single day. Same logic
    for archiving video files can be applied to the metadata.
    """
    def __init__(self):
        self._metadata = {}
        self._metadata_folder = config['snapshots']['metadata']
        self._load_metadata()

    def _load_metadata(self):
        if not os.path.exists(self._metadata_folder):
            os.mkdir(self._metadata_folder)

        for metadata_file in glob.glob('%s/*.yaml' % self._metadata_folder):
            with open(metadata_file) as in_file:
                self._metadata.update(yaml.safe_load(in_file))

    def _get_objects_scores(self, frames_with_objects):  # noqa
        scores = {}
        for f in frames_with_objects:
            for obj in f['objects']:
                obj_type = obj['name']
                obj_score = obj['confidence']
                if obj_type not in scores or scores[obj_type] < obj_score:
                    scores[obj_type] = round(obj_score, 2)

        return scores

    def _get_adjusted_objects_scores(self, frames_with_objects):  # noqa
        scores = {}
        confidence_threshold = config['object_detection']['metadata_threshold']

        for f in frames_with_objects:
            for obj in f['objects']:
                obj_type = obj['name']
                obj_score = obj['confidence']
                if obj_type not in scores:
                    scores[obj_type] = 0
                scores[obj_type] += obj_score

        for obj_type, score in scores.items():
            scores[obj_type] = round(score / len(frames_with_objects), 2)

        scores = {k: v for k, v in scores.items() if v >= confidence_threshold}

        return scores

    def _get_metadata_filename(self, video_file):  # noqa
        metadata_filename = os.path.basename(video_file)[:10] + "-meta.yaml"
        return os.path.join(self._metadata_folder, metadata_filename)

    def _dump_metadata(self, video_file, metadata):
        metadata_file = self._get_metadata_filename(video_file)
        with open(metadata_file, "a") as out_file:
            yaml.dump(metadata, out_file)

    def _get_video_file_metadata_key(self, video_file):  # noqa
        camera = os.path.split(os.path.dirname(video_file))[-1]
        file_key = os.path.basename(video_file)[:-4]
        return '%s_%s' % (camera, file_key)

    def store_metadata(self, video_file, frames_with_objects):
        scores = self._get_adjusted_objects_scores(frames_with_objects)
        key = self._get_video_file_metadata_key(video_file)
        if key in self._metadata:
            raise RuntimeError("Duplicate metadata for %s is not supported." % key)
        self._metadata[key] = scores
        self._dump_metadata(video_file, {key: scores})

    def get_metadata(self, video_file):
        metadata_key = self._get_video_file_metadata_key(video_file)
        return self._metadata.get(metadata_key)
