
if ! [ -d virtualenv ]
	then
		mkdir virtualenv
		virtualenv virtualenv/
	fi

source virtualenv/bin/activate

pip install -r utils/virtualenv.list
