RUN_DIR=~/endeavour
SDX_DIR=~/iSDX
RIBS_DIR=$SDX_DIR/xrs/ribs
TEST_DIR=$1
LOG_FILE=SDXLog.log

set -x

case $2 in
    (1)
        if [ ! -d $RIBS_DIR ]
        then
            mkdir $RIBS_DIR
        fi

        cd $SDX_DIR
        sh pctrl/clean.sh

        rm -f $LOG_FILE
        python logServer.py $LOG_FILE
        ;;

    (2)
        # the following gets around issues with vagrant direct mount
        cd ~
        sudo python $RUN_DIR/examples/$TEST_DIR/mininet/sdx_mininet.py $RUN_DIR/examples/$TEST_DIR/mininet/mininet.cfg $RUN_DIR/examples/$TEST_DIR/config/sdx_global.cfg

        #cd $SDX_DIR/examples/$TEST_DIR/mininext
        #sudo ./sdx_mininext.py
        ;;

    (3)
        cd $SDX_DIR/flanc
        ryu-manager ryu.app.ofctl_rest refmon.py --refmon-config $RUN_DIR/examples/$TEST_DIR/config/sdx_global.cfg &
        sleep 1

        cd $SDX_DIR/xctrl
        python xctrl.py $RUN_DIR/examples/$TEST_DIR/config/sdx_global.cfg

        cd $RUN_DIR/uctrl
        python uctrl.py $RUN_DIR/examples/$TEST_DIR/config/sdx_global.cfg

        cd $SDX_DIR/arproxy
        sudo python arproxy.py $RUN_DIR/examples/$TEST_DIR &
        sleep 1

        cd $SDX_DIR/xrs
        sudo python route_server.py $RUN_DIR/examples/$TEST_DIR &
        sleep 1

        cd $SDX_DIR/pctrl
        sudo python participant_controller.py $RUN_DIR/examples/$TEST_DIR 1 &
        sudo python participant_controller.py $RUN_DIR/examples/$TEST_DIR 2 &
        sudo python participant_controller.py $RUN_DIR/examples/$TEST_DIR 3 &
        sleep 1

        cd $SDX_DIR
        exabgp $RUN_DIR/examples/$TEST_DIR/config/bgp.conf
        ;;
esac
