learning 3 switch stp and 4 switch stp, which topology are 
   s1
  / \
s2 - s3

and

s1====s2
||    ||
s3====s4

respectively.

When using stplib.py to start the 4-switch topology, there will be some add-flow problems.
to add a eth_src parameter to solve this problem.
