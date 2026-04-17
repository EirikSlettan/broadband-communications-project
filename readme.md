### Commands

sudo mn --custom topology/topo.py --topo diamondtopo --link tc --controller remote,ip=127.0.0.1,port=6633 --mac

./pox.py openflow.discovery predictive_lb --mode=predictive

## Testing

Start background traffic: mininet> h4 iperf -s &
mininet> h3 iperf -c 10.0.0.4 -t 30


## Congestion

h4 iperf -s &
h3 iperf -c 10.0.0.4 -t 30 &
h2 iperf -s &
h1 iperf -c 10.0.0.2 -t 20 -i 1


## Predictive traffic

h2 iperf -s &
h4 iperf -s -u &

h1 iperf -c 10.0.0.2 -t 40 -i 1 > predictive.txt &

h3 iperf -c 10.0.0.4 -u -b 1M -t 10 
# wait ~10 sec
h3 iperf -c 10.0.0.4 -u -b 2M -t 10 
# wait ~10 sec
h3 iperf -c 10.0.0.4 -u -b 3M -t 10


## Smooth ramping 

h2 iperf -s &
h4 iperf -s -u &

h1 iperf -c 10.0.0.2 -t 60 -i 1 > h1.txt &

h3 iperf -c 10.0.0.4 -u -b 1.5M -t 10
h3 iperf -c 10.0.0.4 -u -b 2.0M -t 10
h3 iperf -c 10.0.0.4 -u -b 3.5M -t 10
h3 iperf -c 10.0.0.4 -u -b 4.0M -t 10
h3 iperf -c 10.0.0.4 -u -b 5.5M -t 10
h3 iperf -c 10.0.0.4 -u -b 6.0M -t 10


## TCP smooth ramping

h2 iperf -s &
h4 iperf -s &

h1 iperf -c 10.0.0.2 -t 60 -i 1 > h1.txt &

h3 iperf -c 10.0.0.4 -t 10 -P 1
h3 iperf -c 10.0.0.4 -t 10 -P 2
h3 iperf -c 10.0.0.4 -t 10 -P 3
h3 iperf -c 10.0.0.4 -t 10 -P 4
h3 iperf -c 10.0.0.4 -t 10 -P 5
h3 iperf -c 10.0.0.4 -t 10 -P 6
