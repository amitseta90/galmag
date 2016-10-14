import pylab as P

def std_setup():
    P.rc('image', cmap='viridis')
    P.rc('xtick', labelsize=14)
    P.rc('ytick', labelsize=14)
    P.rc('axes', labelsize=15, titlesize=15)
    P.rcParams['axes.color_cycle'] = ['#1f78b4','#a6cee3','#33a02c','#b2df8a',
                                      '#e31a1c','#fb9a99','#ff7f00','#fdbf6f',
                                      '#6a3d9a','#cab2d6',]
    P.rcParams['lines.linewidth'] = 3.0

def plot_r_z_uniform(B,skipr=3,skipz=5):
    """
    Plots a r-z slice of the field. Assumes B is created using a cylindrical
    grid - for a more sophisticated/flexible plotting script which does not
    rely on the grid structure check the plot_slice.

    The plot consists of:
      1) a coloured contourplot of |B|^2
      2) Field lines of the B_x and B_y field
      3) Quivers showing the B_x and B_y field

    Input:
      B -> a B_field or B_field_component object
      field_lines, quiver, contour -> booleans controlling which type of plot
                                      should be displayed. (Default: all True.)
      skipx, skipy -> arguments to tweak the the displaying of the
                      quivers. (Default: skipx=5, skipy=5)
    """
    # Requires a cylindrical grid
    assert B.grid.grid_type == 'cylindrical'

    # Makes a color contour plot
    CP = P.contourf(B.grid.r_cylindrical[:,0,:], B.grid.z[:,0,:],
                  -B.phi[:,0,:], alpha=0.5, linewidths=17.0)
    CB = P.colorbar(CP, label=r'$B_\phi\,[\mu{{\rm G}}]$',)
    P.setp(CP.collections , linewidth=2)


    P.quiver(B.grid.r_cylindrical[::skipr,0,::skipz], B.grid.z[::skipr,0,::skipz],
           B.r_cylindrical[::skipr,0,::skipz],B.z[::skipr,0,::skipz],
           color='0.25', alpha=0.75)

    P.ylim([B.grid.z[:,0,:].min(),
          B.grid.z[:,0,:].max()])
    P.xlim([B.grid.r_cylindrical[:,0,:].min(),
          B.grid.r_cylindrical[:,0,:].max()])

    P.xlabel(r'$R\,[{{\rm kpc}}]$')
    P.ylabel(r'$z\,[{{\rm kpc}}]$')


def plot_x_z_uniform(B,skipx=1,skipz=5):
    """
    A wrapper to use plot_r_z_uniform, which is equivalent in terms of
    indexing.
    """
    # Requires a Cartesian grid
    assert B.grid.grid_type == 'cartesian'

    # Makes a color contour plot
    CP = P.contourf(B.grid.x[:,0,:], B.grid.z[:,0,:],
                  -B.phi[:,0,:], alpha=0.5, linewidths=17.0)
    CB = P.colorbar(CP, label=r'$B_\phi\,[\mu{{\rm G}}]$',)
    P.setp(CP.collections , linewidth=2)


    P.quiver(B.grid.x[::skipx,0,::skipz], B.grid.z[::skipx,0,::skipz],
           B.x[::skipx,0,::skipz],B.z[::skipx,0,::skipz],
           color='0.25', alpha=0.75)

    P.ylim([B.grid.z[:,0,:].min(),
          B.grid.z[:,0,:].max()])
    P.xlim([B.grid.x[:,0,:].min(),
          B.grid.x[:,0,:].max()])

    P.xlabel(r'$x\,[{{\rm kpc}}]$')
    P.ylabel(r'$z\,[{{\rm kpc}}]$')


def plot_x_y_uniform(B,skipx=5, skipy=5, iz=0, field_lines=True, quiver=True,
                     contour=True):
    """
    Plots a x-y slice of the field. Assumes B is created using a cartesian
    grid - for a more sophisticated/flexible plotting script which does not
    rely on the grid structure check the plot_slice.

    The plot consists of:
      1) a coloured contourplot of |B|^2
      2) Field lines of the B_x and B_y field
      3) Quivers showing the B_x and B_y field

    Input:
      B -> a B_field or B_field_component object
      field_lines, quiver, contour -> booleans controlling which type of plot
                                      should be displayed. (Default: all True.)
      skipx, skipy -> arguments to tweak the the displaying of the
                      quivers. (Default: skipx=5, skipy=5)
    """
    # Requires a Cartesian grid
    assert B.grid.grid_type == 'cartesian'

    if contour:
        CP = P.contourf(B.grid.x[:,:,iz], B.grid.y[:,:,iz],
                        P.sqrt(B.x[:,:,iz]**2+B.y[:,:,iz]**2+B.z[:,:,iz]**2),
                        alpha=0.5, linewidths=17.0)
        CB = P.colorbar(CP, label=r'$B\,[\mu{{\rm G}}]$',)
        P.setp(CP.collections , linewidth=2)

    if field_lines:
        P.streamplot(P.array(B.grid.x[:,0,iz]), P.array(B.grid.y[0,:,iz]),
                    -P.array(B.y[:,:,iz]), -P.array(B.x[:,:,iz]),color='r')
    if quiver:
        P.quiver(B.grid.x[::skipx,::skipy,iz], B.grid.y[::skipx,::skipy,iz],
              B.x[::skipx,::skipy,iz],B.y[::skipx,::skipy,iz], color='b')

    P.ylim([B.grid.y[:,:,iz].min(),B.grid.y[:,:,iz].max()])
    P.xlim([B.grid.x[:,:,iz].min(),B.grid.x[:,:,iz].max()])
    P.xlabel(r'$x\,[{{\rm kpc}}]$')
    P.ylabel(r'$y\,[{{\rm kpc}}]$')

    return

def plot_slice():
    raise NotImplemented
