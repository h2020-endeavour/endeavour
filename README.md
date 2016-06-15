# ENDEAVOUR

This is the ENDEAVOUR platform, a Software-Defined eXchange being developed in the context of the Horizon 2020 EU-funded project [ENDEAVOUR: Towards a flexible software-defined network ecosystem](https://www.h2020-endeavour.eu/)

## Setup

At the moment, ENDEAVOUR runs within a Vagrant environment. Follow these simple instructions to set it up for yourself.

### Prerequisites

To get started install these softwares on your ```host``` machine:

1. Install ***Vagrant***, it is a wrapper around virtualization softwares like VirtualBox, VMWare etc.: http://www.vagrantup.com/downloads

2. Install ***VirtualBox***, this would be your VM provider: https://www.virtualbox.org/wiki/Downloads

3. Install ***Git***, it is a distributed version control system: https://git-scm.com/downloads

### Basics

* Clone the ```endeavour``` repository from GitHub:
```bash 
$ git clone https://github.com/endeavour/endeavour.git
```

* Change the directory to ```endeavour```:
```bash
$ cd endeavour
```

* Now run the vagrant up command. This will read the Vagrantfile from the current directory and provision the VM accordingly:
```bash
$ vagrant up
```

## Execution

### Access the VM

```bash
$ vagrant ssh
```

### Switch to the current development branch

ENDEAVOUR is built upon iSDX. We currently maintain our own development version of iSDX at https://github.com/h2020-endeavour/iSDX and develop the necessary extensions as feature branchs.
We currently have two extensions:
* mh-ctrlr - This branch introduces support for a multi-switch IXP fabric.
* mh-ctrlr_load_balancing - This branch introduces a load balancer function over the multi-switch IXP fabric.

```bash
$ cd ~/iSDX
$ git checkout mh-ctrlr
```

### Starting ENDEAVOUR

Run an example instance of the system. The example is based on the settings defined in the ```test-mh``` folder inside ```examples```. 

```bash
$ ~/endeavour/tm-launch.sh test-mh
```

The ```tm-launch.sh``` is a one-script solution to run the entire system.
If you need to run things manually, consider the following more detailed instructions.

### Step by step instructions to test the current code

Open a terminal and run the test topology:

    $ sudo python ~/endeavour/examples/test-mh/mininet/

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
