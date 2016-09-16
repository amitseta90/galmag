# -*- coding: utf-8 -*-

import numpy as np
import scipy.integrate
import scipy.special

from gmf_tool.B_field import B_field

from B_generator import B_generator
from gmf_tool.Grid import Grid
from halo_profiles import simple_V, simple_alpha


class B_generator_halo(B_generator):
    def __init__(self, box, resolution, grid_type='cartesian',
                 default_parameters={}, dtype=np.float):

        super(B_generator_halo, self).__init__(
                                        box=box,
                                        resolution=resolution,
                                        grid_type=grid_type,
                                        default_parameters=default_parameters,
                                        dtype=dtype)
        self.component_count = 0

    @property
    def _builtin_parameter_defaults(self):
        builtin_defaults = {
                            'halo_symmetric_field': True,
                            'halo_n_free_decay_modes': 4,
                            'halo_dynamo_type': 'alpha-omega',
                            'halo_rotation_function': simple_V,
                            'halo_alpha_function': simple_alpha,
                            'halo_Galerkin_ngrid': 250,
                            'halo_growing_mode_only': False,
                            'halo_compute_only_one_quadrant': True
                            }
        return builtin_defaults


    def get_B_field(self, B_sun=10, reversals=None, dr=0.1, dz=0.05,
                          number_of_components=None, **kwargs):
        """ Constructs a B_field object.
            Input:
                  B_sun -> Magnetic field intensity at the solar radius
                           (in muG). Default: 10
                  reversals -> a list containing the r-positions of field
                               reversals over the midplane (units consitent
                               with the grid).
                  dr, dz -> the minimal r and z intervals used in the
                            calculation of the reversals
                  number_of_components -> Number of components to be used.
                    If None, number_of_components = len(reversals)+1.

            Output: List of B_field objects satisfying the criteria
        """
        parsed_parameters = self._parse_parameters(kwargs)

        nGalerkin = parsed_parameters['halo_Galerkin_ngrid']

        # Prepares a spherical grid for the Galerkin expansion
        Galerkin = Grid(box=[[0.0001,2.0], # r range
                             [0.1,np.pi],  # theta range
                             [0.0,0.0]], # phi range
                         resolution=[nGalerkin,nGalerkin,1],
                         grid_type='spherical')
        raise NotImplementedError

        return

    def perturbation_operator(r, theta, phi,
                              Br, Bt, Bp,
                              Vr, Vt, Vp,
                              alpha,
                              Ra,
                              Ro,
                              dynamo_type='alpha-omega',
                              ):

        """ Applies the perturbation operator associated with an
            a dynamo to a magnetic field in spherical coordinates.

            Input:
                r, B, alpha, V: position vector (not radius!), magnetic field,
                alpha and rotation curve, respectively, expressed as 3xNxNxN arrays
                containing the r, theta and phi components in [0,...], [1,...]
                and [2,...], respectively.
                p: dictionary of parameters containing 'Ralpha_h'.
            Output:
                Returns a 3xNxNxN array containing W(B)
        """
        #TODO lfsr: Needs to rewrite curl_spherical and cross in a way that is
        #TODO lfsr: compatible with the d2o's!!!!

        # Computes \nabla \times (\alpha B)
        curl_aB = curl_spherical(r, theta, phi, Br*a, Bt*a, Bp*a) # TODO

        # Computes \nabla \times (V \times B)
        VcrossBr, VcrossBt, VcrossBp = cross(Vr, Vt, Vp, Br, Bt, Bp) #TODO
        curl_VcrossB = curl_spherical(r, theta, phi,
                                      VcrossBr, VcrossBt, VcrossBp)

        WBs = []
        for i in range(3):
            if dynamo_type=='alpha-omega':
                WBs.append(Ra*(curl_aB[i] - curl_aB[2])  \
                              + Ro*curl_VcrossB[i])

            elif dynamo_type=='alpha2-omega':
                WBs.append(Ra*curl_aB[i] + Ro*curl_VcrossB[i])

            else:
                raise AssertionError('Invalid option: dynamo_type={0}'.format(dynamo_type))

        return WBs

    def Galerkin_expansion_coefficients(galerkin_grid,
                                        symmetric=False,
                                        dynamo_type='alpha-omega',
                                        n_free_decay_modes=4,
                                        return_matrix=False,
                                        function_V,
                                        function_alpha):
        """ Calculates the Galerkin expansion coefficients.

            First computes the transformation M defined by:
            Mij = gamma_j, for i=j
            Mij = Wij, for i!=j
            where:
            W_{ij} = \int B_j \cdot \hat{W} B_i
            Then, solves the eigenvalue/eigenvector problem.

            Input:
                r, B, alpha, V: position vector (not radius!), magnetic field,
                alpha and rotation curve, respectively, expressed as 3xNxNxNp arrays
                containing the r, theta and phi components in [0,...], [1,...]
                and [2,...], respectively. Np=1 implies the assumption of
                axisymmetry.
                p: dictionary of parameters containing 'Ralpha_h' and 'Romega_h'.

            Output (Same as the output of numpy.linalg.eig)
              Gammas: n-array containing growth rates (the eigenvalues of Mij)
              ai's: nx3 array containing the Galerkin coefficients associated
                    with each growth rate (the eigenvectors)
        """

        local_r_sph_grid = galerkin_grid.r_spherical.get_local_data()
        local_phi_grid = galerkin_grid.phi.get_local_data()
        local_theta_grid = galerkin_grid.theta.get_local_data()

        # local_B_r_spherical, local_B_phi, local_B_theta (for each mode)
        local_Bmodes = []
        Bmodes = []
        for imode in range(1,nmodes+1):
            # Calculates free-decay modes locally
            local_Bmodes.append(halo_free_decay_modes.get_mode(
                                                            local_r_sph_grid,
                                                            local_theta_grid,
                                                            local_phi_grid,
                                                            imode, symmetry))
            # Initializes global arrays
            Bmodes.append([galerkin_grid.get_prototype(dtype=self.dtype)
                                 for i in xrange(3)])
        for k in range(nmodes):
            # Brings the local array data into the d2o's
            for (g, l) in zip(Bmodes[k], local_Bmodes[k]):
                g.set_local_data(l, copy=False)

        # Computes sintheta
        local_sintheta = N.sin(local_theta_grid)
        # Computes alpha (locally)
        local_alpha = function_alpha(local_r_sph_grid,
                                     local_theta_grid,
                                     local_phi_grid)
        # Computes the various components of V (locally)
        local_Vs = function_V(local_r_sph_grid,
                              local_theta_grid,
                              local_phi_grid)
        # Brings sintheta, rotation curve and alpha into the d2o's
        sintheta = galerkin_grid.get_prototype(dtype=self.dtype)
        sintheta.set_local_data(local_sintheta, copy=False)
        alpha = galerkin_grid.get_prototype(dtype=self.dtype)
        Vs = [galerkin_grid.get_prototype(dtype=self.dtype) for i in xrange(3)]
        alpha.set_local_data(local_alpha, copy=False)
        for (g, l) in zip(Vs, local_Vs):
            g.set_local_data(l, copy=False)

        # Applies the perturbation operator
        WBmodes = []
        for Bmode in Bmodes:
            WBmodes.append(perturbation_operator(galerkin_grid.r_spherical,
                                                 galerkin_grid.theta,
                                                 galerkin_grid.phi,
                                                 Bmode[0], Bmode[1], Bmode[2],
                                                 Vs[0], Vs[1], Vs[2],
                                                 alpha,
                                                 Ra,
                                                 Ro,
                                                 dynamo_type
                                                ))

        Wij = N.zeros((nmodes,nmodes))
        for i in range(n_free_decay_modes):
            for j in range(n_free_decay_modes):
                if i==j:
                    continue
                integrand = galerkin_grid.get_prototype(dtype=self.dtype)
                integrand *= 0.0
                for k in range(3):
                    integrand += Bmode[i][k]*WBmode[j][k]

                integrand *= galerkin_grid.r_spherical**2 * sintheta

                # Integrates over phi TODO
                if dphi:
                    integrand = integrate.simps(integrand, dx=dphi)# TODO
                else:
                    # Assuming axisymmetry
                    integrand = integrand[...,0]*2.0*N.pi
                # Integrates over theta TODO
                integrand = integrate.simps(integrand, dx=dtheta)#TODO
                # Integrates over r
                Wij[i,j] += integrate.simps(integrand, dx=dr)

        # Overwrites the diagonal with its correct values
        for i in range(n_free_decay_modes):
            Wij[i,i] = gamma[i]

        # Solves the eigenvector problem and returns the result
        val, vec = N.linalg.eig(Wij)
        if not return_matrix:
            return val, vec
        else:
            return val, vec, Wij

    def get_B_field(self, **kwargs):
        """ Returns a B_field object containing the specified disk field.
            Note: the coefficients for the components have to be specified
            explicitly through the parameter disk_component_normalization.
        """
        parsed_parameters = self._parse_parameters(kwargs)

        self.component_count = len(parsed_parameters['disk_component_normalization'])
        self._bessel_jn_zeros = scipy.special.jn_zeros(1, self.component_count)

        local_r_cylindrical_grid = self.grid.r_cylindrical.get_local_data()
        local_phi_grid = self.grid.phi.get_local_data()
        local_z_grid = self.grid.z.get_local_data()

        # local_B_r_cylindrical, local_B_phi, local_B_z
        local_arrays = \
            self._convert_coordinates_to_B_values(local_r_cylindrical_grid,
                                                  local_phi_grid,
                                                  local_z_grid,
                                                  parsed_parameters)

        # global_r_cylindrical, global_phi, global_z
        global_arrays = \
            [self.grid.get_prototype(dtype=self.dtype) for i in xrange(3)]

        # bring the local array data into the d2o's
        for (g, l) in zip(global_arrays, local_arrays):
            g.set_local_data(l, copy=False)

        result_field = B_field(grid=self.grid,
                               r_cylindrical=global_arrays[0],
                               phi=global_arrays[1],
                               theta=global_arrays[2],
                               dtype=self.dtype,
                               generator=self,
                               parameters=parsed_parameters)
        return result_field



