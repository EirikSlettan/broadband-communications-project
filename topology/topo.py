from mininet.topo import Topo

class DiamondTopo(Topo):
    def build(self):
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        self.addLink(h1, s1, bw=10, delay='5ms')
        self.addLink(h2, s2, bw=10, delay='5ms')
        self.addLink(h3, s1, bw=10, delay='5ms')
        self.addLink(h4, s2, bw=10, delay='5ms')

        # Path A
        self.addLink(s1, s2, bw=5, delay='10ms')

        # Path B
        self.addLink(s1, s3, bw=5, delay='15ms')
        self.addLink(s3, s2, bw=5, delay='15ms')

topos = {'diamondtopo': DiamondTopo}