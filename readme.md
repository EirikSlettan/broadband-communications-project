### Commands

sudo mn --custom topology/topo.py --topo diamondtopo --link tc --controller remote,ip=127.0.0.1,port=6633 --mac

./pox.py openflow.discovery predictive_lb --mode=predictive

## Testing

Start background traffic: mininet> h4 iperf -s &
mininet> h3 iperf -c 10.0.0.4 -t 30

h2 iperf -s &
h1 iperf -c 10.0.0.2 -t 20 -i 1
h4 iperf -s &
h3 iperf -c 10.0.0.4 -t 30 &
