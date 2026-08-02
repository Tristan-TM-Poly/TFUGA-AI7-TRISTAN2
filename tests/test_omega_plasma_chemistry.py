from omega_plasma_t.chemistry import Reaction,ReactionNetwork

def test_stoichiometry_and_nonnegative_integrator():
    net=ReactionNetwork([Reaction("ionize",{"e":1,"Ar":1},{"e":2,"Ar+":1},1e-14),Reaction("recombine",{"e":1,"Ar+":1},{"Ar":1},1e-13)])
    S=net.stoichiometric_matrix()
    assert S["e"]["ionize"]==1
    assert S["Ar+"]["recombine"]==-1
    hist=net.euler({"e":1e12,"Ar":1e14,"Ar+":1e8},1e-12,10)
    assert all(v>=0 for row in hist for v in row.values())
    assert net.audit()["status"]=="passed"
