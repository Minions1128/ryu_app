echo "=dump-s1-groups============================================================================================================"
ovs-ofctl -O openflow13 dump-groups s1
#echo "=dump-s4-groups============================================================================================================"
#ovs-ofctl -O openflow13 dump-groups s4

echo "=dump-s1-flows============================================================================================================="
ovs-ofctl -O openflow13 dump-flows s1
echo "=dump-s2-flows============================================================================================================="
ovs-ofctl -O openflow13 dump-flows s2
echo "=dump-s3-flows============================================================================================================="
ovs-ofctl -O openflow13 dump-flows s3
echo "=dump-s4-flows============================================================================================================="
ovs-ofctl -O openflow13 dump-flows s4
echo "==========================================================================================================================="
