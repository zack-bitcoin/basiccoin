./reset.sh
cd user1
python workers.py &
cd ../user2
python workers.py &
cd ../user3
python workers.py &
cd ../user4
python workers.py &
cd ../user5
python workers.py

