import argparse
import spectral
import matplotlib.pyplot as plt

import rgb
from prisma import Prisma


def getPca( cube ):

    # compute pca and display covariance matrix
    pc = spectral.principal_components( cube )
    plt.imshow(pc.cov)
    plt.show()

    # retain minimum of 99.9% of total image variance.
    pc_0999 = pc.reduce(fraction=0.999)
    print ( len(pc_0999.eigenvalues) )

    # display 66 bands as 3 pcs
    cube_pc = pc_0999.transform( cube )
    plt.imshow( cube_pc[:,:,:3] )
    plt.show()

    return pc_0999


def parseArguments(args=None):

    """
    parse arguments
    """

    # parse configuration
    parser = argparse.ArgumentParser(description='prisma')
    parser.add_argument('pathname', action="store")

    return parser.parse_args(args)


def main():

    """
    main path of execution
    """

    # parse arguments
    args = parseArguments()

    # read prisma dataset
    prisma = Prisma()
    prisma.loadData( args.pathname )

    # get channel indices closest to central wavelengths of sentinel-2 optical channels
    s2_rgb_wavelengths = [ 492.4, 559.8, 664.6 ] 
    indexes = prisma.getVnirChannelIndexes( s2_rgb_wavelengths )

    # create 24-bit rgb image    
    image = rgb.getImage( [ prisma._vnir[ 'channels' ][ :,:, idx ] for idx in indexes ]  )
    rgb.saveImage( image, prisma.getGcps(), 'c:\\Users\\Chris.Williams\\Desktop\\test.tif' )

    # pc analysis
    vnir_pc = getPca( prisma._vnir[ 'channels' ] )
    swir_pc = getPca( prisma._swir[ 'channels' ] )


    return


# execute main
if __name__ == '__main__':
    main()

