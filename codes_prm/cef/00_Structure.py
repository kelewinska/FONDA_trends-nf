# +
# :Description: Creates folder structure for cef processing
#
# :AUTHOR: Katarzyna Ewa Lewinska
# :DATE: 22 March 2022
# :VERSION: 1.0
# :UPDATES: 17 Apr 2026: nf revisited changes 
# -

# :ENVIRONMENT: #
import os
import sys


# :INPUTS: #
if sys.argv[1] is None:
    parentDir = (r'/data/Dagobah/fonda/grassdata/nf_trend_revisited/')  # parent directory
else:
    parentDir = (sys.argv[1])


lvl3Folder = 'level3'   # main output folder

lowerDir = os.path.join(parentDir, lvl3Folder)

# check whether the lower dir exists and create one if needed
if os.path.exists(lowerDir) is False:
    os.mkdir(lowerDir)

# create, if needed, the output files structure
if os.path.exists(os.path.join(lowerDir,'gv')) is False:
    os.mkdir(os.path.join(lowerDir,'gv'))

if os.path.exists(os.path.join(lowerDir,'npv')) is False:
    os.mkdir(os.path.join(lowerDir,'npv'))

if os.path.exists(os.path.join(lowerDir,'soil')) is False:
    os.mkdir(os.path.join(lowerDir,'soil'))

if os.path.exists(os.path.join(lowerDir,'shade')) is False:
    os.mkdir(os.path.join(lowerDir,'shade'))


# :END OF THE CODE: #