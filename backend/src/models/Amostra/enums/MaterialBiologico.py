from enum import Enum

class MaterialBiologico(str, Enum): 
    # Swabs
    SWAB_ORAL = 'Swab oral'
    SWAB_NASAL = 'Swab nasal'
    SWAB_CLOACAL = 'Swab cloacal'
    SWAB_ORAL_CLOACAL = 'Swab oral e cloacal'
    SWAB_RETAL = 'Swab retal'
    SWAB_TRAQUEAL = 'Swab traqueal'
    SWAB_OCULAR = 'Swab ocular'
    
    # Sangue e derivados
    SANGUE = 'Sangue'
    SANGUE_TOTAL = 'Sangue total'
    SANGUE_EDTA = 'Sangue (EDTA)'
    SORO = 'Soro'
    PAPEL_FILTRO = 'Papel filtro'
    ESFREGACO_SANGUINEO = 'Esfregaço sanguíneo'
    
    # Tecidos e órgãos
    TECIDO = 'Tecido'
    POOL_TECIDOS = 'Pool de tecidos'
    ORGAOS = 'Órgãos'
    BACO = 'Baço'
    FIGADO = 'Fígado'
    PULMAO = 'Pulmão'
    RIM = 'Rim'
    ENCEFALO = 'Encéfalo / Cérebro'
    CORACAO = 'Coração'
    
    # Excretas, secreções e outros
    FEZES = 'Fezes'
    ENEMA = 'Enema'
    LIQUOR = 'Líquor / LCR'
    ECTOPARASITA = 'Ectoparasita'
    PELE = 'Pele'
    PELO = 'Pelo'
    NECROPSIA = 'Necrópsia'
    OUTRO = 'Outro'