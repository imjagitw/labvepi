from enum import Enum

class TipoExame(str, Enum): 
    FEBRE_DO_NILO = 'Febre do Nilo'
    ORTHOFLAVIRIDAE = 'OrthoFlaviviridae'
    FLAVIVIRUS = 'Flavivírus'
    FEBRE_AMARELA = 'Febre Amarela'
    MYCOPLASMA = 'Mycoplasma'
    HERPESVIRIDAE = 'Herpesviridae'
    HERPESVIRUS = 'Herpesvírus'
    TRIPANOSTOMATIDAE = 'Trypanosomatidae'
    RESISTENCIA_BACTERIANA = 'Resistência Bacteriana'
    HEPATOZOON = 'Hepatozoon'
    RAIVA = 'Raiva'
    CHLAMYDIA = 'Chlamydia'
    SARCOCYSTIDAE = 'Sarcocystidae'
    PLASMODIUM_HAEMOPROTEUS = 'Plasmodium e Haemoproteus'
    OUTRO = 'Outro'