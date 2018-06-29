import configuration
from converter_v2.streams import AudioStreamTemplate, VideoStreamTemplate, SubtitleStreamTemplate
"""Processes a video file in steps:
1) Analyse video file
2)
2) Build templates from options"""
class Processor(object):


    def build_templates(self, cfg):
