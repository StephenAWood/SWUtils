# Introduction

These are various utilities I have created to help me work with data and streamline certain tasks.

By Stephen Wood. See the license file for details.

# Requirements

- Python 2.7 or later
- Output files from ACC-Human

# Documentation

## SWConcentrationReader.py

This class is designed to open a standard CMAN.txt or CWOMAN.txt human concentration output file generated by the mechanistic bioaccumulation model ACC-Human. [1]
Usage:
`SWHumanConcentrationReader(filename, startyear=s.DEFAULT_START_YEAR, age_at_model_start=s.DEFAULT_AGE_AT_MODEL_START)`

The one required parameter is the filename/path for the human concentration file. startyear defaults to 1930 (the usual start year for modelling scenarios that involve polychlorinated biphenyls), and age_at_model_start which defaults to 0 (It must be a number from 0 to 9, inclusive). It also assumes that the concentration file outputted from ACC-Human is in the lifetime of organism format, **not** the age group format.

The class also figures out the time step of the output data, the end year of the simulation, and where each individual "resides" in the file. The user can then ask for the longitudinal body burden age trend (LBAT) for individuals born in various years (i.e., 1930, 1940, and so on). The user can also extract data necessary to construct a cross-sectional body burden age trend (CBAT).

## SWNhanesReader.py

This class is designed to read in NHANES data into a nested dictionary. The key in the top level dictionary is the NHANES individual respondent (SEQN) number. The next key is a string for a specific value, i.e. for gender: 'RIAGENDR'. It is geared towards extracting PCB concentrations from the NHANES dataset.

# Additional Information

Please contact me (s@stephenwood.net) if you have any questions

# References

1. Czub G, and McLachlan MS. 2004. Environmental Toxicology and Chemistry 23:2356–2366