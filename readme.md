# Predictive Traffic Engineering in SDN

Project in EEE5138Z Broadband Communication Networks.

The goal is to compare static, reactive, and predictive routing under different traffic conditions.

## Overview

The network consists of a simple topology with two possible paths between hosts:

- Path A (shorter, lower delay)
- Path B (longer, higher delay)

One flow is treated as background traffic, while another is controlled by the SDN controller and can be rerouted.

The controller periodically collects port statistics and decides whether to switch paths.

## Modes

The controller supports three modes:

- **static**  
  Always uses Path A

- **reactive**  
  Switches path when current utilization exceeds a threshold

- **predictive**  
  Uses recent measurements to estimate future utilization and switches earlier

## How it works

- Port statistics are requested periodically from switches
- Link utilization is estimated from byte counters
- In predictive mode, a simple trend (last two samples) is used to estimate future load
- Only traffic between h1 and h2 is rerouted
- Background traffic (h3 ↔ h4) always stays on Path A

## Running

Start Mininet:

```bash
sudo mn --custom topo.py --topo diamondtopo --link tc \
  --controller remote,ip=127.0.0.1,port=6633 --mac
```

Run the controller

```bash
./pox.py openflow.discovery predictive_lb --mode=predictive

Other modes:
--mode=static
--mode=reactive
```
