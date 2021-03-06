
        ----------------------------------------------------------------------

                    --- CAEN SpA - Computing Systems Division --- 

        ----------------------------------------------------------------------
        
        CAEN USB Driver Readme file
        
        ----------------------------------------------------------------------

        Package for Linux kernels 2.6, 3.x, 4.x, 5.x

        October 2020


 The complete documentation can be found in the User's Manual on CAEN's web
 site at: http://www.caen.it.


 Content
 -------

 Readme.txt       		: This file.

 ReleaseNotes.txt 		: Release Notes of the last software release.

 CAENUSBdrvB.c    		: The source file of the driver

 CAENUSBdrvB.h    		: The header file of the driver

 Makefile         		: The Makefile to compile the driver for kernel 2.6 to 4.13
 

 System Requirements
 -------------------

 - Linux kernel Rel. 2.6/3.x/4.x/5.x with gnu C/C++ compiler
 - Tested on kernel v4.18 and v5.4

 Compilation notes:
 
  To compile the CAENUSBdrvB device driver:

  - Execute: make
 
 Installation notes
 ------------------

  To install the CAENUSBdrvB device driver:

  - Execute: make install
  

 Uninstallation notes
 --------------------

  To uninstall the CAENUSBdrvB device driver:

  - Execute: make uninstall


  N.B. Once installed the driver, to use it udev must be restarted.
       Once reboot the pc CAENUSBdrvB will be loaded automatically by the system
