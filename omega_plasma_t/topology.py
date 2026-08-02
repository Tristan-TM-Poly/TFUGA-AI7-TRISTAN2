"""Discrete magnetic-topology diagnostics on structured vector fields."""
from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
Vector=tuple[float,float,float]
def dot(a:Vector,b:Vector)->float: return sum(x*y for x,y in zip(a,b))
def norm(a:Vector)->float: return sqrt(dot(a,a))
@dataclass(frozen=True)
class TopologyAudit:
    divergence_l1:float; divergence_linf:float; magnetic_energy_proxy:float; null_count:int; cell_count:int; status:str

def audit_cartesian_field(field:list[list[list[Vector]]],dx:float,dy:float,dz:float,null_tolerance:float=1e-12)->TopologyAudit:
    if min(dx,dy,dz)<=0: raise ValueError("grid spacings must be positive")
    nx=len(field); ny=len(field[0]) if nx else 0; nz=len(field[0][0]) if ny else 0
    if min(nx,ny,nz)<3: raise ValueError("field must contain at least 3 points on every axis")
    divs=[]; energy=0.0; nulls=0
    for i in range(nx):
      for j in range(ny):
       for k in range(nz):
        b=field[i][j][k]; energy+=0.5*dot(b,b); nulls+=norm(b)<=null_tolerance
    for i in range(1,nx-1):
      for j in range(1,ny-1):
       for k in range(1,nz-1):
        divs.append((field[i+1][j][k][0]-field[i-1][j][k][0])/(2*dx)+(field[i][j+1][k][1]-field[i][j-1][k][1])/(2*dy)+(field[i][j][k+1][2]-field[i][j][k-1][2])/(2*dz))
    l1=sum(abs(x) for x in divs)/len(divs); li=max(abs(x) for x in divs)
    return TopologyAudit(l1,li,energy,int(nulls),nx*ny*nz,"passed" if li<1e-8 else "review")
