# Reconstruct Lambda0 on Belle generic MC
# Only 1% of the unmatched candidates is kept to make the 
# signal background ratio close to 1:1
#
# This script takes two arguments: input_path output_path
#
import basf2 as b2
import modularAnalysis as ma
import b2biiConversion as b2c
import b2biiMonitors as b2m

from variables import variables as va
from variables.utils import create_aliases_for_selected

import sys
import os

b2c.setupB2BIIDatabase(isMC = True)

def print_env():
    """Print relevant env variables"""
    import os
    envlist = ['BELLE2_EXTERNALS_DIR', 'BELLE2_EXTERNALS_SUBSIR',
               'BELLE2_EXTERNALS_OPTION', 'BELLE2_EXTERNALS_VERSION',
               'BELLE2_LOCAL_DIR', 'BELLE2_OPTION', 'BELLE2_RELEASE', 
               'BELLE_POSTGRES_SERVER', 'USE_GRAND_REPROCESS_DATA',
               'PANTHER_TABLE_DIR', 'PGUSER']
    print('ENV START'.center(80, '='))
    for v in envlist:
        print("%30s = %s" % (v, os.getenv(v)))
    print('ENV END'.center(80, '='))

if __name__ == '__main__':
    infile, outfile = sys.argv[1], sys.argv[2]
    
    print_env()
    
    mp = b2.create_path()
    
    b2c.convertBelleMdstToBelleIIMdst(infile, path = mp)
    
    # Life is hard without aliases
    ntuple_vars = ['p', 'M', 'dr', 'distance', 'cosAngleBetweenMomentumAndVertexVectorInXYPlane', 'chiProb',
                   'daughter(0, p)', 'daughter(1, p)', 
                   'daughter(0, atcPIDBelle(4,2))', 'daughter(0, atcPIDBelle(4,3))', 'daughter(0, atcPIDBelle(3,2))',
                   'daughter(1, atcPIDBelle(4,2))', 'daughter(1, atcPIDBelle(4,3))', 'daughter(1, atcPIDBelle(3,2))',
                   'isSignal']
    ## Reconstruction
    bkg_frac = 0.01 # Used to downsample background
    ma.vertexTree('Lambda0:mdst', 0, path = mp)
    ma.matchMCTruth('Lambda0:mdst', path = mp)
    ma.cutAndCopyList('Lambda0:sig', 'Lambda0:mdst', 'isSignal == 1', path = mp)
    ma.cutAndCopyList('Lambda0:bkg', 'Lambda0:mdst', f'isSignal == 0 and random < {bkg_frac}', path = mp)
    ma.copyLists('Lambda0:balanced', ['Lambda0:sig', 'Lambda0:bkg'], path = mp)
    ma.variablesToNtuple('Lambda0:balanced', ntuple_vars, 'lambda', outfile, path = mp)
    
    b2.process(path = mp)
    print(b2.statistics)
