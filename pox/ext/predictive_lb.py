from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.recoco import Timer
from collections import defaultdict, deque
from pox.lib.addresses import EthAddr
import time

log = core.getLogger()

switches = {}
port_history = defaultdict(lambda: deque(maxlen=5))
current_util = defaultdict(float)

current_path = "A"
MODE = "predictive"
THRESHOLD_MBPS = 3.0

H1 = EthAddr("00:00:00:00:00:01")
H2 = EthAddr("00:00:00:00:00:02")
ARP_TYPE = 0x0806


def request_port_stats():
    for connection in switches.values():
        connection.send(of.ofp_stats_request(body=of.ofp_port_stats_request()))


def estimate_util(dpid, port, tx, rx):
    key = (dpid, port)
    now = time.time()
    hist = port_history[key]

    hist.append((now, tx, rx))

    if len(hist) < 2:
        return 0.0

    t1, tx1, rx1 = hist[-2]
    t2, tx2, rx2 = hist[-1]

    dt = t2 - t1
    if dt <= 0:
        return 0.0

    delta_bytes = (tx2 - tx1) + (rx2 - rx1)
    mbps = (delta_bytes * 8.0) / dt / 1_000_000.0
    current_util[key] = mbps
    return mbps


def predict_util(dpid, port):
    key = (dpid, port)
    hist = port_history[key]

    if len(hist) < 3:
        return current_util.get(key, 0.0)

    samples = []
    for i in range(1, len(hist)):
        t1, tx1, rx1 = hist[i - 1]
        t2, tx2, rx2 = hist[i]
        dt = t2 - t1
        if dt > 0:
            delta_bytes = (tx2 - tx1) + (rx2 - rx1)
            samples.append((delta_bytes * 8.0) / dt / 1_000_000.0)

    if len(samples) < 2:
        return samples[-1] if samples else 0.0

    return max(0.0, samples[-1] + (samples[-1] - samples[-2]))


def install_flow(conn, match, out_port, priority=100):
    msg = of.ofp_flow_mod()
    msg.priority = priority
    msg.match = match
    msg.actions.append(of.ofp_action_output(port=out_port))
    conn.send(msg)


def clear_flows():
    for c in switches.values():
        msg = of.ofp_flow_mod(command=of.OFPFC_DELETE)
        msg.match = of.ofp_match()
        c.send(msg)


def install_paths():
    clear_flows()

    s1 = switches.get(1)
    s2 = switches.get(2)
    s3 = switches.get(3)

    if not s1 or not s2:
        return

    if current_path == "A":
        # ---------- ICMP/unicast h1 -> h2 ----------
        install_flow(s1, of.ofp_match(dl_src=H1, dl_dst=H2), 3)
        install_flow(s2, of.ofp_match(dl_src=H1, dl_dst=H2), 1)

        # ---------- ICMP/unicast h2 -> h1 ----------
        install_flow(s2, of.ofp_match(dl_src=H2, dl_dst=H1), 3)
        install_flow(s1, of.ofp_match(dl_src=H2, dl_dst=H1), 1)

        # ---------- ARP request h1 -> h2 ----------
        # h1 sends ARP broadcast into s1 port 1
        install_flow(s1, of.ofp_match(dl_type=ARP_TYPE, in_port=1), 3)
        # same ARP broadcast arrives at s2 from s1 on port 3, forward to h2 on port 1
        install_flow(s2, of.ofp_match(dl_type=ARP_TYPE, in_port=3), 1)

        # ---------- ARP reply h2 -> h1 ----------
        install_flow(s2, of.ofp_match(dl_type=ARP_TYPE, dl_src=H2, dl_dst=H1), 3)
        install_flow(s1, of.ofp_match(dl_type=ARP_TYPE, dl_src=H2, dl_dst=H1), 1)

        log.info("Installed Path A: s1 -> s2")

    else:
        if not s3:
            return

        # ---------- ICMP/unicast h1 -> h2 ----------
        install_flow(s1, of.ofp_match(dl_src=H1, dl_dst=H2), 4)
        install_flow(s3, of.ofp_match(dl_src=H1, dl_dst=H2), 2)
        install_flow(s2, of.ofp_match(dl_src=H1, dl_dst=H2), 1)

        # ---------- ICMP/unicast h2 -> h1 ----------
        install_flow(s2, of.ofp_match(dl_src=H2, dl_dst=H1), 4)
        install_flow(s3, of.ofp_match(dl_src=H2, dl_dst=H1), 1)
        install_flow(s1, of.ofp_match(dl_src=H2, dl_dst=H1), 1)

        # ---------- ARP request h1 -> h2 ----------
        install_flow(s1, of.ofp_match(dl_type=ARP_TYPE, in_port=1), 4)
        install_flow(s3, of.ofp_match(dl_type=ARP_TYPE, in_port=1), 2)
        install_flow(s2, of.ofp_match(dl_type=ARP_TYPE, in_port=4), 1)

        # ---------- ARP reply h2 -> h1 ----------
        install_flow(s2, of.ofp_match(dl_type=ARP_TYPE, dl_src=H2, dl_dst=H1), 4)
        install_flow(s3, of.ofp_match(dl_type=ARP_TYPE, dl_src=H2, dl_dst=H1), 1)
        install_flow(s1, of.ofp_match(dl_type=ARP_TYPE, dl_src=H2, dl_dst=H1), 1)

        log.info("Installed Path B: s1 -> s3 -> s2")


def choose_path():
    global current_path

    # s1 port 3 = direct link to s2
    monitored = (1, 3)

    curr = current_util.get(monitored, 0.0)
    pred = predict_util(*monitored)

    if MODE == "static":
        new_path = "A"
    elif MODE == "reactive":
        new_path = "B" if curr > THRESHOLD_MBPS else "A"
    else:
        new_path = "B" if pred > THRESHOLD_MBPS else "A"

    if new_path != current_path:
        log.info(
            "Switching path from %s to %s (curr=%.3f Mbps, pred=%.3f Mbps)",
            current_path, new_path, curr, pred
        )
        current_path = new_path
        install_paths()


def _handle_ConnectionUp(event):
    switches[event.dpid] = event.connection
    log.info("Switch %s connected", event.dpid)

    if len(switches) >= 3:
        install_paths()


def _handle_PortStatsReceived(event):
    dpid = event.connection.dpid

    for stat in event.stats:
        if stat.port_no >= 65534:
            continue
        estimate_util(dpid, stat.port_no, stat.tx_bytes, stat.rx_bytes)

    choose_path()


def launch(mode="predictive", threshold="3.0"):
    global MODE, THRESHOLD_MBPS

    MODE = mode
    THRESHOLD_MBPS = float(threshold)

    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
    core.openflow.addListenerByName("PortStatsReceived", _handle_PortStatsReceived)

    Timer(1, request_port_stats, recurring=True)

    log.info("Started controller: mode=%s threshold=%.2f Mbps", MODE, THRESHOLD_MBPS)