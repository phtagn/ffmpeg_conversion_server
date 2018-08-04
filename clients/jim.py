from processor import processor
from helpers.helpers import breakdown
from configuration import CfgMgr
import glob
import os
import logging
import sys
log = logging.getLogger()
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)



cfgmgr = CfgMgr()
cfgmgr.load('defaults.ini')


input = "/Volumes/Downloads-1/Les.Aventures.de.Tintin.COMPLETE.MULTi.1080p.BluRay.HDLight.x265-H4S5S"
outputpath = "/Volumes/Films/Enfants/Tintin"

if os.path.isfile(input):
    path_elements = breakdown(input)
    outputpath = outputpath if outputpath else path_elements['dir']
    outputfile = os.path.join(outputpath, f'{path_elements["file"]}.mp4')
    p = processor.Processor(cfgmgr.cfg, input, outputfile, 'mp4')
    p.process()




if os.path.isdir(input):
    thefiles = glob.glob(os.path.join(input, '*.mkv'))
    for afile in thefiles:
        path_elements = breakdown(afile)
        outputpath = outputpath if outputpath else path_elements['dir']
        outputfile = os.path.join(outputpath, f'{path_elements["file"]}.mp4')
        p = processor.Processor(cfgmgr.cfg, afile, outputfile, 'mp4')
        p.process()