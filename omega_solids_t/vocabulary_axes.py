from __future__ import annotations
from itertools import product

TOPOLOGIES = ('dense_bulk','layered','fiber_network','particle_network','open_cell','closed_cell','hierarchical_lattice','interpenetrating_network')
ORDER_CLASSES = ('periodic','quasiperiodic','polycrystalline','nanocrystalline','amorphous','semicrystalline','jammed','programmed_nonequilibrium')
ARCHITECTURES = tuple({
    'index': i,
    'id': f'arch-{topology}-{order}',
    'name': f"{topology.replace('_',' ')} / {order.replace('_',' ')}",
    'topology': topology,
    'order_class': order,
    'hierarchy_depth': 1 + (i % 4),
    'dimensionality': ('3D','2D','1D','effective-3D')[i % 4],
} for i,(topology,order) in enumerate(product(TOPOLOGIES,ORDER_CLASSES)))

DEFECT_PROFILES = (
 {'id':'defect-pristine-reference','kinds':(),'criticality':0.02,'mobility':'none'},
 {'id':'defect-vacancy-dilute','kinds':('vacancy',),'criticality':0.12,'mobility':'thermally_activated'},
 {'id':'defect-interstitial-dilute','kinds':('interstitial',),'criticality':0.14,'mobility':'thermally_activated'},
 {'id':'defect-substitutional-disorder','kinds':('substitution','chemical_disorder'),'criticality':0.18,'mobility':'slow'},
 {'id':'defect-dislocation-network','kinds':('dislocation',),'criticality':0.32,'mobility':'stress_activated'},
 {'id':'defect-grain-boundary-rich','kinds':('grain_boundary',),'criticality':0.28,'mobility':'temperature_dependent'},
 {'id':'defect-stacking-faults','kinds':('stacking_fault',),'criticality':0.24,'mobility':'limited'},
 {'id':'defect-porosity-dilute','kinds':('pore',),'criticality':0.30,'mobility':'fixed'},
 {'id':'defect-porosity-connected','kinds':('pore','percolating_void'),'criticality':0.56,'mobility':'fixed'},
 {'id':'defect-inclusion-population','kinds':('inclusion',),'criticality':0.38,'mobility':'fixed'},
 {'id':'defect-microcrack-population','kinds':('microcrack',),'criticality':0.72,'mobility':'propagating'},
 {'id':'defect-residual-stress','kinds':('residual_stress',),'criticality':0.44,'mobility':'relaxing'},
 {'id':'defect-electronic-traps','kinds':('electronic_trap',),'criticality':0.26,'mobility':'charge_state_dependent'},
 {'id':'defect-interface-debonding','kinds':('interface_debonding',),'criticality':0.68,'mobility':'propagating'},
 {'id':'defect-energetic-cascade','kinds':('vacancy','interstitial','cluster'),'criticality':0.63,'mobility':'history_temperature_dependent'},
 {'id':'defect-multiscale-critical','kinds':('pore','microcrack','residual_stress'),'criticality':0.88,'mobility':'coupled'},
)
PROCESS_PROFILES = (
 {'id':'process-equilibrium-growth','steps':('feedstock','growth','slow_cooling'),'temperature_class':'controlled'},
 {'id':'process-rapid-solidification','steps':('melt','quench'),'temperature_class':'rapid_transient'},
 {'id':'process-powder-consolidation','steps':('powder','compaction','sintering'),'temperature_class':'sintering'},
 {'id':'process-additive-layerwise','steps':('feedstock','layer_deposition','localized_energy','cooling'),'temperature_class':'cyclic_gradient'},
 {'id':'process-solution-deposition','steps':('solution','nucleation','drying','anneal'),'temperature_class':'low_to_moderate'},
 {'id':'process-polymerization-cure','steps':('mixing','polymerization','cure'),'temperature_class':'reaction_controlled'},
 {'id':'process-deformation-heat-treatment','steps':('forming','work_hardening','anneal'),'temperature_class':'thermomechanical'},
 {'id':'process-biogenic-assembly','steps':('precursor','templating','growth','remodeling'),'temperature_class':'ambient_nonequilibrium'},
)
ENVIRONMENT_PROFILES = (
 {'id':'env-ambient-dry','temperature_K':298.15,'pressure_Pa':101325.0,'medium':'dry_air'},
 {'id':'env-humid-reactive','temperature_K':323.15,'pressure_Pa':101325.0,'medium':'humid_reactive'},
 {'id':'env-thermal-extreme','temperature_K':1073.15,'pressure_Pa':101325.0,'medium':'oxidizing_or_inert_unspecified'},
 {'id':'env-field-loaded','temperature_K':298.15,'pressure_Pa':101325.0,'medium':'electric_magnetic_mechanical_fields'},
)
MECHANISM_CATEGORIES = ('elastic','plastic','fracture','thermal','electronic','ionic','magnetic','optical')
MECHANISM_VARIANTS = ('local','collective','interface_controlled','defect_controlled','transport_limited','kinetic','multiscale','nonequilibrium')
MECHANISMS = tuple({
    'index':i,
    'id':f'mech-{category}-{variant}',
    'category':category,
    'variant':variant,
    'required_evidence':('units','baseline','uncertainty','domain_of_validity'),
} for i,(category,variant) in enumerate(product(MECHANISM_CATEGORIES,MECHANISM_VARIANTS)))
