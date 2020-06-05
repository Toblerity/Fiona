import xml.etree.ElementTree as ET
from fiona._meta import _get_metadata_item
from fiona.env import require_gdal_version, GDALVersion


class MetadataItem:
    # since GDAL 2.0
    CREATION_FIELD_DATA_TYPES = "DMD_CREATIONFIELDDATATYPES"
    # since GDAL 2.3
    CREATION_FIELD_DATA_SUB_TYPES = "DMD_CREATIONFIELDDATASUBTYPES"
    CREATION_OPTION_LIST = "DMD_CREATIONOPTIONLIST"
    LAYER_CREATION_OPTION_LIST = "DS_LAYER_CREATIONOPTIONLIST"
    # since GDAL 2.0
    DATASET_OPEN_OPTIONS = "DMD_OPENOPTIONLIST"
    # since GDAL 2.0
    EXTENSIONS = "DMD_EXTENSIONS"
    EXTENSION = "DMD_EXTENSION"
    VIRTUAL_IO = "DCAP_VIRTUALIO"
    # since GDAL 2.0
    NOT_NULL_FIELDS = "DCAP_NOTNULL_FIELDS"
    # since gdal 2.3
    NOT_NULL_GEOMETRY_FIELDS = "DCAP_NOTNULL_GEOMFIELDS"
    # since GDAL 3.2
    UNIQUE_FIELDS = "DCAP_UNIQUE_FIELDS"
    # since GDAL 2.0
    DEFAULT_FIELDS = "DCAP_DEFAULT_FIELDS"
    OPEN = "DCAP_OPEN"
    CREATE = "DCAP_CREATE"


def _parse_options(xml):
    """Convert metadata xml to dict"""
    options = {}
    if len(xml) > 0:

        root = ET.fromstring(xml)
        for option in root.iter('Option'):

            option_name = option.attrib['name']
            opt = {}
            opt.update((k, v) for k, v in option.attrib.items() if not k == 'name')

            values = []
            for value in option.iter('Value'):
                values.append(value.text)
            if len(values) > 0:
                opt['values'] = values

            options[option_name] = opt

    return options


@require_gdal_version('2.0')
def dataset_creation_options(driver):
    """ Returns dataset creation options for driver

    Parameters
    ----------
    driver : str

    Returns
    -------
    dict
        Dataset creation options

    """

    xml = _get_metadata_item(driver, MetadataItem.CREATION_OPTION_LIST)

    # Fix XML
    if driver == 'GML':
        xml = xml.replace("<gml:boundedBy>", "&lt;gml:boundedBy&gt;")
    elif driver == 'GPX':
        xml = xml.replace("<extensions>", "&lt;extensions&gt;")

    options = _parse_options(xml)
    return options


@require_gdal_version('2.0')
def layer_creation_options(driver):
    """ Returns layer creation options for driver

    Parameters
    ----------
    driver : str

    Returns
    -------
    dict
        Layer creation options

    """
    xml = _get_metadata_item(driver, MetadataItem.LAYER_CREATION_OPTION_LIST)
    options = _parse_options(xml)
    return options


@require_gdal_version('2.0')
def dataset_open_options(driver):
    """ Returns dataset open options for driver

    Parameters
    ----------
    driver : str

    Returns
    -------
    dict
        Dataset open options

    """
    xml = _get_metadata_item(driver, MetadataItem.DATASET_OPEN_OPTIONS)
    options = _parse_options(xml)
    return options


@require_gdal_version('2.0')
def print_driver_options(driver):
    """ Print driver options for dataset open, dataset creation, and layer creation.

    Parameters
    ----------
    driver : str

    """

    for option_type, options in [("Dataset Open Options", dataset_open_options(driver)),
                                 ("Dataset Creation Options", dataset_creation_options(driver)),
                                 ("Layer Creation Options", layer_creation_options(driver))]:

        print("{option_type}:".format(option_type=option_type))
        if len(options) == 0:
            print("\tNo options available.")

        else:
            for option_name in options:
                print("\t{option_name}:".format(option_name=option_name))
                if 'description' in options[option_name]:
                    print("\t\tDescription: {description}".format(description=options[option_name]['description']))
                if 'type' in options[option_name]:
                    print("\t\tType: {type}".format(type=options[option_name]['type']))
                if 'default' in options[option_name]:
                    print("\t\tDefault value: {default}".format(default=options[option_name]['default']))
                if 'values' in options[option_name] and len(options[option_name]['values']) > 0:
                    print("\t\tAccepted values: {values}".format(values=",".join(options[option_name]['values'])))
        print("")


@require_gdal_version('2.0')
def extensions(driver):
    """ Returns file extensions supported by driver

    Parameters
    ----------
    driver : str

    Returns
    -------
    list
        List with file extensions

    """
    driver_extensions = set()
    if GDALVersion().runtime().at_least((2, 0)):
        for ext in _get_metadata_item(driver, MetadataItem.EXTENSIONS).split(" "):
            if len(ext) > 0:
                driver_extensions.add(ext)
    for ext in _get_metadata_item(driver, MetadataItem.EXTENSION).split(" "):
        if len(ext) > 0:
            driver_extensions.add(ext)
    return list(driver_extensions)


@require_gdal_version('2.0')
def supports_vsi(driver):
    """ Returns True if driver supports GDAL's VSI*L API

    Parameters
    ----------
    driver : str

    Returns
    -------
    bool

    """
    return _get_metadata_item(driver, MetadataItem.VIRTUAL_IO).upper() == "YES"


@require_gdal_version('2.0')
def supported_field_types(driver):
    """ Returns supported field and sub field types

    Parameters
    ----------
    driver : str

    Returns
    -------
    list
        List with supported field types

    """
    field_types = set()
    for field_type in _get_metadata_item(driver, MetadataItem.CREATION_FIELD_DATA_TYPES).split(" "):
        field_types.add(field_type)

    if GDALVersion().runtime().at_least((2, 3)):
        for field_type in _get_metadata_item(driver, MetadataItem.CREATION_FIELD_DATA_SUB_TYPES).split(" "):
            field_types.add(field_type)

    return list(field_types)
