#!/bin/bash

apt update;
apt -y install python3-pip;
pip3 install flask;
INSTANCE_ID=$(ec2metadata --instance-id);
python3 -c "
from flask import Flask

app = Flask(__name__)


@app.route('/')
@app.route('/cluster1')
@app.route('/cluster2')
def instance_id_res():
    return '"$INSTANCE_ID"'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
";