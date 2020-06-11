import gdal
import numpy as np


class Prisma:

    def __init__( self ):

        """
        constructor
        """

        # initialise members
        self._swir = {}
        self._vnir = {}
        self._geo = {}

        return


    def loadData( self, pathname ):

        """
        load data from file
        """

        # open dataset
        ds = gdal.Open( pathname, gdal.GA_ReadOnly )
        if ds is not None:

            # grab metadata
            meta = ds.GetMetadata( 'SUBDATASETS' )

            # load swir and vnir cubes
            self._swir = self.getCube( meta, 'SWIR' )
            self._vnir = self.getCube( meta, 'VNIR' )
                
            # get geo info
            self._geo = self.getGeoData( meta )

            # load global attributes
            meta = ds.GetMetadata()

            self._swir.update( self.getAttributes( meta, 'SWIR' ) )
            self._vnir.update( self.getAttributes( meta, 'VNIR' ) )

        return


    def getCube( self, meta, prefix ):

        """
        load swir specific data into dictionary        
        """

        # load data cube
        cube = {}

        name = self.getSubDatasetName( meta, '{}_Cube'.format( prefix ) )
        cube[ 'channels' ] = self.getSubDataset( meta[ name ] )

        # load pixel status subdataset
        name = self.getSubDatasetName( meta, '{}_PIXEL_L2_ERR_MATRIX'.format( prefix ) )
        cube[ 'err' ] = self.getSubDataset( meta[ name ] )

        return cube


    def getGeoData( self, meta ):

        """
        load geolocation data fields
        """

        # load data cube
        data = {}

        name = self.getSubDatasetName( meta, 'Latitude' )
        data[ 'latitude' ] = self.getSubDataset( meta[ name ] )

        name = self.getSubDatasetName( meta, 'Longitude' )
        data[ 'longitude' ] = self.getSubDataset( meta[ name ] )

        name = self.getSubDatasetName( meta, 'Time' )
        data[ 'time' ] = self.getSubDataset( meta[ name ] )

        return data


    def getSubDatasetName( self, meta, match ):

        """
        match key value of metadata dictionary
        """

        # cycle through metadata dict
        name = None
        for key, value in meta.items():
            if 'NAME' in key and match in value:

                # name match found
                name = key
                break

        return name                    


    def getAttributes( self, meta, prefix ):

        """
        read global attributes
        """

        # load spectral properties
        prefix =  prefix.capitalize()
        data = {}

        data[ 'wavelength' ] = meta[ 'List_Cw_{}'.format( prefix ) ].strip()
        data[ 'wavelength' ] = np.asarray( [ float(x) for x in data[ 'wavelength' ].split(' ') ] )

        data[ 'amplitude' ] = meta[ 'List_Fwhm_{}'.format( prefix ) ].strip()
        data[ 'amplitude' ] = np.asarray( [ float(x) for x in data[ 'amplitude' ].split(' ') ] )

        # scaling factors
        data[ 'min_scale' ] = float( meta[ 'L2Scale{}Min'.format( prefix ) ] )
        data[ 'max_scale' ] = float( meta[ 'L2Scale{}Max'.format( prefix ) ] )

        return data

        
    def getSubDataset( self, name ):

        """
        read subdataset from prisma h5 file
        """

        # open subdataset
        sds = gdal.Open( name, gdal.GA_ReadOnly )
        if sds is not None:

            bands = []
            for idx in range( 1, sds.RasterCount + 1 ):

                # read and append data
                band = sds.GetRasterBand( idx ).ReadAsArray()
                bands.append( band )

            if len( bands ) > 1:

                # stack list of data into 3d array
                data = np.dstack( bands )
                data = np.transpose( data, ( 2, 1, 0 ) )

            else:

                # single channel of data 
                data = bands[ 0 ]

        return data


    def getVnirChannelIndexes( self, wavelengths ):

        """
        retrieve indices of channels for given wavelengths
        """

        # retrieve indices of channels closest to wavelengths specified in argument
        return np.abs( np.subtract.outer( self._vnir[ 'wavelength' ], wavelengths ) ).argmin(0)


    def getSwirChannelIndexes( self, wavelengths ):

        """
        retrieve indices of channels for given wavelengths
        """

        # retrieve indices of channels closest to wavelengths specified in argument
        return np.abs( np.subtract.outer( self._swir[ 'wavelength' ], wavelengths ) ).argmin(0)


    def getGcps( self, step=20 ):

        """
        get grid of lat / lons as gcps
        """

        # initialise list and dims
        rows, cols = self._geo[ 'longitude' ].shape
        gcps = []

        # loop through lat / lon arrays
        for row in range( 0, rows, step ):
            for col in range( 0, cols, step ):

                # get geo coordinates
                x = self._geo[ 'longitude' ][ row ][ col ]
                y = self._geo[ 'latitude' ][ row ][ col ]
                z = 0.0

                # create gcp
                gcps.append( gdal.GCP( x, y, z, col, row ) )

        return gcps
