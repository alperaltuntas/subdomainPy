## subdomainPy: 
### Python scripts for Subdomain Modeling in ADCIRC+SWAN

Subdomain modeling is an exact reanalysis technique for ADCIRC+SWAN that enables the assessment of local *subdomain* changes with less computational effort than would be required by a complete resimulation of the full domain. So long as the subdomain is large enough to fully contain the altered hydrodynamics, multiple local changes may be simulated within it without the need to calculate new boundary conditions (Baugh et al., 2015).

This repository provides Python sripts that allow users to extract subdomain grids and generate full and subdomain input files including control file, grid information file, nodal attributes file, SWAN control file, and ADCIRC+SWAN boundary condition files.

- [**User Manual**](https://github.com/alperaltuntas/subdomainPy/blob/master/doc/userManual.pdf)

*Subdomain Modeling enables the assesment of many local design and failure scenarios with less computational effort:*

![breaches](https://github.com/alperaltuntas/subdomainPy/blob/master/doc/breaches.png)

### Download:
    $ git clone https://github.com/alperaltuntas/subdomainPy.git

### Home Page:
- [Subdomain Modeling Home Page](http://www4.ncsu.edu/~jwb/subdomain/)

