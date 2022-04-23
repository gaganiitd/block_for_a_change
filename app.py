from flask import Flask, url_for, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import hashlib
import json
from time import time,sleep
from uuid import uuid4
from urllib.parse import urlparse
import qrcode
from qr_code import my_scanner
from email_user import email_the_user
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class BlockChain(object):
    """ Main BlockChain class """
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        # create the genesis block
        self.new_block(previous_hash=1, proof=100)

    @staticmethod
    def hash(block):
        # hashes a block
        # also make sure that the transactions are ordered otherwise we will have insonsistent hashes!
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def new_block(self, proof, previous_hash=None):
        # creates a new block in the blockchain
        block = {
            'index': len(self.chain)+1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block
    def register_miner_node(self, address):
        # add on the new miner node onto the list of nodes
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        return
    @property
    def last_block(self):
        # returns last block in the chain
        return self.chain[-1]

    def new_transaction(self, sender, recipient, amount):
        # adds a new transaction into the list of transactions
        # these transactions go into the next mined block
        self.current_transactions.append({
            "sender":sender,
            "recient":recipient,
            "data":amount,
        })
        return int(self.last_block['index'])+1

    def proof_of_work(self, last_proof):
        # simple proof of work algorithm
        # find a number p' such as hash(pp') containing leading 4 zeros where p is the previous p'
        # p is the previous proof and p' is the new proof
        proof = 0
        while self.validate_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def validate_proof(last_proof, proof):
        # validates the proof: does hash(last_proof, proof) contain 4 leading zeroes?
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, username, password):
        self.username = username
        self.password = password

blockchain = BlockChain()
node_identifier = str(uuid4()).replace('-', '')

@app.route('/', methods=['GET'])
def index():
    if session.get('logged_in'):
        return render_template('home.html')
    else:
        return render_template('index.html', message="Hello!")


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            db.session.add(User(username=request.form['username'], password=request.form['password']))
            db.session.commit()
            return redirect(url_for('login'))
        except:
            return render_template('index.html', message="User Already Exists")
    else:
        return render_template('register.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        u = request.form['username']
        p = request.form['password']
        data = User.query.filter_by(username=u, password=p).first()
        if data is not None:
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('index.html', message="Incorrect Details")

@app.route('/scan', methods=['GET','POST'])
def scanner():
    if session.get('logged_in'):
        data = my_scanner()
        response = {
            'chain': blockchain.chain,
            'length': len(blockchain.chain),
        }
        lst = response['chain']
        f_data = {}
        for i in range(len(lst)):
            if data == lst[i]['previous_hash']:
                f_data = lst[i]['transactions'][0]['data']
                #print(f_data)
            else:
                pass
        return render_template('user_data.html', message=f_data)
    else:
        return redirect(url_for('login'))

@app.route('/add', methods=['GET','POST'])
def add():
    if session.get('logged_in'):
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            address = request.form['address']
            dict = {}
            dict['name'] = name
            dict['email'] = email
            dict['address'] = address
            print(dict)
            last_block = blockchain.last_block
            last_proof = last_block['proof']
            proof = blockchain.proof_of_work(last_proof)
            blockchain.new_transaction(
                sender=0,
                recipient=node_identifier,
                amount=dict,
            )
            previous_hash = blockchain.hash(last_block)
            block = blockchain.new_block(proof, previous_hash)

            response = {
                'message': dict,
                'index': block['index'],
                'transactions': block['transactions'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
            }
            data = block['previous_hash']
            img = qrcode.make(data)
            f_name= block['previous_hash']+".png"
            img.save(f_name)
            sleep(3)
            email_the_user(email,f_name)
            print(jsonify(response,200))
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))

@app.route('/chain', methods=['GET'])
def full_chain():
    if session.get('logged_in'):
        response = {
            'chain': blockchain.chain,
            'length': len(blockchain.chain),
        }
        return jsonify(response), 200
    else:
        return redirect(url_for('login'))
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session['logged_in'] = False
    return redirect(url_for('index'))

if(__name__ == '__main__'):
    app.secret_key = "HelloWorld"
    db.create_all()
    app.run(port=8000)