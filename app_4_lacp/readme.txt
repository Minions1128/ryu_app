app_4_lacp_v1.py implement lacp passive mode
app_4_lacp_v2.py implement lacp active and passive mode. 
    it start with first packet-in event -- active switch send lacpdu to passive switch.
    after severl times comnications, active switch and passive switch will build new lacp neighbor.
    when lacp switch received a packet send to lacp neighbor, it will choose load balance physical port to send.
