import hashlib
import datetime
import json

# Merkle Tree Implementation
class MerkleTree:
    def __init__(self, transactions):
        self.transactions = transactions
        self.root = self.build_merkle_root()
    
    def build_merkle_root(self):
        if not self.transactions:
            return None
        
        # Convert transactions into hashed leaf nodes
        hashes = [self.hash_transaction(tx) for tx in self.transactions]
        
        # Build the tree bottom-up
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:  # If odd, duplicate the last hash
                hashes.append(hashes[-1])
            hashes = [self.hash_pair(hashes[i], hashes[i+1]) for i in range(0, len(hashes), 2)]
        
        return hashes[0]  # Root hash
    
    @staticmethod
    def hash_transaction(transaction):
        return hashlib.sha256(json.dumps(transaction.to_dict(), sort_keys=True).encode()).hexdigest()
    
    @staticmethod
    def hash_pair(hash1, hash2):
        return hashlib.sha256((hash1 + hash2).encode()).hexdigest()

# Transaction class to hold transaction data
class Transaction:
    def __init__(self, sender, receiver, amount, transaction_type):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.transaction_type = transaction_type
    
    def to_dict(self):
        return {"sender": self.sender, "receiver": self.receiver, "amount": self.amount}

# Block class using Merkle Trees
class Block:
    def __init__(self, transactions, previous_hash):
        self.timestamp = datetime.datetime.now()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.merkle_root = MerkleTree(transactions).root  # Calculate Merkle Root
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = f"{self.timestamp}{self.previous_hash}{self.merkle_root}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        while self.hash[:difficulty] != '0' * difficulty:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print("Block mined:", self.hash)

# Blockchain class
class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = []
        self.difficulty = 2
    
    def create_genesis_block(self):
        return Block([], "0")
    
    def get_latest_block(self):
        return self.chain[-1]
    
    def mine_block(self):
        if not self.pending_transactions:
            return "No transactions to mine"

        block = {
            "index": len(self.chain) + 1,
            "transactions": self.pending_transactions,
        }
        self.chain.append(block)
        self.pending_transactions = []  # Clear transactions after mining
        return block
    
    def add_transaction(self, transaction):
        if isinstance(transaction, Transaction):
            self.pending_transactions.append(transaction)
        else:
            print("Invalid transaction format!")
    
    def mine_pending_transactions(self):
        if not self.pending_transactions:
            print("No transactions to mine!")
            return
        
        new_block = Block(self.pending_transactions, self.get_latest_block().hash)
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        self.pending_transactions = []  # Clear pending transactions
    
    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Check if block hash is correct
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Check if Merkle Root is valid (detects transaction tampering)
            if current_block.merkle_root != MerkleTree(current_block.transactions).root:
                return False
            
            # Check if previous hash is correct
            if current_block.previous_hash != previous_block.hash:
                return False

        return True
