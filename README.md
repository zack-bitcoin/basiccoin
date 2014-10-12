Truthcoin-POW
=============

adding abilities from the truthcoin project to basiccoin. https://github.com/psztorc/Truthcoin

Donations: 1GbpRPE83Vjg73KFvTVZ4EnS2qNkiLY5TT

=====INSTALL 
for Ubuntu

    sudo apt-get update
    sudo apt-get install python-numpy git
    git clone https://github.com/zack-bitcoin/Truthcoin-POW.git
    cd Truthcoin-POW

for Arch Linux)

    sudo pacman -S python2-numpy python2-pip
    git clone https://github.com/zack-bitcoin/Truthcoin-POW.git
    cd Truthcoin-POW    

If you have trouble installing the dependencies in Arch Linux, you may want to update your mirror list with `reflector`.
    sudo pacman -S reflector
    reflector --verbose -l 200 -p http --sort rate --save /etc/pacman.d/mirrorlist

Be warned, **this will alter your system!** You may want to make a backup first.
    sudo cp /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.bk
    #do your thing...
    sudo mv /etc/pacman.d/mirrorlist.bk /etc/pacman.d/mirrorlist

====RUN A NODE

    ./threads.py

It will take time to download the blockchain.

====TALK TO THE NODE

    ./truthd.py



For now, there is a 20-block cycle.
1-10: votecoin-holders may give encrypted votes on decisions. (in the final version of truthcoin, this step will take 1000+ blocks)
11-15: votecoin-holders may decrypt their votes
16-20: if there are at least 3 votecoin-holders, and at least 5 decisions they have voted on, then we can do SVD to come to consensus about these decisions.



