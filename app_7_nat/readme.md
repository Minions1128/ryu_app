""" this application implement NAT
    the topology needed is as follow:

             sw1-------sw2
            / | \       |
           /  |  \      |
          /   |   \     |
         h1   h2...h3   h4
    
    s1 is original switch, s2 is nat router
    h1, h2, h3 and h4 are 4 hosts
    only h1, h2 and h3 can ping h4 because of NAT
"""
