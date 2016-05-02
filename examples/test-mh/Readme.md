# Test Setup - MultiHop (large IXP setup)

### Instructions to test the current code

Open a terminal and run the test topology:

    $ sudo python ~/endeavour/examples/test-mh/mininet/simple_sdx.py

Open a second terminal, go to the iSDX folder, checkout the branch mh-ctrlr, 
and run the controller:

    $ cd ~/iSDX
    $ git checkout mh-ctrlr
    $ cd flanc && ryu-manager refmon.py --refmon-config ~/endeavour/examples/test-mh/config/sdx_global.cfg
    
These steps should install the default flows (non matching packets are sent to 
the controller), in the respectives switches and tables.  

You can also try to run the uctrl module (Umbrella Control). 

    $ cd ~/endeavour
    $ python ./uctrl.py ~/endeavour/examples/test-mh/config/sdx_global.cfg

If you run it while the controller is running, you shall see on the controller the flows sent by uctrl. 