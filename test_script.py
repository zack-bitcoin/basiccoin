wait_till_block 0
create_jury jury_id_abc
wait_till_block 1
create_jury jury_id_abc
wait_till_block 2
votecoin_spend 1 jury_id_abc 1234567890123456789012345678901234567890
votecoin_spend 2 jury_id_abc 01234567890123456789012345678901234567890
ask_decision jury_id_abc decision_id_1 text to put in decision
wait_till_block 4
vote_on_decision jury_id_abc decision_id_1 yes
wait_till_block 6
reveal_vote jury_id_abc decision_id_1
wait_till_block 8
info 0
info 1
info 2
info 3
info 4
info 5
info 6
info 7
info 8
 stop
