import osr
import gdal
import numpy as np
from osgeo import gdal_array


def getImage( channels ):

    """
    create 24bit image from numpy floating point arrays
    """

    # create 24bit rgb image for display
    rgb = []
    for channel in channels:
        
        # rescale to 8bit
        limits = np.percentile( channel, [ 5, 95 ] )
        image = np.asarray(  ( ( channel - limits[ 0 ] ) / ( limits[ 1 ] - limits[ 0 ] ) ) * 255 )
        
        # clip and append
        rgb.append( np.asarray( np.clip( image, 0, 255 ), np.uint8 ) )

    # stack list into 3d array
    return np.dstack( rgb )


def saveImage( data, gcps, pathname, **kwargs ): 

    """
    save data to geotiff
    """

    # initialise constants
    rows, cols, bands = data.shape
    dtype = gdal_array.NumericTypeCodeToGDALTypeCode( data.dtype )

    # create output object - single byte band
    driver = gdal.GetDriverByName("GTiff")
    ds = driver.Create( pathname, cols, rows, bands, dtype, options=kwargs.pop( 'options', [] ) )

    # gcps in lat / lon
    srs = osr.SpatialReference() 
    srs.ImportFromEPSG(4326)

    ds.SetGCPs( gcps, srs.ExportToWkt() )

    # flush data to file
    ds.FlushCache()
    ds = None

    # reopen to apply gcps
    ds = gdal.Open( pathname, gdal.GA_Update )

    # copy data into gdal raster
    for idx in range( bands ):
        ds.GetRasterBand( idx + 1 ).WriteArray( data [ :, :, idx ] )

    # flush data to file
    ds.FlushCache()
    ds = None

    return
