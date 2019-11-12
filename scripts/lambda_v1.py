# Reconstruct Lambda0 using B2BII
# 
# Dazhi W.
import basf2 as b2
import modularAnalysis as ma
import b2biiConversion as b2c
import b2biiMonitors as b2m
import os
import sys

from variables import variables
from variables.utils import create_aliases_for_selected
from variables.utils import create_aliases
import variables.collections as vc

b2c.setupB2BIIDatabase(isMC = True)

def print_env(var):
	"""Print environmental variable."""
	print("%30s = %s" % (var, os.getenv(var)))

env_list = ['BELLE2_EXTERNALS_DIR',
	'BELLE2_EXTERNALS_SUBSIR',
	'BELLE2_EXTERNALS_OPTION',
	'BELLE2_EXTERNALS_VERSION',
	'BELLE2_LOCAL_DIR',
	'BELLE2_OPTION',
	'BELLE_POSTGRES_SERVER',
	'USE_GRAND_REPROCESS_DATA',
	'PANTHER_TABLE_DIR',
	'PGUSER']

# Print env variables for check
print("Environmental Variables".center(80, '='))
for v in env_list:
	print_env(v)

# Show input and output file info
print("Input: %s" % sys.argv[1])
print("Ouput: %s" % sys.argv[2])

mp = b2.create_path()

b2c.convertBelleMdstToBelleIIMdst(sys.argv[1], applyHadronBJSkim=True, path=mp)

variables.addAlias('pid_ppi', 'atcPIDBelle(4,2)')
variables.addAlias('pid_pk', 'atcPIDBelle(4,3)')
variables.addAlias('pid_kpi', 'atcPIDBelle(3,2)')

variables.addAlias('cosa', 'cosAngleBetweenMomentumAndVertexVector')
variables.addAlias('cosaXY', 'cosAngleBetweenMomentumAndVertexVectorInXYPlane')
variables.addAlias('goodLambda', 'extraInfo(goodLambda)')

variables.addAlias('abs_dz', 'abs(dz)')
variables.addAlias('abs_dr', 'abs(dr)')

variables.addAlias('min_daug_d0', 'abs(min(daughter(0, d0), daughter(1, d0)))')
variables.addAlias('min_daug_z0', 'abs(min(daughter(0, z0), daughter(1, z0)))')

list_mc = ['isSignal', 'isPrimarySignal', 'mcPDG', 'genMotherPDG', 'mcE', 'mcP', 'mcPT',
          'genParticleID', 'genMotherID']
list_basics = ['M', 'p', 'pt', 'pz']
list_lambda = ['distance', 'abs_dr', 'abs_dz', 'chiProb', 'cosa', 'cosaXY',
               'min_daug_d0', 'min_daug_z0',
               'goodBelleLambda', 'goodLambda']
list_pid = ['pid_ppi', 'pid_pk', 'pid_kpi']
list_event = ['IPX', 'IPY', 'IPZ']

# Variables
# =============================================
# Lambda0
list_ntuple = list_basics + list_lambda + list_event + list_mc
# proton and pion
list_ntuple += create_aliases_for_selected(list_basics + list_pid + list_mc,
                                           'Lambda0 -> ^p+ ^pi-', prefix = ['p', 'pi'])

# Reconstruction
# ==============================================
# No reconstruction. Just MC match the Lambda0:mdst list
ma.vertexTree('Lambda0:mdst', 0, path = mp)
ma.matchMCTruth('Lambda0:mdst', path = mp)
ma.applyCuts('Lambda0:mdst', 'isSignal == 0', path = mp)

# Output
# =============================================
mp.add_module('VariablesToNtuple', particleList='Lambda0:mdst', variables=list_ntuple,
              treeName='lambda', fileName=sys.argv[2])

b2.process(path=mp)

print(b2.statistics)
