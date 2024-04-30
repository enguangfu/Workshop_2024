#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pickle, lzma                         # for data import
import numpy as np
import scipy.integrate as spint             # for ode solver
from jLM.Solvers import  makeSolver         # to build custom solver
from lm import IntMpdRdmeSolver
from jLM.RDME import Sim as RDMESim         # create RDME simulation obj
from jLM.RDME import File as RDMEFile       # deal with final results
from jLM.RegionBuilder import RegionBuilder # to build the spatial geometry
import jLM


# # 1. Spatial Geometry Import
# 
# Here, we directly import the regions data for the analysis, we extract and extrapolate the yeast geometry from cryo-ET data from Tyler Earnest, et al., Phy. Chem. B, 2017.doi:[10.1021/acs.jpcb.7b00672](http://dx.doi.org/10.1021/acs.jpcb.7b00672).
# 
# ![yeast_geo](../images/yeast_geo.gif)
# 
# The geometry of yeast includes 9 regions in total: 
# + nucleus envelope
# + cytoplasm
# + vacuole
# + mitochondria
# + ribosomes
# + plasm membrane
# + cell wall
# + extracellular region
# + nucleoplasm

# In[2]:


latticeData = pickle.load(lzma.open("./supporting_data/yeast-lattice.pkl.xz", "rb"))

siteMap = {n:i for i,n in enumerate(latticeData['names'])}
def boolLattice(x):
    return latticeData['lattice'] == siteMap[x]

# here we extract the region as 3 dimensional bool matrices.

extracellular = boolLattice("extracellular") #| boolLattice("cellWall")
wall = boolLattice("cellWall")
boundary = boolLattice("boundary")
nenv = boolLattice("nuclearEnvelope")
mito = boolLattice("mitochondria")
vac = boolLattice('vacuole')
ribosomes = boolLattice("ribosomes")
membrane = boolLattice("plasmaMembrane")
nucleus = boolLattice("nucleoplasm") # | boolLattice("nuclearPores")
pores = boolLattice("nuclearPores")
cytoplasm = boolLattice("cytoplasm")
# This is the decimation of the latice 
decimation = latticeData['decimation']


# # 2.Create simulation object

# In[3]:


sim = RDMESim("Galactose Switch, RDME/ODE hybrid",
              "T3-Galactose_swtich_yeast.lm",
              latticeData['lattice'].shape,
              latticeData['latticeSpacing'],
              "extracellular",
              dt=50e-6)


# put the region into the simulation object.

# In[4]:


B = RegionBuilder(sim)

B.compose((sim.region('extracellular'), extracellular),
          (sim.region('nuclearEnvelope'), nenv),
          (sim.region('mitochondria'), mito),
          (sim.region('vacuole'), vac),
          (sim.region('plasmaMembrane'), membrane),
          (sim.region('cellWall'), wall),
          (sim.region('cytoplasm'), cytoplasm),
          (sim.region('nucleoplasm'), nucleus),
          (sim.region('nuclearPores'), pores),
          (sim.region('ribosomes_region'), ribosomes))
# (sim.region('obstructions'), obstructions),


# In[5]:


sim.displayGeometry()


# ## 2.2 Simulation parameters

# In[6]:


sim.simulationTime= 10 # 1s
sim.timestep = 50e-6    # 50us, units: s
sim.latticeWriteInterval=2000 # .1s
sim.speciesWriteInterval=2000 # .1s
sim.hookInterval= 2000 #.1s

# define the external Galactose concentration here
externalGal = 11.1e-3 # M
nRibosomes = np.sum(sim.siteLattice==sim.reg.ribosomes_region.idx)
mrnaDiffusion = 0.5e-12


# define some variables for species, regions, rate constants and diffusion coefficients access.

# In[7]:


sp = sim.sp   # species object access
reg = sim.reg # region object access
rc = sim.rc   # rate constant object access
dc = sim.dc   # diffusion constant object access


# # 3. Species Initialization

# ## Reporter system

# In[8]:


with sim.construct():
    #sim.species(name,textRepr, annotation)
    sim.species('DGrep', texRepr='D_{GFP}', annotation="Reporter gene")
    sim.species('DGrep_G4d', texRepr="D_{GFP}{:}G_{4D}", annotation="Activated reporter gene")
    sim.species('DGrep_G4d_G80d', texRepr="D_{GFP}{:}G_{4D}{:}G_{80D}", annotation="Repressed reporter gene")
    sim.species('Grep', texRepr="GFP", annotation="GFP reporter")
    sim.species('RGrep', texRepr="m_{GFP}", annotation="Reporter mRNA")


# ## GAL1

# In[9]:


with sim.construct():
    sim.species('R1',texRepr='m_1', annotation="GAL1 mRNA")
    sim.species('DG1', texRepr='D_{1}', annotation="GAL1 gene")
    sim.species('DG1_G4d', texRepr="D_{1}{:}G_{4D}", annotation="Activated GAL1 gene")
    sim.species('DG1_G4d_G80d', texRepr="D_{1}{:}G_{4D}{:}G_{80D}", annotation="Repressed GAL1 gene")
    sim.species('G1', texRepr="G_1", annotation="Gal1p [galactokinase]")


# ## GAL2

# In[10]:


with sim.construct():
    sim.species('R2',texRepr='m_2', annotation="GAL2 mRNA")
    sim.species('DG2', texRepr='D_{2}', annotation="GAL2 gene")
    sim.species('DG2_G4d', texRepr="D_{2}{:}G_{4D}", annotation="Activated GAL2 gene")
    sim.species('DG2_G4d_G80d', texRepr="D_{2}{:}G_{4D}{:}G_{80D}", annotation="Repressed GAL2 gene")
    sim.species('G2', texRepr="G_2", annotation="Gal2p [permease]")


# ## GAL3

# In[11]:


with sim.construct():
    sim.species('R3',texRepr='m_3', annotation="GAL3 mRNA")
    sim.species('DG3', texRepr='D_{3}', annotation="GAL3 gene")
    sim.species('DG3_G4d', texRepr="D_{3}{:}G_{4D}", annotation="Activated GAL3 gene")
    sim.species('DG3_G4d_G80d', texRepr="D_{3}{:}G_{4D}{:}G_{80D}", annotation="Repressed GAL3 gene")
    sim.species('G3', texRepr="G_3", annotation="Gal3p [transcriptional regulator]")
    sim.species('G3i', texRepr="G^\star_3", annotation="Activated Gal3p (galactose bound)")


# ## GAL4

# In[12]:


with sim.construct():
    sim.species('DG4',texRepr='D_4', annotation="GAL4 gene")
    sim.species('R4',texRepr='m_4', annotation="GAL4 mRNA")
    sim.species('G4', texRepr="G_4", annotation="Gal4p monomer")
    sim.species('G4d', texRepr="G_{4D}", annotation="Gal4p dimer [transcription factor]")


# ## GAL80

# In[13]:


with sim.construct():
    sim.species('R80',texRepr='m_{80}', annotation="GAL80 mRNA")
    sim.species('DG80', texRepr='D_{80}', annotation="GAL80 gene")
    sim.species('DG80_G4d', texRepr="D_{G80}{:}G_{4D}", annotation="Activated GAL80 gene")
    sim.species('DG80_G4d_G80d', texRepr="D_{G80}{:}G_{4D}{:}G_{80D}", annotation="Repressed GAL80 gene")
    sim.species('G80', texRepr="G_{80}", annotation="Gal80p monomer") 
    sim.species('G80d', texRepr="G_{80D}", annotation="Gal80p dimer [inhibits Gal4p]")
    sim.species('G80G3i', texRepr="G_{80D}{:}G^\star_3", annotation="Complex of Gal3p(activated) and Gal80Cd")


# ## Dummy mRNA
# 

# In[14]:


with sim.construct():
    sim.species('Rdummy', texRepr="m_d", annotation='Dummy mRNA')


# ## Ribosomes

# for reaction to take place, we also define ribosomes species for certain translation to take place. 
# 
# Different mRNA requires different ribosome types to start the translation

# In[15]:


with sim.construct():
    sim.species('ribosome', texRepr="R", annotation="Inactive ribosome")
    sim.species('ribosomeD', texRepr="R{:}m_d", annotation="Ribosome translating dummy mRNA")
    sim.species('ribosomeG1', texRepr="R{:}m_1", annotation="Ribosome translating GAL1")
    sim.species('ribosomeG2', texRepr="R{:}m_2", annotation="Ribosome translating GAL2")
    sim.species('ribosomeG3', texRepr="R{:}m_3", annotation="Ribosome translating GAL3")
    sim.species('ribosomeG4', texRepr="R{:}m_4", annotation="Ribosome translating GAL4")
    sim.species('ribosomeG80', texRepr="R{:}m_{80}", annotation="Ribosome translating GAL80")
    sim.species('ribosomeGrep', texRepr="R{:}m_{GFP}", annotation="Ribosome translating GFP")


# # 4. Reaction Initialization
# 
# all the rate constants are from appendix in the paper David M. Bianchi, et al., IET, 2018. 
# 
# doi: [10.1049/iet-syb.2017.0070](https://doi.org/10.1049/iet-syb.2017.0070)
# 
# Since the units of the rates constant are in units   ${min}^{-1}$ or ${molecules}^{-1}\cdot {min}^{-1}$, we need to convert them to $s^{-1}$ or $M^{-1}\cdot s^{-1}$.

# In[16]:


cellVol = 3.57e-14 # L
nav = cellVol*6.022e23  #Navogadro's number * cell volume
invMin2invSec = 1/60.0 # s^-1/min^-1
conv2ndOrder = invMin2invSec*nav # convert to s^-1*M^-1, 2nd order reactions
conv1stOrder = invMin2invSec # convert to s^-1, 1st order reactions


# ## Dimerization

# 
# define all the reactions with type:
# $$ X + X \rightleftharpoons X_d $$
# 
# Remember LM only supports irreversible reactions, so: 
# $$ X + BX \xrightarrow{k_{fd}} X_d $$
# $$ X_d \xrightarrow{k_{rd}} X + X$$
# Dimerization can happen in `cytoplasm` and `nucleoplasm`.

# In[17]:


with sim.construct():
    #sim.rateConst("fd", 0.001*conv2ndOrder, order=2, annotation="Gal4p/Gal80p dimerization")
    #sim.rateConst("rd", 100*conv1stOrder, order=1, annotation="Gal4p/Gal80p dimer dissociation")
    sim.rateConst("fd", 100*conv2ndOrder, order=2, annotation="Gal4p/Gal80p dimerization !!Transposed!!")
    sim.rateConst("rd", 0.001*conv1stOrder, order=1, annotation="Gal4p/Gal80p dimer dissociation !!Transposed!!")
    sim.reaction([sp.G4, sp.G4], [sp.G4d], rc.fd, regions=[reg.cytoplasm, reg.nucleoplasm])
    sim.reaction([sp.G4d], [sp.G4, sp.G4], rc.rd, regions=[reg.cytoplasm, reg.nucleoplasm])
    sim.reaction([sp.G80, sp.G80], [sp.G80d], rc.fd, regions=[reg.cytoplasm, reg.nucleoplasm])
    sim.reaction([sp.G80d], [sp.G80, sp.G80], rc.rd, regions=[reg.cytoplasm, reg.nucleoplasm])


# ## DNA binding

# DNA binding related reactions only happen in `nucleoplasm`.
# 
# 
# First type is DNA bind to $G_{4d}$ to activate the DNA:
# 
# $$ DNA_X + G_{4d} \xrightarrow{k_{f1}} DNA_x\_G_{4d} $$
# $$ DNA_x\_G_{4d} \xrightarrow{k_{r1}} DNA_X + G_{4d}$$
# 
# Second type is Activated DNA bind to $G_{80d}$, to repress the transcription:
# 
# $$ DNA_x\_G_{4d} + G_{80d} \xrightarrow{k_{f2}} DNA_x\_G_{4d}\_G_{80d} $$
# $$ DNA_x\_G_{4d}\_G_{80d} \xrightarrow{k_{r2}} DNA_x\_G_{4d} + G_{80d} $$

# In[18]:


with sim.construct():
    # deine all the rate constants here, rate  constants are defined 
    # based on the number of binding sites
    Kp4 = 0.2600 # 4 binding sites
    Kq4 = 1.1721 
    
    kf1_4 = 0.1
    kf2_4 = 0.1
    kr1_4 = kf1_4/Kp4
    kr2_4 = kf2_4/Kq4
    
    Kp5 = 0.0099 # 5 binding sites
    Kq5 = 0.7408 
    
    kf1_5 = 0.1
    kf2_5 = 0.1
    kr1_5 = kf1_5/Kp5
    kr2_5 = kf2_5/Kq5
    
    
    Kp = 0.0248 # 1 binding site
    Kq = 0.1885 
    kf1 = 0.1
    kr1 = kf1/Kp
    kf2 = 0.1
    kr2 = kf2/Kq

    #convBinding = invMin2invSec*sim.siteNAV

    sim.rateConst("f1", kf1*conv2ndOrder, order=2, annotation="Gene/Gal4p binding [1 site]")
    sim.rateConst("r1", kr1*conv1stOrder, order=1, annotation="Gene/Gal4p dissociation [1 site]")
    sim.rateConst("f2", kf2*conv2ndOrder, order=2, annotation="Gene/Gal80p binding [1 site]")
    sim.rateConst("r2", kr2*conv1stOrder, order=1, annotation="Gene/Gal80p dissociation [1 site]")
    
    sim.rateConst("f1_4", kf1_4*conv2ndOrder, order=2, annotation="Gene/Gal4p binding [4 sites]")
    sim.rateConst("r1_4", kr1_4*conv1stOrder, order=1, annotation="Gene/Gal4p dissociation [4 sites]")
    sim.rateConst("f2_4", kf2_4*conv2ndOrder, order=2, annotation="Gene/Gal80p binding [4 sites]")
    sim.rateConst("r2_4", kr2_4*conv1stOrder, order=1, annotation="Gene/Gal80p dissociation [4 sites]")
    
    sim.rateConst("f1_5", kf1_5*conv2ndOrder, order=2, annotation="Gene/Gal4p binding [5 sites]")
    sim.rateConst("r1_5", kr1_5*conv1stOrder, order=1, annotation="Gene/Gal4p dissociation [5 sites]")
    sim.rateConst("f2_5", kf2_5*conv2ndOrder, order=2, annotation="Gene/Gal80p binding [5 sites]")
    sim.rateConst("r2_5", kr2_5*conv1stOrder, order=1, annotation="Gene/Gal80p dissociation [5 sites]")

    dnas =      [sp.DG1,          sp.DG2,          sp.DG3,          sp.DG80,          sp.DGrep]
    mrnas =     [sp.R1,           sp.R2,           sp.R3,           sp.R80,           sp.RGrep]
    dnaActs =   [sp.DG1_G4d,      sp.DG2_G4d,      sp.DG3_G4d,      sp.DG80_G4d,      sp.DGrep_G4d]
    dnaDeacts = [sp.DG1_G4d_G80d, sp.DG2_G4d_G80d, sp.DG3_G4d_G80d, sp.DG80_G4d_G80d, sp.DGrep_G4d_G80d]
    f1s =       [rc.f1_4,         rc.f1_5,         rc.f1,           rc.f1,            rc.f1_4]
    f2s =       [rc.f2_4,         rc.f2_5,         rc.f2,           rc.f2,            rc.f2_4]
    r1s =       [rc.r1_4,         rc.r1_5,         rc.r1,           rc.r1,            rc.r1_4]
    r2s =       [rc.r2_4,         rc.r2_5,         rc.r2,           rc.r2,            rc.r2_4]
    
    terms = zip(dnas,mrnas,dnaActs,dnaDeacts,f1s,f2s,r1s,r2s)
    for dna,mrna,dnaAct,dnaDeact,f1,f2,r1,r2 in terms:
        sim.reaction([dna,sp.G4d], dnaAct, f1, regions=reg.nucleoplasm)
        sim.reaction(dnaAct, [dna,sp.G4d], r1, regions=reg.nucleoplasm)
        sim.reaction([dnaAct,sp.G80d], dnaDeact, f2, regions=reg.nucleoplasm)
        sim.reaction(dnaDeact, [dnaAct, sp.G80d], r2, regions=reg.nucleoplasm)


# ## G3 activation

# Here we define the whole reactions for $G_3$:

# In[19]:


with sim.construct():
    sim.rateConst("fi", 7.45e-7*conv2ndOrder, order=1, annotation="Gal3p activation; needs to be multiplied by [GAI] in mol/L")
    sim.rateConst("ri", 890.0*conv1stOrder, order=1, annotation="Gal3p deactivation")
    sim.rateConst("fd3i80", 0.025716*conv2ndOrder, order=2, annotation="Gal3p*/Gal80 association")
    sim.rateConst("dr3i80", 0.0159616*conv1stOrder, order=1, annotation="Gal3p*/Gal80 disassociation")
    sim.rateConst("dp_gal3", 0.01155*conv1stOrder, order=1, annotation="GAL3 degradation")
    sim.rateConst("dp_gal3gal80", 0.5*rc.dp_gal3.value, order=1, annotation="Gal3p*:Gal80 degradation")

    #sim.reaction([sp.G3, sp.GAI], sp.G3i, rc.fi, regions=reg.cytoplasm)
    sim.reaction(sp.G3, sp.G3i, rc.fi, regions=reg.cytoplasm) # XXX Hybrid in RDME
    #sim.reaction(sp.G3i, [sp.G3, sp.GAI], rc.ri, regions=intracellular)
    sim.reaction(sp.G3i, sp.G3, rc.ri, regions=reg.cytoplasm) # XXX Modified in RDME
    sim.reaction(sp.G3i, [], rc.dp_gal3, regions=reg.cytoplasm)
    sim.reaction([sp.G3i, sp.G80d], [sp.G80G3i], rc.fd3i80, regions=reg.cytoplasm)
    sim.reaction([sp.G80G3i], [sp.G3i, sp.G80d], rc.dr3i80, regions=reg.cytoplasm)
    sim.reaction([sp.G80G3i], [], rc.dp_gal3gal80, regions=reg.cytoplasm)


# ## Transcription 

# Here we define the transcription reactions and mRNA degradation.
# + Transcription can happen in `nucleoplasm`.
# + mRNA degradation can happen in `cytoplasm`, `nucleoplasm` and `ribosomes`.
# 
# Two types of reactions are: (G1 as example)
# 
# $$
# \begin{aligned}
# D_1: G_{4 D} & \xrightarrow{k_{\text {alphal }}} D_1: G_{4 D}+m_1 \\
# m_1 & \xrightarrow{k_{\text {dr-gall }}} \varnothing
# \end{aligned}
# $$

# In[20]:


with sim.construct():
    sim.rateConst("alpha1", 0.7379*conv1stOrder, order=1, annotation='GAL1 transcription')
    sim.rateConst("alpha2", 2.542*conv1stOrder, order=1, annotation='GAL2 transcription')
    sim.rateConst("alpha3", 0.571429*0.7465*conv1stOrder, order=1, annotation='GAL3 transcription')
    sim.rateConst("ir_gal4", 0.009902*conv1stOrder, order=1, annotation='GAL4 transcription')
    sim.rateConst("alpha_rep", 1.1440*conv1stOrder, order=1, annotation='GFP transcription')
    sim.rateConst("alpha80", 0.6065*conv1stOrder, order=1, annotation='GAL80 transcription')

    sim.rateConst("dr_gal1", 0.02236*conv1stOrder, order=1, annotation='GAL1 mRNA degradation')
    sim.rateConst("dr_gal2", 0.07702*conv1stOrder, order=1, annotation='GAL2 mRNA degradation')
    sim.rateConst("dr_gal3", 0.02666*conv1stOrder, order=1, annotation='GAL3 mRNA degradation')
    sim.rateConst("dr_gal4", 0.02476*conv1stOrder, order=1, annotation='GAL4 mRNA degradation')
    sim.rateConst("dr_rep", 0.03466*conv1stOrder, order=1, annotation='GFP mRNA degradation')
    sim.rateConst("dr_gal80", 0.02888*conv1stOrder, order=1, annotation='GAL80 mRNA degradation')

    tss =   [rc.alpha1,   rc.alpha2,   rc.alpha3,   rc.ir_gal4,  rc.alpha_rep, rc.alpha80] 
    dcys =  [rc.dr_gal1,  rc.dr_gal2,  rc.dr_gal3,  rc.dr_gal4,  rc.dr_rep,    rc.dr_gal80]
    genes = [sp.DG1_G4d,  sp.DG2_G4d,  sp.DG3_G4d,  sp.DG4,      sp.DGrep_G4d, sp.DG80_G4d]
    mrnas = [sp.R1,       sp.R2,       sp.R3,       sp.R4,       sp.RGrep,     sp.R80]

    for ts,dcy,gene,mrna in zip(tss, dcys, genes, mrnas):
        sim.reaction(gene, [gene, mrna], ts, regions=reg.nucleoplasm)
        sim.reaction(mrna,[], dcy, regions=[reg.cytoplasm, reg.nucleoplasm, reg.ribosomes_region])
    otherMrna = 0.5*(6100+18300) #102988
    otherMrnaDecay = np.log(2)/60/20 # 100205
    tsOther = otherMrna*otherMrnaDecay/reg.nucleoplasm.volume/sim.NA
    
    sim.rateConst("dummyTs", tsOther, order=0, annotation='Dummy mRNA transcription')
    sim.rateConst("dummyDeg", otherMrnaDecay, order=1, annotation='Dummy mRNA degradation')
    sim.reaction([], sp.Rdummy, rc.dummyTs, regions=reg.nucleoplasm)
    sim.reaction(sp.Rdummy, [], rc.dummyDeg, regions=[reg.cytoplasm, reg.nucleoplasm, reg.ribosomes_region])


# ## Translation 

# reactions happen in `ribosome` region, and we also define ribosome as a particle in the region for the reaction purpose. 
# 
# First, ribosome has to bind with mRNA, and then start to translate to form the protein $G$ here. 
# 
# Also, mRNA might degrade in the ribosome as a complex.
# 
# $$
# 
# R+m \xrightarrow{k_{rib\_asox }} R: m \\
# R: m \xrightarrow{k_{pp\_gall }} R+m+G \\
# R: m \xrightarrow{k_{dr\_gall }} R
# 
# $$
# 
# 

# In[21]:


with sim.construct():
    #tlInitDet = 100e6 # 10.1016/j.molcel.2006.02.014 [eco]
    tlInitDet = 0.2 * 2000 * mrnaDiffusion * sim.NA * sim.latticeSpacing
    sim.rateConst("rib_assoc", tlInitDet, order=2, annotation='mRNA/Ribosome association rate') # TODO
    
    otherProtein = 5e7 #106198
    otherProtDecay = np.log(2)/60/43 # 104151
    tlOther = otherProtDecay*otherProtein/otherMrna
    sim.rateConst("dummyTl", tlOther, order=1, annotation="Dummy mRNA translation")

    sim.rateConst("ip_gal1", 1.9254*conv1stOrder, order=1, annotation='GAL1 translation')
    sim.rateConst("ip_gal2", 13.4779*conv1stOrder, order=1, annotation="GAL2 translation")
    sim.rateConst("ip_gal3", 55.4518*conv1stOrder, order=1, annotation="GAL3 translation")
    sim.rateConst("ip_gal4", 10.7091*conv1stOrder, order=1, annotation="GAL4 translation")
    sim.rateConst("ip_rep", 5.7762*conv1stOrder, order=1, annotation="GFP translation")
    sim.rateConst("ip_gal80", 3.6737*conv1stOrder, order=1, annotation="GAL80 translation")

    sim.rateConst("dp_gal1", 0.003851*conv1stOrder, order=1, annotation='GAL1 degradation')
    sim.rateConst("dp_gal2", 0.003851*conv1stOrder, order=1, annotation="GAL2 degradation")
    sim.rateConst("dp_gal3", 0.01155*conv1stOrder, order=1, annotation="GAL3 degradation")
    sim.rateConst("dp_gal4", 0.006931*conv1stOrder, order=1, annotation="GAL4 degradation")
    sim.rateConst("dp_rep", 0.01155*conv1stOrder, order=1, annotation="GFP degradation")
    sim.rateConst("dp_gal80", 0.006931*conv1stOrder, order=1, annotation="GAL80 degradation")

    ktls =                 [rc.ip_gal1,    rc.ip_gal2,    rc.ip_gal3,    rc.ip_gal4,    rc.ip_rep,       rc.ip_gal80]
    dcys =                 [rc.dp_gal1,    rc.dp_gal2,    rc.dp_gal3,    rc.dp_gal4,    rc.dp_rep,       rc.dp_gal80] 
    mdcys =                [rc.dr_gal1,  rc.dr_gal2,  rc.dr_gal3,  rc.dr_gal4,  rc.dr_rep,    rc.dr_gal80]
    translatingRibosomes = [sp.ribosomeG1, sp.ribosomeG2, sp.ribosomeG3, sp.ribosomeG4, sp.ribosomeGrep, sp.ribosomeG80]
    prots =                [sp.G1,         sp.G2,         sp.G3,         sp.G4,         sp.Grep,         sp.G80]
    compartments =         [[reg.ribosomes_region, reg.cytoplasm], 
                            [reg.ribosomes_region, reg.cytoplasm, reg.plasmaMembrane], 
                            [reg.ribosomes_region, reg.cytoplasm], 
                            [reg.ribosomes_region, reg.cytoplasm, reg.nucleoplasm], 
                            [reg.ribosomes_region, reg.cytoplasm], 
                            [reg.ribosomes_region, reg.cytoplasm, reg.nucleoplasm]]


    for mrna, translatingRibosome, prot, ktl, dcy,mdcy,rgs in zip(mrnas, translatingRibosomes, prots, ktls, dcys, mdcys,compartments):
        sim.reaction([sp.ribosome, mrna], [translatingRibosome], rc.rib_assoc, regions=reg.ribosomes_region)
        sim.reaction([translatingRibosome], [sp.ribosome, mrna, prot], ktl, regions=reg.ribosomes_region)
        sim.reaction([translatingRibosome], [sp.ribosome], mdcy, regions=reg.ribosomes_region)
    
    sim.reaction([sp.ribosome, sp.Rdummy], sp.ribosomeD, rc.rib_assoc, regions=reg.ribosomes_region)
    sim.reaction(sp.ribosomeD, [sp.ribosome, sp.Rdummy], rc.dummyTl, regions=reg.ribosomes_region)
    sim.reaction(sp.ribosomeD, sp.ribosome, rc.dummyDeg, regions=reg.ribosomes_region)
    


# ## Protein degradation

# $$
# G \xrightarrow{k_{dp\_gall }} \varnothing
# $$

# In[22]:


with sim.construct():
    sim.rateConst("dp_gal1", 0.003851*conv1stOrder, order=1, annotation='GAL1 degradation')
    sim.rateConst("dp_gal2", 0.003851*conv1stOrder, order=1, annotation="GAL2 degradation")
    sim.rateConst("dp_gal3", 0.01155*conv1stOrder, order=1, annotation="GAL3 degradation")
    sim.rateConst("dp_gal4", 0.006931*conv1stOrder, order=1, annotation="GAL4 degradation")
    sim.rateConst("dp_rep", 0.01155*conv1stOrder, order=1, annotation="GFP degradation")
    sim.rateConst("dp_gal80", 0.006931*conv1stOrder, order=1, annotation="GAL80 degradation")

    for prot, dcy,rgs in zip(prots, dcys, compartments):
        sim.reaction(prot,[], dcy, regions=rgs)


# ## ALL reactions

# In[23]:


sim.showReactions()


# # 5. Important Initial counts

# we load the initial mole concentration of each species and change it back to counts.
# 
# Then we use function `sp.species.placeNumberInto(jLm.region, counts)` to initialize the counts.

# In[24]:


# get the 
initMolec = pickle.load(open("./supporting_data/ysZeroGAE.pkl", "rb"))
volScale = np.sum(B.convexHull(sim.siteLattice==reg.plasmaMembrane.idx))*sim.siteV/cellVol
def initMol(x):
    # get the initial number of molecules from the mole
    v = int(initMolec[x]*volScale)
    print(x, v)
    return int(initMolec[x]*volScale)
# intialize the number of genes as 1 for all the genes
sp.DG4.placeNumberInto(reg.nucleoplasm, 1)
for b in ["DG1", "DG2", "DG3", "DGrep", "DG80"]:
    ops = [b+x for x in ["", "_G4d", "_G4d_G80d"]]
    spName = max(ops, key=lambda x:initMolec[x])
    print("{} in state {}".format(b, spName))
    sim.species(spName).placeNumberInto(reg.nucleoplasm, 1)
#place initial protein counts
sp.G1.placeNumberInto(reg.cytoplasm, initMol("G1"))
sp.G2.placeNumberInto(reg.plasmaMembrane, initMol("G2"))
sp.G3.placeNumberInto(reg.cytoplasm, initMol("G3"))
sp.G4d.placeNumberInto(reg.nucleoplasm, initMol("G4d"))
sp.Grep.placeNumberInto(reg.cytoplasm, initMol("Grep"))
# place one dummy mRNA for certain simulatin purposes
sp.Rdummy.placeNumberInto(reg.cytoplasm, int(otherMrna))
# get relative ratio of cytoplasm volume
cscl = reg.cytoplasm.volume/(reg.cytoplasm.volume+reg.nucleoplasm.volume)

# get totoal number of G80 and G80 d,
# _C means in the cytoplasm, G80 means in the nucleoplasm
totM = initMol("G80C") + initMol("G80")
totD = initMol("G80Cd") + initMol("G80d")
sp.G80.placeNumberInto(reg.cytoplasm, int(cscl*totM))
sp.G80.placeNumberInto(reg.nucleoplasm, int((1-cscl)*totM))
sp.G80d.placeNumberInto(reg.cytoplasm, int(cscl*totD))
sp.G80d.placeNumberInto(reg.nucleoplasm, int((1-cscl)*totD))
# place one ribosome particle in each ribosome region 
for x,y,z in np.argwhere(sim.siteLattice==reg.ribosomes_region.idx):
    sp.ribosome.placeParticle(x,y,z,1)


# # 6. Diffusion Initialization

# In[25]:


with sim.construct():
    sim.transitionRate(None, None, None, sim.diffusionZero)


# ## mRNA

# In[26]:


with sim.construct():
    sim.diffusionConst("mrna", mrnaDiffusion, texRepr=r'D_{mRNA}', annotation='Generic mRNA')

    for mrna in sim.speciesList.matchRegex("R.*"):
        sim.transitionRate(mrna, reg.nucleoplasm, reg.cytoplasm, dc.mrna)
        sim.transitionRate(mrna, reg.cytoplasm, reg.nucleoplasm, sim.diffusionZero)
        sim.transitionRate(mrna, reg.nucleoplasm, reg.nucleoplasm, dc.mrna)
        sim.transitionRate(mrna, reg.cytoplasm, reg.cytoplasm, dc.mrna)
        sim.transitionRate(mrna, reg.ribosomes_region, reg.ribosomes_region, dc.mrna)
        sim.transitionRate(mrna, reg.ribosomes_region, reg.cytoplasm, dc.mrna)
        sim.transitionRate(mrna, reg.cytoplasm, reg.ribosomes_region, dc.mrna)


# ## DNA
# 
# Gene locations fixed in space

# In[27]:


with sim.construct():
    for sps in sim.speciesList.matchRegex("D.*"):
        sps.diffusionRate(None, sim.diffusionZero)


# ## Ribosome occlusion

# In[28]:


with sim.construct():
    sim.diffusionConst("prot", 1e-12, texRepr=r'D_{prot}', annotation='Generic protein')
    for sps in [sp.G1, sp.G2, sp.G3, sp.G3i, sp.G4, sp.G4d, sp.G80, sp.G80d, sp.G80G3i, sp.Grep]:
        sps.diffusionRate(reg.cytoplasm, dc.prot)
        sim.transitionRate(sps, reg.ribosomes_region, reg.cytoplasm, sim.diffusionFast)
        sim.transitionRate(sps, reg.cytoplasm, reg.ribosomes_region, sim.diffusionZero)


# ## Transcription factors

# In[29]:


with sim.construct():
    for sps in [sp.G4d, sp.G4d, sp.G80, sp.G80d]:
        sps.diffusionRate(reg.nucleoplasm, dc.prot)
        sim.transitionRate(sps, reg.nucleoplasm, reg.cytoplasm, dc.prot)
        sim.transitionRate(sps, reg.cytoplasm, reg.nucleoplasm, dc.prot)


# ## Cytoplasmic protein

# In[30]:


with sim.construct():
    for sps in [sp.G1, sp.G2, sp.G3, sp.G3i, sp.G80G3i, sp.Grep]:
        sim.transitionRate(sps, reg.cytoplasm, reg.nucleoplasm, sim.diffusionZero) 


# ## Transporter

# In[31]:


with sim.construct():
    sim.transitionRate(sp.G2, reg.cytoplasm, reg.plasmaMembrane, dc.prot)
    sim.transitionRate(sp.G2, reg.plasmaMembrane, reg.cytoplasm, sim.diffusionZero)
    sim.diffusionConst("mem", 0.1e-12, texRepr=r'D_{mem}', annotation='Generic protein on membrane')
    sp.G2.diffusionRate(reg.plasmaMembrane, dc.mem)


# ## Ribosomes

# In[32]:


with sim.construct():
    for sps in sim.speciesList.matchRegex("ribosome.*"):
        sim.transitionRate(sps, None, None, sim.diffusionZero)


# Finish all initialization, show species:

# In[33]:


sim.showAllSpecies()


# # 7.RDME-ODE model

# Here we need to define a custom solver to include ode function.

# In[35]:


import pyximport
pyximport.install(setup_args={ "include_dirs":np.get_include()})
from ode import RHS


# In[36]:


class OdeRdmeHybridSolver:
    """Hybrid solver for Galactose switch
    
    Transport reactions and galactose metabolism handled by ODE, rest by RDME. The
    ODE system is coupled to the RDME by updating the protein counts in the ODE 
    each communication step. New proteins are added to the state unbound to
    galactose. If the number of proteins decreases, both bound and unbound 
    states are decreased by the same proportion and the galactose is
    added back as internal or external galactose. The RDME is coupled to the 
    ODE system through the internal galactose concentration. The rate of
    G3 -> G3i is updated with the internal galactose concentration each
    communication step."""
    def copyInitialConditions(self, cts):
        y = np.zeros(len(self.odeSpNames))
        y[self.odeSpIndex("GAI")] = 0
        y[self.odeSpIndex("G1")] = cts['countBySpecies'][self.rdme.sp.G1]/self.NAV # XXX think about which volume
        y[self.odeSpIndex("G1GAI")] = 0
        y[self.odeSpIndex("G2")] = cts['countBySpecies'][self.rdme.sp.G2]/self.NAV
        y[self.odeSpIndex("G2GAE")] = 0
        y[self.odeSpIndex("G2GAI")] = 0
        self.boundGal = self.rdmeGal(cts)
        return y
  
    def rdmeGal(self, cts):
        return (cts['countBySpecies'][self.rdme.sp.G3i] + cts['countBySpecies'][self.rdme.sp.G80G3i])/self.NAV

    def rdme2odeConc(self, y0, cts):
        y = y0.copy()
        
        g1ode = y0[self.odeSpIndex("G1")]
        g1gaiode = y0[self.odeSpIndex("G1GAI")]
        g1rdme = cts['countBySpecies'][self.rdme.sp.G1]/self.NAV
        
        change = g1rdme-g1ode-g1gaiode
        
        if change > 0:
            y[self.odeSpIndex("G1")] = g1ode + change
        else:
            fracChange = g1rdme/(g1ode+g1gaiode)
            y[self.odeSpIndex("G1")] = g1ode*fracChange
            y[self.odeSpIndex("G1GAI")] = g1gaiode*fracChange
            y[self.odeSpIndex("GAI")] += g1gaiode*(1-fracChange)
            
        
        g2ode = y0[self.odeSpIndex("G2")]
        g2gaiode = y0[self.odeSpIndex("G2GAI")]
        g2gaeode = y0[self.odeSpIndex("G2GAE")]
        g2rdme = cts['countBySpeciesRegion'][self.rdme.sp.G2][self.rdme.reg.plasmaMembrane]/self.NAV
        
        change = g2rdme-g2ode-g2gaiode-g2gaeode
        
        if change >= 0:
            y[self.odeSpIndex("G2")] = g2ode + change
        else:
            fracChange = g2rdme/(g2ode+g2gaiode+g2gaeode)
            y[self.odeSpIndex("G2")] = g2ode*fracChange
            y[self.odeSpIndex("G2GAI")] = g2gaiode*fracChange
            y[self.odeSpIndex("GAI")] += g2gaiode*(1-fracChange)
            y[self.odeSpIndex("G2GAE")] = g2gaeode*fracChange
            
        g0 = self.boundGal
        g1 = self.rdmeGal(cts)
        y[self.odeSpIndex("GAI")] += g1-g0
        self.boundGal = g1
            
        return y
  
        
    def __init__(self, lmFile, initialExternalGalactose):
        super(OdeRdmeHybridSolver, self).__init__()
        self.GAE = initialExternalGalactose
        self.odeYs = None
        self.lastOdeEval = 0
        self.odeEvals = []
        if isinstance(lmFile, (RDMEFile, RDMESim)):
            self.rdme = lmFile
        else:
            self.rdme = RDME.File(lmFile)
        self.cellVol = self.rdme.reg.cytoplasm.volume + self.rdme.reg.nucleoplasm.volume + self.rdme.reg.plasmaMembrane.volume
        self.NAV = 6.022e23*self.cellVol
        self.buildOdeSys(
                 [[["G1","GAI"],  ["G1GAI"],     1.442e5],
                  [["G1GAI"],     ["G1", "GAI"], 30.708],
                  [["G1GAI"],     ["G1"],        55.833],
                  [[                                                                                                                                                                                                                                                                                                                                                                                                                                                     "G2GAI"],     ["G2GAE"],     72.5],
                  [["G2GAE"],     ["G2GAI"],     72.5],
                  [["G2GAE"],     ["G2"], 39.875],
                  [["G2"],        ["G2GAE"],     1.123e5*self.GAE],
                  [["G2", "GAI"], ["G2GAI"],     1.123e5],
                  [["G2GAI"],     ["G2", "GAI"], 39.875]])
        
                  
        self.g3actRidx = self.rdme.reaction(self.rdme.sp.G3, self.rdme.sp.G3i, self.rdme.rc.fi).idx
        self.g3actRc = self.rdme.rc.fi._toLM()
     
                   
    def hookSimulation(self, t, lattice):
         
        cts = self.rdme.particleStatistics(particleLattice=lattice.getParticleLatticeView(),
                                           siteLattice=lattice.getSiteLatticeView())
        if self.odeYs is None:
            ys0 = self.copyInitialConditions(cts)
        else:
            ys0 = self.rdme2odeConc(self.odeYs, cts)
                   
        dt = t-self.lastOdeEval
        if dt>0:
            ys1 = self.stepOde(dt, ys0)
        else:
            ys1 = ys0
            
        self.odeEvals.append((t,ys1))
        self.odeYs = ys1
        self.lastOdeEval = t
            
        assocRt = self.g3actRc*ys1[self.odeSpIndex("GAI")]
        # print(self.rdme.reactionList[self.g3actRidx].rate.value)
        self.setReactionRate(self.g3actRidx, assocRt)
        # print(self.rdme.reactionList[self.g3actRidx].rate.value)
        print("="*80)
        print("t=",t)
        print("ODE")
        for i,n in enumerate(self.odeSpNames):
            print("  {:<16s}{:16.5g}".format(n,self.odeYs[i]))
        print("RDME")
        for n in self.rdme.speciesList:
            print("  {:<16s}{:16d}".format(n.name,cts['countBySpecies'][n]))
        print("new rate: {:.3g}".format(assocRt))
        print("-"*80)
        
        return 0

    def odeSpIndex(self, sp):
        return self.odeSpNames.index(sp)
    
    def buildOdeSys(self, rxns):
        odeSpNames = set()
        for react, prod, _ in rxns:
            odeSpNames |= set(prod) | set(react)
        nsp = len(odeSpNames)
        nrxn = len(rxns)
        stoch = np.zeros((nrxn, nsp), dtype=np.int32)
        dep = np.zeros((nrxn, nsp), dtype=np.int32)
        ks = np.zeros(nrxn, dtype=np.float64)
        self.odeSpNames = sorted(odeSpNames)
        for i, (react, prod, rate) in enumerate(rxns):
            ks[i] = rate
            for r in react:
                dep[i, self.odeSpIndex(r)] += 1
                stoch[i, self.odeSpIndex(r)] -= 1
            for p in prod:
                stoch[i, self.odeSpIndex(p)] += 1
        self.odeStoch = stoch
        self.odeDep = dep
        self.odeKs = ks
    
    def stepOde(self, t, ys0):
        rhs = RHS(self.odeStoch, self.odeDep, self.odeKs)
        ts = np.linspace(0,t, 10)
        ys = spint.odeint(rhs.evaluate, ys0, ts)
        return ys[-1,:]


# In[37]:


# create the custom solver class, and stantiating the solver
Solver = makeSolver(IntMpdRdmeSolver, OdeRdmeHybridSolver)
solver = Solver(sim, externalGal)


# In[38]:


sim.finalize()


# # 8. Start the Simulation

# In[39]:


try:
    traj = sim.run(solver=solver, cudaDevices=[1])
    
finally:
    # when it ends, also save the ode data.
    odeData = dict(ts=np.array([x[0] for x in solver.odeEvals]),
                   ys=np.array([x[1] for x in solver.odeEvals]),
                   names=solver.odeSpNames)
    pickle.dump(odeData, open(traj.filename+"_ode.pkl", "wb"))
