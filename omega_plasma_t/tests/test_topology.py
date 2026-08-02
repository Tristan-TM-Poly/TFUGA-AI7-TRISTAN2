from omega_plasma_t.topology import audit_cartesian_field
def test_uniform_field():
    f=[[[ (1.0,0.0,0.0) for k in range(4)] for j in range(4)] for i in range(4)]
    a=audit_cartesian_field(f,1,1,1); assert a.divergence_linf==0 and a.status=="passed"
