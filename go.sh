./reset.sh
cd user1
python threads.py &
cd ../user2
python threads.py &
cd ../user3
python threads.py &
cd ../user4
python threads.py &
cd ../user5
python threads.py

