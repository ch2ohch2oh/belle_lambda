# Reconstruct Lambda0:mdst usign B2BII and write variables to rootfiles
# This version is more structured

import basf2 as b2
import modularAnalysis as ma
import b2biiConversion as b2c
import b2biiMonitors as b2m
import sys

def print_env():
    """Print relevant env variables"""
    import os
    envlist = ['BELLE2_EXTERNALS_DIR', 'BELLE2_EXTERNALS_SUBSIR',
               'BELLE2_EXTERNALS_OPTION', 'BELLE2_EXTERNALS_VERSION',
               'BELLE2_LOCAL_DIR', 'BELLE2_OPTION', 
               'BELLE_POSTGRES_SERVER', 'USE_GRAND_REPROCESS_DATA',
               'PANTHER_TABLE_DIR', 'PGUSER']
    print('ENV START'.center(80, '='))
    for v in envlist:
        print("%30s = %s" % (v, os.getenv(v)))
    print('ENV END'.center(80, '='))

def reconstructLambda(outlist, match = False, only = None, path = None):
    """Reconstruct Lambda based on Lambda0:mdst
    
    outlist:
        Output particle list name. You can use for example 'Lambda0:belle'
    match:
        Perform MC truth match or not
    only:
        If only == 'signal', then only keep matched signal
        If only == 'background', then only keep background
        Otherwise, no further cuts.
        This option is for generating balanced training samples
    """
    if path == None:
        raise Exception('Path cannot be None!')
    if outlist == 'Lambda0:mdst':
        raise Exception('outlist name cannot be Lambda0:mdst')
        
    inlist = 'Lambda0:mdst'
    ma.vertexTree(inlist, path = path)
    if match:
        ma.matchMCTruth(inlist, path = path)
        if only == 'signal':
            ma.cutAndCopyList(outlist, inlist, 'isSignal == 1', path = path)
        elif only == 'background':
            ma.cutAndCopyList(outlist, inlist, 'isSignal == 0', path = path)
        else:
            ma.cutAndCopyList(outlist, inlist, '', path = path)

def make_ntuple():
    from variables import variables as va
    from variables.utils import create_aliases_for_selected
    
    va.addAlias('PIDppi', 'atcPIDBelle(4,2)')
    va.addAlias('PIDpk', 'atcPIDBelle(4,3)')
    va.addAlias('PIDkpi', 'atcPIDBelle(3,2)')
    # Lambda vertex position relative to IP
    va.addAlias('abs_dz', 'abs(dz)')
    # va.addAlias('abs_dr', 'abs(dr)')
    va.addAlias('cosaXY', 'cosAngleBetweenMomentumAndVertexVectorInXYPlane')
    # Track parameters relative to IP
    # d0 and z0 are relative to the origin!
    va.addAlias('min_dr', 'min(abs(daughter(0, dr)), abs(daughter(1, dr)))')
    va.addAlias('min_dz', 'min(abs(daughter(0, dz)), abs(daughter(1, dz)))')
    
    """Create a list of all the variables to be included in the final ntuple"""
    ntuple = []
    # May have more feature than needed. 
    features = ['dr', 'dz', 'cosaXY', 'min_dr', 'min_dz', 'pt', 'pz', 'chiProb', 'p']
    features += create_aliases_for_selected(['PIDppi', 'PIDpk', 'PIDkpi', 'p'],
                                            'Lambda0 -> ^p+ ^pi-',
                                            prefix = ['proton', 'pi'])
    spectator = ['isSignal' ,'isPrimarySignal', 'mcPDG', 'genMotherPDG']
    spectator += ['IPX', 'IPY', 'IPZ', 'M', 'p', 'goodBelleLambda', 'distance']
    ntuple = features + spectator
    return ntuple

if __name__ == '__main__':
    infile, outfile = sys.argv[1], sys.argv[2]
    mypath = b2.create_path()
    b2c.convertBelleMdstToBelleIIMdst(infile, path = mypath)
    reconstructLambda('Lambda0:belle', match = True, only = 'background', path = mypath)
    ntuple = make_ntuple()
    ma.variablesToNtuple('Lambda0:belle', ntuple, 'Lambda', outfile, path = mypath)
    
    b2.process(path = mypath)
