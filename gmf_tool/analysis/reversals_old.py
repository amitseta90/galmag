""" This module is part of GMF tool
    Draft of reversal finding routines (for disk fields) """

import scipy.optimize as sci
import numpy as N
from os import path
import sys
sys.path.append( path.dirname( path.dirname( path.abspath(__file__))))
import core.disk as D



def get_B_phi(r, B1_B0, B2_B0, params):
    """ Computes B_phi in the case of a superposition of only 3 modes.
        Input: the r coordinate, the ratios of the coefficients B1/B0
        B2/B0 and parameters dict
    """
    from scipy.special import jn_zeros

    mu_n =  jn_zeros(1, 3)
    kn = mu_n
    phi =0
    z =0
    Br, Bphi0, Bz = D.get_B_disk_cyl_component(N.abs(r)/params['R_d'],
                                               phi, z, kn[0], params)
    Br, Bphi1, Bz = D.get_B_disk_cyl_component(N.abs(r)/params['R_d'],
                                               phi, z,kn[1], params)
    Br, Bphi2, Bz = D.get_B_disk_cyl_component(N.abs(r)/params['R_d'],
                                               phi, z, kn[2], params)

    return Bphi0 + B1_B0*Bphi1 + B2_B0*Bphi2


def find_reversals(B2_B0, B1_B0, params=None, return_number=False,
                             max_number_of_reversals=60, xtol=1e-4):
    """ Finds the number of reversals as a function of the ration between
    components.
    Input:
        B2_B0, B1_B0: the ratios B2/B0 and B1/B0
        params: parameters dicionary (but Cn will be ignored!)
      optional
        full_output: see output
        max_number_of_reversals: the maximum possible number of reversals
                                 considered
        xtol: the tolerance for the root finder
    """
    global contador

    # The initial guess is uniformly distributed
    initial_guess = N.linspace(1e-3,params['R_d'],max_number_of_reversals)

    roots, infodict, ler, msg = sci.fsolve(get_B_phi, initial_guess,
                       args=(B1_B0, B2_B0,params),
                       full_output=True, xtol=xtol)

    # Excludes the borders
    # TODO remove the magic numbers
    ok = roots > 0.05
    ok *= roots < params['R_d']-0.05

    # Removes repeated roots (fsolve will return 1 root per initial guess)
    # TODO This requirement of 4 decimals is rather arbitrary..
    reversals = N.unique(N.around(roots[ok],4))
    ok = reversals < params['R_d']
    reversals = reversals[ok]


    # Run it again, to avoid spurious solutions
    initial_guess = reversals
    roots, infodict, ler, msg = sci.fsolve(get_B_phi, initial_guess,
                       args=(B1_B0, B2_B0,params),
                       full_output=True, xtol=xtol)

    # Excludes the borders
    # TODO remove the magic numbers
    ok = roots>0.05
    ok *= roots<params['R_d']-0.05

    # Removes repeated roots (fsolve will return 1 root per initial guess)
    # TODO This requirement of 1 decimal is very arbitrary..
    reversals = N.unique(N.around(roots[ok],1))
    ok = reversals < params['R_d']
    reversals = reversals[ok]

    # Checks whether it is not something spurious
    # TODO remove the magic numbers
    real_reversal = N.zeros_like(reversals).astype(bool)
    for i, possible_rev in enumerate(reversals):
        plus = get_B_phi(possible_rev+0.1,B1_B0, B2_B0,params)
        minus = get_B_phi(possible_rev-0.1,B1_B0, B2_B0,params)
        if plus*minus < 0:
            real_reversal[i] = True

    reversals = reversals[real_reversal]

    # Plots solutions... for testing.. comment out or remove?
    if reversals.size>3:
        P.subplot(1,2,1)
        contador +=1
        r = N.linspace(0,params['R_d'],50)
        P.plot(r, get_B_phi(r, B1_B0, B2_B0, params),
                label='reversals: {2} B1/B0={0} B2/B0={1}'.format(
                    B1_B0, B2_B0,reversals.size))
        P.title(reversals)
        P.plot(r, N.zeros(r.shape), 'k:')
        P.legend(loc='lower left', frameon=False)
        P.xlabel('$r$')
        P.ylabel('$B_\phi$')

        P.subplot(1,2,2)
        P.xlabel('$r$')
        P.ylabel('$B_\phi$')

        mu_n =  jn_zeros(1, 3)
        kn = mu_n/params['R_d']
        phi =0
        z =0
        Br, Bphi0, Bz = get_B_disk_cyl_component(r,phi,z,kn[0], params)
        Br, Bphi1, Bz = get_B_disk_cyl_component(r,phi,z,kn[1], params)
        Br, Bphi2, Bz = get_B_disk_cyl_component(r,phi,z,kn[2], params)

        P.plot(r, Bphi0, label=r'$B_\phi^{(0)}$')
        P.plot(r, Bphi1, label=r'$B_\phi^{(1)}$')
        P.plot(r, Bphi2, label=r'$B_\phi^{(2)}$')
        P.legend(loc='lower left', frameon=False)
        P.show()
        print(B2_B0, B1_B0, reversals, reversals[1:]-reversals[:-1])

    if return_number:
        return reversals.size
    else:
        return reversals



def get_reversal_data(params=None, B2_B0_range=[-3,3], B1_B0_range=[-3,3],
                      n=35, processes=8,pool=None):
    """ Inputs (all optional):
          params: dictionary containing parameters (the values of Cn will be
            ignored)
          n: number of points to sample
          B2_B0_range: list containing range of values of B2/B0, e.g. [-1,1]
          B1_B0_range: list range of values of B1/B0
          processes: number of processors available for the calculation
        Output:
          B1_B0: nxn (grid) array containing B1/B0
          B2_B0: nxn (grid) array containing B2/B0
          nrevs: nxn array containing the number of reversals
          R0: nxn array containing the positions of the first (i.e. close to
            origin) reversal
          R1: nxn array containing the positions of the second reversal
          R2: nxn array containing the positions of the third reversal
          In nrevs, R0, R1, R2, NaN marks absence.
    """
    import parmap

    if params is None:
        params = { 'Ralpha_d': 1.0,
                   'h_d'     : 2.25,  # kpc
                   'R_d': 15.0, # kpc
                   'D_d'     : -15.0,
                   'Cn_d'    : N.ones(3) }

    # Generates grid of B2/B0 or B1/B0
    B2_B0 = N.linspace(B2_B0_range[0],B2_B0_range[1],n)
    B1_B0 = N.linspace(B1_B0_range[0],B1_B0_range[1],n)
    b20_grid, b10_grid = N.meshgrid(B2_B0,B1_B0)

    # Finds all the reversals (in parallel!)
    list_reversals = parmap.starmap(find_reversals,
                                    zip(b20_grid.ravel(), b10_grid.ravel()),
                                    params, processes=processes, pool=pool)

    # Initializes arrays which will store the reversals' positions
    R0 = N.empty_like(b20_grid)*N.NaN
    R1 = N.empty_like(b20_grid)*N.NaN
    R2 = N.empty_like(b20_grid)*N.NaN
    nrevs = N.empty_like(b20_grid)*N.NaN

    # Reorganizes (there may be a better way..)
    for i, reversals in enumerate(list_reversals):
        grid_idx = N.unravel_index(i, b20_grid.shape)
        nrevs[grid_idx] = reversals.size
        nrev = nrevs[grid_idx]
        if nrev>0:
            r = N.sort(reversals)
            R0[grid_idx] = reversals[0]
            if nrev>1:
                R1[grid_idx] = reversals[1]
                if nrev>2:
                    R2[grid_idx] = reversals[2]

    return b10_grid, b20_grid, nrevs, R0, R1, R2


# Do some testing if running as a script
if __name__ == "__main__"  :
    import pylab as P
    # n-dependent part
    number_of_bessel = 3

    B2_B0 = 0.86440678
    B1_B0 = -3
    # Parameters
    params = { 'Ralpha_d': 1.0,
              'h_d'     : 0.5,  # kpc
              'R_d': 15.0, # kpc
              'D_d'     : -15.0,
              'Cn_d'    : N.array([1,B1_B0,B2_B0])
            }

    print find_reversals(B2_B0,B1_B0, params=params)
    r = N.linspace(0,params['R_d'],50)
    Bp = get_B_phi(r, B1_B0, B2_B0, params)
    P.plot(r, Bp)

    r_dl = N.linspace(0,1,50) # This needs to be organised later. At the moment
                             # get_B_disk_cyl gets dimensionless arguments
                             # while get_B_disk get dimensional
    phi_dl = 0.0*r_dl
    z_dl = 0.0*r_dl

    Br,Bp,Bz = D.get_B_disk_cyl(r_dl,phi_dl,z_dl, params)
    P.plot(r, Bp)
    P.grid()
    P.figure()
    z_dl = N.linspace(-1,1,50)
    z = z_dl*params['h_d']
    r_dl = z_dl/z_dl * 0.1
    phi_dl = z_dl * 0.0

    # Try constant r, phi
    Br,Bp,Bz = D.get_B_disk_cyl(r_dl,phi_dl,z_dl, params)
    P.plot(z, Bp,label=r'$B_\phi$')
    P.plot(z, Br,label=r'$B_r$')
    P.plot(z, Bz,label=r'$B_z$')
    P.legend()

    ## Try constant x,y
    #P.figure()
    #l = 0.1*params['R_d']
    #Bx,By,Bz = D.get_B_disk(l,0,z, params)
    #P.plot(z, Bx,label=r'$B_x$')
    #P.plot(z, By,label=r'$B_y$')
    #P.plot(z, Bz,label=r'$B_z$')
    #P.legend()

    P.show()