class Language:
    """
    This class is a simple enumeration container for the different languages implemented
    """
    English = 'en'
    Spanish = 'sp'
    French = 'fr'


# This variable is a global parameter to hold the language state for the running program
CurrentLanguage = Language.English

EnglishDictionary = {
    'ABOUT_DIALOG': 'This program was created by NREL for the United States Department of Energy.',
    'Choose File to Update...': 'Choose File to Update...',
    'About...': 'About...',
    'File Path': 'File Path',
    'You must restart the app to make the language change take effect.  Would you like to restart now?':
        'You must restart the app to make the language change take effect.  Would you like to restart now?',
    'Old Version': 'Original IDF Version',
    'Keep Intermediate Versions of Files?': 'Keep Intermediate Versions of Files?',
    'Update File': 'Update File',
    'Close': 'Close',
    'Exit': 'Exit',
    'Menu': 'Menu',
    'Cancel Run': 'Cancel Run',
    "EnergyPlus Installation": "EnergyPlus Installation",
    'Choose E+ Folder...': 'Choose E+ Folder...',
    "Selected Directory: ": "Selected Directory: ",
    "Install Details: ": "Install Details: ",
    'EnergyPlus Version': 'EnergyPlus Version',
    'Program Initialized': 'Program Initialized',
    "IDF Selection": "IDF Selection",
    "Invalid Version": "Invalid Version",
    "Selected IDF: ": "Selected IDF: ",
    "File Details: ": "File Details: ",
    "Language Confirmation": "Language Confirmation",
    'Running Transition': 'Running Transition',
    "Choose EnergyPlus Install Root": "Choose EnergyPlus Install Root",
    'Transition Cancelled': 'Transition Cancelled',
    'Completed Transition': 'Completed Transition',
    'Failed Transition': 'Failed Transition',
    'All transitions completed successfully - Open run directory for transitioned file':
        'All transitions completed successfully - Open run directory for transitioned file',
    'Could not open run directory': 'Could not open run directory',
    'Open Run Directory': 'Open Run Directory',
    'Cannot find a matching transition tool for this idf version':
        'Cannot find a matching transition tool for this idf version',
    'Open File for Transition': 'Open File for Transition',
    'IDF File doesn\'t exist at path given; cannot transition':
        'IDF File doesn\'t exist or invalid E+ install; cannot transition',
    'IDF File exists, ready to go': 'IDF File exists, ready to go',
    "Attempting to cancel simulation ...": "Attempting to cancel simulation ...",
    "Transition cancelled": "Transition cancelled",
}

SpanishDictionary = {
    'ABOUT_DIALOG': 'Este programa fue creado por el NREL para el Departamento de Energia de los Estados Unidos.',
    'Choose File to Update...': 'Elegir archivo para actualizar ...',
    'About...': 'Acerca de...',
    'File Path': 'Ruta de archivo',
    'You must restart the app to make the language change take effect.  Would you like to restart now?':
        'Debe reiniciar la aplicacion para que el cambio de idioma tenga efecto. Le gustaria reiniciar ahora?',
    'Old Version': 'Version antigua',
    'Keep Intermediate Versions of Files?': 'Mantener versiones intermedias de Archivos?',
    'Update File': 'Actualizar archivo',
    'Close': 'Cerca',
    'Exit': 'Salida',
    'Menu': 'Menú',
    'Cancel Run': 'Cancelar Ejecutar',
    "EnergyPlus Installation": "EnergyPlus instalación",
    'Choose E+ Folder...': 'Elige E+ Carpeta...',
    "Selected Directory: ": "Directorio seleccionado: ",
    "Install Details: ": "Detalles de instalación: ",
    'EnergyPlus Version': 'Versión del EnergyPlus',
    'Program Initialized': 'Programa Initialized',
    "IDF Selection": "IDF Selección",
    "Selected IDF: ": "Sélection de IDF: ",
    "Invalid Version": "Versión inválida",
    "File Details: ": "Detalles del archivo: ",
    "Language Confirmation": "Confirmar idioma",
    'Running Transition': 'Transición corriendo',
    "Choose EnergyPlus Install Root": "Elija raíz de instalación de EnergyPlus",
    'Transition Cancelled': 'transición Cancelado',
    'Completed Transition': 'Transición completado',
    'Failed Transition': 'La transición fallida',
    'All transitions completed successfully - Open run directory for transitioned file':
        'Todas las transiciones completada con éxito - Abrir directorio de ejecución para el archivo de la transición',
    'Could not open run directory': 'No se pudo abrir directorio de ejecución',
    'Open Run Directory': 'Directorio de ejecución abierta',
    'Cannot find a matching transition tool for this idf version':
        'No se puede encontrar una herramienta de transición a juego para esta versión de la FID',
    'Open File for Transition': 'Abrir archivo para la Transición',
    'IDF File doesn\'t exist at path given; cannot transition':
        'IDF El archivo no existe en la ruta dada; no puede transición',
    'IDF File exists, ready to go': 'existe IDF del archivo, listo para ir',
    "Attempting to cancel simulation ...": "Intentando cancelar la simulación ...",
    "Transition cancelled": "Transición cancelada",
}

FrenchDictionary = {
    'ABOUT_DIALOG': 'Ce logiciel a ete cree par NREL pour United States Department of Energy.',
    'Choose File to Update...': 'Choisissez Fichier pour mettre a jour ...',
    'About...': 'Sur...',
    'File Path': 'Chemin du fichier',
    'You must restart the app to make the language change take effect.  Would you like to restart now?':
        'Vous devez relancer le logiciel pour effectuer le changement de langue. Voulez-vous relancer maintenant?',
    'Old Version': 'Ancienne version',
    'Keep Intermediate Versions of Files?': 'Gardez versions intermediaires de fichiers?',
    'Update File': 'Mise a jour de fichiers',
    'Close': 'Fermer',
    'Exit': 'Sortir',
    'Menu': 'Menu',
    'Cancel Run': 'Annuler Run',
    "EnergyPlus Installation": "EnergyPlus Installation",
    'Choose E+ Folder...': 'Choisir E+ Dossier...',
    "Selected Directory: ": "Répertoire sélectionné: ",
    "Install Details: ": "Détails de l'installation: ",
    'EnergyPlus Version': 'Version du EnergyPlus',
    'Program Initialized': 'Programme initialisé',
    "IDF Selection": "IDF Sélection",
    "Invalid Version": "Version invalide",
    "Selected IDF: ": "Sélection de IDF: ",
    "File Details: ": "Détails du fichier: ",
    "Language Confirmation": "Confirmer la langue",
    'Running Transition': 'Transition en cours',
    "Choose EnergyPlus Install Root": "Choisissez la racine d'installation d'EnergyPlus",
    'Transition Cancelled': 'transition Annulé',
    'Completed Transition': 'transition Terminé',
    'Failed Transition': 'transition Échec',
    'All transitions completed successfully - Open run directory for transitioned file':
        'Toutes les transitions complété avec succès - répertoire d\'exécution Ouvert pour le fichier transition',
    'Could not open run directory': 'Impossible d\'ouvrir le répertoire run',
    'Open Run Directory': 'Open Directory Run',
    'Cannot find a matching transition tool for this idf version':
        'Vous ne pouvez pas trouver un outil de transition correspondant pour cette version idf',
    'Open File for Transition': 'Ouvrir un fichier pour la transition',
    'IDF File doesn\'t exist at path given; cannot transition':
        'IDF fichier n\'existe pas au chemin donné; ne peut pas passer',
    'IDF File exists, ready to go': 'IDF fichier existe, prêt à aller',
    "Attempting to cancel simulation ...": "Tentative d'annulation de la simulation ...",
    "Transition cancelled": "Transition annulée",
}


def set_language(lang):
    """
    This is the interface for changing the language, call this, save settings, then restart the program
    :param lang: A language identifier from the :py:class:`Languages` enumeration class
    """
    global CurrentLanguage
    CurrentLanguage = lang


def report_missing_keys():
    """
    This function simply scans dictionaries to see if any keys are missing from them compared to a baseline.
    The baseline is currently the English dictionary.
    This function simply reports to the terminal.
    """
    base_keys = EnglishDictionary.keys()
    known_dictionaries = {
        'Spanish': SpanishDictionary, 'French': FrenchDictionary
    }
    for dict_name, dictionary in known_dictionaries.items():  # add here
        print("Processing missing keys from dictionary: " + dict_name)
        for key in base_keys:
            if key not in dictionary:
                print("Could not find key: \"%s\"" % key)


def translate(key):
    """
    This function translates a string into a dictionary.

    :param key: The string to translate
    :return: The translated string
    """
    # if for some reason blank, just return blank
    if key is None or key == "":
        return ""

    # start with English, but switch based on language
    dictionary = EnglishDictionary
    if CurrentLanguage == Language.Spanish:
        dictionary = SpanishDictionary
    elif CurrentLanguage == Language.French:
        dictionary = FrenchDictionary

    # if the key is there, return it, otherwise return a big flashy problematic statement
    if key in dictionary:
        return dictionary[key]
    else:
        print("Could not find this key in the dictionary: \"%s\"" % key)
        return "TRANSLATION MISSING"


if __name__ == "__main__":
    report_missing_keys()
